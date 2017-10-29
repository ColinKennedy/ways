#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module that holds ContextParser - A class fills in Context's mapping.'''

# IMPORT STANDARD LIBRARIES
import collections
import functools
import itertools
import os
import re

# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT LOCAL LIBRARIES
from .core import check


ENCLOSURE_TOKEN_REGEX = r'(\{[^\{\}]+\})'
TOKEN_REGEX = r'\{([^\{\}]+)\}'


class ContextParser(object):

    '''A class that's used to fill out missing values in a Context's mapping.

    Some quick terminology. If you see the word 'token', it means a
    piece of a string that needs to be filled out, such as 'some_{TOKEN}_here'.

    A field is the token + its information. For example, if the token being
    filled out is optional or if input to a token is valid.

    This class is meant to expand and resolve the tokens inside the mapping
    of a Context object.

    '''

    def __init__(self, context):
        '''Create the parser and store our Context object.

        Args:
            context (<situation.Context>): The Context to resolve and parse.

        '''
        super(ContextParser, self).__init__()
        self.context = context
        self._data = dict()

    def is_valid(self, key, value, resolve_with='regex'):
        if resolve_with != 'regex':
            raise NotImplementedError('This is not supported yet')

        mapping_details = self.get_all_mapping_details()
        try:
            info = mapping_details[key]
        except KeyError:
            return False

        try:
            expression = info['parse'][resolve_with]
        except KeyError:
            return True

        return re.match(expression, value) is not None

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
            if resolve_type.lower() in ('env', 'environment', 'env_vars'):
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

    def get(self, value, default=None):
        try:
            return self[value]
        except KeyError:
            return default

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

    def get_child_tokens(self, token, enclosure=False):
        mapping_details = self.get_all_mapping_details()

        try:
            mapping = mapping_details[token].get('mapping', '')
        except KeyError:
            return []

        if mapping:
            return find_tokens(mapping, enclosure=enclosure)

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

    def get_token_parse(self, name, parse_type, groups=False):
        '''Get the parse expression for some token name.

        Args:
            name (str):
                The name of the token to get parse details from.
            parse_type (str):
                The engine type whose expression will be returned. If no
                parse_type is given, the stored parse_type is used.
            groups (:obj:`bool`, optional):
                If True, each parse token will output with (?P<NAME>{value})
                wrapped around it. If False, it will just return the value.
                This is more for regex, than anything else

        Todo:
            groups is gross. Maybe come up with something better. Like a
            parse-specific group description. Or maybe not.

        Returns:
            The parse expression used for the given token.

        '''
        def make_regex_group(name, parse):
            return '(?P<{name}>{parse})'.format(name=name, parse=parse)

        def _get_parse_type_info(token_details, parse_type):
            '''Get the serialized information about some token's parse.

            This data typically comes from Plugin Sheets and looks like this:

            Example:
                >>> token_details = {
                >>>     'SCENE':
                >>>         'parse':
                >>>             'regex': '[A-Z]{5,}'
                >>>             'glob': '*'
                >>> }
                >>> parse_type = 'regex'

                >>> _get_parse_type_info(token_details, parse_type)
                >>> # Result: '*'

            Returns:
                str; The contents of the parse type.

            '''
            return token_details['parse'][parse_type]

        details = self.get_all_mapping_details()

        try:
            value = details[name]['parse'][parse_type]
            if not groups:
                return value
        except KeyError:
            pass

        try:
            mapping = details[name]['mapping']
        except KeyError:
            return ''

        raise NotImplementedError('Need to make unittests and "search" for te parse')
        # def recurse_child_tokens_yield(token, formatter):
        #     '''Search a token downwards through it children to yield values.

        #     If the formatter can't get a proper value back from a token,
        #     we use the token's mapping to search down its children
        #     (its subtokens) recursively until we have a full string.

        #     Args:
        #         token (str):
        #             The token to get the parse value of.
        #         formatter (callable[str]):
        #             The function that we'll use to in order to get parse details.

        #     Yields:
        #         tuple[str, str]: A piece of the token.

        #     '''
        #     # TODO : Note - This function requires regex, to work.
        #     #        Do something so that we don't have to use it
        #     #
        #     child_tokens = self.get_child_tokens(token)

        #     replacements = {}
        #     if not child_tokens:
        #         yield
        #         return

        #     items = dict()
        #     format_splitter = re.compile('(\{[^{}]+\})')
        #     mapping = details[token]['mapping']
        #     mapping_split = [item for item in format_splitter.split(mapping) if item]

        #     for child in child_tokens:
        #         try:
        #             value = formatter(details[child])
        #             items[child] = value
        #         except KeyError:
        #             for value in recurse_child_tokens_yield(child, formatter=formatter):
        #                 items[child] = value

        #     for item in mapping_split:
        #         try:
        #             yield (item[1:-1], item.format(**items))
        #         except KeyError:
        #             pass

        # def recurse_child_tokens(token, formatter):
        #     '''Walk a token and search for its parse value, using its children.

        #     If a token has no value for some formatter, we construct it,
        #     automatically, by using the token's mapping and substituting its
        #     subtokens recursively until we can get a full string.

        #     Each child token is yielded as they are found, from left to right,
        #     along with the token's mapping, and the output is joined together
        #     to build a parse type.

        #     Args:
        #         token (str):
        #             The token to get the parse value of.
        #         formatter (callable[str]):
        #             The function that we'll use to in order to get parse details.

        #     Returns:
        #         str: A token's parse type information, using its child subtokens.

        #     '''
        #     output = list(recurse_child_tokens_yield(token=token, formatter=formatter))

        #     if not groups:
        #         return ''.join([out[1] for out in output])

        #     return ''.join(
        #         [make_regex_group(out[0], out[1]) for out in output])

        # formatter = functools.partial(_get_parse_type_info, parse_type=parse_type)
        # return recurse_child_tokens(name, formatter=formatter)

    def get_str(self, resolve_with='',
                depth=-1, holdout=None, groups=None, display_tokens=False):
        r'''Create a string representation of the Context's mapping.

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
            depth = 9000  # Some ridiculously high number

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
                #        didn't cause errors in my unittests.
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


def find_tokens(mapping, enclosure=False):
    '''list[str]: The tokens to fill in. inside of a mapping.'''
    pattern = TOKEN_REGEX
    if enclosure:
        pattern = ENCLOSURE_TOKEN_REGEX
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


if __name__ == '__main__':
    print(__doc__)

