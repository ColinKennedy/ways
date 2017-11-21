#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module to help you debug all of your Context, Plugin, and Action objects.'''


# IMPORT STANDARD LIBRARIES
# scspell-id: 3c62e4aa-c280-11e7-be2b-382c4ac59cfd
import uuid
import functools
import collections

# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT WAYS LIBRARIES
import ways

# IMPORT LOCAL LIBRARIES
from ..core import loop
from ..helper import common

# TODO : Maybe move this to find.py and then move the path class out


def _create_fake_uuid():
    return 'ways_generated-' + uuid.uuid4().hex


def _return_tail_of_hierarchy(obj):
    return obj[-1]


def _get_uuid_from_dict(obj):
    try:
        uuid_ = obj[common.WAYS_UUID_KEY]
    except (AttributeError, KeyError):
        uuid_ = _create_fake_uuid()

    return uuid_


def _get_ways_uuid_from_descriptor(obj):
    info = common.decode(obj.get('item'))
    if info is None:
        info = dict()

    return _get_uuid_from_dict(info)


def _get_ways_uuid_from_plugin(obj):
    try:
        uuid_ = obj[common.WAYS_UUID_KEY]
    except KeyError:
        try:
            uuid_ = obj['item']
        except KeyError:
            uuid_ = _create_fake_uuid()

    return uuid_


def startswith(base, leaf):
    '''Check if all tuple items match the start of another tuple.

    Raises:
        ValueError: If base is shorted than leaf.

    '''
    if len(base) < len(leaf):
        raise ValueError('Base cannot be smaller than leaf')

    for root, item in six.moves.zip(base, leaf):
        if root != item:
            return False
    return True


def trace_actions(obj, *args, **kwargs):
    '''Get actions that are assigned to the given object.

    Args:
        obj (:class:`ways.api.Action` or \
             :class:`ways.api.AssetFinder` or \
             :class:`ways.api.Context` or \
             :class:`ways.api.Find`):
            The object to get the actions of.
        *args (list):
            Position args to pass to ways.get_actions.
        **kwargs (dict[str]):
            Keyword args to pass to ways.get_actions.

    Returns:
        list[:class:`ways.api.Action` or callable]:
            The actions in the hierarchy.

    '''
    hierarchy = trace_hierarchy(obj)
    return ways.get_actions(hierarchy, *args, **kwargs)


def trace_action_names(obj, *args, **kwargs):
    '''Get the names of all actions available to a Ways object.

    Args:
        obj (:class:`ways.api.Action` or \
             :class:`ways.api.AssetFinder` or \
             :class:`ways.api.Context` or \
             :class:`ways.api.Find`):
            The object to get the action names of.
        *args (list):
            Position args to pass to ways.get_action_names.
        **kwargs (dict[str]):
            Keyword args to pass to ways.get_action_names.

    Returns:
        list[str]: The names of all actions found for the Ways object.

    '''
    hierarchy = trace_hierarchy(obj)
    return ways.get_action_names(hierarchy, *args, **kwargs)


def trace_actions_table(obj, *args, **kwargs):
    '''Find the names and objects of every action registered to Ways.

    Args:
        obj (:class:`ways.api.Action` or \
             :class:`ways.api.AssetFinder` or \
             :class:`ways.api.Context` or \
             :class:`ways.api.Find`):
            The object to get the available actions table of.
        *args (list):
            Position args to pass to ways.get_actions_info..
        **kwargs (dict[str]):
            Keyword args to pass to ways.get_action_info.

    Returns:
        dict[str, :class:`ways.api.Action` or callable]:
            The names and actions of an object.

    '''
    hierarchy = trace_hierarchy(obj)
    return ways.get_actions_info(hierarchy, *args, **kwargs)


def trace_all_descriptor_results():
    '''list[dict[str]]: The load/failure information about each Descriptor.'''
    return ways.DESCRIPTOR_LOAD_RESULTS


def trace_all_plugin_results():
    '''list[dict[str]]: The results of each plugin's load results.'''
    return ways.PLUGIN_LOAD_RESULTS


