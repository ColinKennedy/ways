#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''The workhorse of the package - A module that contains Context objects.

Context objects are persistent objects that are created
using a Flyweight pattern. Once one instance of a Context is created, it is
reused whenever it possibly can - which means it can be treated like a monostate.

Reference:
    http://sourcemaking.com/design_patterns/flyweight
    http://sourcemaking.com/design_patterns/flyweight/python/1

The Python example is written in Python 3 but is the same idea.

Parts of the Context are generated at runtime and cannot be directly
modified (like, for example, its Plugin objects). Other parts are freely
changeable and will stay the same even if the Context is instantiated
elsewhere in the code (like metadata).

'''

# IMPORT STANDARD LIBRARIES
import collections
import functools
import itertools
import operator
import platform
import copy
import os
import re

# IMPORT THIRD-PARTY LIBRARIES
from six import moves
import six

# IMPORT LOCAL LIBRARIES
from . import connection as conn
from .core import pathrip
from . import common
from . import cache
from . import parse
from . import trace


class _AssignmentFactory(object):

    '''A Flyweight factory used to create and hold onto Context instances.'''

    def __init__(self, class_type):
        '''Create the factory that registers a specific class type of object.

        Args:
            class_type (classobj): The class to instantiate with this factory.

        '''
        super(_AssignmentFactory, self).__init__()
        self._class_type = class_type
        self._instances = collections.defaultdict(dict)

    def get_instance(self, hierarchy, assignment, force=False):
        '''Get an instance of our class if it exists and make it if does not.

        Args:
            hierarchy (tuple[str] or str):
                The position where all the plugins for our instance would live.
            assignment (str): The category/grouping of the instance.
            force (:obj:`bool`, optional):
                If False and the Context has no plugins, return None.
                If True, return the empty Context. Default is False.

        Returns:
            class_type or NoneType:
                An instance of our stored class. If the Context that is
                queried doesn't have any Plugin objects defined for it, it's
                considered 'empty'. To avoid faults in our code,
                we return None, in this case.

        '''
        if isinstance(hierarchy, self._class_type):
            # A Context object was passed, by mistake. Just return it
            return hierarchy

        # Get our instance, if there is one
        try:
            return self._instances[hierarchy][assignment]
        except KeyError:
            pass

        # Make our instance
        return self._make_and_store_new_instance(hierarchy, assignment, force=force)

    def _make_and_store_new_instance(self, hierarchy, assignment, force=False):
        '''Create and store our new class instance.

        Args:
            hierarchy (tuple[str] or str):
                The position where all the plugins for our instance would live.
            assignment (str):
                The priority mapping for this instance's plugins.
            force (:obj:`bool`, optional):
                If False and the Context has no plugins, return None.
                If True, return the empty Context. Default is False.

        Returns:
            A new instance of our class type.

        '''
        def make_and_store_instance(hierarchy, assignment):
            '''A syntax-sugar method that makes the instance and caches it.'''
            instance = self._class_type(hierarchy, assignment=assignment)
            self._instances[hierarchy][assignment] = instance
            return instance

        hierarchy = common.split_hierarchy(hierarchy)
        # If no plugins were defined or if the plugins are specifically stated
        # as "not findable" (like an incomplete Context Plugin)
        # we return None to avoid making an undefined Context
        #
        history = cache.HistoryCache()

        try:
            if not history.plugin_cache['hierarchy'][hierarchy][assignment]:
                raise KeyError
        except KeyError:
            # Is the user specified a null assignment (aka they want all plugins
            # from every assignment) and there are plugins, just pass it through
            #
            is_forcible = (not assignment and history.plugin_cache['hierarchy'].get(hierarchy))

            if force or is_forcible:
                # Register the context, even though it doesn't have plugins
                return make_and_store_instance(hierarchy, assignment)

            # Return nothing, no Plugin objects were found so no Context
            # will be built
            #
            return

        plugins = []

        # Add any Context objects that these plugins depend on
        hierarchies = []
        for plugin in history.plugin_cache['hierarchy'][hierarchy][assignment]:
            try:
                used = plugin.get_uses()
            except AttributeError:
                used = []
            hierarchies.extend(used)

        for uses in hierarchies:
            plugins.append(
                get_context(uses, assignment=assignment, force=True))

        for plugin in history.plugin_cache['hierarchy'][hierarchy][assignment]:
            try:
                if plugin.is_findable():
                    plugins.append(plugin)
            except AttributeError:
                # If the plugin doesn't say whether it is findable, just assume
                # that the information was just omitted and that it is findable
                #
                plugins.append(plugin)

        if not force and not plugins:
            return

        return make_and_store_instance(hierarchy, assignment)

    def clear(self):
        '''Remove every Context instance that this object knows about.

        If a Context is re-queried after this method is run, a new instance
        for the Context will be created and returned.

        Running this method is not recommended because it messes with the
        internals of Ways.

        '''
        self._instances.clear()


class _AliasAssignmentFactory(_AssignmentFactory):

    '''Extend the _AssignmentFactory object to include Context aliases.'''

    def __init__(self, class_type):
        '''Create this object and our empty alias dictionary.

        Args:
            class_type (classobj): The class to instantiate with this factory.

        '''
        super(_AliasAssignmentFactory, self).__init__(class_type=class_type)
        self.aliases = dict()

    def is_aliased(self, hierarchy):
        '''bool: If this hierarchy is an alias for another hierarchy.'''
        return hierarchy in self.aliases and self.aliases.get(hierarchy) != hierarchy

    def resolve_alias(self, hierarchy):
        '''Assuming that the given hierarchy is an alias, follow the alias.

        Args:
            hierarchy (tuple[str] or str):
                The location to look for our instance. In this method,
                hierarchy is expectex to be an alias for another hierarchy
                so we look for the real hierarchy, here.

        Returns:
            tuple[str]:
                The base hierarchy that this alias is meant to represent.

        '''
        current = tuple()

        while current != hierarchy:
            # On the first run, current will be empty so we just assign it
            # to hierarchy straightaway - so that the try/except will start
            #
            if current == tuple():
                current = hierarchy

            # Keep following the aliases until we get to the real hierachy
            try:
                current = self.aliases[current]
            except KeyError:
                break

        resolved_hierarchy = common.split_hierarchy(current)
        return resolved_hierarchy

    def get_instance(self, hierarchy, assignment, follow_alias=False, force=False):
        '''Get an instance of our class if it exists and make it if does not.

        Args:
            hierarchy (tuple[str] or str):
                The location to look for our instance.
            assignment (str):
                The category/grouping of the instance.
            follow_alias (:obj:`bool`, optional):
                If True, the instance's hierarchy is assumed to be an alias
                for another hierarchy and the returned instance will use
                the "real" hierachy. If False, the instance will stay as
                the aliased hierarchy, completely unmodified.
                Default is False.
            force (:obj:`bool`, optional):
                If False and the Context has no plugins, return None.
                If True, an empty Context is returned. Default is False.

        Returns:
            self._class_type() or NoneType:
                An instance of our preferred class. If the Context that is
                queried doesn't have any Plugin objects defined for it, it's
                considered 'empty'. To avoid faults in our code,
                we return None, by default.

        '''
        if isinstance(hierarchy, self._class_type):
            # A Context object was passed, by mistake. Just return it again
            return hierarchy

        hierarchy = common.split_hierarchy(hierarchy)

        instance = super(_AliasAssignmentFactory, self).get_instance(
            hierarchy=hierarchy, assignment=assignment, force=force)

        if not self.is_aliased(hierarchy):
            return instance

        resolved_hierarchy = self.resolve_alias(hierarchy)

        if not follow_alias:
            return instance

        # Follow the alias to get a Context with the 'real' hierarchy
        return super(_AliasAssignmentFactory, self).get_instance(
            hierarchy=resolved_hierarchy, assignment=assignment, force=force)

    def clear(self):
        '''Remove all the stored aliases in this instance.'''
        super(_AliasAssignmentFactory, self).clear()
        self.aliases = dict()


class Context(object):

    '''A collection of plugins that are read in order to resolve its methods.'''

    def __init__(self, hierarchy, assignment='', connection=None):
        '''The object that will be used to describe a location on disk.

        Attributes:
            data (dict[str]):
                Completely arbitrary information that the user can customize
                and store anything on. Because Context objects are Flyweights,
                this information will persist no matter where this Context is
                called.

        Args:
            hierarchy (tuple[str] or str):
                The location to look for our instance. This location will be
                used to sort and cache our instance once its class is defined.
            assignment (str):
                The category/grouping of the instance. Default: ''.
            connection
                (:obj:`dict[str, callable[list[<ways.api.Plugin>]]]`,
                 optional):
                Context objects are built outf of Plugin objects that are defined
                and retrieved at runtime. Since most Context objects are built
                of more than one Plugin, we need to know how to merge
                Plugin objects so that we can get a single value.
                This attribute, connection, describes how Context
                objects resolve. Default: context_connection_info().

        Raises:
            ValueError:
                If a part of a hierarchy has bad characters
                (characters that are not alpha-numeric or [-| |_|/]).

        '''
        from . import finder as find

        super(Context, self).__init__()

        hierarchy = common.split_hierarchy(hierarchy)

        # Check each term in the hierarchy for bad characters
        bad_characters_comp = re.compile(r'[^a-zA-Z0-9_\-/ ]+')
        for part in hierarchy:
            bad_characters = bad_characters_comp.search(part)

            if bad_characters:
                raise ValueError(
                    'Bad characters: "{chars}" in hierarchy, "{hier}".'
                    ''.format(chars=bad_characters, hier=hierarchy))

        if connection is None:
            connection = context_connection_info()

        # TODO : Deprecate self.assignment and self.hierarchy - since these
        #        shouldn't really be changed anyway
        #
        self.assignment = assignment
        self.actions = find.Find(self)
        self.cache = cache.HistoryCache()
        self.connection = connection
        self.hierarchy = hierarchy

        self._user_data = self._init_data()

    @property
    def data(self):
        '''dict[str]: Data that was automatically generated and user data.'''
        data = dict(self._init_data())
        data.update(self._user_data)

        return data

    @data.setter
    def data(self, value):
        '''Set the user data to whatever the given value is.

        Note:
            This function cannot modify the data that was generated from the
            plugins for this Context - that data is intentionally read-only.

        Args:
            dict[str]: The new user data.

        '''
        self._user_data = value

    def _init_data(self):
        '''dict[str]: The default data on a Context.'''
        data = conn.get_left_right_priority(
            self.plugins, method=operator.attrgetter('data'))

        if not data:
            return dict()

        return data

    def get_all_plugins(self, hierarchy='', assignment=''):
        '''list[<pathfinder.plugin.Plugin>]: The found plugins, if any.'''
        if hierarchy == '':
            hierarchy = self.hierarchy

        return self.cache.get_plugins(hierarchy, assignment)

    @property
    def plugins(self):
        '''The found plugins for this instance.

        What determines if a Plugin is "found" depends on a number of factors.
        First, the plugin needs to be somewhere in the hierarchy of the Context,
        have the same assignment, and the platform(s) assigned to the Plugin
        must match our current system's platform. If a platform override is
        specified (aka if WAYS_PLATFORM has been set) then the Plugin
        object's platform has to match that, instead.

        Raises:
            ValueError: If the platform in WAYS_PLATFORM was invalid.
            ValueError: If the plugin found has a platform that is not found
                        in our recognized_platforms variable.

        Returns:
            list[<pathfinder.plugin.Plugin>]: The found plugins.

        '''
        plugins = self.get_all_plugins(
            hierarchy=self.hierarchy, assignment=self.assignment)

        output = []
        for plugin in plugins:
            try:
                self.validate_plugin(plugin)
            except (EnvironmentError, OSError):
                continue

            output.append(plugin)

        return output

    def get_action(self, name):
        '''<pathfinder.commander.Action> or NoneType: The Action object.'''
        return self.cache.get_action(
            name=name, hierarchy=self.hierarchy, assignment=self.assignment)

    def get_assignment(self):
        '''str: The assignment for this Context.'''
        return self.assignment

    def get_hierarchy(self):
        '''tuple[str]: The path to this Context.'''
        return self.hierarchy

    def get_parser(self):
        '''<parse.ContextParser>: A parser copy that points to this Context.'''
        return parse.ContextParser(self)

    def get_str(self, *args, **kwargs):
        r'''Get the Context's mapping as filled-out text.

        Args:
            *args (list): Positional args to send to parse.ContextParser.get_str.
            **kwargs (list): Keyword args to send to parse.ContextParser.get_str.

        '''
        return parse.ContextParser(self).get_str(*args, **kwargs)

    def get_mapping_details(self):
        '''The information on this Context that describes its mapping.

        This information is critical to how a Context's parser builds into
        a file path. Without it, you cannot get a proper filepath out of a
        Context.

        Returns:
            dict[str]: The information.

        '''
        try:
            function = self.connection['get_mapping_details']
        except KeyError:
            return dict()

        value = function(self.plugins)

        if not value:
            return dict()

        return value

    @classmethod
    def validate_plugin(cls, plugin):
        '''Check if a plugin is "valid" for this Context.

        Typically, a plugin is invalid if it was meant for a different OS
        (example), a Windows plugin shouldn't be added to a Context that is
        being run on a Linux machine.

        Args:
            plugin (<ways.api.Plugin>): The plugin to check.

        Raises:
            OSError:
                If the user specified an unrecognized environment using the
                PLATFORM_ENV_VAR environment variable.
            EnvironmentError:
                If the plugin's environment does not match this environment.

        Returns:
            <ways.api.Plugin>: The plugin (completely unmodified).

        '''
        # These platforms are the what platform.system() could return
        try:
            recognized_platforms = os.environ[common.PLATFORMS_ENV_VAR].split(os.pathsep)
        except KeyError:
            recognized_platforms = {'darwin', 'java', 'linux', 'windows'}

        system_platform = platform.system().lower()
        current_platform = os.getenv(common.PLATFORM_ENV_VAR, system_platform)

        if current_platform not in recognized_platforms:
            raise OSError(
                'Found platform: "{plat}" was invalid. Options were, '
                '"{opt}". Detected system platform was: "{d_plat}".'
                ''.format(plat=current_platform,
                          opt=recognized_platforms,
                          d_plat=system_platform))

        # Filter plugins if the its platform does not match our expected platforms
        platform_aliases = {'*', 'all', 'everything'}
        plug_platforms = common.get_platforms(plugin)

        # Prevent a Plugin that has a incorrectly-formatted platform
        # from being filtered
        #
        if plug_platforms == '':
            plug_platforms = '*'

        plug_platforms = common.split_by_comma(
            plug_platforms, as_type=set)

        # If the Plugin has some syntax that means "Just use this
        # for every platform" then add the plugin to output_plugins
        #
        use_all_platforms = platform_aliases & plug_platforms
        if use_all_platforms:
            plug_platforms = recognized_platforms

        if current_platform not in plug_platforms:
            raise EnvironmentError(
                'Platform: "{plat}" was not found in any options, "{opt}".'
                ''.format(plat=current_platform, opt=plug_platforms))

        return plugin

    def checkout(self, assignment=common.DEFAULT_ASSIGNMENT):
        '''Make a new Context instance and return it, with the same hierarchy.

        Args:
            assignment (:obj:`str`, optional): The new assignment to get.

        Returns:
            Context: The new Context object.

        '''
        return get_context(self.get_hierarchy(), assignment=assignment)

    def revert(self):
        '''Set the data on this instance back to its default.'''
        self.data = self._init_data()

    def __getattr__(self, key):
        '''Try to get this object's attributes by looking through connections.

        Args:
            key (str): The attribute to get.

        Raises:
            AttributeError: If this object's self.connections doesn't have a
                            a description for the given key.

        Returns:
            Whatever that connection returns.

        '''
        try:
            return functools.partial(self.connection[key], self.plugins)
        except KeyError:
            raise AttributeError('Attribute: "{attr}" was not defined in '
                                 'object "{obj}".'.format(
                                     attr=key, obj=self.__class__.__name__))

    def as_dict(self, changes=True):
        '''Convert this object into a dictionary.

        This is slightly different from a standard repr(Context) because
        it will include items that are not part of the Context's initialization.

        It also creates a deepcopy of its contents, so that modifications to
        this dictionary won't affect the original object.

        Args:
            changes (:obj:`bool`, optional):
                If True, the output will contain original plugin data as well
                as any changes that the user made over top of the original.
                If False, only the original information is returned.
                Default is True.

        Returns:
            dict[str]: A copy of the current information of this class.

        '''
        data = {
            'assignment': self.assignment,
            'actions': copy.deepcopy(trace.trace_actions_table(self)),
            'cache': self.cache,
            'connection': self.connection,
            'hierarchy': self.hierarchy,
        }
        if changes:
            data['data'] = self.data
        else:
            data['data'] = self._init_data()

        return data


__FACTORY = _AliasAssignmentFactory(Context)


@common.memoize
def context_connection_info():
    '''A cached set of connection functions for our Context object.

    Returns:
        dict[str, callable[<ways.api.Plugin>]]:
            Functions used to resolve a number of Plugins into a single output.

    '''
    def _get_latest_plugins(plugins):
        '''Get the latest plugins of any group of hierarchies.

        To keep relative plugins that have the same hierarchy from
        stacking and yielding bad results, we check which plugins were
        defined in which hierarchies and get the last-defined of each

        '''
        hierarchies = collections.OrderedDict()
        for plugin in sorted(plugins, key=operator.methodcaller('get_hierarchy')):
            hierarchies.setdefault(plugin.get_hierarchy(), [])
            hierarchies[plugin.get_hierarchy()].append(plugin)

        output = []
        for plugins_ in six.itervalues(hierarchies):
            output.append(plugins_[-1])

        return output

    def get_platforms_lowered(obj):
        '''Try to catch formatting issues with platforms by lowering them.

        platform.system() is what we use to validate if platforms are
        correctly written and each of its options are all in lower case
        so we'll intentionally lowercase our OSes, here.

        Args:
            obj (<plugin.Plugin>): The plugin to get the platforms of.

        Returns:
            str: The lowered platform name.

        '''
        platforms = obj.get_platforms()
        obj_type = platforms.__class__
        return obj_type([plat.lower() for plat in platforms])

    def get_mapping(plugins):
        '''Get the mapping of our plugins and resolve it to absolute, if needed.

        If the latest plugin in our list of plugins is absolute, just return
        its mapping. If not though, then that means the plugin is relative and
        we must instead resolve the mapping into absolute again.

        Args:
            plugins (list[<plugin.Plugin>]): The plugin to get the mapping of.

        Raises:
            RuntimeError: If there is no absolute plugin in our list of plugins,
                          this function cannot be resolved into absolute.

        Returns:
            str: The resolved mapping.

        '''
        def build_appended_mapping(plugins):
            '''Resolve a group of relative plugins into a single mapping.

            Args:
                plugins (list[<ways.api.Plugin>]):
                    The plugins to create a single mapping.

            Returns:
                str: A single, relative mapping for a group of plugins.

            '''
            appended_mapping = ''

            for plugin in _get_latest_plugins(plugins):
                mapping = plugin.get_mapping()

                if common.PARENT_TOKEN in mapping:
                    mapping = mapping.replace(common.PARENT_TOKEN, appended_mapping)
                else:
                    mapping = appended_mapping + mapping
                appended_mapping = mapping

            return appended_mapping

        try:
            latest_absolute_plugin = next(
                plugin for plugin in reversed(plugins) if not plugin.get_uses())
        except StopIteration:
            raise RuntimeError('This should not happen. Every plugin found '
                               'was a relative plugin. No absolute (root) '
                               'plugin was found.')

        abs_index = plugins.index(latest_absolute_plugin)

        # In order to resolve the absolute mapping, we need a root path to use
        base_mapping = conn.get_right_most_priority(
            plugins[:abs_index + 1], method=operator.methodcaller('get_mapping'))

        # TODO : Can't we move this block above base_mapping?
        # The resolved mapping came from an absolute plugin
        # so we can just return it
        #
        if plugins[-1] == latest_absolute_plugin:
            return base_mapping

        # Make a single, relative mapping from a group of relative Plugins
        appended_mapping = build_appended_mapping(plugins[abs_index + 1:])

        # Try to add our parent mapping into the relative mapping wherever
        # the user says to do it. Otherwise, just append it
        #
        if common.PARENT_TOKEN in appended_mapping:
            # Do not use format (because there may be tokens like {root/{JOB}})
            # In this mapping
            #
            # If you use a default formatter class then I guess it'd be OK
            #
            resolved_mapping = appended_mapping.replace(common.PARENT_TOKEN, base_mapping)
        else:
            resolved_mapping = base_mapping + appended_mapping

        return resolved_mapping

    def get_max_folder(plugins):
        '''Get the max folder that this Context is allowed to move into.

        Args:
            plugins (list[<plugin.Plugin>]): The plugin to get the max folder of.

        Returns:
            str: The furthest up that this Context is allowed to move.

        '''
        def startswith_iterable(root, startswith):
            '''Check if every element of an iterable partially matches another.

            It's like 'asdfd'.startswith('a'), but for lists. Use this instead
            of set().issubset() if you need to keep position of the iterables.

            Args:
                root (iterable): The bigger item.
                startswith (iterable):
                    The smaller item that we want to check if it is a subset
                    of root.

            Returns:
                bool: If the first iterable starts with the second element.

            '''
            if len(startswith) > len(root):
                return False

            for root_item, starts_item in moves.zip(root, startswith):
                if root_item != starts_item:
                    return False
            return True

        max_folders = []
        for plugin in _get_latest_plugins(plugins):
            plugin_max_folder = plugin.get_max_folder()

            if not max_folders:
                max_folders.append(plugin_max_folder)
                continue

            recent_max_folder = max_folders[-1]
            # To deal with poorly formatted folder input, we normalize the
            # paths and then split them by '/' and '\' before comparing them
            #
            plugin_max = pathrip.split_path_asunder(os.path.normcase(plugin_max_folder))
            recent_max = pathrip.split_path_asunder(os.path.normcase(recent_max_folder))

            if startswith_iterable(plugin_max, recent_max):
                # If the next folder is a more detailed version of the first,
                # just replace the most recent folder
                #
                max_folders[-1] = plugin_max_folder
            elif max_folders[-1] != plugin_max_folder:
                max_folders.append(plugin_max_folder)

        # Normalize and return our absolute max-folder path
        return os.path.normpath(''.join(max_folders))

    return {
        'is_hidden': conn.get_right_most_priority,
        'is_navigatable': conn.get_right_most_priority,
        'is_selectable': conn.get_right_most_priority,

        'get_groups': functools.partial(
            conn.get_intersection_priority,
            method=operator.methodcaller('get_groups')),

        'get_mapping': get_mapping,

        'get_mapping_details': functools.partial(
            conn.get_left_right_priority,
            method=operator.methodcaller('get_mapping_details')),

        'get_max_folder': get_max_folder,

        'get_platforms': functools.partial(
            conn.get_intersection_priority,
            method=get_platforms_lowered),

        'get_skip_to': conn.get_right_most_priority,
    }


def get_context(hierarchy,
                assignment='',
                follow_alias=False,
                force=False,
                *args,
                **kwargs):
    '''Get a persistent Context at some hierarchy/assignment location.

    This function uses a Flyweight factory to manage the instance objects
    that it returns.

    Reference:
        http://sourcemaking.com/design_patterns/flyweight
        http://sourcemaking.com/design_patterns/flyweight/python/1

    Args:
        hierarchy (tuple[str]):
            The location to look for our instance.
        assignment (str):
            The category/grouping of the instance. If no assignment is given,
            Ways will gather plugins in the order defined in the
            WAYS_PRIORITY environment variable and create plugins
            based on that.
        *args (list):
            If an object instance is found at the hierarchy/assignment,
            this gets passed to the instantiation of that object.
        *kwargs (dict[str]):
            If an object instance is found at the hierarchy/assignment,
            this gets passed to the instantiation of that object.

    Returns:
        <class_tuple instance> or NoneType:
            An instance of that class. If the Context that is
            queried doesn't have any Plugin objects defined for it, it's
            considered 'empty'. To avoid faults in our code,
            we return None.

    '''
    return __FACTORY.get_instance(
        hierarchy,
        assignment=assignment,
        follow_alias=follow_alias,
        force=force,
        *args, **kwargs)


def register_context_alias(alias_hierarchy, old_hierarchy, force=False):
    '''Set a hierarchy to track the changes of another hierarchy.

    This function lets you refer to plugins and Context objects
    without specifying their full names.

    Example:
        >>> class SomePlugin(plugin.Plugin):
        >>>     def get_mapping(self):
        >>>         return '/some/path/here'

        >>>     def get_hierarchy(self):
        >>>         return ('nuke', 'scenes')

        >>>     def get_platforms(self):
        >>>         return '*'

        >>> class AnotherPlugin(plugin.Plugin):
        >>>     def get_mapping(self):
        >>>         return '/some/path/here'

        >>>     def get_hierarchy(self):
        >>>         return ('maya', 'scenes')

        >>>     def get_platforms(self):
        >>>         return '*'

        >>> sit.register_context_alias('maya_scenes', 'maya/scenes')
        >>> context = sit.get_context('maya_scenes')
        >>> # The resulting Context object has the hierarchy ('maya_scenes', )
        >>> # but has all of the plugins from 'maya/scenes'

        >>> sit.register_context_alias('maya_scenes', 'nuke/scenes')

        >>> # Now, the Context('maya_scenes') is pointing to a Nuke Context
        >>> # we can immediately work with this Context without having to
        >>> # re-instantiate the Context

    Raises:
        ValueError:
            If the alias is the same as the hierarchy that it's trying to
            be aliased to or if the alias was already defined.

    '''
    old_hierarchy = common.split_hierarchy(old_hierarchy)

    if alias_hierarchy.startswith(common.HIERARCHY_SEP):
        pieces = itertools.chain(
            [common.HIERARCHY_SEP], common.split_hierarchy(alias_hierarchy))
        alias_hierarchy = tuple(item for item in pieces)
    else:
        alias_hierarchy = common.split_hierarchy(alias_hierarchy)

    if old_hierarchy == alias_hierarchy:
        raise ValueError('Hierarchy: "{hier}" cannot be aliased to itself'
                         ''.format(hier=old_hierarchy))

    if alias_hierarchy in __FACTORY.aliases:
        raise ValueError('Alias: "{alias}" was already defined.'.format(
            alias=alias_hierarchy))

    __FACTORY.aliases[alias_hierarchy] = old_hierarchy

    # Link the plugins from the old hierarchy to our alias
    # so that your plugin cache now has two keys that both point to the same
    # list
    #
    # We do this so that, if needed, users can call a Context explicitly by its
    # alias name, directly, or have the option to "follow" the alias back to its
    # base plugin hierarchy.
    #
    history = cache.HistoryCache()

    history.plugin_cache['hierarchy'].setdefault(
        old_hierarchy, collections.OrderedDict())
    history.plugin_cache['hierarchy'][alias_hierarchy] = \
        history.plugin_cache['hierarchy'][old_hierarchy]


def resolve_alias(hierarchy):
    '''Get the real hierarchy that the given alias represents.

    Args:
        hierarchy (iter[str] or str): The alias hierarchy to convert.

    Returns:
        tuple[str]: The real hierarchy.

    '''
    return __FACTORY.resolve_alias(hierarchy)


def clear_aliases():
    '''Remove all the stored aliases in this instance.'''
    __FACTORY.clear()


def clear_contexts():
    '''Remove every Context instance that this object knows about.

    If a Context is re-queried after this method is run, a new instance
    for the Context will be created and returned.

    Running this method is not recommended because it messes with the
    internals of Ways.

    '''
    __FACTORY.clear()

