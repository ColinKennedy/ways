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

        default = []
        ways.api.add_action_default('get_assets', default)
        self.assertEqual(default, context.actions.get_assets())
