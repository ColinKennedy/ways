#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Build tests for Plugin objects - like how they are made and their methods.'''

# IMPORT STANDARD LIBRARIES
import tempfile
import textwrap
import os

# IMPORT 'LOCAL' LIBRARIES
from . import common_test
import ways.api


class PluginCreationTestCase(common_test.ContextTestCase):

    '''Test to make sure that Plugin objects are created, properly.'''

    def test_create_plugin_from_class(self):
        '''Build a plugin from a Python class.'''
        hierarchy = ('maya', 'exports')
        plugin = common_test.create_plugin(hierarchy=hierarchy)

        found_instances = self.cache.plugin_cache['hierarchy'][hierarchy]['master']
        self.assertEqual([plug.__class__ for plug in found_instances], [plugin])

    # def test_create_plugin_from_loaded_python_file(self):
    #     '''Find a Python file and load it to get its Python class.'''

    # def test_create_plugin_from_inline_json_file(self):
    #     '''Find a Python file that defines a plugin using JSON.'''

    # def test_create_plugin_from_inline_yaml_file(self):
    #     '''Find a Python file that defines a plugin using YAML.'''

    def test_create_plugin_from_json(self):
        '''Read a JSON file directly and make a plugin from it.'''
        hierarchy = ('27ztt' , 'whatever')

        # Build our context file and an action to go with it
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
            ''')

        self._make_plugin_folder_with_plugin2(
            contents=contents, ending='.json')

        found_instances = self.cache.plugin_cache['hierarchy'][hierarchy]['master']
        self.assertEqual([plug.get_hierarchy() for plug in found_instances],
                         [hierarchy])

    def test_create_plugin_from_yaml(self):
        '''Read a YAML file directly and make a plugin from it.'''
        hierarchy = ('27ztt' , 'whatever')
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                some_unique_plugin_name:
                    hierarchy: 27ztt/whatever
            ''')

        folder = tempfile.mkdtemp()

        self._make_plugin_folder_with_plugin2(contents=contents, ending='.yml')

        context = ways.api.get_context('27ztt/whatever')
        self.assertEqual(context.get_hierarchy(), ('27ztt', 'whatever'))

    def test_failed_plugin_duplicate_uses(self):
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    mapping: 'something'
                    hierarchy: 27ztt
                relative_plugin:
                    mapping: '{root}/foo'
                    hierarchy: '{root}/whatever'
                    uses:
                        - 27ztt
                        - 27ztt
                    data:
                        something: true

            ''')

        # TODO : Make this function actually pass. And once it passes, test it
        #        just checking for data like this:
        #
        # TODOID: 751 (search for related sections with this ID)
        #
        with self.assertRaises(ValueError):
            self._make_plugin_folder_with_plugin2(contents=contents, ending='.yml')

    # def test_failed_plugin_self_referring_uses(self):
    #     contents = textwrap.dedent(
    #         '''
    #         globals: {}
    #         plugins:
    #             a_parse_plugin:
    #                 mapping: 'something'
    #                 hierarchy: 27ztt
    #             relative_plugin:
    #                 mapping: '{root}/foo'
    #                 hierarchy: '{root}/whatever'
    #                 uses:
    #                     - 27ztt/whatever

    #         ''')

    #     self._make_plugin_folder_with_plugin2(contents=contents, ending='.yml')

    #     # TODO : What do I do about this one?
    #     # contents = textwrap.dedent(
    #     #     '''
    #     #     globals: {}
    #     #     plugins:
    #     #         another:
    #     #             mapping: 'something/else'
    #     #             hierarchy: 27ztt/whatever

    #     #     ''')

    #     # plugin_path = self._make_plugin_folder_with_plugin2(
    #     #     contents=contents, ending='.yml')

    #     context = ways.api.get_context('27ztt/whatever/whatever')
    #     raise ValueError(context.get_mapping())
    #     raise ValueError(context.get_hierarchy())
    #     raise ValueError(context)


class PluginMethodTestCase(common_test.ContextTestCase):
    def test_get_groups_failed(self):
        '''If a Plugin is created incorrectly, try to fix the groups.'''
        contents = {
            'globals': {},
            'plugins': {
                'a_parse_plugin': {
                    'mapping': '/jobs/{JOB}/some_kind/of/real_folders',
                    'mapping_details': {
                        'JOB': {
                            'mapping': '{JOB_NAME}_{JOB_ID}',
                            'parse': {},
                        },
                    },
                    'groups': ('', '', ''),
                    'hidden': False,
                    'navigatable': True,
                    'selectable': True,
                    'hierarchy': '31tt/whatever',
                    'uuid': '0d255517-dbbf-4a49-a8d0-285a06b2aa6d',
                    'id': 'models',
                },
            },
        }

        plugin_file = self._make_plugin_folder_with_plugin(contents=contents)

        self.cache.add_search_path(os.path.dirname(plugin_file))
        context = ways.api.get_context('31tt/whatever')
        self.assertEqual(context.get_groups(), ('*', ))

    def test_get_groups(self):
        '''Test get_groups on a Plugin object.'''
        contents = {
            'globals': {},
            'plugins': {
                'a_parse_plugin': {
                    'mapping': '/jobs/{JOB}/some_kind/of/real_folders',
                    'mapping_details': {
                        'JOB': {
                            'mapping': '{JOB_NAME}_{JOB_ID}',
                            'parse': {},
                        },
                    },
                    'groups': ('*', ),
                    'hidden': False,
                    'navigatable': True,
                    'selectable': True,
                    'hierarchy': '31tt/whatever',
                    'uuid': '0d255517-dbbf-4a49-a8d0-285a06b2aa6d',
                    'id': 'models',
                },
            },
        }
        plugin_file = self._make_plugin_folder_with_plugin(contents=contents)

        self.cache.add_search_path(os.path.dirname(plugin_file))
        context = ways.api.get_context('31tt/whatever')
        self.assertEqual(context.get_groups(), ('*', ))


class PluginMergeMethodTestCase(common_test.ContextTestCase):

    '''Test that individual methods work for relative plugins.'''

    def test_get_mapping(self):
        contents = textwrap.dedent(
            '''
            plugins:
                root:
                    hierarchy: foo
                    mapping: something
                relative:
                    hierarchy: '{root}/bar'
                    mapping: '{root}/yyz'
                    uses:
                        - foo

            '''
        )
        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('foo/bar')
        expected_mapping = 'something/yyz'
        self.assertEqual(expected_mapping, context.get_mapping())


if __name__ == '__main__':
    print(__doc__)

