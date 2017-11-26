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

    def _setup_actions(self, main=False):
        '''Create a couple Actions and add them to Ways.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo:
                    hierarchy: some/hierarchy
                another:
                    hierarchy: action/hierarchy
                bar_plugin:
                    hierarchy: bar
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

        if main:
            contents += textwrap.dedent(
                """
                def main():
                    '''Add defaults for actions.'''
                    ways.api.add_action_default('some_action', [])
                """
            )
        self._make_plugin(contents=contents)

    def test_action_0001_fail(self):
        '''Call an Action from a hierarchy that doesn't have one should fail.'''
        self._setup_actions()

        for index, hierarchy in enumerate(['some/hierarchy', 'action/hierarchy', 'bar']):
            context = ways.api.get_context(hierarchy)
            if index == 2:
                with self.assertRaises(AttributeError):
                    context.actions.some_action()
            else:
                context.actions.some_action()

    def test_action_0002_default(self):
        '''Call a missing Action that has a default value assigned.'''
        self._setup_actions(main=True)

        for index, hierarchy in enumerate(['some/hierarchy', 'action/hierarchy', 'bar']):
            context = ways.api.get_context(hierarchy)
            context.actions.some_action()


class AppendingTestCase(common_test.ContextTestCase):

    '''Test that appending works correctly.'''

    def test_all_append_types(self):
        '''Test that all types of appends work correctly.'''
        contents = textwrap.dedent(
            '''
            plugins:
                root:
                    hierarchy: foo
                another:
                    hierarchy: bar
                    mapping: a_mapping
                absolute_append:
                    hierarchy: foo
                    data:
                        something_to_add: here
                relative_append:
                    hierarchy: ''
                    mapping: something
                    path: true
                    uses:
                        - foo
                        - bar
            ''')

        self._make_plugin_sheet(contents=contents)

        foo_context = ways.api.get_context('foo')
        bar_context = ways.api.get_context('bar')

        self.assertEqual('something', foo_context.get_mapping())
        self.assertEqual('a_mappingsomething', bar_context.get_mapping())
        self.assertEqual({'something_to_add': 'here'}, foo_context.data)


class CustomClassTestCase(common_test.ContextTestCase):

    '''All tests for class injection.'''

    def setUp(self):
        '''Create a basic hierarchy and add it to Ways.'''
        super(CustomClassTestCase, self).setUp()

        contents = textwrap.dedent(
            '''
            plugins:
                foo:
                    hierarchy: some/thing/context
                    mapping: /jobs/{JOB}/folder
            ''')

        self._make_plugin_sheet(contents=contents)

    def test_default_asset(self):
        '''Check that a default Asset is returned when we expect it.'''
        info = {'foo': 'bar'}
        context = 'some/thing/context'
        asset = ways.api.get_asset(info, context)
        self.assertEqual(ways.api.Asset, asset.__class__)

    def test_custom_class_simple(self):
        '''Register a class to Ways.'''
        contents = textwrap.dedent(
            """
            import ways.api

            class SomeNewAssetClass(object):

                '''Some class that will take the place of our Asset.'''

                def __init__(self, info, context):
                    '''Create the object.'''
                    super(SomeNewAssetClass, self).__init__()
                    self.context = context

                def example_method(self):
                    '''Run some method.'''
                    return 8

                def another_method(self):
                    '''Run another method.'''
                    return 'bar'

            def main():
                '''Register a default Asset class for 'some/thing/context.'''
                context = ways.api.get_context('some/thing/context')
                ways.api.register_asset_class(SomeNewAssetClass, context)
            """)

        self._make_plugin(contents=contents)

        asset = ways.api.get_asset({'JOB': 'something'}, context='some/thing/context')
        self.assertEqual(8, asset.example_method())

    def test_custom_class_init(self):
        '''Make a custom __init__ method for a custom Asset class.'''
        contents = textwrap.dedent(
            """
            import ways.api

            class AssetClass(object):
                def __init__(self):
                    super(AssetClass, self).__init__()


            def a_custom_init_function(info, context, *args, **kwargs):
                '''Purposefully ignore the info and context that gets passed.'''
                return asset_class(info, *args, **kwargs)


            def main():
                '''Make a default Asset with a non-default init function.'''
                ways.api.register_asset_class(
                    AssetClass, 'some/thing/context', init=a_custom_init_function)
            """)

        asset = ways.api.get_asset({}, 'some/thing/context')
        self.assertNotEqual(ways.api.Asset, asset)
