#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module that holds classes which abstract how Plugin objects are created.

A file path can be described with FolderDescriptor and more advanced constructs,
like a descriptor that gets its Plugin objects from a database, are listed here.

FolderDescriptor Types:
+++++++++++++++++++++++
FolderDescriptor - Get plugin files from a file path
GitLocalDescriptor - Get plugin files from a local git repository
GitRemoteDescriptor - Get plugin files from an online git repository

'''

# IMPORT STANDARD LIBRARIES
import os
import copy
import glob
import json
import tempfile
import functools
import itertools
import collections

# IMPORT THIRD-PARTY LIBRARIES
# pylint: disable=import-error
from six.moves.urllib import parse
import six
import yamlordereddictloader

# IMPORT LOCAL LIBRARIES
from . import plugin as plug
from . import situation as sit
from . import common
from . import dict_classes
from .core import check

GLOBALS_KEY = 'globals'
PLUGIN_INFO_FILE_NAME = '.waypoint_plugin_info'


class FileDescriptor(object):

    '''A generic abstraction that helps find Plugin objects for our code.

    Note:
        Any FileDescriptor class that returns back Plugin objects is valid
        (Descriptors can query from a database, locally on file, etc, etc.
        It's all good) except there is one major constraint. FileDescriptor-like
        objects cannot append to state asynchronously. In other words,
        If a FileDescriptor manages threads that each find Plugin objects and
        append to a list of Plugin objects whenever each thread finishes, the
        Plugin objects can potentially append out of order - which will lead to
        terrible results.

        It's recommended to not use threading at all unless this return process
        is properly managed (like with a queue or some other kind of idea).

    '''

    def __init__(self, items):
        '''Create the object and initialize its default values.

        Args:
            items (iterable[str] or str):
                The paths that this FileDescriptor looks for to find Plugin objects.

        '''
        super(FileDescriptor, self).__init__()
        self.items = check.force_itertype(items)
        self._default_plugin_info = {
            'assignment': common.DEFAULT_ASSIGNMENT,
            'recursive': False,
        }

    @classmethod
    def _conform_plugin_info(cls, info):
        '''Mutate the input's hierarchy to something that this object can use.

        Warning:
            This method does not return and modifies the object directly,
            without making a copy.

        '''
        info['hierarchy'] = common.split_hierarchy(info['hierarchy'])

    # TODO : When I remove 'items', it causes a unittest to fail. FIXME
    def _get_files(self, items):
        '''list[str]: Get all supported Plugin files.'''
        return list(self.filter_plugin_files(self.items))

    @classmethod
    def get_supported_extensions(cls):
        '''list[str]: The Plugin file extensions.'''
        loaders = get_loaders()
        return tuple(extension for _, info in loaders.items() for extension in info['extensions'])

    @classmethod
    def filter_plugin_files(cls, items):
        '''Only get back the files that are likely to be plugin files.'''
        extensions = cls.get_supported_extensions()

        for path in items:
            name, ext = os.path.splitext(os.path.basename(path))

            if name != PLUGIN_INFO_FILE_NAME and ext.lower() in extensions:
                yield path

    def get_plugins(self, items=None):
        '''Get the Plugin objects that this instance is able to find.

        Note:
            This object will sort the items it is given before retrieving its
            Plugin objects so files/folders that are given different priorities
            depending on how their paths are named.

        Args:
            items (iterable[str] or str):
                The paths that this FileDescriptor looks for to find Plugin objects.
                If not items are given, the instance's stored items are used,
                instead.

        Returns:
            list[<ways.api.Plugin>]: The plugins.

        '''
        if items is None:
            items = self.items

        files = self._get_files(items)

        plugins = []

        # Turn files into gold - Plugin gold!
        for file_ in files:
            data = try_load(file_)

            if not data:
                # TODO : Needs logging
                continue

            # TODO : Make it so we don't load this for each file.
            #        Or at the very least for FolderDescriptor (since it's)
            #        guaranteed to the same information, each time
            #
            plugin_info = self.get_plugin_info(file_)

            # TODO : This whole plugin resolution could be cleaner. FIXME

            # If the Plugin Sheet has a 'globals' section declared, get its info
            assignment = plugin_info.get('assignment', common.DEFAULT_ASSIGNMENT)
            plugin_assignment_ = data.get('globals', dict()).get('assignment', assignment)

            # Iterate over the plugins found in the Plugin Sheet
            for plugin, info in six.iteritems(data['plugins']):
                self._conform_plugin_info(info)

                # If the plugin has a specific assignment given, use that,
                # instead of what might be written in a config file or in globals
                #
                assignment_ = info.get('assignment')
                if assignment_:
                    plugin_assignment = assignment_
                else:
                    plugin_assignment = plugin_assignment_

                plugins.extend(self._build_plugins(file_, plugin, info, plugin_assignment))

        return plugins

    @classmethod
    def _build_plugins(cls, source, plugin, info, assignment):
        '''Create a Plugin or multiple Plugin objects.

        This method is a companion to get_plugins and basically just exists
        to make it get_plugins more readable.

        Args:
            source (str):
                The location to a file on disk that defined plugin.
            plugin (str):
                The key that was used in the Plugin Sheet file where the plugin
                was defined.
            info (dict[str]):
                Any data about the plugin to include when the Plugin initializes.
                In particular, "uses" is retrieved to figure out if plugin is
                an absolute or relative plugin.
            assignment (str):
                The placement that this Plugin will go into.

        Returns:
            list[<ways.api.DataPlugin>]:
                Generated plugins. One Plugin object
                if info.get('uses', []) is empty or several, depending on the
                length of the list of values that 'uses' returns.

        '''
        duplicate_uses_message = 'Plugin: "{plug}" has duplicate hierarchies ' \
                                 'in uses, "{uses}". Remove all duplicates.'

        plugins = []
        # There are two types of Context-Plugins, absolute and relative
        # If a plugin has 'uses' defined, that plugin is relative
        # because it needs another plugin/Context to function.
        #
        # We use all Context hierarchies defined in 'uses' to create
        # absolute plugins from each relative plugin
        #
        uses = info.get('uses', [])
        if uses:
            duplicates = _get_duplicates(uses)

            # TODO : "if duplicates:" stops bugs from occurring
            #        if a user wrote a plugin that has duplicate items in
            #        'uses'. This could even just be a copy/paste error
            #        and basically should never be intentional
            #
            #        That said, just raising an error is really bad. We
            #        should just "continue" and log the failure so that
            #        a user can look it up, later
            #
            # TODOID: 751 (search for related sections with this ID)
            #
            if duplicates:
                raise ValueError(duplicate_uses_message.format(
                    plug=plugin, uses=duplicates))

            for hierarchy in uses:
                if is_valid_plugin(hierarchy, info):
                    continue

                context = sit.get_context(
                    hierarchy, assignment=assignment, force=True)
                info_ = cls._make_relative_context_absolute(info, parent=context)

                plugin = plug.DataPlugin(
                    sources=(source, ),
                    info=dict_classes.ReadOnlyDict(info_),
                    assignment=assignment)
                plugins.append((plugin, assignment))
        else:
            plugin = plug.DataPlugin(
                sources=(source, ),
                info=dict_classes.ReadOnlyDict(info),
                assignment=assignment)
            plugins.append((plugin, assignment))

        return plugins

    @classmethod
    def _make_relative_context_absolute(cls, info, parent):
        '''Rebuild the plugin information, using a parent Context.

        Note:
            Not every item in our info is resolved to absolute immediately.
            Only the things that must be absolute (like hierarchy) are changed.
            For all the other things that may still be relative, like mapping,
            max_folder, etc., it's up to the Context to resolve it.

        Args:
            info (dict[str]):
                The information to resolve into absolute information.

        Returns:
            dict[str]: The resolved, absolute information.

        '''
        info = copy.copy(info)
        hierarchy = info['hierarchy']
        hierarchy_ = []
        parent_hierarchy = parent.get_hierarchy()

        root_was_found = False
        for piece in hierarchy:
            if common.PARENT_TOKEN in piece:
                root_was_found = True
                piece = piece.format(root=(common.HIERARCHY_SEP).join(parent_hierarchy))
                # Extend the hierarchy so that we avoid accidentally making
                # a nested tuple (a tuple with tuples in it)
                #
                new_piece_hierarchy = common.split_hierarchy(piece)
                hierarchy_.extend(new_piece_hierarchy)
            else:
                hierarchy_.append(piece)

        # If the user didn't write {root} anywhere in the relative Context,
        # assume that they just wanted to append its hierarchy to the parent
        #
        if not root_was_found:
            hierarchy_ = parent_hierarchy + hierarchy

        info['hierarchy'] = tuple(hierarchy_)

        return info

    def get_plugin_info(self, path):
        '''Given some file path, get its metadata info.

        Args:
            path (str): The path to some directory containing plugin objects.

        Returns:
            dict[str]: The information about this plugin path.

        '''
        def find_info_file(path):
            '''Look up a directory, starting at some path, for an info file.'''
            plugin_info_file = ''
            last_item = None

            # This is a bit ghetto but just add an extra name to the path
            # so that when os.path.dirname happens, we start with the current
            # dir
            #
            path = os.path.join(path, 'asdfasdf')

            while last_item != path:
                last_item = path
                path = os.path.dirname(path)

                for extension in self.get_supported_extensions():
                    plugin_file = os.path.join(path, PLUGIN_INFO_FILE_NAME + extension)

                    if os.path.isfile(plugin_file):
                        plugin_info_file = plugin_file
                        break

            return plugin_info_file

        item = find_info_file(path)

        data = None
        if item:
            data = try_load(item)

        if not data:
            return self._default_plugin_info
        return data

    def __eq__(self, other):
        return self.items == other.items


class FolderDescriptor(FileDescriptor):

    '''A generic abstraction that helps find Plugin objects for our code.

    Note:
        Any FolderDescriptor class that returns back Plugin objects is valid
        (Descriptors can query from a database, locally on file, etc, etc.
        It's all good) except there is one major constraint. FolderDescriptor-like
        objects cannot append to state asynchronously. In other words,
        If a FolderDescriptor manages threads that each find Plugin objects and
        append to a list of Plugin objects whenever each thread finishes, the
        Plugin objects can potentially append out of order - which will lead to
        terrible results.

        It's recommended to not use threading at all unless this return process
        is properly managed (like with a queue or some other kind of idea).

    '''

    def __init__(self, items):
        '''Create the object and initialize its default values.

        Args:
            items (iterable[str] or str):
                The paths that this Descriptor looks for to find Plugin objects.

        '''
        super(FolderDescriptor, self).__init__(items=items)

    def _get_files(self, items):
        if items is None:
            items = self.items

        file_paths = []
        for path in items:
            metadata = self.get_plugin_info(path)

            # Figure out how to iterate to get the files we need
            if metadata.get('recursive', self._default_plugin_info['recursive']):
                files = (os.path.join(root, file_) for root, dirs, files
                         in os.walk(path) for file_ in files)
            else:
                files = (item for item in glob.iglob(os.path.join(path, '*'))
                         if os.path.isfile(item))

            file_paths.extend(sorted(self.filter_plugin_files(files)))

        return file_paths


class GitLocalDescriptor(FolderDescriptor):

    '''An object to describe a local git repository.

    This class simply conforms its input to something that its base class can
    read and then calls it. Otherwise that, it's not particularly special.

    '''

    def __init__(self, path, items, branch='master'):
        '''Create this instance and store its path and branch information.

        Args:
            path (str): The root path to the local git repository.
            items (iterable[str]):
                The folders that contain plugin files. These paths can be either
                absolute or relative to path.
            branch (:obj:`str`, optional):
                The branch of the git repository to use.

        '''
        # TODO : I added this patch to deal with the way that urlparse.parse_qs
        #        gets back items. For some reason, strings would could be as a
        #        list with just a single path like ['/some/location'] instead of
        #        '/some/location'. I should really just sanitize my inputs,
        #        instead of this weird patch
        #
        if not isinstance(path, six.string_types):
            path = path[0]

        self.path = path
        self.branch = branch

        items_ = []
        for item in check.force_itertype(items):
            if os.path.isabs(item) and not os.path.exists(item):
                raise IOError('File/Folder: "{0}" does not exist'.format(item))
            elif os.path.isabs(item) and os.path.exists(item):
                items_.append(item)
                continue

            item_ = os.path.normpath(os.path.join(path, item))
            if not os.path.exists(item_):
                raise IOError(
                    'File/Folder: "{}" is relative but no absolute path could '
                    'be found using path, "{}"'.format(item, path))
            items_.append(item_)

        super(GitLocalDescriptor, self).__init__(items=items_)


class GitRemoteDescriptor(GitLocalDescriptor):

    '''A Descriptor that clones an online Git repository.'''

    def __init__(self, url, items, path='', branch='master'):
        '''Clone the repository locally and read its contents for plugins.

        Args:
            url (str):
                The absolute URL to some git repository local/remote repo.
            items (list[str]):
                The paths to search for plugin files. These items can be
                absolute paths or paths that are relative to the cloned repo.
            path (:obj:`str`, optional):
                The location to clone this repository into.
                If the directory exists, it's assumed that this repository
                was already cloned to the location and its contents are read
                directly. If it does not exist, the repo is cloned there.
                If no path is given, a temporary directory is used.
            branch (:obj:`str`, optional):
                The branch in this repository to checkout and use.
                Default: 'master'.

        '''
        # We do an inner import here for Python 3.3 - Because it looks like
        # GitPython isn't supported for that Python version
        # (pip install GitPython failed when I tried it)
        #
        # TODO : Find an alternative for GitPython
        #
        import git

        if not path:
            path = tempfile.mkdtemp()

        repo = url.split('/')[-1]
        if repo.endswith('.git'):
            repo = repo[:-4]

        if not os.path.isdir(os.path.join(path, repo)):
            git.Repo.clone_from(url, path)

        super(GitRemoteDescriptor, self).__init__(path=path, items=items, branch=branch)


def is_valid_plugin(hierarchy, info):
    '''Detect if a plugin's hierarchy is invalid, given its loaded information.

    A plugin that has cyclic dependencies is considered "invalid".

    Example:
        >>> cat plugin.yml
        ... plugins:
        ...     relative_plugin1:
        ...         hierarchy: mocap
        ...         mapping: '{root}/scenes/mocap'
        ...         uses:
        ...             - mocap

    In the above example, that plugin refers to itself and could cause
    runtime errors.

    Args:
        hierarchy (str): Some hierarchy to check.
        info (dict[str]):
            The loaded information of some plugin from a Plugin Sheet file.

    Returns:
        If the plugin is valid.

    '''
    uses = info.get('uses', [])
    joined = (common.HIERARCHY_SEP).join(info.get('hierarchy', tuple()))
    return hierarchy in uses and joined in uses


def _get_duplicates(obj):
    '''Get all items in some iterable object that occur more than once.

    This is just a helper function - because the original code isn't obvious.
    Args:
        obj (iter): The object to test.

    Returns:
        list: The duplicate items.

    '''
    return [item for item, count in collections.Counter(obj).items() if count > 1]


@common.memoize
def get_loaders():
    '''Get descriptions for how we load Plugin Sheet files.

    This method will return different options, depending on what modules are
    installed in your environment. For example, pyyaml (import yaml) isn't
    shipped with Python in Windows, by default. YAML descriptions are only
    loaded if they're installed on the system.

    Note:
        This function is cached after it is run.

    Returns:
        dict[str]: The installed loaders.

    '''
    def load_hook(info):
        '''A function to modify some loaded data.

        This function is used specifically for use_yaml and use_json,
        to make sure that certain loaded keys come in as certain object types.

        '''
        if 'groups' in info:
            info['groups'] = tuple(info['groups'])
        return info

    def use_yaml():
        '''Try to load a description for YAML.'''
        extensions = ('.yml', '.yaml')

        def is_valid(item):
            '''If this item is a valid YAML file.'''
            return item.endswith(extensions)

        try:
            import yaml
        except ImportError:
            return dict()

        def load_wrap(file_path, func, after):
            '''Load a file using func and then run another function after load.

            Args:
                file_path (str): The absolute path to a file to load.
                func (callable[str]): The loader function to run
                                      (yaml.safe_load/json.load/etc)
                after (callable[str]): The function to load after file_path
                                       has been deserialized.

            Returns:
                The loaded information from func.

            '''
            value = func(file_path)
            after(value)
            return value

        # _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

        # def dict_representer(dumper, data):
        #     return dumper.represent_dict(six.iteritems(data))

        # def dict_constructor(loader, node):
        #     return collections.OrderedDict(loader.construct_pairs(node))

        # yaml.add_representer(collections.OrderedDict, dict_representer)
        # yaml.add_constructor(_mapping_tag, dict_constructor)

        safe_load = functools.partial(yaml.safe_load, Loader=yamlordereddictloader.Loader)
        safe_load_function = functools.partial(load_wrap, func=safe_load, after=load_hook)
        load = functools.partial(yaml.load, Loader=yamlordereddictloader.Loader)
        load_function = functools.partial(load_wrap, func=load, after=load_hook)

        return {
            'yaml': {
                'exceptions': (yaml.constructor.ConstructorError, ),
                'extensions': extensions,
                'is_valid': is_valid,
                'load': (safe_load_function, load_function),
            },
        }

    def use_json():
        '''Try to load a description for JSON.'''
        extensions = ('.json', )

        def is_valid(item):
            '''If this item is a valid JSON file.'''
            return item.endswith(extensions)

        load_function = functools.partial(json.load, object_hook=load_hook)

        return {
            'json': {
                'exceptions': (ValueError, TypeError, IOError),
                'extensions': extensions,
                'is_valid': is_valid,
                'load': (load_function, ),
            },
        }

    output_dict = dict()
    for loader in [use_json, use_yaml]:
        output_dict.update(loader())

    return output_dict


def try_load(path, default=None):
    '''Try our best to load the given file, using a number of different methods.

    The path is assumed to be a file that is serialized, like JSON or YAML.

    Args:
        path (str):
            The absolute path to some file with serialized data.
        default (:obj:`dict`, optional):
            The information to return back if no data could be found.
            Default is an empty dict.

    Returns:
        dict: The information stored on this object.

    '''
    def not_found_raise_error(*args, **kwargs):  # pylint: disable=unused-argument
        '''Just a generic function that will raise an error.

        This function is never run unless no loader was found for the given path.

        '''
        raise ValueError('This exception is just a placeholder')

    if default is None:
        default = dict()

    if not os.path.isfile(path):
        return default

    # Try to find a recommended loader
    try:
        loader = find_loader(path)
    except NotImplementedError:
        loader = not_found_raise_error

    # Have some fallback loaders ready, in case the first loader fails
    loaders = get_loaders()
    loader_options = tuple(loader for _, info in loaders.items()
                           for loader in info['load'])

    all_other_load_options = set(loader_options) - {loader}

    # Try the loaders until some data could be found using one of them

    known_loader_exceptions = tuple(exception for _, info in loaders.items()
                                    for exception in info.get('exceptions', []))

    for loader_option in itertools.chain([loader], all_other_load_options):
        try:
            with open(path, 'r') as file_:
                return loader_option(file_)
        except known_loader_exceptions:  # pylint: disable=catching-non-exception
            pass

    return default


def find_loader(path):
    '''Get the callable method needed to parse this file.

    Args:
        path (str): The path to get the loader of.

    Returns:
        callable[file]: A method that is used to load a Python file object
                        for the given path.

    '''
    lower = path.lower()
    most_preferred_load_index = 0

    for loader in get_loaders().values():
        if loader['is_valid'](lower):
            return loader['load'][most_preferred_load_index]

    extensions = FileDescriptor.get_supported_extensions()

    raise NotImplementedError(
        'Path: "{path}" has no implementation. Expected one of "{opt}".'
        ''.format(path=path, opt=extensions))


def serialize(obj):
    '''Make the given descriptor information into a standard URL encoding.

    Args:
        obj (dict[str]): The Descriptor information to serialize.
        This is normally somehing like
        {'create_using': ways.api.FolderDescriptor}.

    Returns:
        str: The output encoding.

    '''
    # pylint: disable=redundant-keyword-arg
    return parse.urlencode(obj, True)


def conform_decode(info):
    '''Make sure that 'create_using' returns a single string.

    This function is a hacky solution because I don't understand why,
    for some reason, decoding will decode a string as a list.

    TODO: Remove this awful function.

    '''
    output = dict(info)
    try:
        value = output['create_using']
    except KeyError:
        pass
    else:
        if check.is_itertype(value):
            output['create_using'] = value[0]

    return output
