#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A set of functions that make working with the cache in Ways easier.'''


# IMPORT STANDARD LIBRARIES
# scspell-id: 3c62e4aa-c280-11e7-be2b-382c4ac59cfd
import os
import imp
import sys
import collections

# IMPORT THIRD-PARTY LIBRARIES
import six
import six.moves

# IMPORT WAYS LIBRARIES
import ways

# IMPORT LOCAL LIBRARIES
from . import common


def _conform_plugins_with_assignments(plugins):
    '''Mutate a list of Plugin objects into a list of Plugin/assignment pairs.

    We have no way of knowing if a Descriptor is returning a list of
    Plugin/assignment pairs (which is what Ways needs) or just a simple
    list of Plugin objects or both. This function helps make sure that, no matter
    what the user initially created, Ways can use it.

    Example:
        >>> plugins1 = [ways.api.Plugin()]
        >>> plugins2 = [(ways.api.Plugin(), 'master')]
        >>> plugins3 = [(ways.api.Plugin(), 'master'), ways.api.Plugin()]
        >>> _conform_plugins_with_assignments(plugins)
        >>> print(plugins1)
        >>> print(plugins2)
        >>> print(plugins3)
        >>> # Result: [(ways.api.Plugin(), 'master')]
        >>> # Result: [(ways.api.Plugin(), 'master')]
        >>> # Result: [(ways.api.Plugin(), 'master')]

    Args:
        plugins (list[<ways.api.Plugin>]):
            The plugins to change.

    Returns:
        list[tuple[<ways.api.Plugin>, str]]:
            The original list of Plugin objects - but now including assignments.

    '''
    for index, info in enumerate(plugins):
        try:
            plugin = info[0]
            assignment = info[1]
        except (TypeError, IndexError):
            plugin = info
            assignment = common.DEFAULT_ASSIGNMENT
        plugins[index] = (plugin, assignment)

    return plugins


def _resolve_descriptor(description):
    '''Build a descriptor object from different types of user input.

    Args:
        description (dict or str):
            Some information to create a descriptor object from.
            If the descriptor is a string and it is a directory on the path,
            ways.api.Descriptor is returned. If it is an encoded URI,
            the string is parsed into a dict and processed.
            If it's a dict, the dictionary is used, as-is.

    Returns:
        <ways.api.Descriptor> or NoneType:
            Some descriptor object that works with the given input.

    '''
    from . import descriptor  # Avoiding a cyclic import

    def get_description_from_path(path):
        '''Build a descriptor from a string path.'''
        func = None
        try:
            if os.path.isdir(path):
                func = descriptor.FolderDescriptor
            elif os.path.isfile(path):
                func = descriptor.FileDescriptor
        except TypeError:
            return

        if func:
            return func(path)

    def get_description_info(description):
        '''Build a descriptor from an encoded URI.'''
        if not isinstance(description, six.string_types):
            return None

        description = six.moves.urllib.parse.parse_qs(description)
        if not description:
            return None

        # Make sure that single-item elements are actually single-items
        # Sometimes dicts come in like this, for example:
        # {
        #     'create_using': ['ways.api.GitLocalDescriptor']
        # }
        #
        description['create_using'] = \
            description.get('create_using', ['ways.api.FolderDescriptor'])[0]

        return get_description_from_dict(description)

    def get_description_from_dict(description):
        '''Build a descriptor from a Python dict.'''
        def try_load(obj, description):
            '''Load the object, as-is.'''
            return obj(**description)

        # Keys that Ways uses to register a Descriptor that are not meant to
        # be passed to the Descriptor's __init__ function
        #
        reserved_keys = ('create_using', common.WAYS_UUID_KEY)

        descriptor_class = description.get(
            'create_using', descriptor.FolderDescriptor)
        actual_description = {key: value for key, value
                              in description.items() if key not in reserved_keys}

        try:
            descriptor_class = common.import_object(descriptor_class)
        except (AttributeError, ImportError):
            pass

        try:
            return try_load(descriptor_class, actual_description)
        except Exception:
            # TODO : LOG the err
            raise ValueError('Found object, "{cls_}" could not be called. '
                             'Please make sure it is on the PYTHONPATH and '
                             'there are no errors in the class/function.'
                             ''.format(cls_=descriptor_class))

    final_descriptor = None
    for choice_strategy in (get_description_info,
                            get_description_from_path,
                            get_description_from_dict):
        final_descriptor = choice_strategy(description)

        if final_descriptor is not None:
            break

    return final_descriptor


