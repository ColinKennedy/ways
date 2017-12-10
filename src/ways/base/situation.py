#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''The most important part of Ways - A module that contains Context objects.

Context objects are persistent objects that are created
using a Flyweight pattern. Once one instance of a Context is created, it is
reused whenever the same Context is called again - which means it can be
used like a monostate.

Reference:
    http://sourcemaking.com/design_patterns/flyweight
    http://sourcemaking.com/design_patterns/flyweight/python/1

The Python example is written in Python 3 but is the same idea.

Parts of the Context are generated at runtime and cannot be directly
modified (like, for example, its Plugin objects). Other parts are dynamic (like
the Context.data property).

'''

# IMPORT STANDARD LIBRARIES
# scspell-id: 3c62e4aa-c280-11e7-be2b-382c4ac59cfd
import os
import re
import copy
import inspect
import operator
import platform
import functools
import collections

# IMPORT THIRD-PARTY LIBRARIES
import six
from six import moves

# IMPORT WAYS LIBRARIES
import ways

# IMPORT LOCAL LIBRARIES
from . import finder as find
from . import factory
from . import connection as conn
from ..core import pathrip
from ..helper import common
from ..parsing import parse


class Context(object):

    '''A collection of plugins that are read in order to resolve its methods.'''

    def __init__(self, hierarchy, assignment='', connection=None):
        '''Create the instance and store its location in the Ways hierarchy.

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
                (:obj:`dict[str, callable[list[:class:`ways.api.Plugin`]]]`,
                    optional):
                Context objects are built out of Plugin objects that are defined
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
        #        probably will not change
        #
        self.assignment = assignment
        self.actions = find.Find(self)
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
            plugins for this Context - that data is read-only.

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

    @property
    def plugins(self):
        '''Find all of the "valid" plugins for this instance.

        What decides if a Plugin is "found" depends on a number of factors.
        First, the plugin needs to be inside the hierarchy of the Context,
        have the same assignment, and the platform(s) assigned to the Plugin
        must match our current system's platform. If a platform override is
        specified (aka if WAYS_PLATFORM has been set) then the Plugin
        object's platform has to match that, instead.

        Raises:
            ValueError: If the platform in WAYS_PLATFORM was invalid.
            ValueError: If the plugin found has a platform that is not found
                        in our recognized_platforms variable.

        Returns:
            list[:class:`ways.api.Plugin`]: The found plugins.

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
        ''':class:`ways.api.Action` or callable or NoneType: The Action.'''
        action = ways.get_action(
            name=name, hierarchy=self.hierarchy, assignment=self.assignment)

        # If this object is a class, then assume that it's a ways.api.Action
        # and that it needs to be instantiated so that we can run __call__ on it
        #
        if inspect.isclass(action):
            action = action()

        return action

    def get_all_plugins(self, hierarchy='', assignment=''):
        '''list[:class:`ways.api.Plugin`]: The found plugins, if any.'''
        if not hierarchy:
            hierarchy = self.hierarchy

        if not assignment:
            assignment = self.assignment

        return ways.get_plugins(hierarchy, assignment)

    def get_assignment(self):
        '''str: The assignment for this Context.'''
        return self.assignment

    def get_hierarchy(self):
        '''tuple[str]: The path to this Context.'''
        return self.hierarchy

    def get_parser(self):
        ''':class:`ways.api.ContextParser`: A parser copy that points to this Context.'''
        return parse.ContextParser(self)

    def get_str(self, *args, **kwargs):
        '''Get the Context's mapping as filled-out text.

        Args:
            *args (list): Positional args to send to ways.api.ContextParser.get_str.
            **kwargs (dict): Keyword args to send to ways.api.ContextParser.get_str.

        '''
        return parse.ContextParser(self).get_str(*args, **kwargs)

    def get_mapping_details(self):
        '''Get the information that describes a Context instance's mapping.

        This function is the same as "mapping_details" key that you'd see in a
        Plugin Sheet file and is critical to how a Context's parser builds
        into a file path.

        Without it, you cannot get a proper filepath out of a Context.

        Returns:
            dict[str]: The information.

        '''
        function = self.connection['get_mapping_details']
        value = function(self.plugins)

        if not value:
            return dict()

        return value

    def get_mapping_tokens(self, mapping=''):
        '''list[str]: Get all of the tokens that are in this Context's mapping.'''
        if not mapping:
            mapping = self.get_mapping()

        return parse.find_tokens(mapping)

    def get_all_tokens(self):
        '''Get the tokens in this Context's mapping and any subtokens.

        Subtokens are tokens that are inside another token's mapping.

        Returns:
            set[str]: All of the tokens known to this Context.

        '''
        tokens = set(self.get_mapping_tokens())
        for _, info in six.iteritems(self.get_mapping_details()):
            mapping = info.get('mapping')
            tokens.update(self.get_mapping_tokens(mapping))

        return tokens

    @classmethod
    def validate_plugin(cls, plugin):
        '''Check if a plugin is "valid" for this Context.

        Typically, a plugin is invalid if it was meant for a different OS
        (example), a Windows plugin shouldn't be added to a Context that is
        being run on a Linux machine.

        Args:
            plugin (:class:`ways.api.Plugin`): The plugin to check.

        Raises:
            OSError:
                If the user specified an unrecognized environment using the
                PLATFORM_ENV_VAR environment variable.
            EnvironmentError:
                If the plugin's environment does not match this environment.

        Returns:
            :class:`ways.api.Plugin`: The plugin (completely unmodified).

        '''
        recognized_platforms = ways.get_known_platfoms()

        current_platform = get_current_platform()

        if current_platform not in recognized_platforms:
            system_platform = platform.system().lower()
            raise OSError(
                'Found platform: "{platform_}" was invalid. Options were, '
                '"{opt}". Detected system platform was: "{d_plat}".'
                ''.format(platform_=current_platform,
                          opt=recognized_platforms,
                          d_plat=system_platform))

        # Filter plugins if the its platform does not match our expected platforms
        platform_aliases = {'*', 'all', 'everything'}
        plug_platforms = common.get_platforms(plugin)

        # Prevent a Plugin that has a bad-formatted platform from being filtered
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
            :class:`ways.api.Context`: The new Context object.

        '''
        return get_context(self.get_hierarchy(), assignment=assignment)

    def revert(self):
        '''Set the data on this instance back to its default.'''
        self.data = self._init_data()

    def as_dict(self, changes=True):
        '''Convert this object into a dictionary.

        This is different from a standard repr(Context) because
        it will include items that are not part of the Context's initialization.

        It also creates a deepcopy of its contents, so that any changes to
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
            'actions': copy.deepcopy(ways.get_actions_info(self.get_hierarchy())),
            'connection': self.connection,
            'hierarchy': self.hierarchy,
        }
        if changes:
            data['data'] = self.data
        else:
            data['data'] = self._init_data()

        return data

    def get_groups(self):
        '''tuple[str]: The groups that this Context belongs to.'''
        return self.connection['get_groups'](self.plugins)

    def is_path(self):
        '''bool: If the user indicated that the given mapping is a filepath.'''
        for plugin in reversed(self.plugins):
            value = plugin.is_path()
            if value is not None:
                return value

        return False

    def get_mapping(self):
        '''str: The mapping that describes this Context.'''
        mapping = self.connection['get_mapping'](self.plugins)

        if self.is_path():
            # TODO : Make a good function here to check if a \ is "escaped"
            if get_current_platform().lower() == 'windows':
                mapping = mapping.replace('/', '\\')
                mapping = mapping.replace(r'\\', r'\\\\')
            else:
                mapping = mapping.replace('\\', '/')
        return mapping

    def get_max_folder(self):
        '''str: The highest mapping point that this Context lives in.'''
        return self.connection['get_max_folder'](self.plugins)

    def get_platforms(self):
        '''Get The OSes that this Context runs on.

        The recognized platforms for this method is anything that platform.system()
        would return. (Examples: ['darwin', 'java', 'linux', 'windows']).

        Returns:
            set[str]: The platforms that this Context is allowed to run on.

        '''
        return self.connection['get_platforms'](self.plugins)

    def __repr__(self):
        '''str: The full representation of this object.'''
        return "{cls_}(hierarchy='{hier}', assignment={ass}, data={data})".format(
            cls_=self.__class__.__name__,
            hier=self.hierarchy,
            ass=self.assignment,
            data=self.data,
        )

    def __str__(self):
        '''str: A simple representation of this object.'''
        return "{cls_}(hierarchy='{hier}', assignment={ass})".format(
            cls_=self.__class__.__name__,
            hier=(common.HIERARCHY_SEP).join(self.hierarchy),
            ass=self.assignment,
        )


