#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Common functions used for tracing that cannot go into trace.py.

This module is used in situation.py. If a function in this module were used
and imported by trace.py, it'd create a cyclic import.

'''

# IMPORT STANDARD LIBRARIES
import functools

# IMPORT THIRD-PARTY LIBRARIES
import six


def _trace_method_resolution(context, method, plugins=False):
    '''Show the progression of how a Context's method is resolved.

    This function does that actual work of trace_method_resolution.

    Args:
        context (:class:`ways.api.Context`):
            Some Context to alter and get the items of back.
        method (callable):
            Some function on a Context object.
        plugins (:obj:`bool`, optional):
            If False, the result at every step of the method will be returned.
            If True, the Plugin that created each result will be returned al
            along with the result at every step. Default is False.

    Returns:
        list: The plugin resolution at each step.

    '''
    def substitute_return(obj, *args, **kwargs):  # pylint: disable=unused-argument
        '''Just return the first object that was given to the function.

        Args:
            args: The positional items of get_all_plugins, which we will ignore.
            kwargs: The keyword items of get_all_plugins, which we will ignore.

        Returns:
            The object.

        '''
        return obj

    all_plugins = context.get_all_plugins()

    results = []
    for index in six.moves.range(1, len(all_plugins) + 1):
        context.get_all_plugins = \
            functools.partial(substitute_return, all_plugins[:index])

        known_exceptions = (
            # If you're using OS-specific plugins and the very first plugin
            # is incompatible, it'll cause errors with certain methods
            #
            # This behavior should not stop this function from running because
            # the next plugin after might be fine. Just return None for errors
            #
            RuntimeError,
        )
        try:
            result = method()
        except known_exceptions:
            result = None

        if plugins:
            results.append((result, all_plugins[index - 1]))
        else:
            results.append(result)

    return results


def trace_method_resolution(method, plugins=False):
    '''Show the progression of how a Context's method is resolved.

    Args:
        method (callable):
            Some function on a Context object.
        plugins (:obj:`bool`, optional):
            If False, the result at every step of the method will be returned.
            If True, the Plugin that created each result will be returned al
            along with the result at every step. Default is False.

    Returns:
        list: The plugin resolution at each step.

    '''
    context = method.__self__
    original = context.get_all_plugins

    output = []

    try:
        output = _trace_method_resolution(context, method, plugins)
    except Exception:
        context.get_all_plugins = original
        raise

    context.get_all_plugins = original

    return output
