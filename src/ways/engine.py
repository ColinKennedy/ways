#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import re

# IMPORT THIRD-PARTY LIBRARIES
import six


def _make_regex_pattern_groups(info):
    def make_regex_group(group, expression):
        return '(?P<{name}>{expression})'.format(name=group, expression=expression)

    output = dict()
    for key, value in six.iteritems(info):
        output[key] = make_regex_group(key, value)

    return output


def get_token_parse(name, parser, parse_type):
    return __TYPES[parse_type]['get_token_parse'](name, parser)


def get_token_parse_regex(name, parser, groups=False):
    mapping, info = _recursive_child_token_parse_regex(name, parser)
    if groups:
        info = _make_regex_pattern_groups(info)

    if info:
        return mapping.format(**info)
    return mapping


def get_value_from_parent(name, parent, parser, parse_type):
    return __TYPES[parse_type]['get_value_from_parent'](name, parent, parser)


def get_value_from_parent_regex(name, parent, parser):
    '''Do a Parent-Search using regex and return its value.'''
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
