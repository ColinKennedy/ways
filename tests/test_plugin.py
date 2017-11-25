#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Build tests for Plugin objects - like how they are made and their methods.'''

# IMPORT STANDARD LIBRARIES
import os
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from . import common_test


class PluginCreationTestCase(common_test.ContextTestCase):

    '''Test to make sure that Plugin objects are created, properly.'''

    def test_create_plugin_from_class(self):
        '''Build a plugin from a Python class.'''
        hierarchy = ('maya', 'exports')
        plugin = common_test.create_plugin(hierarchy=hierarchy)

        found_instances = ways.PLUGIN_CACHE['hierarchy'][hierarchy]['master']
        self.assertEqual([plug.__class__ for plug in found_instances], [plugin])

    # def test_create_plugin_from_loaded_python_file(self):
    #     '''Find a Python file and load it to get its Python class.'''

    # def test_create_plugin_from_inline_json_file(self):
    #     '''Find a Python file that defines a plugin using JSON.'''

    # def test_create_plugin_from_inline_yaml_file(self):
    #     '''Find a Python file that defines a plugin using YAML.'''

    def test_create_plugin_from_json(self):
        '''Read a JSON file directly and make a plugin from it.'''
        hierarchy = ('27ztt', 'whatever')

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

        found_instances = ways.PLUGIN_CACHE['hierarchy'][hierarchy]['master']
        self.assertEqual([plug.get_hierarchy() for plug in found_instances],
                         [hierarchy])

    def test_create_plugin_from_yaml(self):
        '''Read a YAML file directly and make a plugin from it.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                some_unique_plugin_name:
                    hierarchy: 27ztt/whatever
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents, ending='.yml')

        context = ways.api.get_context('27ztt/whatever')
        self.assertEqual(context.get_hierarchy(), ('27ztt', 'whatever'))

    def test_failure_duplicate_uses(self):
        '''When a user has two exact same hierarchies in uses, raise Exception.'''
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

    '''Test the methods on a generic ways.api.Plugin class.'''

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
                    'hierarchy': '31tt/whatever',
                    'uuid': '0d255517-dbbf-4a49-a8d0-285a06b2aa6d',
                },
            },
        }

        plugin_file = self._make_plugin_folder_with_plugin(contents=contents)

        ways.api.add_search_path(os.path.dirname(plugin_file))
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
                    'hierarchy': '31tt/whatever',
                    'uuid': 'some_uuid',
                },
                'b_parse_plugin': {
                    'mapping': '/jobs/{JOB}/some_kind/of/real_folders/inner',
                    'mapping_details': {
                        'JOB': {
                            'mapping': '{JOB_NAME}_{JOB_ID}',
                            'parse': {},
                        },
                    },
                    'groups': tuple(),  # Just adding this plugin for coverage
                    'hierarchy': '31tt/whatever',
                    'uuid': 'a_unique_uuid',
                },
                'c_parse_plugin': {
                    'mapping': '/jobs/{JOB}/some_kind/of/real_folders/inner',
                    'mapping_details': {
                        'JOB': {
                            'mapping': '{JOB_NAME}_{JOB_ID}',
                            'parse': {},
                        },
                    },
                    'groups': ('some_groups', 'another'),
                    'hierarchy': '31tt/whatever',
                    'uuid': '0d255517-dbbf-4a49-a8d0-285a06b2aa6d',
                },
            },
        }
        plugin_file = self._make_plugin_folder_with_plugin(contents=contents)

        ways.api.add_search_path(os.path.dirname(plugin_file))
        context = ways.api.get_context('31tt/whatever')
        self.assertEqual(context.get_groups(), ('some_groups', 'another'))


class PluginMergeMethodTestCase(common_test.ContextTestCase):

    '''Test that individual methods work for relative plugins.'''

    def test_get_mapping(self):
        '''Make sure get_mapping works properly with a relative Plugin setup.'''
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
