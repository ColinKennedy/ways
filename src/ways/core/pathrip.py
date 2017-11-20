#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tools for dealing with file paths.

All of these functions should be OS-independent or at least indicate if not.

'''

# IMPORT STANDARD LIBRARIES
import os

# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT LOCAL LIBRARIES
from . import check


def split_os_path_asunder(path):
    '''Split up a path, even if it is in Windows and has a letter drive.

    Args:
        path (str): The path to split up into parts.

    Returns:
        list[str]: The split path.

    '''
    drive, path = os.path.splitdrive(path)
    paths = split_path_asunder(path)
    if drive:
        return [drive] + paths
    return paths


def split_path_asunder(path):
    r'''Split a path up into individual folders.

    This function is OS-independent but does not take into account Windows
    drive letters. For that, check out split_os_path_asunder.

    Reference:
        http://www.stackoverflow.com/questions/4579908.

    Note:
        If this method is used on Windows paths, it's recommended to
        os.path.splitdrive() before running this method on some path, to
        handle edge cases where driver letters have different meanings
        (example: c:path versus c:\path)

    Args:
        path (str): The path to split up into parts.

    Returns:
        list[str]: The split path.

    '''
    parts = []
    while True:
        newpath, tail = os.path.split(path)
        if newpath == path:
            assert not tail
            if path:
                parts.append(path)
            break
        parts.append(tail)
        path = newpath
    parts.reverse()
    return parts


def get_subfolder_root(path, subfolders, method='tail'):
    '''Find the path of some path, using some consecutive subfolders.

    Args:
        path (str): The path to get the root of.
        subfolders (list[str] or str): The folders to search for in the path.
        method (:obj:`callable[str, list[str]] or str`, optional):
            The strategy used to get the root subfolders. A function is
            acceptable or a preset string can be used.
            String options:
            'tail': Search a path to get the longest possible match
                    (the last tail).

    Returns:
        str: The root path that contains the subfolders.

    '''
    subfolders = check.force_itertype(subfolders)
    subfolders_copy = list(subfolders)
    subfolders = []
    for folder in subfolders_copy:
        subfolders.extend(split_os_path_asunder(folder))

    if isinstance(method, six.string_types):
        methods = {
            'tail': get_subfolder_root_tail,
        }

        method = methods[method.lower()]

    return method(path, subfolders)


def get_subfolder_root_tail(path, subfolders):
    '''Get the longest match of some path, using some subfolders.

    Example:
        >>> root = '/jobs/rnd_ftrack/shots/sh01/maya/scenes/modeling/RELEASE/some_file_name.ma'
        >>> subfolders = ['maya/scenes']
        >>> get_subfolder_root_tail(root, subfolders)
        '/jobs/rnd_ftrack/shots/sh01/maya/scenes'

    Note:
        If a path has more than one match for subfolders, the last match
        is used.

    Args:
        path (str): The path to get the root of.
        subfolders (list[str] or str): The folders to search for in the path.

    Returns:
        str: The path that matches some subfolder or an empty string.

    '''
    root_parts = split_os_path_asunder(path)
    subfolders = list(reversed(subfolders))
    current_subfolder_index = 0
    final_index = -1
    for index, part in enumerate(reversed(root_parts)):
        try:
            current_part_to_find = subfolders[current_subfolder_index]
        except IndexError:
            final_index = index
            break

        if part == current_part_to_find:
            current_subfolder_index += 1
        else:
            # The subfolders are assumed to be consecutive - so if it's not a
            # match, restart from the beginning and keep iterating over the
            # path
            #
            current_subfolder_index = 0

    if final_index == -1:
        return ''

    return os.path.join(*root_parts[:-1 * (final_index - len(subfolders))])
