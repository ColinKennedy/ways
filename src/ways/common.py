#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A collection of functions that are used by modules in this package.

Honestly, this module won't be added to that much.

'''

# IMPORT STANDARD LIBRARIES
import functools
import string
import os

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
PLATFORM_ENV_VAR = 'WAYS_PLATFORM'
PLATFORMS_ENV_VAR = 'WAYS_PLATFORMS'
PLUGINS_ENV_VAR = 'WAYS_PLUGINS'
PRIORITY_ENV_VAR = 'WAYS_PRIORITY'

PARENT_TOKEN = '{root}'


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
        dict: The resulting dict, from our obj string.

    '''
    if '}{' in format_string:
        raise ValueError(
            'format_string: "{temp}" was invalid. Curly braces cannot be used, '
            'back to back'.format(temp=format_string))

    info = dict()

    for prefix, field, _, _ in reversed(list(string.Formatter().parse(format_string))):
        if not prefix:
            # We reached the beginning of the formatted str so just return obj
            info[field] = obj
            continue

        try:
            remainder, value = obj.rsplit(prefix, 1)
        except ValueError:
            # If this block rus, it means that there was a mismatch between
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


split_hierarchy = functools.partial(split_into_parts, split=HIERARCHY_SEP)


split_by_comma = functools.partial(split_into_parts, split=',')


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


def memoize(function):
    '''Create cache of values for a function.'''
    memo = {}

    def wrapper(*args):
        '''Run the original function and store its output, given some args.'''
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv

            return rv

    return wrapper

