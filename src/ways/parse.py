#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module that holds ContextParser - A class fills in Context's mapping.'''

# IMPORT STANDARD LIBRARIES
import os
import re
import itertools
import collections

# IMPORT LOCAL LIBRARIES
from . import engine
from .core import check

ENCLOSURE_TOKEN_REGEX = r'(\{[^\{\}]+\})'
RESERVED_ENV_VAR_PARSE_TYPES = ('env', 'environment', 'env_vars')
TOKEN_REGEX = r'\{([^\{\}]+)\}'


class ContextParser(object):

    '''A class that's used to fill out missing values in a Context's mapping.

    Some quick terms: If you see the word 'token', it means a
    piece of a string that needs to be filled out, such as 'some_{TOKEN}_here'.

    A field is the token + its information. For example, if the token being
    filled out is optional or if input to a token is valid.

    This class is meant to expand and resolve the tokens inside the mapping
    of a Context object.

    '''

    def __init__(self, context):
        '''Create the parser and store our Context object.

        Args:
            context (:class:`ways.api.Context`): The Context to resolve and parse.

        '''
        super(ContextParser, self).__init__()
        self.context = context
        self._data = dict()

    def is_valid(self, token, value, resolve_with='regex'):
        '''Check if a given value will work for some Ways token.

        Args:
            token (str):
                The token to use to check for the given value.
            value:
                The object to check for validity.
            resolve_with (:obj:`str`, optional):
                The parse type to use to check if value is valid for token.
                Only 'regex' is supported right now. Default: 'regex'.

        Returns:
            bool:
                If the given value was valid.

        '''
        # TODO : factor out using engine.py
        if resolve_with != 'regex':
            raise NotImplementedError('This is not supported yet')

        mapping_details = self.get_all_mapping_details()
        try:
            info = mapping_details[token]
        except KeyError:
            return True

        try:
            expression = info['parse'][resolve_with]
        except KeyError:
            try:
                expression = self.get_token_parse(token, resolve_with)
            except KeyError:
                # If we have no expression then just assume True
                return True

        return re.match(expression, value) is not None

    # pylint: disable=too-many-arguments
    @classmethod
    def resolve_with_tokens(cls, mapping, tokens, details, options, groups, display_tokens):
        '''Substitute tokens in our mapping for anything that we can find.

        Args:
            mapping (str): The path that will be resolved and substituted.
            tokens (list[str]): The pieces inside of the mapping to resolve.
            details (dict[str]): All of the token/subtoken information available
                                 to resolve the tokens in this mapping.
            options (list[str]): The different ways to resolve the tokens.
            groups (:obj:`dict[str, str] or iterable[str, str]`, optional):
                A mapping of token names and a preferred token value to
                substitute it with. This variable takes priority over all
                types of resolve_with types. Default is None.
            display_tokens (:obj:`bool`, optional):
                Whether or not to add regex (?P<TOKEN_NAME>) tags around all
                of our resolved text.

        Returns:
            str: The resolved mapping.

        '''
        # TODO : Factor out display_tokens once this module is completely
        #        refactored to not require/expect regex input
        #
        def make_value(token, value):
            '''Wrap the output value with a regex token group, if needed.'''
            if display_tokens:
                return '(?P<{token}>{value})'.format(token=token, value=value)
            return value

        for token, resolve_type in itertools.product(tokens, options):
            # If the user has specific values to use for a token, use them now
            try:
                parse_info = make_value(token, groups[token])
            except KeyError:
                pass
            else:
                token = '{' + token + '}'
                mapping = mapping.replace(token, str(parse_info))
                continue

            # env/environment are reserved keywords and resolve from the
            # user's environment. All other resolve_types are processed normally
            #
            if resolve_type.lower() in RESERVED_ENV_VAR_PARSE_TYPES:
                token_key = '{' + token + '}'
                parse_info = make_value(token, os.getenv(token, token_key))
                mapping = mapping.replace(token_key, str(parse_info))
                continue

            # If we've gotten to this point in the loop, it means that we must
            # try to find parse info for the token. Carry on, my Wayward Son.
            #
            try:
                parse_info = make_value(token, details[token]['parse'][resolve_type][token])
            except KeyError:
                continue
            except TypeError:
                # If the user forgot to write the key twice, be forgiving
                # and assume that they meant to do this:
                #
                # >>> 'JOB': {
                # >>>     'mapping': '{JOB_NAME}_{JOB_ID}',
                # >>>     'parse': {
                # >>>         'glob': {
                # >>>             'JOB': '*',
                # >>>         },
                # >>>     },
                # >>> },
                #
                # When they actually wrote this:
                # >>> 'JOB': {
                # >>>     'mapping': '{JOB_NAME}_{JOB_ID}',
                # >>>     'parse': {
                # >>>         'glob': '*',
                # >>>     },
                # >>> },
                #
                parse_info = make_value(token, details[token]['parse'][resolve_type])

            token = '{' + token + '}'
            mapping = mapping.replace(token, str(parse_info))

        return mapping

    def get_tokens(self, required_only=False):
        '''Get the tokens in this instance.

        Args:
            required_only (:obj:`bool`, optional):
                If True, do not return optional tokens.
                If False, return all tokens, required and optional.
                Default is False.

        Returns:
            list[str]: The requested tokens.

        '''
        if required_only:
            return self.get_required_tokens()

        return list(self.get_all_mapping_details().keys())

    def get_child_tokens(self, token):
        '''Find the child tokens of a given token.

        Args:
            token (str): The name of the token to get child tokens for.

        Returns:
            list[str]: The child tokens for the given token. If the given token
                       is not a parent to any child tokens, return nothing.

        '''
        mapping_details = self.get_all_mapping_details()

        try:
            mapping = mapping_details[token].get('mapping', '')
        except KeyError:
            return []

        if mapping:
            return find_tokens(mapping)

        return []

    def get_required_tokens(self):
        '''list[str]: Get the tokens for this Context that must be filled.'''
        full_mapping_details = self.get_all_mapping_details()
        required_tokens = []

        for key, info in full_mapping_details.items():
            if info.get('required', True) and key not in required_tokens:
                required_tokens.append(key)

        return required_tokens

    def get_all_mapping_details(self):
        '''Get the combined mapping details of this Context.

        Note:
            The "true" combined mapping details of our Context is actually
            just Context.get_mapping_details(). This method can produce
            different results because it is yielding/updating
            Context.get_mapping_details() with all of its plugin's data.
            Use with caution.

        Returns:
            dict[str]: The combined mapping_details of our Context and plugins.

        '''
        contents = dict()

        for mapping_details in self.get_mapping_details():
            contents.update(mapping_details)
        return contents

    def get_mapping_details(self):
        '''Get the parse-mapping details of our entire Context.

        Basically, we take the collection of all of the mapping details of
        the Context, as is, which we know is the "sum" of all of the Context's
        plugin's mapping_details. But we also yield each plugin individually,
        in case some information was lost, along the way.

        Yields:
            dict[str]: The mapping details of this Context.

        '''
        for plugin in itertools.chain([self.context], reversed(self.context.plugins)):
            yield plugin.get_mapping_details()

    def get_token_parse(self, name, parse_type):
        '''Get the parse expression for some token name.

        Args:
            name (str):
                The name of the token to get parse details from.
            parse_type (str):
                The engine type whose expression will be returned

        Returns:
            The parse expression used for the given token.

        '''
        details = self.get_all_mapping_details()

        try:
            return details[name]['parse'][parse_type]
        except KeyError:
            pass

        try:
            details[name]['mapping']
        except KeyError:
            # If we don't have a mapping for this token, there's nothing
            # more that we can do
            #
            return ''

        return engine.get_token_parse(name, self, parse_type)

    # pylint: disable=too-many-arguments
    def get_str(self, resolve_with='',
                depth=-1, holdout=None, groups=None, display_tokens=False):
        r'''Create a string of the Context's mapping.

        Note:
            holdout and groups cannot have any common token names.

        Args:
            resolve_with (:obj:`iterable[str] or str`, optional):
                The types of ways that our parser is allowed to resolve a path.
                These are typically some combination of ('glob', 'regex', 'env')
                are are defined with our Plugin objects that make up a Context.
            depth (:obj:`int`, optional):
                The number of times this method are allowed to expand
                the mapping before it must return it. If depth=-1, this method
                will expand mapping until there are no more tokens left to
                expand or no more subtokens to expand with. Default: -1.
            holdout (:obj:`set[str]`, optional):
                If tokens (pre-existing or expanded) are in this list, they
                will not be resolved. Default is None.
            groups (:obj:`dict[str, str] or iterable[str, str]`, optional):
                A mapping of token names and a preferred token value to
                substitute it with. This variable takes priority over all
                types of resolve_with types. Default is None.
            display_tokens (:obj:`bool`, optional):
                If True, the original name of the token will be included in
                the output of the mapping, even it its contents are expanded.
                Example: '/some/{JOB}/here' -> r'/some/(?P<JOB>\w+_\d+)/here'.
                It's recommended to keep this variable as False because
                the syntax used is only regex-friendly. But if you really want
                it, it's there. Default is False.

        Raises:
            ValueError: If groups got a bad value.
            ValueError: If groups and holdout have any common elements.
                        It's impossible to know what to do in that case because
                        both items have conflicting instructions.

        Returns:
            str: The resolved string.

        '''
        # Conform holdout and groups to valid input
        if holdout is None:
            holdout = set()
        else:
            holdout = check.force_itertype(holdout)
            holdout = set(holdout)

        if groups is None:
            groups = dict()
        elif not isinstance(groups, collections.Mapping):
            try:
                groups = {key: value for key, value in groups}
            except TypeError:
                raise ValueError(
                    'Groups: "{grps}" was invalid. A dict or iterable object '
                    'with (key, value) pairs was expected.'.format(grps=groups))

        # Add our given groups info onto the stored data on this instance
        data = self._data.copy()
        data.update(groups)
        groups = data

        conflicting_keys = holdout & set(groups.keys())
        if conflicting_keys:
            raise ValueError('Keys: "{keys}" are in holdout and groups. '
                             'Choose one or the other. Cannot continue.'
                             ''.format(keys=conflicting_keys))

        mapping = self.context.get_mapping()

        if is_done(mapping):
            return mapping

        resolve_with = check.force_itertype(resolve_with)

        if depth == -1:
            depth = 9000  # A high number that will keep the loop going

        for current_depth in range(depth):
            # Make a copy and then try to expand the mapping using every
            # plugin that we can see
            #
            mapping_copy = mapping
            mapping_details = self.get_all_mapping_details()
            tokens_left = find_tokens(mapping)

            if not tokens_left:
                break

            # Try to resolve the mapping and expand it, if there are any
            # tokens left to expand
            #
            tokens_that_are_not_in_holdout = set(tokens_left) - holdout
            mapping = self.resolve_with_tokens(
                details=mapping_details,
                display_tokens=display_tokens,
                groups=groups,
                mapping=mapping,
                options=resolve_with,
                tokens=tokens_that_are_not_in_holdout,
            )
            mapping = expand_mapping(mapping=mapping, details=mapping_details)

            # If nothing changed, even after a mapping was expanded, it means
            # there are no more child tokens left to expand.
            #
            # We might as well exit early, since there's nothing left to do.
            #
            mapping_changed = mapping_copy != mapping
            if not mapping_changed:
                # TODO : At the time of writing (2017-10-15 10:50:05.823780)
                #        replacing this block with just a "break" statement
                #        did not cause errors in my unittests.
                #
                #        Possibly come back to this part, once there are more
                #        tests
                #
                current_depth = depth

            current_depth += 1
            if current_depth >= depth:
                # Try to resolve, one last time, before exiting
                mapping = self.resolve_with_tokens(
                    details=mapping_details,
                    display_tokens=display_tokens,
                    groups=groups,
                    mapping=mapping,
                    options=resolve_with,
                    tokens=find_tokens(mapping),
                )
                break

        return mapping

    def get_value_from_parent(self, name, parent, parse_type):
        '''Get the value of a token using another parent token.

        Args:
            name (str): The token to get the value of.
            parent (str): The parent token that is believed to have a value.
                          If it has a value, it is used to parse and return
                          a value for the name token.
            parse_type (str): The parse engine to use.

        Returns:
            The value of the name token.

        '''
        return engine.get_value_from_parent(name, parent, self, parse_type)

    def __getitem__(self, key):
        '''Get the value of some key on this instance.'''
        return self._data[key]

    def __setitem__(self, key, value):
        '''Set the value of some key on this instance.'''
        self._data[key] = value

    def __contains__(self, other):
        '''Check if a token is in this instance.'''
        return other in self._data


def is_done(mapping):
    '''bool: If there are still tokens to fill in, inside the mapping.'''
    return not re.search(TOKEN_REGEX, mapping)


def find_tokens(mapping):
    '''list[str]: The tokens to fill in. inside of a mapping.'''
    pattern = TOKEN_REGEX
    return re.findall(pattern, mapping)


def expand_mapping(mapping, details):
    '''Split the tokens in a mapping into subtokens, if any are available.

    Args:
        mapping (str): The mapping to expand.
        details (dict[str]): The information about the mapping that will be used
                             to expand it.

    Returns:
        str: The expanded mapping.

    '''
    keys_to_expand = set(find_tokens(mapping)) & set(details.keys())
    for key in keys_to_expand:
        info = details[key]
        token = '{' + key + '}'

        inner_mapping = info.get('mapping', token)
        mapping = mapping.replace(token, inner_mapping)

        # If no mapping is defined for some mapping_detail,
        # we assume that the key is as far-down as possible.
        #
        # We do not recurse in this case to avoid a cyclic-recursion
        #
        if inner_mapping != token:
            expand_mapping(mapping, details)
    return mapping
