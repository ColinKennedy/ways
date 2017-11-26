#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module that has a strategies for resolving Context/Plugin conflicts.

Depending on the Context object's attributes, it may be best to return a
compound of all of the Context object's plugins, or the first-defined one or
maybe the last defined Plugin object's value or even some other,
special behavior.

The point is, whatever the strategy is, this module contains all of the
different ways that a Context object's Plugin's values 'resolve' into a single
output.

Note:
    In all cases, the plugins that are given to these functions are assumed to
    be in 'ascending' order. In other words, the 0th index of plugins is the
    oldest plugin and the -1 index is the latest plugin.

'''


# IMPORT STANDARD LIBRARIES
# scspell-id: 3c62e4aa-c280-11e7-be2b-382c4ac59cfd
import copy
import functools

# IMPORT LOCAL LIBRARIES
from ..core import grouping


def get_right_most_priority(plugins, method):
    '''Get the most-latest value of the given plugins.

    Note:
        If a Plugin runs method() successfully but gives a value that returns
        False (like '', or dict(), or [], etc), keep searching until an
        explicit value is found.

    Args:
        plugins (list[:class:`ways.api.Plugin`]):
            The plugins to get the the values from.
        method (callable[:class:`ways.api.Plugin`]):
            The callable function to use to call some value from a Plugin object.

    Raises:
        NotImplementedError:
            If the given method has no implementation in all of the given
            Plugin objects or if the output value would have been None.

    Returns:
        The output type of the given method.

    '''
    if not plugins:
        return

    for plugin in reversed(plugins):
        try:
            value = method(plugin)
        except AttributeError:
            pass
        else:
            if not value:
                continue
            return value


def try_and_return(methods):
    '''Try every given method until one of them passes and returns some value.

    Args:
        methods (iterable[callable]): Functions that takes no arguments to run.

    Returns:
        The output of the first method to execute successfully or None.

    '''
    for method in methods:
        try:
            return method()
        except Exception:
            # TODO : LOGGING
            pass


def generic_iadd(obj, other):
    '''Unify the different ways that built-in Python objects implement iadd.

    It's important to note that this method is very generic and also unfinished.
    Feel free to add any other others, as needed. As long as they return a
    non-None value when successful and a None value when unsuccessful, any
    method is okay to use. (The logic for the non-None/None can be changed, too).

    Args:
        obj: Some object to add.
        other: An object to add into obj.

    Returns:
        The value that obj removes once other is added into it.

    '''
    def update_(obj, other):
        '''Run a dict's "iadd" function.'''
        obj.update(other)

        return obj

    def iadd(obj, other):
        '''Use the actual __iadd__ method of a custom Python object.'''
        obj += other
        return obj

    setter_methods = (
        functools.partial(iadd, obj, other),
        functools.partial(update_, obj, other),
    )

    value = try_and_return(setter_methods)
    if value is None:
        raise ValueError('The two objects, "{obj1}" and "{obj2}" could not be '
                         'added together.'.format(obj1=obj, obj2=other))
    return value


def get_left_right_priority(plugins, method):
    '''Add all values of all plugins going from start to finish (left to right).

    Args:
        plugins (list[:class:`ways.api.Plugin`]):
            The plugins to get the the values from.
        method (callable[:class:`ways.api.Plugin`]):
            The callable function to get some value from a Plugin object.

    Returns:
        The compound value that was created from all of the plugins.

    '''
    value = None
    for plugin in plugins:
        return_value = method(plugin)
        if value is None:
            value = copy.deepcopy(return_value)
        else:
            value = generic_iadd(value, return_value)

    return value


def get_intersection_priority(plugins, method):
    '''Get only the common elements from all plugin Objects and return them.

    Note:
        Right now this function is only needed for get_groups() but could be
        abstracted if necessary, later.

    Args:
        plugins (list[:class:`ways.api.Plugin`]):
            The plugins to get the the intersected values from.

    Returns:
        The intersected value from all of the given Plugin objects.

    '''
    groups = [method(plugin) for plugin in plugins]

    if len(groups) == 1:
        return groups[0]

    intersection = groups[0]
    for group in groups[1:]:
        intersection = grouping.get_ordered_intersection(intersection, group)
    return intersection
