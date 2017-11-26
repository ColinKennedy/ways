#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test for the "getting_started.rst" documentation page.'''

# IMPORT STANDARD LIBRARIES
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from .. import common_test


class GettingStartedTestCase(common_test.ContextTestCase):

    '''Test the code listed in the getting_started.rst documentation file.'''

    def test_hello_world_yaml(self):
        '''Make the most minimal plugin.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('some/context')
        self.assertNotEqual(context, None)

    def test_yaml_with_metadata(self):
        '''Test loading a YAML file with some metadata.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
                    data:
                        some:
                            arbitrary:
                                - info1
                                - info2
                                - 3
                                - bar
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('some/context')
        data = context.data['some']['arbitrary']
        self.assertEqual(data, ['info1', 'info2', 3, 'bar'])

    def test_persistent_context(self):
        '''Check to make sure that Context objects are Flyweights (persistent).'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
                    data:
                        some:
                            arbitrary:
                                - info1
                                - info2
                                - 3
                                - bar
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('some/context')
        context.data['some']['arbitrary'].append('bar2')

        def some_function():
            '''Do the test using a Context in a different scope.'''
            a_new_context = ways.api.get_context('some/context')
            data = ['info1', 'info2', 3, 'bar', 'bar2']
            self.assertEqual(data, a_new_context.data['some']['arbitrary'])

        some_function()

    def test_asset_initialization(self):
        '''Test to make sure that every way to instantiate an Asset works.'''
        contents = textwrap.dedent(
            '''
            plugins:
                job:
                    hierarchy: 'some/context'
                    mapping: /jobs/{JOB}/here
            ''')

        self._make_plugin_sheet(contents=contents)

        path = '/jobs/foo/here'

        # Test the different ways to initialize this asset
        asset1 = ways.api.get_asset((('JOB', 'foo'), ), 'some/context')
        asset2 = ways.api.get_asset({'JOB': 'foo'}, 'some/context')
        asset3 = ways.api.get_asset(path, 'some/context')

        job = 'foo'
        value = asset3.get_value('JOB')

        self.assertEqual(asset1, asset2, asset3)
        self.assertEqual(path, asset3.get_str())
        self.assertEqual(job, value)

    def test_context_action(self):
        '''Create an Action and register it to a Context.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
            ''')

        self._make_plugin_sheet(contents=contents)

        folders = ['/library', 'library/grades', 'comp', 'anim']

        common_test.build_action('create', folders)

        context = ways.api.get_context('some/context')
        output = context.actions.create(folders)
        self.assertEqual(folders, output)

    def test_context_action_function(self):
        '''Test that action functions work correctly.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
            ''')

        self._make_plugin_sheet(contents=contents)

        folders = ['/library', 'library/grades', 'comp', 'anim']

        def some_action(obj):
            '''Return our folders.'''
            del obj
            return folders

        context = ways.api.get_context('some/context')
        ways.api.add_action(some_action, hierarchy='some/context')
        context.actions.some_action()

        # If you don't want to use the name of the function, you can give the action
        # a name
        #
        ways.api.add_action(some_action, 'custom_name', hierarchy='some/context')
        self.assertEqual(folders, context.actions.custom_name())

    def test_context_vs_asset_action(self):
        '''Test the differences between Context.actions and Asset.actions.'''
        contents = textwrap.dedent(
            '''
            plugins:
                job:
                    hierarchy: 'some/context'
                    mapping: /jobs/{JOB}/here
            ''')

        self._make_plugin_sheet(contents=contents)

        folders = ['/library', 'library/grades', 'comp', 'anim']
        common_test.build_action('get_info', folders)

        asset = ways.api.get_asset({'JOB': 'foo'}, context='some/context')
        asset_info = asset.actions.get_info(folders)

        context = ways.api.get_context('some/context')
        standalone_context_info = context.actions.get_info(folders)

        asset_context_info = asset.context.actions.get_info(folders)

        self.assertEqual(folders, asset_info)
        self.assertEqual(folders, standalone_context_info)
        self.assertEqual(folders, asset_context_info)
