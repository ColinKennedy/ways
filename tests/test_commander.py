#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test Action and Find-related methods and helper functions.'''

# IMPORT STANDARD LIBRARIES
import os
import glob
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
# IMPORT 'LOCAL' LIBRARIES
from . import common_test


class CommanderTestCase(common_test.ContextTestCase):

    '''Test the items in the commander.py module.'''

    def setUp(self):
        '''Store a copy of our environment to restore to when tests complete.'''
        super(CommanderTestCase, self).setUp()
        self.environment = dict(os.environ)

    def test_use_actions_on_context(self):
        '''Run an assigned action Context, using the Context, directly.'''
        hierarchy = '27ztt/whatever'
        common_test.create_action('get_foo', hierarchy)

        # Build our context file and an action to go with it
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
                    mapping: /tmp/{JOB}/{SCENE}/{SHOTNAME}/real_folder
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)
        context = ways.api.get_context(hierarchy)

        # This should not fail
        self.assertTrue(context.actions.get_foo())

    def test_use_actions_on_asset(self):
        '''Run an assigned action Asset, using the Asset, directly.'''
        hierarchy = '27ztt/whatever'
        common_test.create_action('get_foo', hierarchy)

        # Build our context file and an action to go with it
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
                    mapping: /tmp/{JOB}/{SCENE}/{SHOTNAME}/real_folder
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        info = {
            'JOB': 'asdfds',
            'SCENE': 'ttt',
            'SHOTNAME': 'aaaa'
        }
        asset = ways.api.get_asset(info, context=hierarchy)
        self.assertTrue(asset.actions.get_foo())

    def test_use_parent_action(self):
        '''Allow parent Context actions used by child Contexts.'''
        hierarchy = '27ztt/whatever'
        common_test.create_action('get_foo', hierarchy)

        # Build our context file and an action to go with it
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
                    mapping: /tmp/{JOB}/{SCENE}/{SHOTNAME}/real_folder
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        info = {
            'JOB': 'asdfds',
            'SCENE': 'ttt',
            'SHOTNAME': 'aaaa'
        }
        asset = ways.api.get_asset(info, context=hierarchy)
        self.assertTrue(asset.actions.get_foo())

    def test_add_action(self):
        '''Add an Action object to an existing Context.'''
        class SomeAction(ways.api.Action):

            '''Some example Action.'''

            name = 'get_assets'

            @classmethod
            def get_hierarchy(cls):
                '''Gather the hierarchy.'''
                return ('27ztt', 'whatever')

            def __call__(self, *args, **kwargs):
                '''Do something.'''
                # Use env vars if no resolution tags were given
                kwargs.setdefault('resolve_with', 'env')

                base_path = self.context.get_str(*args, **kwargs)
                if not os.path.isdir(base_path):
                    return []
                return glob.glob(os.path.join(base_path, '*'))

        # Build our context file and an action to go with it
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
                    mapping: /tmp/{JOB}/{SCENE}/{SHOTNAME}/real_folder
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('27ztt/whatever')

        # Make a fake environment that has files
        os.environ['JOB'] = 'job_123'
        os.environ['SCENE'] = 'shots'
        os.environ['SHOTNAME'] = 'sh01'

        root_folder = '/tmp/job_123/shots/sh01/real_folder'
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        self.temp_paths.append(root_folder)

        open(os.path.join(root_folder, 'asset.1001.tif'), 'a').close()
        open(os.path.join(root_folder, 'asset.1002.tif'), 'a').close()
        open(os.path.join(root_folder, 'asset.1003.tif'), 'a').close()

        expected_asset_files = [
            '/tmp/job_123/shots/sh01/real_folder/asset.1001.tif',
            '/tmp/job_123/shots/sh01/real_folder/asset.1002.tif',
            '/tmp/job_123/shots/sh01/real_folder/asset.1003.tif',
        ]
        action = context.get_action(SomeAction.name)
        self.assertNotEqual(action, None)
        self.assertEqual(action(), expected_asset_files)

    def test_add_function_to_context(self):
        '''Create a fake-action using just a simple function.'''
        hierarchy = '27ztt/whatever'

        # Build our context file and an action to go with it
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
                    mapping: /tmp/{JOB}/{SCENE}/{SHOTNAME}/real_folder
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context(hierarchy)

        action_name = 'get_database_name'
        database_value = 'some/database/URL/or/something'
        ways.api.add_action(lambda: database_value, name=action_name, hierarchy=hierarchy)

        action = context.get_action(action_name)
        self.assertEqual(action(), database_value)

    def test_no_command_in_context(self):
        '''Try to get an Action object for some Context but have it fail.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
                    mapping: /tmp/{JOB}/{SCENE}/{SHOTNAME}/real_folder
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('27ztt/whatever')

        self.assertEqual(context.get_action('nonexistent_action'), None)

    def tearDown(self):
        '''Put the environment back to the way it was, originally.'''
        super(CommanderTestCase, self).tearDown()

        for key, value in self.environment.items():
            os.environ[key] = value


class FindCommanderTestCase(common_test.ContextTestCase):

    '''Wrap a Context with a Find class and test its methods.'''

    def test_wrap_command_with_find(self):
        '''Call Action objects using a basic Find class.'''
        class SomeAssetAction(ways.api.Action):  # pylint: disable=unused-variable

            '''Some example asset action.'''

            name = 'get_assets'

            @classmethod
            def get_hierarchy(cls):
                '''Gather the hierarchy.'''
                return ('27ztt', 'whatever')

            def __call__(self, obj, *args, **kwargs):
                '''Do something.'''
                # Use env vars if no resolution tags were given
                kwargs.setdefault('resolve_with', 'env')

                base_path = self.context.get_str(*args, **kwargs)
                if not os.path.isdir(base_path):
                    return []
                return glob.glob(os.path.join(base_path, '*'))

        # Build our context file and an action to go with it
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
                    mapping: /tmp/{JOB}/{SCENE}/{SHOTNAME}/real_folder
            ''')


        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('27ztt/whatever')

        # Make a fake environment that has files
        os.environ['JOB'] = 'job_123'
        os.environ['SCENE'] = 'shots'
        os.environ['SHOTNAME'] = 'sh01'

        root_folder = '/tmp/job_123/shots/sh01/real_folder'
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        self.temp_paths.append(root_folder)

        open(os.path.join(root_folder, 'asset.1001.tif'), 'a').close()
        open(os.path.join(root_folder, 'asset.1002.tif'), 'a').close()
        open(os.path.join(root_folder, 'asset.1003.tif'), 'a').close()

        expected_asset_files = [
            '/tmp/job_123/shots/sh01/real_folder/asset.1001.tif',
            '/tmp/job_123/shots/sh01/real_folder/asset.1002.tif',
            '/tmp/job_123/shots/sh01/real_folder/asset.1003.tif',
        ]

        # Build our finder
        find = ways.api.Find(context)
        self.assertEqual(find.get_assets(), expected_asset_files)

    def test_action_not_found(self):
        '''Test to make sure that Actions that are not found return None.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
                    mapping: /tmp/{JOB}/{SCENE}/{SHOTNAME}/real_folder
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('27ztt/whatever')

        find = ways.api.Find(context)

        with self.assertRaises(AttributeError):
            find.get_people_in(place='zimbabwe')

    def test_find_action_default(self):
        '''Return default values for Action methods that Find knows about.'''
        # Build our context file and an action to go with it
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 27ztt/whatever
                    mapping: /tmp/{JOB}/{SCENE}/{SHOTNAME}/real_folder
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('27ztt/whatever')

        ways.api.Find.add_to_defaults('get_assets', [])

        find = ways.api.Find(context)

        with self.assertRaises(AttributeError):
            find.get_assets()
