#!/usr/bin/env python
# -*- coding: utf-8 -*-

r'''A collection of functions for the parse types in Ways.

Maybe in the future this module will be a place where users can "register"
their own engines but, for right now, lets just K.I.S.S and assume people
will want regex for over 90% of their needs.

'''

# IMPORT STANDARD LIBRARIES
import re

# IMPORT THIRD-PARTY LIBRARIES
import six


def _make_regex_pattern_groups(info):
    '''Create regex group patterns for some info.

    Basically, just adds (?P<{foo}>) around every value in a dict.

    Args:
        info (dict[str: str]): The group name and value to replace.

    Returns:
        dict[str: str]: The output dict.

    '''
    def make_regex_group(group, expression):
        return '(?P<{name}>{expression})'.format(name=group, expression=expression)

    output = dict()
    for key, value in six.iteritems(info):
        output[key] = make_regex_group(key, value)

    return output


def get_token_parse(name, parser, parse_type):
    '''Get the parse token for some token name, using a given parse_type.

    Args:
        name (str):
            The token to get the token parse of.
        parser (<ways.api.ContextParser>):
            The parser which presumably contains any information needed to
            retrieve a token parse value.
        parse_type (str):
            The engine to use when getting our token parse information.
            Example: 'regex'.

    Returns:
        str: The token parse.

    '''
    return __TYPES[parse_type]['get_token_parse'](name, parser)


def get_token_parse_regex(name, parser, groups=False):
    '''Get the parse token for some token name, using regex.

    Args:
        name (str):
            The token to get the token parse of.
        parser (<ways.api.ContextParser>):
            The parser which presumably contains any information needed to
            retrieve a token parse value.
        groups (:obj:`bool`, optional):
            Whether or not to include (?P<{foo}>) around every value in the
            returned dict. Warning: Using this on a nested token can cause
            nested groups so it's not always recommended to enable this.
            Default is False.

    Returns:
        str: The token parse.

    '''
    mapping, info = _recursive_child_token_parse_regex(name, parser)
    if groups:
        info = _make_regex_pattern_groups(info)

    if info:
        return mapping.format(**info)
    return mapping


def get_value_from_parent(name, parent, parser, parse_type):
    '''Use a token or its parent to get some stored value from a parser.

    Args:
        name (str):
            The token to get the value of. If no value is found for this token,
            parent is used to parse and return a value.
        parent (str):
            The token which is a parent of the name token. This parent
            should have a value or be able to get a value which we then
            parse and return.
        parser (<ways.api.ContextParser>):
            The parser which presumably contains any information needed to
            retrieve the name token's value.
        parse_type (str):
            The engine to use when getting our token parse information.
            Example: 'regex'.

    Returns:
        str: The value for the name token.

    '''
    return __TYPES[parse_type]['get_value_from_parent'](name, parent, parser)


def get_value_from_parent_regex(name, parent, parser):
    '''Do a Parent-Search using regex and return its value.

    Args:
        name (str):
            The token to get the value of. If no value is found for this token,
            parent is used to parse and return a value.
        parent (str):
            The token which is a parent of the name token. This parent
            should have a value or be able to get a value which we then
            parse and return.
        parser (<ways.api.ContextParser>):
            The parser which presumably contains any information needed to
            retrieve the name token's value.

    Returns:
        str: The value for the name token.

    '''
    mapping, info = _recursive_child_token_parse_regex(parent, parser)

    if info:
        info = _make_regex_pattern_groups(info)
        mapping = mapping.format(**info)

    parent_value = parser[parent]
    match = re.match(mapping, parent_value)

    if not match:
        return ''

    child_value = match.group(name)
    return child_value


# def to_dict(layer):
#     import collections
#     to_ret = layer
#     if isinstance(layer, collections.OrderedDict):
#         to_ret = dict(layer)

#     try:
#         for key, value in to_ret.items():
#             to_ret[key] = to_dict(value)
#     except AttributeError:
#         pass

#     return to_ret


def _recursive_child_token_parse_regex(name, parser):
    # details = to_dict(parser.get_all_mapping_details())
    # from pprint import pprint; pprint(details, indent=4)
    try:
        mapping = parser.get_all_mapping_details()[name]['mapping']
    except KeyError:
        # We're at the last child - this token has no other child tokens
        # so it must have some regex value. Return it!
        #
        return (parser.get_all_mapping_details()[name]['parse']['regex'], dict())


    info = dict()
    for child in parser.get_child_tokens(name):
        # token_parse = parser.get_token_parse(child, 'regex')
        token_parse = get_token_parse_regex(child, parser, groups=False)
        info[child] = token_parse

    return (mapping, info)


__TYPES = {
    'regex': {
        'get_token_parse': get_token_parse_regex,
        'get_value_from_parent': get_value_from_parent_regex,
    },
}