def init_plugins():
    '''Create the Descriptor and Plugin objects found in our environment.

    This method ideally should only ever be run once, when Ways first starts.

    '''
    ways.clear()

    def get_items_from_env_var(env_var):
        '''Get all non-empty items in some environment variable.'''
        items = []
        for item in os.getenv(env_var, '').split(os.pathsep):
            item = item.strip()
            if item:
                items.append(item)
        return items

    plugin_files = []
    # TODO : This is too confusing. There are "Plugin" files which are just
    #        Python files that get read, PluginSheets, which are
    #        YAML/JSON/Python files that contains Plugins. And Plugin class,
    #        which isn't even a file. This needs to be fixed
    #
    for item in get_items_from_env_var(common.PLUGINS_ENV_VAR):
        files = common.get_python_files(item)
        if not files:
            files = [item]

        plugin_files.extend(files)

    for item in plugin_files:
        load_plugin(item)

    for item in get_items_from_env_var(common.DESCRIPTORS_ENV_VAR):
        add_descriptor(item)


def add_descriptor(description, update=True):
    '''Add an object that describes the location of Plugin objects.

    Args:
        description (dict or str):
            Some information to create a descriptor object from.
            If the descriptor is a string and it is a directory on the path,
            ways.api.FolderDescriptor is returned. If it is
            an encoded URI, the string is parsed into a dict and processed.
            If it's a dict, the dictionary is used, as-is.
        update (:obj:`bool`, optional):
            If True, add this Descriptor's plugins to Ways.
            If False, the user must register a Descriptor's plugins.
            Default is True.

    '''
    info = {'item': description}

    try:
        final_descriptor = _resolve_descriptor(description)
    except ValueError:
        _, _, traceback_ = sys.exc_info()
        info.update(
            {
                'status': common.FAILURE_KEY,
                'reason': common.RESOLUTION_FAILURE_KEY,
                'traceback': traceback_,
            }
        )
        ways.DESCRIPTOR_LOAD_RESULTS.append(info)
        # TODO : logging?
        print('Description: "{desc}" could not become a descriptor class.'
              ''.format(desc=description))
        return

    try:
        final_descriptor = final_descriptor.get_plugins
    except AttributeError:
        pass

    if not callable(final_descriptor):
        _, _, traceback_ = sys.exc_info()
        info.update(
            {
                'status': common.FAILURE_KEY,
                'reason': common.NOT_CALLABLE_KEY,
                'traceback': traceback_,
            }
        )
        ways.DESCRIPTOR_LOAD_RESULTS.append(info)
        # TODO : logging?
        print('Description: "{desc}" created a descriptor that cannot '
              'load plugins.'.format(desc=description))
        return

    ways.DESCRIPTORS.append(final_descriptor)

    info.update(
        {
            'status': common.SUCCESS_KEY,
        }
    )
    ways.DESCRIPTOR_LOAD_RESULTS.append(info)

    if update:
        update_plugins()

    return final_descriptor


