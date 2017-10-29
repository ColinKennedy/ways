#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Asset objects are objects that store per-instance data for Context objects.

They are necessary because Context objects are flyweights and, because of that,
cannot carry instance data.

Attibutes:
    ASSET_FACTORY (dict[tuple[str]: dict[str]]:
        This dict should not be messed with directly. You should use
        the functions provided in this module, instead.

        It is a global dictionary that stores classes that are meant to swap
        for an Asset object. ASSET_FACTORY's key is the hierarchy that a class
        will be applied to and its value is a dict that looks like this:

        'class': The class to swap for.
        'init': A custom inititialization function for the class (if needed).
        'children': If True, the class is used for all hierarchies that build
        off of the given hierarchy. If False, the class only applies to the
        given hierarchy.

'''

# IMPORT STANDARD LIBRARIES
import collections
import functools
import itertools
import os
import re

# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT LOCAL LIBRARIES
from . import situation as sit
from . import finder as find
from .core import compat
from . import common
from . import trace


__DEFAULT_OBJECT = object()
ASSET_FACTORY = dict()


class Asset(object):

    '''An object that contains a Context and data about the Context.

    The idea of this class is to keep Context information highly abstract,
    and let Context parse/use that information. Depending on what the Context
    is for, it could be used to ground the information to a filesystem or
    a database or some other structure that the Context knows about.

    '''

    def __init__(self, info, context=None, parse_type='regex'):
        '''Create the instance and store its info and Context.

        Note:
            It goes without saying that the keys in info must match all tokens
            in the Context (or at least all required tokens) to be valid.

        Args:
            info (dict or str):
                The information about this asset to store.
            context (:obj:`<sit.Context>`, optional):
                The context that this instance belongs to.
                If no Context is given, a Context is automatically assigned.
            parse_type (:obj:`str`, optional):
                The engine that will be used to used to check to make sure
                that a value is OK before setting it onto our parser.
                If no context is given, this engine is also used to try
                to resolve the info given to this asset. Default: 'regex'.

        '''
        super(Asset, self).__init__()
        self.parse_type = parse_type

        if context is None:
            # context = sit.find_context_from_info(info, parse_type=self.parse_type)
            raise NotImplementedError('Havent implemented an auto-find Context function yet')

        info = expand_info(info, context)

        self.info = info
        self.context = context

        missing_tokens = self.get_missing_required_tokens()
        if missing_tokens:
            raise ValueError(
                'Info: "{info}" could not resolve Context, "{context}". '
                'Info is missing tokens, "{keys}"'.format(
                    info=self.info, context=self.context, keys=missing_tokens))

    @property
    def actions(self):
        '''AssetFinder: The wrapped Find object.'''
        return AssetFinder(finder=find.Find(self.context), asset=self)

    def get_missing_required_tokens(self):
        '''Find any token that still needs to be filled for our parser.

        If a token is missing but it has child tokens and all of those tokens
        are defined, it is excluded from the final output. If the missing token
        is a child of some parent token that is defined, then the value of
        the token is parsed. If the parse is successful, the token is excluded
        from the final output.

        Returns:
            list[str]: Any tokens that have no value.

        '''
        parser = self.context.get_parser()
        required_tokens = parser.get_required_tokens()

        # Start filling the parser
        for key, value in six.iteritems(self.info):
            parser[key] = value

        # Get missing tokens
        missing_tokens = []
        for token in required_tokens:
            if token not in parser:
                missing_tokens.append(token)

        # Try to resolve the tokens
        # TODO : If I reverse the list, could I get away with not creating a
        #        copy? Check with unittests + do some profiling
        #
        #        Check after coverage
        #
        for token in list(missing_tokens):
            if self.get_value(token):
                missing_tokens.remove(token)

        return missing_tokens

    def get_str(self, required=True, force=False, *args, **kwargs):
        '''Get the full path to the asset, if any.

        Args:
            required (:obj:`bool`, optional):
                If True and there are tokens that are required that still
                are not, raise an error to keep this instance from returning.
                If False, return it even if not all required pieces were met.

                This variable is very useful if we want to make sure that this
                instance has all of the necessary pieces before calling this
                function. Default is True.
            force (:obj:`bool`, optional):
                If False, values are checked against their tokens
                before being set. If True, values are set for each token, even
                if they are not valid input for that token. Default is False.
            *args (list): Positional args to send to ContextParser.get_str.
            **kwargs (list): Keywords args to send to ContextParser.get_str.

        Raises:
            ValueError: If required is True (in other words, we assume that)

        Returns:
            str: The resolved string for this instance.

        '''
        parser = self.context.get_parser()

        for key, value in six.iteritems(self.info):
            parser[key] = value

        unfilled_tokens = []
        for token in self.get_unfilled_tokens():
            value = self.get_value(token)
            if not value:
                unfilled_tokens.append(token)

        required_tokens = parser.get_required_tokens()
        missing_required_tokens = set(required_tokens) & set(unfilled_tokens)

        if required and missing_required_tokens:
            raise ValueError('Required tokens: "{tokens}" must be filled. '
                             'Cannot retrieve path.'.format(
                                 tokens=sorted(missing_required_tokens)))

        return parser.get_str(*args, **kwargs)

    def get_token_parse(self, name, parse_type=''):
        '''Get the parse expression for some token name.

        Args:
            name (str):
                The name of the token to get parse details from.
            parse_type (:obj:`str`, optional):
                The engine type whose expression will be returned. If no
                parse_type is given, the stored parse_type is used.

        Returns:
            The parse expression used for the given token.

        '''
        if parse_type == '':
            parse_type = self.parse_type

        parser = self.context.get_parser()
        return parser.get_token_parse(name=name, parse_type=parse_type)

    def get_unfilled_tokens(self, required_only=False):
        '''Get the tokens in this instance that still don't have values.

        Args:
            required_only (:obj:`bool`, optional):
                If True, do not return optional tokens.
                If False, return all tokens, required and optional.
                Default is False.

        Returns:
            list[str]: The tokens that still need values.

        '''
        parser = self.context.get_parser()
        tokens = parser.get_tokens(required_only=required_only)

        for key, value in six.iteritems(self.info):
            if parser.is_valid(key, value):
                parser[key] = value

        unfilled_tokens = []
        for token in tokens:
            if token not in parser:
                unfilled_tokens.append(token)
        return unfilled_tokens

    def get_value(self, name, parse_type='regex'):
        '''Get some information about this asset, using a token-name.

        If the information is directly available, we return it. If it isn't
        though, it is searched for, using whatever information that we do have.

        If the token name is a child of another token that is defined, we
        use the parent token to "build" a value for the token that was requested.

        If the token name is a parent of some other tokens that all have values,
        we try to "build" it again, by composition of this child tokens.

        In both cases, the connection is very implicit. But it lets you do this:

        Example:
            >>> shot_info = {
            ...     'JOB': 'someJob',
            ...     'SCENE': 'SOMETHING',
            ...     'SHOT': 'sh0010'  # Pretend SHOT_NUMBER is a child of SHOT
            ... }
            >>> shot_asset = resource.Asset(shot_info, context='job/scene/shot')
            >>> shot_asset.get_value('SHOT_NUMBER')
            ... # Result: '0010'

        Args:
            name (str): The token to get the value of.

        Returns:
            str: The value at the given token.

        '''
        def get_value_from_parent(token, parser, details):
            '''Get the value of a token by looking up at its parent, recursively.

            In order for this function to return anything, the parent of token
            must be filled out. Or the parent of that parent etc etc.

            This function is very special because it is able to use a mixture
            of different text parsing engines to get the desired result.

            Args:
                token (str):
                    The token to get the value of, by looking at its parent(s).
                parser (<ways.api.ContextParser>):
                    The parser associated with the Context associated
                    with this Asset.
                details (dict[str: dict[str]]):
                    The mapping_details for our Context.

            Returns:
                str: The found value. Returns nothing if no value was found.

            '''
            def get_value_from_parent_parser(parent, value, parse_type):
                '''Use regex to get a value, using known parent tokens.

                Args:
                    parent (str):
                        The name of the parent token to try to get a
                        parse-value for.
                    value (str):
                        The value of the parent token.
                    parser_type (str):
                        The type of parser to use.
                        The parser associated with the Context which is
                        associated with this Asset instance.

                Returns:
                    dict[str]: The values that were found for each token
                               and each parent token.

                '''
                pattern = parser.get_token_parse(parent, parse_type=parse_type, groups=True)

                if not pattern:
                    return dict()

                value = _expand_using_parse_types(pattern, value)

                if not value:
                    return dict()

            def get_value_from_parent_format(parent, value, details):
                '''Try to expand the parent token, using its mapping.

                Note:
                    This function will basically always pass as long as
                    two things are true.
                    1. The mapping cannot have items side-by-side
                       Example:
                           valid - {FOO}_{BAR}
                           invalid - {FOO}{BAR}

                      If two items are back to back, we can't know where
                      one item starts and one item ends. We'd need regex
                      or glob or something else to determin that.
                    2. The value doesn't match the mapping.
                       Example:
                           valid -
                               mapping - {FOO}_{BAR}
                               value - SOME_THING
                           invalid -
                               mapping - {FOO}_{BAR}
                               value - SOME-THING

                Examples:
                    >>> parent = 'SHOT_NAME'
                    >>> value = 'SH_0020'
                    >>> details = {'SHOT_NAME': {'mapping': '{SHOT_PREFIX}_{SHOT_NUMBER}'}}
                    >>> get_value_from_parent_format(parent, value, details)
                    ... {'SHOT_PREFIX': 'SH', 'SHOT_NUMBER': '0020'}

                Args:
                    parent (str):
                        The parent token to expand and get the value of.
                    value (str):
                        The token to split into its pieces.
                    details (dict[str: dict[str]]):
                        The mapping_details for our Context.

                Returns:
                    dict[str: str]:
                        The pieces of a string, broken into its various pieces.

                '''
                mapping = details[parent].get('mapping', '')
                try:
                    return common.expand_string(mapping, value)
                except ValueError:
                    # If the value or mapping is malformated, fail silently
                    # so that the next option can be tried.
                    #
                    return ''

            parents = []
            for name in six.iterkeys(details):
                children = parser.get_child_tokens(name)

                if token in children:
                    parents.append(name)

            if not parents:
                return ''

            options = [
                functools.partial(get_value_from_parent_format, details=details),
                functools.partial(get_value_from_parent_parser, parse_type=parse_type),
            ]
            for parent in parents:
                try:
                    value = self.info[parent]
                except KeyError:
                    value = get_value_from_parent(parent, parser, details)

                for option in options:
                    parent_split_info = option(parent, value)
                    if parent_split_info:
                        return parent_split_info[token]

            return ''

        def get_value_from_children(token, parser, details):
            '''Get a value from a parent token by getting its child values.

            Args:
                token (str):
                    The token to get the value of by looking at its children.
                parser (<ways.api.ContextParser>):
                    The parser associated with the Context associated
                details (dict[str: dict[str]]):
                    The mapping_details for our Context.

            Returns:
                dict[str: str]: The found tokens and their values.

            '''
            mapping = details.get(token, dict()).get('mapping', '')
            if not mapping:
                return ''

            children = parser.get_child_tokens(token)
            if not children:
                return ''

            info = dict()

            for child in children:
                try:
                    value = self.info[child]
                except KeyError:
                    value = get_value_from_children(child, parser, details)

                info[child] = value

            return mapping.format(**info)

        try:
            # If we have a direct value for the given name, return it
            return self.info[name]
        except KeyError:
            pass

        parser = self.context.get_parser()
        details = parser.get_all_mapping_details()

        value = get_value_from_parent(name, parser, details)
        if value:
            return value

        # TODO : swap Parent-Search and Child-Search. More often than not,
        #        it will make systems faster (I think)
        #
        return get_value_from_children(name, parser, details)

    def set_value(self, key, value, force=False):
        '''Store the given value to some key.

        Args:
            key (str): The token that our value will be stored into.
            value (str): The value to store.
            force (:obj:`bool`, optional):
                If False, values are checked against their tokens
                before being set. If True, values are set for each token, even
                if they are not valid input for that token. Default is False.

        '''
        parser = self.context.get_parser()

        if (not force and parser.is_valid(key, value)) or force:
            self.info[key] = value

    def __eq__(self, other):
        '''bool: If the two Asset objects have the same data stored.'''
        return isinstance(other, self.__class__) and self.info == other.info

    def __repr__(self):
        '''str: A printout of the current class and its properties.'''
        return '{cls_}(info={info}, context={context}, parse_type={parse!r})' \
               ''.format(cls_=self.__class__.__name__,
                         info=self.info,
                         context=self.context,
                         parse=self.parse_type)


# TODO : Could I possibly do this without a class?
# TODO : The name of this class doesn't match find.Find. FIXME
#
class AssetFinder(compat.DirMixIn, object):

    '''A class that wraps a Find class with the current asset.

    Ways Action objects don't assume anything about their input. This
    is normally a good thing because it keeps Actions flexible.
    But if we're working with an Action that expects an Asset object, we'd
    have to do this all the time:

    Example:
        >>> asset = resource.get_asset({'info': 'here'}, context='some/context')
        >>> output = asset.context.actions.get_foo(action, some='other', args=4)

    Gross, right?

    So instead what we do is add AssetFinder as an 'actions' property and
    then forcefully pass the Asset as the first argument to Actions.

    Example:
        >>> asset = resource.get_asset({'info': 'here'}, context='some/context')
        >>> output = asset.actions.get_foo(some='other', args=4)

    That's much better.

    '''

    def __init__(self, finder, asset):
        '''Create the instance and store a Find and an Asset object.

        Args:
            finder (<find.Find>): The Find object to get actions from.
            asset (<resource.Asset>): The asset to pass into every function.

        '''
        super(AssetFinder, self).__init__()
        self._finder = finder
        self._asset = asset

    def __getattr__(self, name):
        '''Try to pass missing calls to the stored Context's actions.

        Returns:
            callable: The function for the given name.

        '''
        def add_asset_info_to_function(func, asset):
            '''Pass the given asset to our original function.

            Args:
                func (callable):
                    The function to call. It must take at least one arg and
                    the first arg must take an Asset object.

            '''
            def function(*args, **kwargs):
                '''Run the original function but with an Asset added to it.'''
                return func(asset, *args, **kwargs)

            function.__doc__ = func.__doc__

            return function

        function = self._finder.__getattr__(name)

        return add_asset_info_to_function(func=function, asset=self._asset)

    def __dir__(self):
        '''list[str]: Add Action names to the list of return items.'''
        return sorted(
            set(itertools.chain(
                self.__dict__.keys(),
                trace.trace_action_names(self._finder.context),
                super(AssetFinder, self).__dir__())))


def get_asset(info, context=None, *args, **kwargs):
    '''Get some class object that matches the given Context and wraps some info.

    Args:
        info (dict[str] or str):
            The info to expand. If the input is a dict, it is passed through
            and returned. If it is a string, the string is parsed against the
            given context.
        context (:obj:`<sit.Context> or str or tuple[str]`, optional):
            The Context to use for the asset. If a string is given, it is
            assumed to be the Context's hierarchy and a Context object
            is constructed.
        *args (list): Optional position variables to pass to our found
                      class's constructor.
        **kwargs (list): Optional keyword variables to pass to our found
                         class's constructor.

    Raises:
        NotImplementedError:
            If context is None. There's no auto-find-context option yet.

    Returns:
        The found class object or NoneType. If no class definition was found
        for the given Context, return a generic Asset object.

    '''
    if context is None:
        raise NotImplementedError('Havent implemented an auto-find Context function yet')

    context = sit.get_context(context)
    info = expand_info(info, context=context)
    context_hierarchy = context.get_hierarchy()

    class_type = Asset  # Asset is our fallback if no other type was defined.
    init = functools.partial(make_default_init, class_type)

    # Try to find a class type from one of our parent hierarchies
    for index in reversed(range(len(context_hierarchy) + 1)):
        # We use len - 1 because we already
        hierarchy = tuple(context_hierarchy[:index])

        hierarchy_info = ASSET_FACTORY.get(hierarchy, dict())

        try:
            class_type_ = ASSET_FACTORY[hierarchy]['class']
            init_ = ASSET_FACTORY[hierarchy]['init']
        except KeyError:
            continue

        if hierarchy == context_hierarchy or hierarchy_info.get('children', False):
            class_type = class_type_
            init = init_

    try:
        return init(info, context, *args, **kwargs)
    except Exception:
        return


def expand_info(info, context=None):
    '''Get parsed information, using the given Context.

    Note:
        This function requires regex in order to parse.

    Todo:
        Maybe I can abstract the parser to use different parse options, like I
        did in get_value_from_parent. And then if that doesn't work, I can
        add the option to "register" a particular parser.

    Args:
        info (dict[str] or str):
            The info to expand. If the input is a dict, it is passed through
            and returned. If it is a string, the string is parsed against the
            given context.
        context (:obj:`<sit.Context>`, optional):
            The Context that will be used to parse info.
            If no Context is given, the Context is automatically found.
            Default is None.

    Raises:
        NotImplementedError:
            If context is None. There's no auto-find-context option yet.

    Returns:
        dict[str]: The asset info.

    '''
    if context is None:
        raise NotImplementedError('Havent implemented an auto-find Context function yet')

    # Is already a dict
    if isinstance(info, dict):
        return info

    # Context is probably a string like '/jobs/jobName/here'. If that's the case
    # then we'll expand it into a dict by using a Context's mapping.
    #
    # i.e. path is '/jobs/jobName/here'
    #      context mapping is '/jobs/{JOB}/here'
    #      Result: {'JOB': 'jobName'}
    #
    try:
        return _expand_using_context(context, info, default=dict())
    except AttributeError:
        pass

    # Is it an iterable-pair object that we can make into a dict?
    # i.e. (('some': 'thing'), ) -> {'some': 'thing'}
    #
    try:
        return dict(info)
    except TypeError:
        pass


def _get_expand_choices():
    '''Get a description of each registered parse type and how it creates a dict.

    An example implmentation for regex would be
    {'regex': lambda pat, text: re.match(pat, text).groupdict()}.

    As long as the parse type can return a dict, given some text, it's valid.

    Returns:
        <collections.OrderedDict[str: callable]:
            The parse type and expansion function.

    '''
    # TODO : Make an abstract registry for "expansion" parse_types ?
    choices = collections.OrderedDict()

    def regex_groupdict(pattern, text):
        '''Get a dictionary of named keys for each text match, in pattern.'''
        match = re.match(pattern, text)

        try:
            return match.groupdict()
        except AttributeError:
            return dict()

    choices['default'] = common.expand_string
    choices['regex'] = regex_groupdict

    return choices


def _get_expand_order(order=None):
    '''Get the parse-order that Ways will use to expand a str into a dict.

    This order is defined by the WAYS_EXPAND_CHOICE_ORDER
    environment variable or, if that variable doesn't contain anything,
    the order that parsers were registered will be used, instead.

    Args:
        order (:obj:`list[str]`, optional):
            If this argument has a value, then it is simply returned.
            If it doesn't have a value, we try to get the value from
            the current environment settings. If we can't, we use
            the order of parse-type registration.

    Returns:
        list[str]:
            The order for Ways to use to expand strings.

    '''
    # TODO : It's a bit presumptuous to assume that we know what order people
    #        would like to parse a string. Maybe make a better system than
    #        just forcing the user to use the keys from _get_expand_choices ...
    #
    if order is not None:
        return order

    environment = os.getenv('WAYS_EXPAND_CHOICE_ORDER', '')

    if environment:
        order = environment.split(os.pathsep)
    else:
        order = _get_expand_choices().keys()

    return order


def _expand_using_context(context, text, choices=None, default=__DEFAULT_OBJECT):
    '''Expand some text into a dictionary of information, using a Context.

    Args:
        context (<ways.api.Context>):
            The Context to get parse text for and then use.
        text (str):
            The text to expand.
        choices (:obj:`dict[str: callable]`, optional):
            The parse type and associated function for that parse type that
            should be used to convert a Context into a pattern which we can
            apply to our text. If no choices are given, some default choices
            are given for you.
        default:
            The object to return if nothing is found.

    Returns:
        dict or default:
            The expanded items, if any option in order was successful.
            If no function was successful,
            it returns whatever the default value was.

    '''
    order = _get_expand_order()

    if choices is None:
        choices = _get_expand_choices()

    if default == __DEFAULT_OBJECT:
        default = dict()

    # TODO : register these keys/values as plugins or something?
    pattern_getter = collections.OrderedDict()
    pattern_getter['default'] = functools.partial(context.get_str, display_tokens=True)
    pattern_getter['regex'] = functools.partial(context.get_str, resolve_with=('regex', ), display_tokens=True)

    for key in order:
        getter = pattern_getter.get(key, lambda: None)
        pattern = getter()
        if pattern:
            value = _expand_using_parse_types(
                parse=pattern, text=text, choices=choices, default=default)

            if value:
                return value

    return default


def _expand_using_parse_types(parse, text, choices=None, default=__DEFAULT_OBJECT):
    '''Expand some text, using a parse string of some kind.

    We say "some kind" because the parse string could be a Python format string
    or a regex pattern, for example.

    Args:
        context (<ways.api.Context>):
            The Context to get parse text for and then use.
        text (str):
            The text to expand.
        choices (:obj:`dict[str: callable]`, optional):
            The parse type and associated function for that parse type that
            should be used to convert text into a string. If no choices
            are given, some default choices are given for you.
        default:
            The object to return if nothing is found.

    Returns:
        dict or default:
            The expanded items, if any option in order was successful.
            If no function was successful,
            it returns whatever the default value was.

    '''
    order = _get_expand_order()

    if choices is None:
        choices = _get_expand_choices()

    if default == __DEFAULT_OBJECT:
        default = dict()

    for choice in order:
        value = choices[choice](parse, text)

        if value:
            break

    if not value:
        value = default

    return value


def register_asset_class(class_type, context, init=None, children=False):
    '''Change get_asset to return a different class, instead of an Asset.

    The Asset class is useful but it may be too basic for some people's purposes.
    If you have an existing class that you'd like to use with Ways,

    Args:
        class_type (classobj):
            The new class to use, instead.
        context (str or <sit.Context>):
            The Context to apply our new class to.
        init (:obj:`callable`, optional):
            A function that will be used to create an instance of class_type.
            This variable is useful if you need to customize your class_type's
            __init__ in a way that isn't normal (A common example: If you want
            to create a class_type that does not pass context into its __init__,
            you can use this variable to catch and handle that).
        children (:obj:`bool`, optional):
            If True, this new class_type will be applied to child hierarchies
            as well as the given Context's hierarchy. If False, it will only be
            applied for this Context. Default is False.

    '''
    if init is None:
        init = functools.partial(make_default_init, class_type)

    context = sit.get_context(context, force=True)

    ASSET_FACTORY[context.get_hierarchy()] = dict()
    ASSET_FACTORY[context.get_hierarchy()]['class'] = class_type
    ASSET_FACTORY[context.get_hierarchy()]['init'] = init
    ASSET_FACTORY[context.get_hierarchy()]['children'] = children


def make_default_init(class_type, *args, **kwargs):
    '''Just make the class type, normally.'''
    return class_type(*args, **kwargs)


def reset_asset_classes(hierarchies=tuple()):
    '''Clear out the class(es) that is registered under a given hierarchy.

    Args:
        hierarchies (iter[tuple[str]]):
            All of the hierarchies to remove custom Asset classes for.
            If nothing is given, all hierarchies will be cleared.

    '''
    if not hierarchies:
        hierarchies = ASSET_FACTORY.keys()

    for key in hierarchies:
        if key not in ASSET_FACTORY:
            continue

        # Reset the key
        ASSET_FACTORY[key] = ASSET_FACTORY[key].__class__()


if __name__ == '__main__':
    print(__doc__)

