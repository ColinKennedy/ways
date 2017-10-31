#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module to help you debug all of your Context, Plugin, and Action objects.'''

# IMPORT STANDARD LIBRARIES
import collections

# IMPORT WAYS LIBRARIES
import ways

# IMPORT LOCAL LIBRARIES
from . import common

# TODO : Maybe move this to find.py and then move the path class out


def trace_actions(obj, *args, **kwargs):
    '''Get actions that are assigned to the given object.

    Args:
        obj (<ways.resource.Action> or or <ways.resource.AssetFinder> or
             <ways.api.Context> or <ways.finder.Find>):
            The object to get the actions of.
        *args (list):
            Positional args to pass to ways.get_actions.
        **kwargs (dict[str]):
            Keyword args to pass to ways.get_actions.

    Returns:
        list[<ways.resource.Action> or callable]:
            The actions in the hierarchy.

    '''
    hierarchy = trace_hierarchy(obj)
    return ways.get_actions(hierarchy, *args, **kwargs)


def trace_action_names(obj, *args, **kwargs):
    '''Get the names of all actions available to a Ways object.

    Args:
        obj (<ways.resource.Action> or or <ways.resource.AssetFinder> or
             <ways.api.Context> or <ways.finder.Find>):
            The object to get the actions of.
        *args (list):
            Positional args to pass to ways.get_action_names.
        **kwargs (dict[str]):
            Keyword args to pass to ways.get_action_names.

    Returns:
        list[str]: The names of all actions found for the Ways object.

    '''
    hierarchy = trace_hierarchy(obj)
    return ways.get_action_names(hierarchy, *args, **kwargs)


def trace_actions_table(obj, *args, **kwargs):
    '''The names/objects of every action found for some Ways object.

    Args:
        obj (<ways.resource.Action> or or <ways.resource.AssetFinder> or
             <ways.api.Context> or <ways.finder.Find>):
        *args (list):
            Positional args to pass to ways.get_actions_info..
        **kwargs (dict[str]):
            Keyword args to pass to ways.get_action_info.

    Returns:
        dict[str: <ways.resource.Action> or callable]:
            The names and actions of an object.

    '''
    hierarchy = trace_hierarchy(obj)
    return ways.get_actions_info(hierarchy, *args, **kwargs)


def trace_all_plugin_results():
    '''list[dict[str]]: The results of each plugin's load results.'''
    return ways.PLUGIN_LOAD_RESULTS


def trace_all_plugin_results_info():
    '''Get the load-results for each plugin that Ways found.

    Not all plugins that we attempt to load will, though (maybe the file)
    has a syntax error or something).

    Using this function we can check
    1. What plugins that Ways found and tried to load.
    2. If our plugin loaded and, if not, why.

    Returns:
        <collections.OrderedDict>[str: dict[str]]:
            The keys are absolute paths to valid Python files
            the values are dicts that contain information about what happened
            during the load.

    '''
    info = collections.OrderedDict()
    for result in ways.PLUGIN_LOAD_RESULTS:
        info[result['item']] = result

    return info


def trace_context(obj):
    '''Get a Context, using some object.

    This function assumes that the given object is a Ways class that
    only has 1 Context associated with it (not several).

    Args:
        obj: Some Ways object instance.

    Returns:
        <ways.api.Context> or NoneType: The found Context.

    '''
    # TODO : Remove this inner import
    from . import situation as sit

    if isinstance(obj, sit.Context):
        # Is it a Context already? If so, return it
        return obj

    # Is it a AssetFinder?
    # TODO : This dir check is super ghetto. Make this better!
    #
    if 'finder' in dir(obj):
        obj = obj.finder

    # Try to find the context - assuming obj was finder.Find or an action, etc.
    try:
        context_ = obj.context
        if isinstance(context_, sit.Context):
            return context_
    except AttributeError:
        pass

    try:
        # Maybe this is a hierarchy. In which case, use it to create a Context
        return sit.get_context(obj)
    except Exception:
        return


def trace_assignment(obj):
    '''str: Get the assignment for this object.'''
    try:
        obj = obj.finder
    except AttributeError:
        pass

    try:
        obj = obj.context
    except AttributeError:
        pass

    try:
        return obj.get_assignment()
    except AttributeError:
        return common.DEFAULT_ASSIGNMENT


def trace_hierarchy(obj):
    '''Try to find a hierarchy associated with the given object.

    Args:
        obj (<ways.resource.Action> or or <ways.resource.AssetFinder> or
             <ways.api.Context> or <ways.finder.Find>):
            The object to get the actions of.

    Returns:
        tuple[str]: The hierarchy of some object.

    '''
    hierarchy = ''

    try:
        hierarchy = obj.get_hierarchy()
    except AttributeError:
        pass

    if hierarchy:
        return common.split_hierarchy(hierarchy)

    obj = trace_context(obj)

    if obj is None:
        return tuple()

    hierarchy = tuple()

    try:
        hierarchy = obj.hierarchy
    except AttributeError:
        pass

    if hierarchy:
        return common.split_hierarchy(hierarchy)

    return hierarchy


# TODO : Make tests for this function and uncomment it
# TODO : Also move it to someplace in this file, alphabetical, when it's done
# def trace_context_plugins_info(context):
#     context = trace_context(context)

#     plugins = []
#     for plugin in context.get_all_plugins(assignment=''):
#         info = {'plugin': plugin}

#         try:
#             context.validate_plugin(plugin, use_environment=True)
#         except OSError as err:
#             info.update({
#                 'status': common.FAILURE_KEY,
#                 'reason': common.ENVIRONMENT_FAILURE_KEY,
#                 'traceback': traceback_,
#             })
#         except EnvironmentError as err:
#             info.update({
#                 'status': common.FAILURE_KEY,
#                 'reason': common.PLATFORM_FAILURE_KEY,
#                 'traceback': traceback_,
#             })
#         else:
#             info['status'] = common.SUCCESS_KEY

#         plugins.append(info)

#     return plugins


# # TODO : Finish this
# def get_context_plugins_report(context):
#     context = trace_context(context)
#     trace_context_plugins_info(context)


def get_all_hierarchies():
    '''set[tuple[str]]: The Contexts that have plugins in our environment.'''
    return set(trace_hierarchy(plug) for plug in ways.PLUGIN_CACHE.get('all_plugins', []))


def get_all_assignments():
    '''set[str]: All of the assignments found in our environment.'''
    return set(trace_assignment(plug) for plug in ways.PLUGIN_CACHE.get('all_plugins', []))
