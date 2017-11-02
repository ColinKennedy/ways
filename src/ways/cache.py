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


def _resolve_descriptor(description):
    '''Build a descriptor object from a variety of input.

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
            descriptor_class = common.import_object(descriptor_class)
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
    #        which isn't even a file. This needs to be fixed, badly
    #
    for item in get_items_from_env_var(common.PLUGINS_ENV_VAR):
        plugin_files.extend(common.get_python_files(item))

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
            If True, add this Descriptor's plugins to Ways immediately.
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
    ways.ACTION_CACHE.setdefault(hierarchy, collections.OrderedDict())
    ways.ACTION_CACHE[hierarchy].setdefault(assignment, dict())
    ways.ACTION_CACHE[hierarchy][assignment][name] = action


def add_search_path(path, update=True):
    '''Add a directory to search for Plugin objects.

    Note:
        This is just a convenience method that calls add_descriptor,
        under the hood.

    Args:
        path (str):
            The full path to a directory with plugin files.
        update (:obj:`bool`, optional):
            If True, add this Descriptor's plugins to Ways immediately.
            If False, the user must register a Descriptor's plugins.
            Default is True.

    '''
    return add_descriptor(path, update=update)


def get_assignments(hierarchy):
    '''list[str]: Get the assignments for a hierarchy key in plugins.'''
    hierarchy = common.split_hierarchy(hierarchy)
    return ways.PLUGIN_CACHE['hierarchy'][hierarchy].keys()


def get_all_plugins():
    '''list[<pathfinder.plugin.Plugin>]: Every registered plugin.'''
    return ways.PLUGIN_CACHE['all_plugins']


def get_all_contexts():
    '''Get or Create every Context instance that has plugins.

    Warning:
        This method can potentially be slow if there are a lot of Context
        objects left to be defined. That said, the second time this method
        is called, it'll be fast because the Context instances will
        be retrieved from the Context flyweight cache.

    Returns:
        list[<ways.api.Context>]: The Context objects defined in this system.

    '''
    from . import situation
    contexts = []
    used_hierarchy_assignment_pairs = []
    for hierarchy, info in six.iteritems(ways.PLUGIN_CACHE['hierarchy']):
        for assignment in six.iterkeys(info):
            pair = (hierarchy, assignment)
            if pair not in used_hierarchy_assignment_pairs:
                used_hierarchy_assignment_pairs.append(pair)
                contexts.append(situation.get_context(
                    hierarchy=hierarchy, assignment=assignment))
    return contexts


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


# TODO : This function could use more unittests and a facelift
def find_context(path, sort_with='', resolve_with=('glob', ), search=glob.glob):
    '''Get the best Context object for some path.

    Important:
        This function calls get_all_contexts, which is a
        very expensive method because it instantiates every Context for
        every hierarchy/assignment that Ways sees in the cache if it doesn't
        already exist. The second time this function runs it will be fast though
        because every hierarchy/assignment will use the cached Context objects.

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
    rearranged_contexts = sort_type(get_all_contexts())
    for context in rearranged_contexts:
        found_paths = search(context.get_str(resolve_with=resolve_with))
        if path in found_paths:
            return context
