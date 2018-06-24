#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Generic classes and functions to reuse for the Ways test suite.'''

# IMPORT STANDARD LIBRARIES
import os
import sys
import json
import shutil
import tempfile
import unittest

# IMPORT THIRD-PARTY LIBRARIES
from six.moves import io

# IMPORT WAYS LIBRARIES
import ways
import ways.api
from ways.base import situation as sit
from ways.helper import common

_SYS_PATH = list(sys.path)
_ORIGINAL_ENVIRON = os.environ.copy()


class ContextTestCase(unittest.TestCase):

    '''A test case for Context objects that manages temp folders and a cache.'''

    environment = os.environ.copy()

    def setUp(self):
        '''Create a cache and a place to put temp folders, for later cleanup.'''
        ways.clear()
        sit.clear_aliases()
        sit.clear_contexts()

        self.temp_paths = []

    def _make_plugin_sheet(
            self,
            contents=None,
            ending='.yml',
            folder='',
            register=True):
        '''Create a Plugin Sheet using some folder and register it to Ways.'''
        import yaml

        if isinstance(contents, dict):
            contents = yaml.dump(contents)

        if contents is not None:
            contents = yaml.load(contents)

        plugin_file = make_folder_plugin(
            contents=contents, ending=ending, folder=folder)
        self.temp_paths.append(os.path.dirname(plugin_file))

        if register:
            ways.api.add_search_path(os.path.dirname(plugin_file))

        return plugin_file

    def _make_plugin(self, contents):
        '''str: Create a Python plugin file and load it into Ways.'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as file_:
            file_.write(contents)
            name = file_.name

        ways.api.add_plugin(name)
        self.temp_paths.append(name)

        return name

    def tearDown(self):
        '''Reset any changes made to our environment during test runs.'''
        del sys.path[:]
        sys.path.extend(_SYS_PATH)

        # Delete temp folders and files
        for item in self.temp_paths:
            if os.path.isdir(item):
                try:
                    shutil.rmtree(item)
                except WindowsError:  # pylint: disable=undefined-variable
                    pass
            elif os.path.isfile(item):
                os.remove(item)

        # Reset any changes in our environment
        for key in list(os.environ.keys()):
            if key in _ORIGINAL_ENVIRON:
                os.environ[key] = _ORIGINAL_ENVIRON[key]
            else:
                del os.environ[key]


class Capturing(list):

    '''a Python context that silences lines written to stdout.'''

    def __init__(self):
        '''Create a handle for stringio and for stdout.'''
        super(Capturing, self).__init__()
        self._stdout = []
        self._stringio = None

    def __enter__(self):
        '''Start capturing stdout by piping sys.stdout to a temporary list.'''
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self

    def __exit__(self, *args):
        '''Store the lines captured from stdout onto this instance.

        Also, restore the old pipe to stdout so that we can print to
        the terminal again.

        '''
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio
        sys.stdout = self._stdout


def make_plugin_folder(
        func,
        ending,
        contents=None,
        folder=''):
    '''str: Make a folder and put a plugin inside of it.'''
    if contents is None:
        contents = {
            'globals': {},
            'plugins': {
                'some_unique_plugin_name': {
                    'hierarchy': '/asdf/whatever',
                    'uuid': '0d255517-dbbf-4a49-a8d0-285a06b2aa6d',
                    'id': 'models',
                },
            }
        }

    if folder == '':
        folder = tempfile.mkdtemp()

    plugin_file = os.path.join(folder, 'example_plugin' + ending)

    with open(plugin_file, 'w') as file_:
        func(contents, file_)

    return plugin_file


def make_folder_plugin_yaml(contents=None, folder=''):
    '''str: Make a folder and put a plugin inside of it.'''
    # We import yaml in this function so that, just in case the user doesn't
    # have pyyaml installed, we can minimize the number of unittests effected
    #
    import yaml
    return make_plugin_folder(
        func=yaml.dump, ending='.yml', contents=contents, folder=folder)


def make_folder_plugin_json(contents=None, folder=''):
    '''str: Make a folder and put a plugin inside of it.'''
    return make_plugin_folder(
        func=json.dump, ending='.json', contents=contents, folder=folder)


def make_folder_plugin(ending='.yml', contents=None, folder=''):
    '''str: Make a folder and put a plugin inside of it.'''
    if ending in ['.yml', '.yaml']:
        return make_folder_plugin_yaml(contents=contents, folder=folder)
    elif ending == '.json':
        return make_folder_plugin_json(contents=contents, folder=folder)

    return ''


def create_action(text, hierarchy=('a', )):
    '''Create some action with a name and hierarchy.'''
    class ActionObj(ways.api.Action):

        '''Some action.'''

        name = text

        @classmethod
        def get_hierarchy(cls):
            return hierarchy

        def __call__(self, *args, **kwargs):
            return True

    return ActionObj


def create_plugin(hierarchy=('a', ),
                  assignment=common.DEFAULT_ASSIGNMENT,
                  platforms=('*', ),
                  data=None):
    '''Create some Plugin with a name and hierarchy.

    This is a convenience method just to make unittests shorter. This should
    not be used in production.

    '''
    if data is None:
        data = dict()

    class PluginObj(ways.api.Plugin):

        '''A generic Plugin.'''

        _data = data

        @classmethod
        def get_assignment(cls):
            '''str: some assignment.'''
            return assignment

        @classmethod
        def get_hierarchy(cls):
            '''tuple[str]: The hierarchies.'''
            return hierarchy

        @classmethod
        def get_platforms(cls):
            '''Get the platforms.'''
            return platforms

    return PluginObj


def build_action(action, folders=None, hierarchy='some/context'):
    '''Create an Action object and return it.'''
    if folders is None:
        folders = []

    class SomeAction(ways.api.Action):

        '''A subclass that will automatically be registered by Ways.

        The name of the class (SomeAction) can be anything but the name
        property must be correct. Also, get_hierarchy must match the Context
        hierarchy that this action will apply to.

        '''

        name = action
        items = []

        @classmethod
        def get_hierarchy(cls):
            return hierarchy

        def __call__(self, obj, folders):
            '''Do something.'''
            return folders

    SomeAction.items = folders
    return SomeAction
