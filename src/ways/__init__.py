#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''The main location where loaded plugin and action objects are managed.'''

# IMPORT STANDARD LIBRARIES
import os
import collections

# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT LOCAL LIBRARIES
# TODO : ugh this import is bad. FIXME
#        It's only used so that we can clear our Context instances
#        Find a better way to do this. Maybe store the instances here, too?
#
# pylint: disable=wrong-import-position
from . import common
from . import resource
from . import situation as sit

six.add_move(six.MovedModule('mock', 'mock', 'unittest.mock'))

__version__ = "0.1.0b1"


ACTION_CACHE = collections.OrderedDict()
DESCRIPTORS = []
DESCRIPTOR_LOAD_RESULTS = []
PLUGIN_CACHE = collections.OrderedDict()
PLUGIN_CACHE['hierarchy'] = collections.OrderedDict()
PLUGIN_CACHE['all'] = []
PLUGIN_LOAD_RESULTS = []


def _get_actions(hierarchy, assignment=common.DEFAULT_ASSIGNMENT, duplicates=False):
    '''Get the actions defined for a plugin hierarchy.

    Args:
        hierarchy (tuple[str]):
            The specific description to get plugin/action objects from.
        assignment (:obj:`str`, optional):
            The group to get items from. Default: 'master'.
        duplicates (:obj:`bool`, optional):
            If True, The first Action that is found will be returned.
            If False, all actions (including parent actions with the same
            name) are all returned. Default is False.

    Returns:
        list[list[str], list[<ways.api.Action> or callable]]:
            0: All of the names of each action that was found.
            1: The object that was created for a specific action.

    '''
    action_names = []
    objects = []

    for actions in get_actions_iter(hierarchy, assignment=assignment):
        for name, obj in six.iteritems(actions):
            is_a_new_action = name not in action_names

            if is_a_new_action or duplicates:
                action_names.append(name)
                objects.append(obj)
    return action_names, objects


