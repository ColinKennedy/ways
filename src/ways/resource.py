#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=too-many-lines
'''Asset objects are objects that store per-instance data for Context objects.

They are necessary because Context objects are flyweights and, because of that,
cannot carry instance data.

Attributes:
    ASSET_FACTORY (dict[tuple[str]: dict[str]]:
        This dict should not be changed directly. You should use
        the functions in this module, instead.

        It is a global dictionary that stores classes that are meant to swap
        for an Asset object. ASSET_FACTORY's key is the hierarchy of the Context
        and its value is another dict, which looks like this:

        'class': The class to swap for.
        'init': A custom inititialization function for the class (if needed).
        'children': If True, the class is used for all hierarchies that build
        off of the given hierarchy. If False, the class is only added to the
        given hierarchy.

'''


# IMPORT STANDARD LIBRARIES
# scspell-id: 3c62e4aa-c280-11e7-be2b-382c4ac59cfd
import os
import re
import ast
import functools
import itertools
import collections

# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT WAYS LIBRARIES
import ways

# IMPORT LOCAL LIBRARIES
from . import pylev
from . import trace
from . import common
from . import finder as find
from . import situation as sit
from .core import check
from .core import compat

__DEFAULT_OBJECT = object()
ASSET_FACTORY = dict()


class Asset(object):

    '''An object that contains a Context and data about the Context.

    The idea of this class is to keep Context information abstract,
    and let Context parse/use that information. Depending on what the Context
    is for, it could be used to ground the information to a filesystem or
    a database or some other structure that the Context knows about.

    '''

    def __init__(self, info, context, parse_type='regex'):
        '''Create the instance and store its info and Context.

        Note:
            Keys in info must match all tokens in the Context
            (or at least all required tokens) or the Context will fail to
            initialize.

        Args:
            info (dict or str):
                The information about this asset to store.
            context (ways.api.Context):
                The context that this instance points to.
            parse_type (:obj:`str`, optional):
                The engine that will be used to used to check to make sure
                that a value is OK before it is set on this instance.

        Raises:
            ValueError:
                If the information could not be found from a string or
                if one or more of this Asset's tokens were not filled by
                the information that was found.

        '''
        super(Asset, self).__init__()
        self.parse_type = parse_type

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

        If a token is missing but it has child tokens and all of the child
        tokens are defined, it is excluded from the final output. If
        the missing token is a child of some parent token that is defined,
        then the value of the token is parsed. If the parse is successful,
        the token is excluded from the final output.

        Returns:
            list[str]: Any tokens that have no value.

        '''
        return _get_missing_required_tokens(context=self.context, info=self.info)

    def get_str(self, required=True, *args, **kwargs):
        '''Get the full path to the asset, if any.

        Args:
            required (:obj:`bool`, optional):
                If True and there are tokens that are required that still
                are not filled, raise an error.  If False, return the
                incomplete string.  Default is True.
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

        return [token for token in tokens if token not in self.info]

    def get_value(self, name, real=False):
        '''Get some information about this asset, using a token-name.

        If the information is directly available, we return it. If it isn't
        though, it is searched for, using whatever information that we do have.

        If the token name is a child of another token that is defined, we
        use the parent token to "build" a value for the token that was requested.

        If the token name is a parent of some other tokens that all have values,
        we try to "build" it again, by combining all of the child tokens.

        In both cases, the return value is created but not defined.
        But it lets you do this:

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
            real (:obj:`bool`, optional):
                If True, the original parsed value is returned. If False and
                the given token has functions defined in "before_return" then
                those functions will process the output and then return it.
                Default is False.

        Returns:
            The value at the given token.

        '''
        # Create a parser and fill it up with all of the info we can
        # so that we can use it using Parent-Search and Child-Search
        #
        parser = self.context.get_parser()
        for key, value in six.iteritems(self.info):
            parser[key] = value

        details = parser.get_all_mapping_details()
        value = self._get_value(name, parser)

        if real:
            return value

        # Modify the value before it is returned to the user, if they say to
        before_return = check.force_itertype(
            details.get(name, dict()).get('before_return', []))

        for function in before_return:
            # TODO : change with something better
            try:
                function = common.import_object(function)
            except ImportError:
                pass
            else:
                value = function(value)
                continue

            try:
                value = ast.literal_eval(
                    '{function}({value})'.format(function=function, value=value))
                # literal_eval will raise ValueError if the string has syntax errors
            except (ValueError, NameError):
                try:
                    # TODO : Remove this eval
                    # pylint: disable=eval-used
                    value = eval('{function}({value})'.format(function=function, value=value))
                except NameError:
                    # NameError will happen if the function is not importable
                    raise ValueError('Function: "{func}" could not be run'.format(func=function))

        return value

    def _get_value(self, name, parser):
        '''Get some information about this asset, using a token-name.

        If the information is directly available, we return it. If it isn't
        though, it is searched for, using whatever information that we do have.

        If the token name is a child of another token that is defined, we
        use the parent token to "build" a value for the token that was requested.

        If the token name is a parent of some other tokens that all have values,
        we try to "build" it again, by combining all of the child tokens.

        In both cases, the return value is created but not defined.
        But it lets you do this:

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
            parser (:class:`ways.api.ContextParser`, optional):
                The parse that contains the information about our Context
                and Asset.

        Returns:
            str: The value at the given token.

        '''
        return _get_value(name, parser, self.info)

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
# pylint: disable=too-few-public-methods
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
            finder (:class:`ways.api.Find`): The object to get actions from.
            asset (:class:`ways.api.Asset`): The object to pass to every function.

        '''
        super(AssetFinder, self).__init__()
        self.finder = finder
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

        function = self.finder.__getattr__(name)

        # Finder returns a functools.partial. So we'll unpack it by getting
        # ".func" and then insert our own Asset object into it, instead
        #
        function = function.func

        return add_asset_info_to_function(func=function, asset=self._asset)

    def __dir__(self):
        '''list[str]: Add Action names to the list of return items.'''
        return sorted(
            set(itertools.chain(
                self.__dict__.keys(),
                trace.trace_action_names(self.finder.context),
                super(AssetFinder, self).__dir__())))


def _expand_using_context(context, text, choices=None, default=__DEFAULT_OBJECT):
    '''Expand some text into a dictionary of information, using a Context.

    Args:
        context (:class:`ways.api.Context`):
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
    pattern_getter['regex'] = functools.partial(
        context.get_str, resolve_with=('regex', ), display_tokens=True)

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
        context (:class:`ways.api.Context`):
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