def add_action(action, name='', hierarchy='', assignment=common.DEFAULT_ASSIGNMENT):
    '''Add a created action to Ways.

    Args:
        action (<ways.api.Action>):
            The action to add. Action objects are objects that act
            on Context objects to gather some kind of information.
        name (:obj:`str`, optional):
            A name to identify this action. The name must be unique
            to this hierarchy/assignment or it might override another
            pre-existing Action in the same location.
            If no name is given, the name on the action is tried, instead.
            Default: ''.
        assignment (:obj:`str`, optional): The group to add this action to,
                                            Default: 'master'.

    Raises:
        RuntimeError: If no hierarchy is given and no hierarchy could be
                        found on the given action.
        RuntimeError: If no name is given and no name could be found
                        on the given action.

    '''
    if name == '':
        try:
            name = action.name
        except AttributeError:
            pass

        try:
            if name == '':
                name = action.__name__
        except AttributeError:
            raise RuntimeError('Action: "{act!r}" has no name property '
                               'and no name was specified to add_action. '
                               'add_action cannot continue.'
                               ''.format(act=action))

    # TODO : Possibly change with a "get_hierarchy" function
    if hierarchy == '':
        try:
            hierarchy = action.get_hierarchy()
        except AttributeError:
            raise RuntimeError('Action: "{act!r}" has no get_hierarchy '
                               'method and no hierarchy was given to '
                               'add_action. add_action cannot continue.'
                               ''.format(act=action))

    hierarchy = common.split_hierarchy(hierarchy)

    # Set defaults (if needed)
    ways.ACTION_CACHE.setdefault(hierarchy, collections.OrderedDict())
    ways.ACTION_CACHE[hierarchy].setdefault(assignment, dict())

    ways.ACTION_CACHE[hierarchy][assignment][name] = action


# pylint: disable=invalid-name
add_search_path = add_descriptor
add_search_path.__doc__ = add_descriptor.__doc__


def get_assignments(hierarchy):
    '''list[str]: Get the assignments for a hierarchy key in plugins.'''
    hierarchy = common.split_hierarchy(hierarchy)
    return ways.PLUGIN_CACHE['hierarchy'][hierarchy].keys()


def get_all_plugins():
    '''list[<pathfinder.plugin.Plugin>]: Every registered plugin.'''
    return ways.PLUGIN_CACHE['all']


# TODO : This should be renamed. Since this isn't a Plugin but a PluginSheet
def load_plugin(item):
    '''Load the Python file as a plugin.

    Args:
        item (str): The absolute path to a valid Python file (py or pyc).

    '''
    info = {'item': item}

    try:
        module = imp.load_source('module', item)
    except Exception as err:
        _, _, traceback_ = sys.exc_info()
        info.update(
            {
                'status': common.FAILURE_KEY,
                'reason': common.IMPORT_FAILURE_KEY,
                'exception': err,
                'traceback': traceback_,
            }
        )
        ways.PLUGIN_LOAD_RESULTS.append(info)
        return

    # Add the WAYS_UUID in the file, if it was defined
    try:
        info[common.WAYS_UUID_KEY] = module.WAYS_UUID
    except AttributeError:
        pass

    try:
        func = module.main
    except AttributeError:
        # A plugin file isn't required to have a main function
        # so we can just return, here
        #
        info.update(
            {
                'status': common.SUCCESS_KEY,
                'details': 'no_main_function',
            }
        )
        return

    try:
        func()
    except Exception as err:
        _, _, traceback_ = sys.exc_info()
        info.update(
            {
                'status': common.FAILURE_KEY,
                'reason': common.LOAD_FAILURE_KEY,
                'exception': err,
                'traceback': traceback_,
            }
        )
        ways.PLUGIN_LOAD_RESULTS.append(info)
        return

    info.update(
        {
            'status': common.SUCCESS_KEY,
        }
    )
    ways.PLUGIN_LOAD_RESULTS.append(info)


def update_plugins():
    '''Look up every plugin in every descriptor and register them to Ways.'''
    plugins = [plugin for descriptor_method in ways.DESCRIPTORS
               for plugin in descriptor_method()]

    _conform_plugins_with_assignments(plugins)

    for plugin, assignment in plugins:
        ways.add_plugin(plugin, assignment=assignment)
