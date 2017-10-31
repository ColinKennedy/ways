#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Create a persistent cache that stores all the Plugin and Action objects.'''

# IMPORT STANDARD LIBRARIES
import os
import re
import imp
import sys
import glob
import collections

# IMPORT THIRD-PARTY LIBRARIES
import six
import six.moves

# IMPORT WAYS LIBRARIES
import ways

# IMPORT LOCAL LIBRARIES
from . import common
from .retro import single


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

    def __init__(self):
        '''Create the cache and a default priority.'''
        super(HistoryCache, self).__init__()
        self.descriptors = []
        self.plugin_cache = ways.PLUGIN_CACHE
        self.action_cache = ways.ACTION_CACHE
        self.plugin_cache.setdefault('hierarchy', collections.OrderedDict())
        self.plugin_cache.setdefault('all_plugins', [])
        self.plugin_load_results = ways.PLUGIN_LOAD_RESULTS
        self.descriptor_load_results = []

        self.init_plugins()

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
            except Exception:
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

        try:
            final_descriptor = self._resolve_descriptor(description)
        except ValueError:
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

    @classmethod
    def add_plugin(cls, *args, **kwargs):
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

    def get_assignments(self, hierarchy):
        '''list[str]: Get the assignments for a hierarchy key in plugins.'''
        hierarchy = common.split_hierarchy(hierarchy)
        return self.plugin_cache['hierarchy'][hierarchy].keys()

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
            list[<ways.api.Context>]: The Context objects defined in this system.

        '''
        from . import situation
        contexts = []
        used_hierarchy_assignment_pairs = []
        for hierarchy, info in six.iteritems(self.plugin_cache['hierarchy']):
            for assignment in six.iterkeys(info):
                pair = (hierarchy, assignment)
                if pair not in used_hierarchy_assignment_pairs:
                    used_hierarchy_assignment_pairs.append(pair)
                    contexts.append(situation.get_context(
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
    history = HistoryCache()
    history.add_descriptor(*args, **kwargs)


# TODO : This function could use more unittests and a facelift
def find_context(path, sort_with='', resolve_with=('glob', ), search=glob.glob):
    '''Get the best Context object for some path.

    Important:
        This function calls cache.HistoryCache.get_all_contexts(), which is a
        very expensive method because it is instantiating every Context for
        every hierarchy/assignment that is in the cache. Once it is run though,
        this method should be fast because the flyweight factory for each
        Context will just return the instances you already created.

    Args:
        path (str):
            The relative or absolute path to use to find some Context.
        sort_with (:obj:`str`, optional):
            The method for sorting.

            Options are: ('default', 'levenshtein-pre', 'levenshtein')
            Default: 'default'.
        resolve_with (tuple[str]):
            The methods that can be used to resolve this context.

            Options are:
                [('glob', ), ('env', ), ('env', 'glob'), ('glob', 'env')]

            regex matching is not supported, currently.
            Default: ('glob', ).
        search (callable[str]):
            The function that will be run on the resolved Context mapping.
            We search for path in this function's output to figure out if the
            Context and path are a match.

    Raises:
        NotImplementedError:
            If resolve_with gets bad options.
        ValueError:
            If the sort_with parameter did not have a proper implementation or
            if the picked implementation is missing third-party plugins that
            need to be installed.

    Returns:
        <ways.api.Context> or NoneType: The matched Context.

    '''
    def sort_levenshtein(contexts, path):
        '''Sort all contexts based on how similar their mapping is to path.

        Args:
            contexts (list[<ways.api.Context>]):
                The Context objects to sort.
            path (str):
                The path which will be used as a point of reference for our
                string algorithm.

        Raises:
            ValueError:
                This function requires the python-Levenshtein package
                to be installed.

        Returns:
            list[<ways.api.Context>]: The sorted Context objects.

        '''
        try:
            import Levenshtein
        except ImportError:
            raise ValueError('Cannot use a Levenshtein algorithm. '
                             'It was not installed')

        def levenshtein_sort(context):
            '''Compare the Context mapping to our path.

            Returns:
                float:
                    A ratio, from 0 to 1, of how closely the Context object's
                    mapping resembles the given path.

            '''
            mapping = context.get_mapping()

            # Remove all tokens (example: i/am/a/{TOKEN}/here)
            # so that our results are skewed by any of the token's contents
            #
            mapping_replace = re.sub('({[^{}]*})', mapping, '')
            return Levenshtein.ratio(mapping_replace, path)

        return sorted(contexts, key=levenshtein_sort)

    def do_not_sort(contexts):
        '''Do not sort any Context object and just return them all.'''
        return contexts

    path = os.path.normcase(path)

    resolve_options = [('glob', ), ('env', ), ('env', 'glob'), ('glob', 'env')]
    if resolve_with not in resolve_options:
        raise NotImplementedError('resolve_with: "{res}" is not valid for '
                                  'the find_context method. Options were, '
                                  '"{opt}".'.format(res=resolve_with,
                                                    opt=resolve_options))
        # TODO : I 'could' add 'regex' support but only if I can guarantee
        #        there are required tokens, {}s left to expand. Maybe sometime
        #        later

    if sort_with == '':
        sort_with = 'default'

    sort_types = {
        'default': do_not_sort,
        'levenshtein-pre': sort_levenshtein,
        'levenshtein': sort_levenshtein,
    }

    try:
        sort_type = sort_types[sort_with]
    except KeyError:
        raise ValueError('Sort type: "{sort}" is invalid. Options were: "{opt}".'
                         ''.format(sort=sort_with, opt=sort_types.keys()))

    # Process each Context until a proper Context object is found
    history = HistoryCache()
    rearranged_contexts = sort_type(history.get_all_contexts())
    for context in rearranged_contexts:
        found_paths = search(context.get_str(resolve_with=resolve_with))
        if path in found_paths:
            return context


if __name__ == '__main__':
    print(__doc__)
