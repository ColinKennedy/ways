#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import unittest
import tempfile
import random
import shutil
import string
import json
import yaml
import sys
import os

# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT 'LOCAL' LIBRARIES
from ways import situation as sit
from ways import common
from ways import cache
import ways.api



_SYS_PATH = list(sys.path)
_ORIGINAL_ENVIRON = os.environ.copy()


class ContextTestCase(unittest.TestCase):

    '''A test case for Context objects that manages temp folders and a cache.'''

    environment = os.environ.copy()

    def setUp(self):
        '''Create a cache and a place to put temp folders, for later cleanup.'''
        self.cache = cache.HistoryCache()
        self.cache.clear()
        sit.clear_aliases()
        sit.clear_contexts()

        self.temp_paths = []

    def _make_plugin_folder_with_plugin2(
            self,
            contents=None,
            ending='.yml',
            folder='',
            register=True):
        if contents is not None:
            contents = yaml.load(contents)

        plugin_file = make_plugin_folder_with_plugin(
            contents=contents, ending=ending, folder=folder)
        self.temp_paths.append(os.path.dirname(plugin_file))

        if register:
            self.cache.add_search_path(os.path.dirname(plugin_file))

        return plugin_file

    def _make_plugin_folder_with_plugin(
            self,
            contents=None,
            ending='.yml',
            folder=''):
        plugin_file = make_plugin_folder_with_plugin(contents=contents, ending=ending, folder=folder)
        self.temp_paths.append(os.path.dirname(plugin_file))
        return plugin_file

    def tearDown(self):
        del sys.path[:]
        sys.path.extend(_SYS_PATH)

        # Delete temp folders and files
        for item in self.temp_paths:
            if os.path.isdir(item):
                shutil.rmtree(item)
            elif os.path.isfile(item):
                os.remove(item)

        # Reset any changes in our environment
        for key in list(os.environ.keys()):
            if key in _ORIGINAL_ENVIRON:
                os.environ[key] = _ORIGINAL_ENVIRON[key]
            else:
                del os.environ[key]


def make_plugin_folder_with_plugin_load(
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
                    'hidden': False,
                    'navigatable': True,
                    'selectable': True,
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


def make_plugin_folder_with_plugin_yaml(contents=None, folder=''):
    '''str: Make a folder and put a plugin inside of it.'''
    # We import yaml in this function so that, just in case the user doesn't
    # have pyyaml installed, we can minimize the number of unittests effected
    #
    import yaml
    return make_plugin_folder_with_plugin_load(func=yaml.dump, ending='.yml', contents=contents, folder=folder)


def make_plugin_folder_with_plugin_json(contents=None, folder=''):
    '''str: Make a folder and put a plugin inside of it.'''
    return make_plugin_folder_with_plugin_load(func=json.dump, ending='.json', contents=contents, folder=folder)


def make_plugin_folder_with_plugin(ending='.yml', contents=None, folder=''):
    '''str: Make a folder and put a plugin inside of it.'''
    if ending in ['.yml', '.yaml']:
        return make_plugin_folder_with_plugin_yaml(
            contents=contents, folder=folder)
    elif ending == '.json':
        return make_plugin_folder_with_plugin_json(
            contents=contents, folder=folder)


def create_action(text, hierarchy=('a', )):
    '''Create some action with a name and hierarchy.'''
    # pylint: disable=W0612
    class ActionObj(ways.api.Action):

        '''Some action.'''

        name = text

        @classmethod
        def get_hierarchy(cls):
            return hierarchy

        def __call__(self, *args, **kwargs):
            return True


def create_plugin(hierarchy=('a', ), assignment=common.DEFAULT_ASSIGNMENT, platforms=('*', ), data=None):
    '''Create some Plugin with a name and hierarchy.

    This is a convenience method just to make unittests shorter. This should
    not be used in production.

    '''
    if data is None:
        data = dict()

    # pylint: disable=W0612
    class PluginObj(ways.api.Plugin):

        _data = data

        @classmethod
        def get_assignment(cls):
            '''str: some assignment.'''
            return assignment

        @classmethod
        def get_hierarchy(cls):
            '''tuple[str]: The hierarchies.'''
            return hierarchy

        def get_platforms(self):
            return platforms

    return PluginObj


if __name__ == '__main__':
    print(__doc__)

