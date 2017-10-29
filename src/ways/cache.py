#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Create a persistent cache that stores all the Plugin and Action objects.'''

# IMPORT STANDARD LIBRARIES
import collections
import imp
import sys
import os

# IMPORT THIRD-PARTY LIBRARIES
from six.moves.urllib import parse
import six.moves
import ways
import six

# IMPORT LOCAL LIBRARIES
from .retro import single
from . import common


# TODO : Check to see if this class is even necessary. We may be able to get
#        away with a simple set of functions!
#
@six.add_metaclass(single.SingletonContainer)
class HistoryCache(object):

    '''A singleton that stores every Plugin and Action.

    It also determines how those objects are collected, which is later used
    by retrieved and resolved by Context objects.

    Note:
        Here's a short description about Context, Action, and Plugin objects
        are stored in this cache.

        A Context is nothing without Plugin objects. Which Plugin objects
        that a Context uses is determined by that Context's hierarchy.
        For example, a Context with hierarchy "some/hierarchy" will inherit
        from the 'some' Context (and, consequently, all of that parent Context's
        Plugin objects) and then all of the Plugins found in "some/hierarchy".

        It's very common for a Context to be built from other Contexts as
        well as Plugins, since Context and Plugin have very similar interfaces.

        Actions work exactly the same way. Actions are bound to a hierarchy.
        If an Action is requested for a Context and it isn't defined, the
        Context will look up its hierarchy of Context objects and try to find
        an Action with the same name.

    '''

    def __init__(self, priority=''):
        '''Create the cache and a default priority.

        Args:
            priority (:obj:`tuple[str] or str`, optional):
                The order that assignments will be checked for plugins
                and actions. This variable is only used when no assignment
                is given, basically as a fallback.

                If no priority is given, it defaults to ('master', ), and only
                auto-searches for master plugins and actions.

        '''
        super(HistoryCache, self).__init__()
        priority = common.split_by_comma(priority)
        self._priority = priority

        self.descriptors = []
        self.plugin_cache = ways.PLUGIN_CACHE
        self.action_cache = ways.ACTION_CACHE
        self.plugin_cache.setdefault('hierarchy', collections.OrderedDict())
        self.plugin_cache.setdefault('all_plugins', [])
        self.plugin_load_results = []
        self.descriptor_load_results = []

        self.init_plugins()

    @property
    def priority(self):
        '''The default list of assignments to search through for objects.

        This list is controlled by the WAYS_PRIORITY variable.

        For example, os.environ['WAYS_PRIORITY'] = 'master:job'
        will have very different runtime behavior than
        os.environ['WAYS_PRIORITY'] = 'job:master'.

        Todo:
            Give a recommendation (in docs) for where to read more about this.

        Returns:
            tuple[str]: The assignments to search through.

        '''
        if self._priority:
            priority = self.priority
        else:
            priority = os.getenv(common.PRIORITY_ENV_VAR, common.DEFAULT_ASSIGNMENT)
        return priority.split(os.pathsep)

    @classmethod
    def _get_from_assignment(cls, obj_cache, hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
        '''A simple helper method to get hierarchy/assignment details.

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

    @classmethod
    def _resolve_descriptor(cls, description):
        '''Build a descriptor object from a variety of input.

        Args:
            description (dict or str):
                Some information to create a descriptor object from.
                If the descriptor is a string and it is a directory on the path,
                ways.descriptor.Descriptor is returned. If it is
                an encoded URI, the string is parsed into a dict and processed.
                If it's a dict, the dictionary is used, as-is.

        Returns:
            <ways.descriptor.Descriptor> or NoneType:
                Some descriptor object that works with the given input.

        '''
        from . import descriptor  # Avoiding a cyclic import

        def get_description_from_path(desc):
            '''Build a descriptor from a string path.'''
            func = None
            try:
                if os.path.isdir(desc):
                    func = descriptor.FolderDescriptor
                elif os.path.isfile(desc):
                    func = descriptor.FileDescriptor
            except TypeError:
                return

            if func:
                return func(desc)

        def get_description_info(description):
            '''Build a descriptor from an encoded URI.'''
            if not isinstance(description, six.string_types):
                return None

            description = parse.parse_qs(description)
            if not description:
                return None

            # Make sure that single-item elements are actually single-items
            # Sometimes dicts come in like this, for example:
            # {
            #     'create_using': ['ways.api.GitLocalDescriptor']
            # }
            #
            description['create_using'] = description.get('create_using', ['ways.api.FolderDescriptor'])[0]

            return get_description_from_dict(description)

        def get_description_from_dict(description):
            '''Build a descriptor from a Python dict.'''
            def try_load(obj, description):
                return obj(**description)


            descriptor_class = description.get(
                'create_using', descriptor.FolderDescriptor)
            actual_description = {key: value for key, value
                                  in description.items() if key != 'create_using'}

            try:
                descriptor_class = import_object(descriptor_class)
            except (AttributeError, ImportError):
                pass

            try:
                return try_load(descriptor_class, actual_description)
            except Exception as err:
                # TODO : LOG the err
                raise ValueError('Detected object, "{cls_}" could not be called. '
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

    def init_plugins(self):
        '''Create the Descriptor and Plugin objects found in our environment.

        This method should only be run, once, when the cache is first
        initialized.

        '''
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
        #        which isn't even a file. This needs to be fixed, badly
        #
        for item in get_items_from_env_var(common.PLUGINS_ENV_VAR):
            plugin_files.extend(common.get_python_files(item))

        for item in plugin_files:
            self.load_plugin(item)

        for item in get_items_from_env_var(common.DESCRIPTORS_ENV_VAR):
            self.add_descriptor(item)

    def add_descriptor(self, description, update=True):
        '''Add an object that describes the location of Plugin objects.

        Args:
            description (dict or str):
                Some information to create a descriptor object from.
                If the descriptor is a string and it is a directory on the path,
                ways.api.FolderDescriptor is returned. If it is
                an encoded URI, the string is parsed into a dict and processed.
                If it's a dict, the dictionary is used, as-is.
            update (:obj:`bool`, optional):
                If True, immediately recalculate all of the Plugin objects
                in this cache. Default is True.

        '''
        info = {'item': description}

        final_descriptor = self._resolve_descriptor(description)
        if final_descriptor is None:
            _, _, traceback_ = sys.exc_info()
            info.update(
                {
                    'status': common.FAILURE_KEY,
                    'reason': common.RESOLUTION_FAILURE_KEY,
                    'traceback': traceback_,
                }
            )
            self.descriptor_load_results.append(info)
            # TODO : logging?
            print('Description: "{desc}" could not become a descriptor class.'.format(desc=description))
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
            self.descriptor_load_results.append(info)
            # TODO : logging?
            print(
                'Description: "{desc}" created a descriptor that cannot '
                'load plugins.'.format(desc=description))
            return

        self.descriptors.append(final_descriptor)

        info.update(
            {
                'status': common.SUCCESS_KEY,
            }
        )
        self.descriptor_load_results.append(info)

        if update:
            self.update()

        return final_descriptor

    def add_action(self, action, name='', hierarchy='', assignment=common.DEFAULT_ASSIGNMENT):
        '''Add a created action to this cache.

        Args:
            action (<ways.api.Action>):
                The action to add. Action objects are objects that act
                upon Context objects to gather some kind of information.
            name (:obj:`str`, optional):
                A name to associate with this action. The name must be unique
                to this hierarchy/assignment or it risks overriding another
                Action that might already exist at the same location.
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
        self.action_cache.setdefault(hierarchy, collections.OrderedDict())
        self.action_cache[hierarchy].setdefault(assignment, dict())
        self.action_cache[hierarchy][assignment][name] = action

    def add_plugin(self, *args, **kwargs):
        '''Add a created plugin to this cache.

        Args:
            plugin (<ways.api.Plugin>):
                The plugin to add. These Plugin objects describe parts of a
                Context.
            assignment (:obj:`str`, optional): The group to add this plugin to,
                                               Default: 'master'.

        '''
        return ways.add_plugin(*args, **kwargs)

    def add_search_path(self, path, update=True):
        '''Add a directory to search for Plugin objects.

        Note:
            This is just a convenience method that calls add_descriptor,
            under the hood.

        Args:
            path (str):
                The full path to a directory with plugin files.
            update (:obj:`bool`, optional):
                If True, immediately recalculate all of the Plugin objects
                in this cache. Default is True.

        '''
        self.add_descriptor(path, update=update)

    def get_action(self, name, hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
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
        for actions in self._get_actions_iter(hierarchy, assignment=assignment):
            try:
                return actions[name]
            except (TypeError, KeyError):  # TypeError in case action is None
                pass

    def get_action_names(self, hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
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
        actions = self._get_actions(
            hierarchy=hierarchy,
            assignment=assignment,
            duplicates=False)

        names = []
        for name in actions[action_names_index]:
            # Maintain definition order but also make sure they are all unique
            if name not in names:
                names.append(name)

        return names

    def get_actions(self, hierarchy, assignment=common.DEFAULT_ASSIGNMENT, duplicates=False):
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

        actions = self._get_actions(
            hierarchy=hierarchy,
            assignment=assignment,
            duplicates=duplicates)
        return actions[action_objects_index]

    def get_actions_info(self, hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
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

        for name, obj in six.moves.zip(*self._get_actions(hierarchy, assignment, duplicates=False)):
            actions[name] = obj

        return actions

    def _get_actions(self, hierarchy, assignment=common.DEFAULT_ASSIGNMENT, duplicates=False):
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

        for actions in self._get_actions_iter(hierarchy, assignment=assignment):
            for name, obj in six.iteritems(actions):
                is_a_new_action = name not in action_names

                if is_a_new_action or duplicates:
                    action_names.append(name)
                    objects.append(obj)
        return action_names, objects

    def _get_actions_iter(self, hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
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
            priority = self.priority

            if not priority:
                # As a fallback if self.priority gives us nothing, just use the
                # actions in the order that they were added
                #
                priority = self.action_cache[hierarchy].keys()

            for assignment in priority:
                try:
                    return self.action_cache[hierarchy][assignment]
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
                return self._get_from_assignment(
                    obj_cache=self.action_cache,
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

    def get_assignments(self, hierarchy):
        '''list[str]: Get the assignments for a hierarchy key in plugins.'''
        hierarchy = common.split_hierarchy(hierarchy)
        return self.plugin_cache['hierarchy'][hierarchy].keys()

    def get_plugins(self, hierarchy, assignment=common.DEFAULT_ASSIGNMENT):
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
        # TODO : Remove this relative import
        from . import situation as sit

        def _search_for_plugin(hierarchy):
            '''Find all plugins in some hierarchy for every assignment.'''
            items = []
            for assignment in self.priority:
                try:
                    items.extend(self.plugin_cache['hierarchy'][hierarchy][assignment])
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
                return self._get_from_assignment(
                    obj_cache=self.plugin_cache['hierarchy'],
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

    def get_all_plugins(self):
        '''list[<pathfinder.plugin.Plugin>]: Every registered plugin.'''
        return self.plugin_cache['all_plugins']

    def get_all_contexts(self):
        '''Get or Create every Context instance that has plugins.

        Warning:
            This method can potentially be slow if there are a lot of Context
            objects left to be defined. That said, the second time this method
            is called, it'll be fast because the Context instances will
            be retrieved from the flyweight cache.

        Returns:
            list[<sit.Context>]: The Context objects defined in this system.

        '''
        from . import situation as sit
        contexts = []
        used_hierarchy_assignment_pairs = []
        for hierarchy, info in six.iteritems(self.plugin_cache['hierarchy']):
            for assignment in six.iterkeys(info):
                pair = (hierarchy, assignment)
                if pair not in used_hierarchy_assignment_pairs:
                    used_hierarchy_assignment_pairs.append(pair)
                    contexts.append(sit.get_context(
                        hierarchy=hierarchy, assignment=assignment))
        return contexts

    # TODO : This should be renamed. Since this isn't a Plugin but a PluginSheet
    def load_plugin(self, item):
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
            self.plugin_load_results.append(info)
            return

        try:
            func = module.main
        except AttributeError:
            # A plugin file isn't required to have a main function
            # so we can just return, here
            #
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
            self.plugin_load_results.append(info)
            return

        info.update(
            {
                'status': common.SUCCESS_KEY,
            }
        )
        self.plugin_load_results.append(info)

    def update(self):
        '''Look up every plugin in every descriptor and register them.'''
        plugins = [plugin for descriptor_method in self.descriptors
                   for plugin in descriptor_method()]

        _conform_plugins_with_assignments(plugins)

        for plugin, assignment in plugins:
            self.add_plugin(plugin, assignment=assignment)

    def clear(self):
        '''Remove all Plugin and Action objects from this cache.'''
        self.plugin_load_results = self.plugin_load_results.__class__()
        self.descriptor_load_results = self.descriptor_load_results.__class__()
        self.descriptors = self.descriptors.__class__()

        ways.clear()


def _conform_plugins_with_assignments(plugins):
    '''Mutate a list of Plugin objects into a list of Plugin/assignment pairs.

    We have no way of knowing if a Descriptor is returning a list of
    Plugin/assignment pairs (which is what Ways needs) or just a simple
    list of Plugin objects or some mixture of the two. This function smoothes
    any inconsistencies into something that Ways can use.

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


def add_descriptor(*args, **kwargs):
    history = HistoryCache()
    history.add_descriptor(*args, **kwargs)


if __name__ == '__main__':
    print(__doc__)

