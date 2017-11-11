#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A collection of functions that are used by modules in this package.

This module is not likely to change often.

'''


# IMPORT STANDARD LIBRARIES
# scspell-id: 3c62e4aa-c280-11e7-be2b-382c4ac59cfd
import os
import string
import functools

# IMPORT LOCAL LIBRARIES
from .core import check

HIERARCHY_SEP = '/'
DEFAULT_ASSIGNMENT = 'master'

FAILURE_KEY = 'failed'
SUCCESS_KEY = 'success'

ENVIRONMENT_FAILURE_KEY = 'environment_failure'
IMPORT_FAILURE_KEY = 'import_failure'
LOAD_FAILURE_KEY = 'load_failure'
NOT_CALLABLE_KEY = 'not_callable'

PLATFORM_FAILURE_KEY = 'platform_failure'
RESOLUTION_FAILURE_KEY = 'resolution_failure'

DESCRIPTORS_ENV_VAR = 'WAYS_DESCRIPTORS'
PARSERS_ENV_VAR = 'WAYS_PARSERS'
PLATFORM_ENV_VAR = 'WAYS_PLATFORM'
PLATFORMS_ENV_VAR = 'WAYS_PLATFORMS'
PLUGINS_ENV_VAR = 'WAYS_PLUGINS'
PRIORITY_ENV_VAR = 'WAYS_PRIORITY'

PARENT_TOKEN = '{root}'

WAYS_UUID_KEY = 'uuid'


def expand_string(format_string, obj):
    '''Split a string into a dict using a Python-format string.

    Warning:
        Format-strings that have two tokens side-by-side are invalid.
        They must have at least some character between them.
        This format_string is invalid '{NAME}{ID}',
        this format_string is valid '{NAME}_{ID}'.

    Example:
        >>> shot = 'NAME_010'
        >>> format_string = '{SHOT}_{ID}'
        >>> expand_string(format_string, shot)
        ... {'SHOT': 'NAME', 'ID': '010'}

    Args:
        format_string (str): The Python-format style string to use to split it.
        obj (str): The string to split out into a dict.

    Raises:
        ValueError: If the format_string given is invalid.

    Returns:
        dict: The created dict from our obj string.

    '''
    if '}{' in format_string:
        # pylint: disable=bad-format-string
        raise ValueError('format_string: "{temp_}" was invalid. Curly braces, '
                         '"}{" cannot be used, back to back.'
                         ''.format(temp_=format_string))

    info = dict()

    # The string is reversed and processed from end to beginning
    for prefix, field, _, _ in reversed(list(string.Formatter().parse(format_string))):
        if not prefix:
            # We got to the beginning of the formatted str so just return obj
            info[field] = obj
            continue

        try:
            remainder, value = obj.rsplit(prefix, 1)
        except ValueError:
            # If this block runs it means that there was a bad match between
            # the formatted_string and obj.
            #
            # Example:
            #     >>> text = '/jobs/some_job/some_kind/of/real_folders'
            #     >>> pattern = '/jobs/{JOB}/some_kind/of/real_folders/inner'
            #     >>> expand_string(pattern, text)  # Raises ValueError
            #
            # To prevent false positives, we'll return an empty dict
            #
            return dict()

        if field:
            info[field] = value

        obj = remainder

    return info


def get_platforms(obj):
    '''tuple[str]: The the platform(s) for the given object.'''
    try:
        return obj.get_platforms()
    except AttributeError:
        return ('*', )


def get_python_files(item):
    '''Get the Python files at some file or directory.

    Note:
        If the given item is a Python file, just return it.

    Args:
        item (str): The absolute path to a file or folder.

    Returns:
        list[str]: The Python files at the given location.

    '''
    if os.path.isfile(item):
        return [item]
    elif os.path.isdir(item):
        files = []
        for item_ in os.listdir(item):
            item_ = os.path.join(item, item_)
            if os.path.isfile(item_) and item_.lower().endswith(('.pyc', '.py')):
                files.append(item_)

        return files
    return []


def split_into_parts(obj, split, as_type=tuple):
    '''Split a string-like object into parts, using some split variable.

    Example:
        >>> path = 'some/thing'
        >>> split_into_parts(path, split='/')
        ... ('some', 'thing')

    Args:
        obj (str or iterable): The object to split.
        split (str): The character(s) to split obj by.
        as_type (:obj:`callable[iterable[str]]`, optional):
            The type to return from this function. Default: tuple.

    Returns:
        as_type[str]: The split pieces.

    '''
    obj = check.force_itertype(obj)
    obj = (part.strip() for obj_ in obj for part in obj_.split(split))
    return as_type(part for part in obj if part)


# pylint: disable=invalid-name
split_hierarchy = functools.partial(split_into_parts, split=HIERARCHY_SEP)


# pylint: disable=invalid-name
split_by_comma = functools.partial(split_into_parts, split=',')


def import_object(name):
    '''Import a object of any kind, as long as it is on the PYTHONPATH.

    Args:
        name (str): An import name (Example: 'ways.api.Plugin')

    Raises:
        ImportError: If some object down the name chain was not importable or
                     if the entire name could not be found in the PYTHONPATH.

    Returns:
        The imported module, classobj, or callable function, or object.

    '''
    components = name.split('.')
    module = __import__(components[0])
    for comp in components[1:]:
        module = getattr(module, comp)
    return module


def memoize(function):
    '''Create cache of values for a function.'''
    memo = {}

    def wrapper(*args):
        '''Run the original function and store its output, given some args.'''
        if args in memo:
            return memo[args]

        value = function(*args)
        memo[args] = value

        return value

    return wrapper


def decode(obj):
    return conform_decode(urlparse.parse_qs(obj))


def conform_decode(info):
    '''Make sure that 'create_using' returns a single string.

    This function is a hacky solution because I don't understand why,
    for some reason, decoding will decode a string as a list.

    TODO: Remove this function by cleaning the input from urlencode.

    '''
    output = dict(info)

    def change_list_to_string(key, obj):
        try:
            value = obj[key]
        except KeyError:
            pass
        else:
            if check.is_itertype(value):
                output[key] = value[0]

    change_list_to_string('create_using', output)
    change_list_to_string(WAYS_UUID_KEY, output)

    return output
