#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Comparison operators and other useful functions.'''

from __future__ import unicode_literals

# IMPORT THIRD-PARTY LIBRARIES
import six


def is_string_instance(obj):
    '''bool: If the object is a string instance.'''
    return isinstance(obj, six.string_types)


def is_string_type(obj):
    '''bool: If the object is a string type.'''
    return obj == str


def is_itertype(obj, allow_outliers=False, outlier_check=is_string_instance):
    '''Check if the obj is iterable. Returns False if string by default.

    Args:
        obj (any): The object to check for iterable methods
        allow_outliers (:obj:`bool`, optional):
            If True, returns True if obj is string
        outlier_check (:obj:`function`, optional): A function to use to check
            for 'bad itertypes'. This function does nothing if allow_outliers
            is True. If nothing is provided, strings are checked and rejected.

    Returns:
        bool: If the input obj is a proper iterable type.

    '''
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        if not allow_outliers and outlier_check(obj):
            return False
    return True


def force_itertype(obj, allow_outliers=False, itertype=None):
    '''Change the given object into an iterable object, if it isn't one already.

    Args:
        obj (any): The object(s) to wrap in a list iterable
        allow_outliers (:obj:`bool`, optional):
            If True, returns True if obj is string
        itertype (callable):
            Any iterable object that is callable, such as list, set, dict, etc.

    Returns:
        list[obj]: A list, containing objects if is_itertype is False

    '''
    if itertype is None:
        itertype = lambda value: [value]

    if not is_itertype(obj=obj, allow_outliers=allow_outliers):
        obj = itertype(obj)
    return obj