def _get_from_assignment(obj_cache, hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
    '''Get a plugin from some hierarchy and assignment, if it exists.

    Args:
        obj_cache (dict[str, dict[str]]):
            Some mapping object that contains details that
            hierarchy and assignment will try to access.
        hierarchy (tuple[str]):
            The specific description to get plugin/action objects from.
        assignment (:obj:`str`, optional):
            The group to get items from. Default: 'master'.

    Returns:
        The output of the assignment, if any. Ideally, a dict.

    '''
    try:
        return obj_cache[hierarchy][assignment]
    except KeyError:
        return dict()


def get_actions(hierarchy, assignment=common.DEFAULT_ASSIGNMENT, duplicates=False):
    '''Get back all of the action objects for a plugin hierarchy.

    Args:
        hierarchy (tuple[str]):
            The specific description to get plugin/action objects from.
        assignment (:obj:`str`, optional):
            The group to get items from. Default: 'master'.
        duplicates (:obj:`bool`, optional):
            If True, The first Action that is found will be returned.
            If False, all actions (including parent actions with the same
            name) are all returned. Default is False.

    Returns:
        list[<ways.api.Action> or callable]:
            The actions in the hierarchy.

    '''
    action_objects_index = 1

    actions = _get_actions(
        hierarchy=hierarchy,
        assignment=assignment,
        duplicates=duplicates)
    return actions[action_objects_index]


def get_actions_iter(hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
    '''Get the actions at a particular hierarchy.

    Args:
        hierarchy (tuple[str]):
            The location of where this Plugin object is.
        assignment (:obj:`str`, optional):
            The group that the PLugin was assigned to. Default: 'master'.
            If assignment='', all plugins from every assignment is queried.

    Yields:
        dict[str: <ways.api.Action>]:
            The actions for some hierarchy.

    '''
    def _search_for_item(hierarchy):
        '''Find the first action in our cache that we can find.'''
        priority = get_priority()

        if not priority:
            # As a fallback if get_priority gives us nothing, just use the
            # actions in the order that they were added
            #
            priority = ACTION_CACHE[hierarchy].keys()

        for assignment in priority:
            try:
                return ACTION_CACHE[hierarchy][assignment]
            except KeyError:
                continue

    # The use of 'not assignment' is very intentional. Do not change
    #
    # Excluding an assignment is a very explicit decision, because the
    # default assignment value is 'master'. Sending assignment='' means that
    # the user wants to consider all assignments, not one specifically.
    #
    if not assignment:
        assignment_method = _search_for_item
    else:
        def assignment_method(hierarchy):
            '''Create a simple partial method that only takes hierarchy.'''
            return _get_from_assignment(
                obj_cache=ACTION_CACHE,
                hierarchy=hierarchy,
                assignment=assignment)

    # This iterates over a hierarchy from bottom to top and returns the
    # first action it finds. It's a very different behavior than get_plugins
    #
    hierarchy_len = len(hierarchy)
    for index in six.moves.range(hierarchy_len):
        try:
            yield assignment_method(hierarchy[:hierarchy_len - index])
        except KeyError:
            continue


def get_action_names(hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
    '''Get the names of all actions available for some plugin hierarchy.

    Args:
        hierarchy (tuple[str]):
            The specific description to get plugin/action objects from.
        assignment (:obj:`str`, optional):
            The group to get items from. Default: 'master'.

    Returns:
        list[str]: The names of all actions found for the Ways object.


    '''
    action_names_index = 0
    actions = _get_actions(hierarchy=hierarchy, assignment=assignment, duplicates=False)

    names = []
    for name in actions[action_names_index]:
        # Maintain definition order but also make sure they are all unique
        if name not in names:
            names.append(name)

    return names


def get_actions_info(hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
    '''Get the names and objects for all Action objects in a hierarchy.

    Args:
        hierarchy (tuple[str]):
            The specific description to get plugin/action objects from.
        assignment (:obj:`str`, optional):
            The group to get items from. Default: 'master'.

    Returns:
        dict[str: <ways.api.Action> or callable]:
            The name of the action and its associated object.

    '''
    actions = collections.OrderedDict()

    for name, obj in six.moves.zip(*_get_actions(hierarchy, assignment, duplicates=False)):
        actions[name] = obj

    return actions


def get_action(name, hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
    '''Find an action based on its name, hierarchy, and assignment.

    The first action that is found for the hierarchy is returned.

    Args:
        name (str): The name of the action to get. This name is assigned to
                    the action when it is defined.
        hierarchy (tuple[str]): The location of where this Action object is.
        assignment (:obj:`str`, optional): The group that the Action was
                                            assigned to. Default: 'master'.

    Returns:
        <pathfinder.commander.Action> or NoneType: The found Action object
                                                    or nothing.

    '''
    for actions in get_actions_iter(hierarchy, assignment=assignment):
        try:
            return actions[name]
        except (TypeError, KeyError):  # TypeError in case action is None
            pass


def get_plugins(hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
    '''Find an plugin based on its name, hierarchy, and assignment.

    Every plugin found at every level of the given hierarchy is collected
    and returned.

    Args:
        name (str):
            The name of the plugin to get. This name needs to be assigned
            to the plugin when it is defined.
        hierarchy (tuple[str]):
            The location of where this Plugin object is.
        assignment (:obj:`str`, optional):
            The group that the PLugin was assigned to. Default: 'master'.
            If assignment='', all plugins from every assignment is queried.

    Returns:
        list[<pathfinder.plugin.Plugin>]:
            The found plugins, if any.

    '''
    def _search_for_plugin(hierarchy):
        '''Find all plugins in some hierarchy for every assignment.'''
        items = []
        for assignment in get_priority():
            try:
                items.extend(PLUGIN_CACHE['hierarchy'][hierarchy][assignment])
            except KeyError:
                continue

        return items

    # The use of 'not assignment' is very intentional. Do not change
    #
    # Excluding an assignment is a very explicit decision, because the
    # default assignment value is 'master'. Sending assignment='' means that
    # the user wants to consider all assignments, not one specifically.
    #
    if not assignment:
        assignment_method = _search_for_plugin
    else:
        def assignment_method(hierarchy):
            '''Create a scoped function that only need hierarchy as input.'''
            return _get_from_assignment(
                obj_cache=PLUGIN_CACHE['hierarchy'],
                hierarchy=hierarchy,
                assignment=assignment)

    plugins = []
    hierarchy = sit.resolve_alias(hierarchy)

    # This iterates over a hierarchy from top to bottom and gets every
    # plugin at each level of the hierarchy that it finds.
    #
    # So, for example
    # ('some', 'hierarchy', 'here')
    #
    # Will get the plugins for ('some', ),
    # then the plugins for ('some', 'hierarchy'),
    # and finally plugins for ('some', 'hierarchy', 'here')
    #
    for index in six.moves.range(len(hierarchy)):
        plugins.extend(assignment_method(hierarchy[:index + 1]))

    return plugins


def get_parse_order():
    '''list[str]: The order to try all of the parsers registered by the user.'''
    return os.getenv(common.PARSERS_ENV_VAR, 'regex').split(os.pathsep)


def get_priority():
    '''Determine the order that assignments are searched through for plugins.

    This list is controlled by the WAYS_PRIORITY variable.

    For example, os.environ['WAYS_PRIORITY'] = 'master:job'.
    Since job plugins come after master plugins, they are given
    higher priority

    Todo:
        Give a recommendation (in docs) for where to read more about this.

    Returns:
        tuple[str]: The assignments to search through.

    '''
    return os.getenv(common.PRIORITY_ENV_VAR, common.DEFAULT_ASSIGNMENT).split(os.pathsep)


def add_plugin(plugin, assignment='master'):
    '''Add a plugin to Ways.

    Args:
        plugin (<ways.api.Plugin>):
            The plugin to add.
        assignment (:obj:`str`, optional):
            The assignment of the plugin. Default: 'master'.

    '''
    # Set defaults (if needed)
    hierarchy = plugin.get_hierarchy()

    PLUGIN_CACHE['hierarchy'].setdefault(hierarchy, collections.OrderedDict())
    PLUGIN_CACHE['hierarchy'][hierarchy].setdefault(assignment, [])

    # Add the plugin if it doesn't already exist
    all_plugins = PLUGIN_CACHE['all']
    if plugin not in all_plugins:
        PLUGIN_CACHE['hierarchy'][plugin.get_hierarchy()][assignment].append(plugin)
        all_plugins.append(plugin)


def clear():
    '''Remove all Ways plugins and actions.'''
    ACTION_CACHE.clear()
    try:
        PLUGIN_CACHE['hierarchy'].clear()
    except KeyError:
        pass

    try:
        PLUGIN_CACHE['all_plugins'][:] = []
    except KeyError:
        pass

    del PLUGIN_LOAD_RESULTS[:]
    del DESCRIPTOR_LOAD_RESULTS[:]
    del DESCRIPTORS[:]
    sit.clear_aliases()
    sit.clear_contexts()
    resource.reset_asset_classes()


if __name__ == '__main__':
    print(__doc__)
