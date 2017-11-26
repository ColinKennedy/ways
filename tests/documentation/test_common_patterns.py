#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tests for all of the "common_patterns.rst" documentation page.'''

# IMPORT STANDARD LIBRARIES
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from .. import common_test


class AutoFindTestCase(common_test.ContextTestCase):

    '''All tests to help auto-find Context objects.'''

    def _setup_common_plugins(self):
        '''Create some plugins and register them to Ways for some tests.'''
        contents = textwrap.dedent(
            '''
            plugins:
                something:
                    hierarchy: foo
                    mapping: /jobs/{JOB}/shots
            ''')

        self._make_plugin_sheet(contents=contents)

    def test_autofind_basic(self):
        '''Find the Context for an Asset, using the Context's mapping.'''
        self._setup_common_plugins()

        value = '/jobs/someJobName_12391231/shots'
        asset = ways.api.get_asset(value)

        self.assertNotEqual(None, asset)

    def test_autofind_dict(self):
        '''Find the Context for an Asset, using a dict and Context mapping.'''
        self._setup_common_plugins()

        value = {'JOB': 'someJobName_12391231'}
        asset = ways.api.get_asset(value)

        self.assertNotEqual(None, asset)

    def test_autofind_fail(self):
        '''Show what happens when Ways cannot find the right Context.'''
        contents = textwrap.dedent(
            '''
            plugins:
                something:
                    hierarchy: foo
                    mapping: /jobs/{JOB}/shots
                another:
                    hierarchy: bar
                    mapping: generic.{JOB}.string.here
            ''')

        self._make_plugin_sheet(contents=contents)

        value = {'JOB': 'someJobName_12391231'}

        with self.assertRaises(ValueError):
            ways.api.get_asset(value)

    def test_autofind_with_details(self):
        '''Find a Context by parsing the mapping using mapping_details.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                something:
                    hierarchy: foo
                    mapping: /jobs/{JOB}/shots
                    mapping_details:
                        JOB:
                            parse:
                                regex: '\d+'
                another:
                    hierarchy: bar
                    mapping: generic.{JOB}.string.here
                    mapping_details:
                        JOB:
                            parse:
                                regex: '\w+'
            ''')

        self._make_plugin_sheet(contents=contents)

        value = {'JOB': 'someJobName_12391231'}
        asset = ways.api.get_asset(value)
        self.assertEqual(('bar', ), asset.context.get_hierarchy())


class ActionTestCase(common_test.ContextTestCase):

    '''A set of tests for Action objects.'''

    def test_action_fail(self):
        '''Call an Action from a hierarchy that doesn't have one should fail.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo:
                    hierarchy: some/hierarchy
                another:
                    hierarchy: action/hierarchy
            ''')

        self._make_plugin_sheet(contents=contents)

        contents = textwrap.dedent(
            '''
            import ways.api

            class ActionOne(ways.api.Action):

                name = 'some_action'

                @classmethod
                def get_hierarchy(cls):
                    return 'some/hierarchy'

                def __call__(self, obj):
                    return ['t', 'a', 'b', 'z']


            class ActionTwo(ways.api.Action):

                name = 'some_action'

                @classmethod
                def get_hierarchy(cls):
                    return 'action/hierarchy'

                def __call__(self, obj):
                    return [1, 2, 4, 5.4, 6, -2]
            ''')

        self._make_plugin(contents=contents)

        for index, hierarchy in enumerate(['some/hierarchy', 'action/hierarchy', 'bar']):
            context = ways.api.get_context(hierarchy)
            if index == 2:
                with self.assertRaises(AttributeError):
                    context.actions.some_action()
            else:
                context.actions.some_action()