def _get_expand_choices():
    '''Get a description of each registered parse type and how it creates a dict.

    An example implmentation for regex would be
    {'regex': lambda pat, text: re.match(pat, text).groupdict()}.

    As long as the parse type can return a dict, given some text, it's valid.

    Returns:
        <collections.OrderedDict>[str: callable]:
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


def _get_recursive_parents(token, parser):
    '''Get every known parent token for some token and those parent's parents.

    Args:
        token (str):
            The token to start retrieving parent tokens from.
        parser (:class:`ways.api.ContextParser`):
            The parser to use to get parent tokens.

    Returns:
        list[str]: The found parent tokens.

    '''
    def _yield_parent_details(token, parser, details):
        '''Yield parent tokens for a given token, by looking at a token's details.

        This function exists just so that we don't have to call
        parser.get_all_mapping_details() for each iteration. This makes the
        call slightly more efficient.

        '''
        for parent in six.iterkeys(details):
            if parent == token:
                # A token shouldn't ever be a child of itself so we can skip it
                continue

            children = parser.get_child_tokens(parent)

            if token in children:
                yield parent

                for parent_ in _yield_parent_details(parent, parser, details):
                    yield parent_

    details = parser.get_all_mapping_details()
    return list(_yield_parent_details(token, parser, details))


def get_asset(info, context=None, *args, **kwargs):
    '''Get some class object that matches the given Context and wraps some info.

    Args:
        info (dict[str] or str):
            The info to expand. If the input is a dict, it is passed through
            and returned. If it is a string, the string is parsed against the
            given context. Generally speaking, it's better to give a string that
            is an exact or partial match to a Context's mapping than it is to
            give a dict. This is doubly true if no context is given.
        context (:class:`ways.api.Context` or str or tuple[str]`, optional):
            The Context to use for the asset. If a string is given, it is
            assumed to be the Context's hierarchy and a Context object
            is constructed. If nothing is given, the best possible Context
            is "found" and tried. This auto-find process is not guaranteed.
            Default is None.
        *args (list): Optional position variables to pass to our found
                      class's constructor.
        **kwargs (dict): Optional keyword variables to pass to our found
                         class's constructor.

    Raises:
        NotImplementedError:
            If context is None. There's no auto-find-context option yet.

    Returns:
        The found class object or NoneType. If no class definition was found
        for the given Context, return a generic Asset object.

    '''
    if not context:
        context = _find_context_using_info(info)
        if context is None:
            raise ValueError('Context could not be found for info, "{info}".'.format(info=info))
    else:
        context = sit.get_context(context)

    info = expand_info(info, context=context)
    hierarchy = context.get_hierarchy()

    _, init = get_asset_info(hierarchy)

    try:
        return init(info, context, *args, **kwargs)
    except Exception:
        return


def get_asset_class(hierarchy):
    '''Get the class that is registered for a Context hierarchy.'''
    return get_asset_info(hierarchy)[0]


def get_asset_info(hierarchy):
    '''Get the class and initialization function for a Context hierarchy.

    Args:
        hierarchy (tuple[str] or str):
            The hierarchy to get the asset information of.

    Returns:
        tuple[classobj, callable]:
            The class type and the function that is used to instantiate it.

    '''
    class_type = Asset  # Asset is our fallback if no other type was defined.
    init = functools.partial(make_default_init, class_type)

    # Try to find a class type from one of our parent hierarchies
    for index in reversed(range(len(hierarchy) + 1)):
        hierarchy_piece = tuple(hierarchy[:index])

        hierarchy_info = ASSET_FACTORY.get(hierarchy_piece, dict())

        try:
            class_type_ = ASSET_FACTORY[hierarchy_piece]['class']
            init_ = ASSET_FACTORY[hierarchy_piece]['init']
        except KeyError:
            continue

        if hierarchy_piece == hierarchy or hierarchy_info.get('children', False):
            class_type = class_type_
            init = init_
            break

    return (class_type, init)


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
        return dict()


def _get_missing_required_tokens(context, info):
    '''Find any token that still needs to be filled for our parser.

    If a token is missing but it has child tokens and all of those tokens
    are defined, it is excluded from the final output. If the missing token
    is a child of some parent token that is defined, then the value of
    the token is parsed. If the parse is successful, the token is excluded
    from the final output.

    Args:
        context (:class:`ways.api.Context`):
            The Context to use to get missing tokens.
        info (dict[str: str]):
            Token-value pairs that should match 1-to-1 with Context.

    Returns:
        list[str]:
            Any tokens that have no value.

    '''
    parser = context.get_parser()
    required_tokens = parser.get_required_tokens()

    # Start filling the parser
    for key, value in six.iteritems(info):
        parser[key] = value

    # Get missing tokens
    missing_tokens = []
    for token in required_tokens:
        if token not in parser:
            missing_tokens.append(token)

    # Try to resolve the tokens
    # TODO : If I reverse the list, could I get away with not creating a
    #        copy of missing_tokens? Check with unittests + do some profiling
    #
    #        Check after coverage
    #
    for token in list(missing_tokens):
        value = _get_value(token, parser=parser, info=info)
        if value:
            parser[token] = value
            missing_tokens.remove(token)

    return missing_tokens


def _get_value(name, parser, info):
    '''Get some information about this asset, using a token-name.

    If the information is directly available, we return it. If it isn't
    though, it is searched for, using whatever information that we do have.

    If the token name is a child of another token that is defined, we
    use the parent token to "build" a value for the token that was requested.

    If the token name is a parent of some other tokens that all have values,
    we try to "build" it again, by combining all of the child tokens.

    In both cases, the return value is created but not defined.
    But it lets you do this:

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
        parser (:class:`ways.api.ContextParser`, optional):
            The parse that contains the information about our Context
            and Asset.
        info (dict[str: str]):
            All of the token-value pairs to use to find a value.

    Returns:
        str: The value at the given token.

    '''
    def get_value_from_parent(token, parser, info):
        '''Get the value of a token by looking up at its parent, recursively.

        In order for this function to return anything, the parent of token
        must be filled out. Or the parent of that parent etc etc.

        This function is very special because it is able to use a mixture
        of different text parsing engines to get the desired result.

        Args:
            token (str):
                The token to get the value of, by looking at its parent(s).
            parser (:class:`ways.api.ContextParser`):
                The parser associated with the Context associated
                with this Asset.
            info (dict[str: str]):
                All of the token-value pairs to use to find a value.

        Returns:
            str: The found value. Returns nothing if no value was found.

        '''
        def get_value_from_parent_regex(parent):
            '''Use regex to get a value, using known parent tokens.

            Args:
                parent (str):
                    The name of the parent token to try to get a
                    parse-value for.

            Returns:
                dict[str]: The values that were found for each token
                            and each parent token.

            '''
            details = parser.get_all_mapping_details()
            try:
                # We must have a mapping to proceed
                details[parent]['mapping']
            except KeyError:
                return dict()

            info = dict()
            for child in parser.get_child_tokens(parent):
                value = parser.get_value_from_parent(child, parent, 'regex')
                info[child] = value

            return info

        def get_value_from_parent_format(parent):
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

            Returns:
                dict[str: str]:
                    The pieces of a string, broken into its various pieces.

            '''
            details = parser.get_all_mapping_details()
            try:
                value = parser[parent]
                return common.expand_string(details[parent].get('mapping', ''), value)
            except KeyError:
                return dict()

        # Try once to get the value if the parser already has it
        # If not, we'll try to search for it
        #
        try:
            return parser[token]
        except KeyError:
            pass

        parents = _get_recursive_parents(token, parser)

        if not parents:
            return ''

        def build_value_from_parents(token, parents, info):
            '''Get the value by checking every parent of a token recursively.

            Warning:
                This function will modify any parser that is passed into it.
                The parser is changed intentionally so that the value
                can be referenced during recursion (It's treated as
                persistent data that gets reused).

            Args:
                token (str):
                    The token to get the value of by looking at its parents.
                parents (list[str]):
                    The parents of token and any parents of those parents.
                    This list should always start with the immediate parent
                    of token, followed by other parents-of-parents.
                info (dict[str: str]):
                    All of the token-value pairs to use to find a value.

            Returns:
                str: The output value.

            '''
            options = [
                get_value_from_parent_format,
                get_value_from_parent_regex,
            ]

            for parent in parents:
                value = ''
                try:
                    value = info[parent]
                except KeyError:
                    pass

                for option in options:
                    try:
                        info = option(parent)
                        value = info.get(token)
                        if value:
                            return value
                    except Exception:
                        pass

                try:
                    parents[1:]
                except IndexError:
                    return ''

                # If we've reached this point, it means that we tried to get
                # the value of the parent be couldn't. But there's another
                # parent above this parent token so lets keep searching
                # until there's no more parents to search
                #
                value = build_value_from_parents(parent, parents[1:], info)
                if value:
                    # NOTE: We intentionally add the found value to a parser
                    #       before retrying to hopefully find the next value
                    #       faster / more efficiently
                    #
                    parser[parent] = value
                    return _get_value(token, parser=parser, info=info)

        return build_value_from_parents(token, parents, info)

    def get_value_from_children(token, parser, info):
        '''Get a value from a parent token by getting its child values.

        Args:
            token (str):
                The token to get the value of by looking at its children.
            parser (:class:`ways.api.ContextParser`):
                The parser associated with the Context associated
            info (dict[str: str]):
                All of the token-value pairs to use to find a value.

        Returns:
            dict[str: str]: The found tokens and their values.

        '''
        mapping = details.get(token, dict()).get('mapping', '')
        if not mapping:
            return ''

        children = parser.get_child_tokens(token)
        if not children:
            return ''

        info_ = dict()

        for child in children:
            try:
                value = info[child]
            except KeyError:
                value = get_value_from_children(child, parser, info)

            info_[child] = value

        return mapping.format(**info_)

    try:
        # If we have a direct value for the given name, return it
        return info[name]
    except KeyError:
        pass

    details = parser.get_all_mapping_details()

    value = get_value_from_parent(name, parser, info)
    if value:
        return value

    # TODO : swap Parent-Search and Child-Search. More often than not,
    #        it will make systems faster (I think)
    #
    return get_value_from_children(name, parser, info)


# pylint: disable=too-many-branches,too-many-locals
def _find_context_using_info(obj):
    '''Use some Asset's info, get the best-possible Context.

    This function is meant to assist "get_asset" whenever a Context is not given.

    Args:
        obj (dict[str: str] or str):
            The information used to get the Context.
            It's best to give a string whenever possible but a dict can be
            used instead, if not.

    Returns:
        <ways.api.Context>: The "best-guess" Context for some information.

    '''
    def contains_all_tokens(context, obj):
        '''Check that every token in a Context has a vaild value.

        Args:
            context (:class:`ways.api.Context`):
                The Context to check for valid token values.
            obj (dict[str: str]):
                The token-value pairs for our Context to check if they're valid.

        Returns:
            bool: If every token for our Context has a valid value.

        '''
        parser = context.get_parser()
        details = parser.get_all_mapping_details()

        for token, value in six.iteritems(obj):
            if token not in details:
                # If this section of code runs, it means the user passed in
                # more information that necessary. Just skip it
                #
                continue

            # Check to make sure our value is OK
            if not parser.is_valid(token, value):
                return False

        return not _get_missing_required_tokens(context, obj)

    def get_ranking(context, obj):
        '''Find how similar a given string is to a Context's mapping.

        Args:
            context (:class:`ways.api.Context`):
                The context to get the mapping of and use for ranking.
            obj (str):
                The string to compare to the given Context and rank.

        Returns:
            float:
                A value from 0 to N - 0 being having no correlation and N
                being some increasing correlation.

        '''
        mapping = context.get_mapping()

        # This algorithm gets thrown off by any contents inside {}s
        # so we're going to make the mapping from strings like
        # '/jobs/{JOBS}/here' into '/jobs//here' to make the sort more fair
        #
        mapping = re.sub('({[^{}}]*)', mapping, '')

        return pylev.levenshtein(mapping, obj)

    def get_best_context_by_rankings(contexts, mapping):
        '''Find the Context that best matches a mapping.

        Args:
            contexts (list[:class:`ways.api.Context`]):
                The Context objects to consider.
            mapping (str):
                The asset string that will be used to find the best Context.
                The "best" Context is determined by how closely a Context's
                mapping is, compared to this given mapping.

        Raises:
            ValueError:
                If two values tie for the "best" Context and Ways cannot choose
                one of them.

        Returns:
            :class:`ways.api.Context`: The best match.

        '''
        rankings = [get_ranking(context, mapping) for context in contexts]
        high_score = max(rankings)

        # If the high score is listed twice then we can't know which Context
        # to use so raise an error
        high_scorers = []
        for context, ranking in six.moves.zip(contexts, rankings):
            if ranking == high_score:
                high_scorers.append(context)

        there_was_a_tie_for_first_place = len(high_scorers) > 1

        if there_was_a_tie_for_first_place:
            raise ValueError(
                'Two or more Context objects were selected. Cannot continue.',
                high_scorers)

        return contexts[rankings.index(high_score)]

    def get_context_info_from_pool(contexts, pool):
        '''Assign information to given Contexts using a pool of Context info.

        To keep computations light, we filter out the best possible Context
        candidates and then get their information from the total Contexts.

        Args:
            contexts (list[:class:`ways.api.Context`]):
                The Context objects to get token information for.
            pool (list[tuple[:class:`ways.api.Context`, dict[str, str]]]):
                All of the known Contexts and their token info that Ways knows of.

        Returns:
            pool (list[tuple[:class:`ways.api.Context`, dict[str, str]]]):
                The original Context objects and its pool information.

        '''
        return {context: pool[context] for context in contexts}

    def get_valid_contexts(info):
        '''Filter out Contexts that expect different info that what is given.

        Args:
            info (list[tuple[:class:`ways.api.Context`, dict[str, str]]]):
                All of the known Contexts and their token info that Ways knows of.

        Returns:
            list[:class:`ways.api.Context`]:
                The Context objects that are all compatible with their given info.

        '''
        valid_contexts = []
        for context, details in six.iteritems(info):
            parser = context.get_parser()

            # We're going to try to invalidate every token of a Context using
            # every parser that Ways knows about. If the Context doesn't
            # ever return False then that means it is 'valid'
            #
            tokens_and_parsers = itertools.product(
                six.iteritems(details), ways.get_parse_order())
            for (token, value), parse_type in tokens_and_parsers:
                if not parser.is_valid(token, value, parse_type):
                    break
            else:
                valid_contexts.append(context)

        return valid_contexts

    def tiebreak(contexts, info):
        '''Attempt to find the "best" Context from a group of tied Contexts.

        Ways does this by looking at the parse groups defined for each Context.
        If the Context objects's found information doesn't match what the
        Context expects, it's "excluded". The Context that survives validation
        is declared the "winner" because there was nothing wrong with it.

        Args:
            contexts (list[:class:`ways.api.Context`]):
                The tied Context objects to get a "best" Context of.
            info (list[dict[:class:`ways.api.Context`: dict[str, str]]]):
                All of the known Contexts and their token info that Ways knows of.

        Raises:
            ValueError:
                If the tie could not be broken. i.e. Two or more Contexts
                with are both valid, given the user's information.

        Returns:
            <ways.api.Context>: The "winner" Context.

        '''
        tied_info = get_context_info_from_pool(contexts, info)
        valid_contexts = get_valid_contexts(tied_info)

        if len(valid_contexts) == 1:
            # Tie-break succeeded
            return valid_contexts[0]

        raise ValueError(
            'Ways got two or more Contexts that tied for mapping, "{mapping}. '
            'Ways cannot decide which Contexts to use, "{contexts}".'
            ''.format(mapping=mapping, contexts=contexts))

    mapping = ''
    contexts_ = sit.get_all_contexts()
    contexts_with_info = dict()
    contexts = []
    if not isinstance(obj, collections.Mapping):
        mapping = obj

        # The user gave a string - so let's make it into a dict
        # whatever string -> dict conversions are successful *might* be the
        # context that we're looking to find - so add them
        #
        for context in contexts_:
            try:
                expanded_info = common.expand_string(context.get_mapping(), obj)
                if not expanded_info:
                    raise ValueError
            except (ValueError, RuntimeError):
                # expand_string raises an error if context.get_mapping is invalid
                pass
            else:
                contexts.append(context)
                contexts_with_info[context] = expanded_info

        if not contexts:
            raise ValueError('No plugins found had mappings. Cannot continue.')
    else:
        # Otherwise, if it is a mapping (i.e. a dict), we use all contexts
        for context in contexts_:
            if contains_all_tokens(context, obj):
                contexts.append(context)
                contexts_with_info[context] = obj

    # We'll find the Context we're searching for faster if we sort the more
    # likely candidates to the front. But we can only do that if obj is a string
    #
    # In this example, we use a Levenshtein sort to figure out the "best" Context
    #
    if mapping:
        try:
            return get_best_context_by_rankings(contexts, mapping)
        except ValueError as err:
            # Try to break the tie, if we can
            tied_contexts = err.args[-1]
            return tiebreak(tied_contexts, contexts_with_info)

    valid_contexts = []
    for context in contexts:
        try:
            Asset(obj, context)
        except ValueError:
            continue
        valid_contexts.append(context)

    if len(valid_contexts) == 1:
        return valid_contexts[0]

    # Try to break the tie, if we can
    return tiebreak(valid_contexts, contexts_with_info)


def register_asset_info(class_type, context, init=None, children=False):
    '''Change get_asset to return a different class, instead of an Asset.

    The Asset class is useful but it may be too basic for some people's purposes.
    If you have an existing class that you'd like to use with Ways,

    Args:
        class_type (classobj):
            The new class to use, instead.
            context (str or :class:`ways.api.Context`):
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