__FACTORY = factory.AliasAssignmentFactory(Context)


@common.memoize
def context_connection_info():
    '''Get a default description of how attributes combine in a Context object.

    Returns:
        dict[str, callable[:class:`ways.api.Plugin`]]:
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
            obj (:class:`ways.api.Plugin`): The plugin to get the platforms of.

        Returns:
            str: The lowered platform name.

        '''
        platforms = obj.get_platforms()
        if '*' in platforms:
            platforms.update(ways.get_known_platfoms())
            platforms.remove('*')
        obj_type = platforms.__class__
        return obj_type([platform_.lower() for platform_ in platforms])

    def get_mapping(plugins):
        '''Get the mapping of our plugins and resolve it to absolute, if needed.

        If the latest plugin in our list of plugins is absolute, just return
        its mapping. If not though, then that means the plugin is relative and
        we must instead resolve the mapping into absolute again.

        Args:
            plugins (list[:class:`ways.api.Plugin`]):
                The plugin to get the mapping of.

        Raises:
            RuntimeError: If there is no absolute plugin in our list of plugins,
                          this function cannot be resolved into absolute.
            RuntimeError: If not a single plugin provided has a mapping.

        Returns:
            str: The resolved mapping.

        '''
        def build_appended_mapping(plugins):
            '''Resolve a group of relative plugins into a single mapping.

            Args:
                plugins (list[:class:`ways.api.Plugin`]):
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

        if not plugins:
            raise RuntimeError(
                'No plugins were found. If you are using a custom assignment, '
                'make sure that the assignment is listed in WAYS_PRIORITY or it '
                'may have been skipped.')

        try:
            latest_absolute_plugin = next(
                plugin for plugin in reversed(plugins) if not plugin.get_uses())
        except StopIteration:
            raise RuntimeError('This should not happen. Every plugin found was '
                               'a relative plugin. No absolute (root) plugin '
                               'was found.')

        abs_index = plugins.index(latest_absolute_plugin)

        # In order to resolve the absolute mapping, we need a root path to use
        base_mapping = conn.get_right_most_priority(
            plugins[:abs_index + 1], method=operator.methodcaller('get_mapping'))

        if base_mapping is None:
            raise RuntimeError('None of the plugins provided have mappings. Cannot continue.')

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
            plugins (list[:class:`ways.api.Plugin`]): The plugins to use.

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
        for plugin in plugins:
            plugin_max_folder = plugin.get_max_folder()
            if not plugin_max_folder:
                continue
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
        joined = ''.join(max_folders)

        if not joined:
            return ''

        return os.path.normpath(joined)

    return {
        'get_groups': functools.partial(
            conn.get_right_most_priority,
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


def get_all_contexts():
    '''Get or Create every Context instance that has plugins.

    Warning:
        This method can potentially be slow if there are a lot of Context
        objects left to be defined. That said, the second time this method
        is called, it'll be fast because the Context instances will
        be retrieved from the Context flyweight cache.

    Returns:
        list[:class:`ways.api.Context`]: Every Context object found by Ways.

    '''
    contexts = []
    used_hierarchy_assignment_pairs = []
    for hierarchy, info in six.iteritems(ways.PLUGIN_CACHE['hierarchy']):
        for assignment in six.iterkeys(info):
            pair = (hierarchy, assignment)
            if pair not in used_hierarchy_assignment_pairs:
                used_hierarchy_assignment_pairs.append(pair)
                contexts.append(get_context(hierarchy=hierarchy, assignment=assignment))
    return contexts


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
        **kwargs (dict[str]):
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


def get_current_platform():
    '''Get the user-defined platform for Ways.

    If WAYS_PLATFORM is not defined, the user's system OS is returned instead.

    Returns:
        str: The platform.

    '''
    system_platform = platform.system().lower()
    return os.getenv(common.PLATFORM_ENV_VAR, system_platform)


def register_context_alias(alias_hierarchy, old_hierarchy):
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
        >>> context = ways.api.get_context('maya_scenes')
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
    ways.PLUGIN_CACHE['hierarchy'].setdefault(
        old_hierarchy, collections.OrderedDict())
    ways.PLUGIN_CACHE['hierarchy'][alias_hierarchy] = \
        ways.PLUGIN_CACHE['hierarchy'][old_hierarchy]


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