def trace_all_load_results():
    '''Get the load results of every plugin and descriptor.

    If the UUID for a Descriptor cannot be found,
    Ways will automatically assign it a UUID.

    Using this function we can check
    1. What plugins that Ways found and tried to load.
    2. If our plugin loaded and, if not, why.

    Returns:
        dict[str, :class:`collections.OrderedDict` [str, dict[str]]]:
            The main dictionary has two keys, "descriptors" and "plugins".
            Each key has an OrderedDict that contains the UUID of each
            Descriptor and plugin and their objects.

    '''
    info = dict()

    info['descriptors'] = collections.OrderedDict()
    for result in trace_all_descriptor_results():
        info['descriptors'][_get_ways_uuid_from_descriptor(result)] = result

    info['plugins'] = collections.OrderedDict()
    for result in trace_all_plugin_results():
        info['plugins'][_get_ways_uuid_from_plugin(result)] = result

    return info


def trace_context(obj):
    '''Get a Context, using some object.

    This function assumes that the given object is a Ways class that
    only has 1 Context added to it (not several).

    Args:
        obj: Some Ways object instance.

    Returns:
        :class:`ways.api.Context` or NoneType: The found Context.

    '''
    # TODO : Remove this inner import
    from ..base import situation as sit

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


def trace_hierarchy(obj):  # noqa: D301
    '''Try to find a hierarchy for the given object.

    Args:
        obj (:class:`ways.api.Action` or \
             :class:`ways.api.AssetFinder` or \
             :class:`ways.api.Context` or \
             :class:`ways.api.Find`):
            The object to get the hierarchy of.

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

        if plugins:
            results.append((method(), all_plugins[index - 1]))
        else:
            results.append(method())

    return results


def __default_hook(obj):
    '''Return back the original object.'''
    return obj


def __default_predicate(obj):
    '''Return True.'''
    return bool(obj)


def _get_hierarchy_tree(
        hierachies,
        predicate=__default_predicate,
        hook=__default_hook):
    '''Iterate over a tree of hierarchies, producing a dict-tree.

    Args:
        hierachies (list[tuple[str]]):
            The hierachies to build into a tree.
        predicate (:obj:`callable[str or tuple[str]]`, optional):
            If False, the hierarchy will not be added to the tree.
            If True, the hierarchy will be added to the tree.
        hook (:obj:`callable[str or tuple[str]]`, optional):
            A function to run on a part before it is added to the tree.

    Returns:
        dict:
            The final hierarchy tree.

    '''
    output = dict()

    for hierarchy in hierachies:
        previous_dict = output

        for part in loop.walk_items(hierarchy):
            if not predicate(part):
                continue

            part = hook(part)

            previous_dict.setdefault(part, dict())
            previous_dict = previous_dict[part]

    return output


def get_action_hierarchies(action):
    '''Get the Context hierachies that this Action is registered for.

    .. note ::
        get_action_hierarchies will return every Action that matches the given
        Action name. So if multiple classes/functions are all registered
        under the same name, then every hierarchy that those Actions use will be
        returned. However, if a object like a function or class that was
        registered, only that object's hierarchies will be returned.

    Args:
        action (str or class or callable):
            The action to get the hierachies of.

    Returns:
        set[tuple[str]]: The hierarchies for the given Action.

    '''
    actions = get_all_action_hierarchies()
    if action in actions:
        return actions[action]['hierarchies']

    output = set()
    for info in six.itervalues(actions):
        if action == info['name']:
            output.update(info['hierarchies'])

    return output


def get_all_action_hierarchies():
    '''Organize every Action that is registered into Ways by object and hierarchy.

    Returns:
        dict[class or callable: dict[str: str or set]]:
            Actions are stored as either classes or functions.
            Each Action's value is a dict which contains the hierachies
            that the Action is applied to and its registered name.

    '''
    actions = dict()

    for hierarchy, info in six.iteritems(ways.ACTION_CACHE):
        for action_info in six.itervalues(info):
            for name, action in six.iteritems(action_info):
                actions.setdefault(action, dict())
                actions[action].setdefault('hierarchies', set())
                actions[action]['hierarchies'].add(hierarchy)
                actions[action]['name'] = name

    return actions


def get_all_hierarchies():
    '''set[tuple[str]]: The Contexts that have plugins in our environment.'''
    return set(trace_hierarchy(plug) for plug in ways.PLUGIN_CACHE.get('all', []))


def get_all_hierarchy_trees(full=False):
    '''Get a description of every Ways hierarchy.

    Examples:
        >>> get_all_hierarchy_trees(full=True)
        >>> {
        >>>     ('foo', ): {
        >>>         ('foo', 'bar'): {
        >>>             ('foo' 'bar', 'fizz'): {},
        >>>         },
        >>>         ('foo', 'something', 'buzz'): {
        >>>             ('foo', 'something', 'buzz', 'thing'): {},
        >>>         },
        >>>     },
        >>> }

        >>> get_all_hierarchy_trees(full=False)
        >>> {
        >>>     'foo': {
        >>>         'bar': {
        >>>             'fizz': {},
        >>>         },
        >>>         'something': {
        >>>             'buzz': {
        >>>                 'thing': {},
        >>>             },
        >>>         },
        >>>     },
        >>> }

    Args:
        full (:obj:`bool`, optional):
            If True, each item in the dict will be its own hierarchy.
            If False, only a single part will be written.
            See examples for details. Default is False.

    Returns:
        :class:`collections.defaultdict[str]`: The entire hierarchy.

    '''
    if not full:
        return _get_hierarchy_tree(get_all_hierarchies(), hook=_return_tail_of_hierarchy)

    return _get_hierarchy_tree(get_all_hierarchies())


def get_all_assignments():
    '''set[str]: All of the assignments found in our environment.'''
    return set(trace_assignment(plug) for plug in ways.PLUGIN_CACHE.get('all', []))


def get_child_hierarchies(hierarchy):
    '''list[tuple[str]]: Get hierarchies that depend on the given hierarchy.'''
    base_hierarchy = trace_hierarchy(hierarchy)
    children = set()
    for plugin in ways.PLUGIN_CACHE['all']:
        hierarchy = plugin.get_hierarchy()

        # If the plugin's hierarchy is less than the base, it is probably
        # above it. Which means it doesn't inherit from this hierachy
        #
        is_parent = len(hierarchy) < len(base_hierarchy)

        if not is_parent and base_hierarchy != hierarchy and startswith(hierarchy, base_hierarchy):
            children.add(hierarchy)

    return children


def get_child_hierarchy_tree(hierarchy, full=False):
    '''Get all of the hierarchies that inherit the given hierarchy.

    Examples:
        >>> get_all_hierarchy_trees(full=True)
        >>> {
        >>>     ('foo', ): {
        >>>         ('foo', 'bar'): {
        >>>             ('foo' 'bar', 'fizz'): {},
        >>>         },
        >>>         ('foo', 'something', 'buzz'): {
        >>>             ('foo', 'something', 'buzz', 'thing'): {},
        >>>         },
        >>>     },
        >>> }

        >>> get_all_hierarchy_trees(full=False)
        >>> {
        >>>     'foo': {
        >>>         'bar': {
        >>>             'fizz': {},
        >>>         },
        >>>         'something': {
        >>>             'buzz': {
        >>>                 'thing': {},
        >>>             },
        >>>         },
        >>>     },
        >>> }

    Args:
        hierarchy (tuple[str]):
            The hierarchy to get the child hierarchy items of.
        full (:obj:`bool`, optional):
            If True, each item in the dict will be its own hierarchy.
            If False, only a single part will be written.
            See examples for details. Default is False.

    Returns:
        :class:`collections.defaultdict[str]`: The entire hierarchy.

    '''
    def try_startswith(hierarchy, obj):
        '''Check if a hierarchy starts with another hierarchy.

        If the startswith function raises a ValueError, just assume False.

        '''
        if hierarchy == obj:
            return False

        try:
            return startswith(obj, hierarchy)
        except ValueError:
            return False

    hierarchy = trace_hierarchy(hierarchy)
    children = get_child_hierarchies(hierarchy)

    if not full:
        return _get_hierarchy_tree(children,
                                   predicate=functools.partial(try_startswith, hierarchy),
                                   hook=_return_tail_of_hierarchy)
    return _get_hierarchy_tree(
        children,
        predicate=functools.partial(try_startswith, hierarchy))
