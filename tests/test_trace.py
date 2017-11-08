#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Query things about our API objects.

For example, this module will test to make sure that you can query the actions
available to a Context or another object. Or if you want to know what plugins
make up a Context and where those plugins exist on-disk (for debugging or
whatever other purpose). Or some other reportive info that we want to know.

'''

# IMPORT STANDARD LIBRARIES
import os
import tempfile
import textwrap

# IMPORT WAYS LIBRARIES
import ways
import ways.api
from ways import common

# IMPORT LOCAL LIBRARIES
from . import common_test

# TODO : The types of plugin-trace tests that we need to make sure works
#
# - defined in file
# - defined out of file
# - defined out of file - imported from another file
# - explicitly registered
# - explicitly registered function
#
# TODO : Also test for loaded descriptors
# TODO : Have a way to test which descriptor loaded which plugins?
# TODO : Get plugin by UUID
# TODO : Get all plugin UUIDs
# TODO : Make these tests lighter by only defining actions once in a single
#        function and just reuse it, instead of relying on ActionRegistry to do
#        it for you
# TODO : Get parse order
# TODO : Possibly make a set parse order function


# pylint: disable=too-few-public-methods
class Common(common_test.ContextTestCase):

    '''Just a class that has a couple setup methods that subclasses need.'''

    def _setup_simple_contexts(self):
        '''Build a generic set of Context objects and return one of them.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            parse:
                                regex: '[0-9]+'
                                glob: '*'
            ''')

        plugin_file = self._make_plugin_folder_with_plugin2(contents=contents)

        ways.api.add_search_path(os.path.dirname(plugin_file))

        return ways.api.get_context('a/context')


class TraceTestCase(Common):

    '''Test methods that are meant to help find info in Ways objects.'''

    # def test_get_assignments(self):
    #     pass

    # def test_get_action(self):
    #     pass

    @classmethod
    def _get_object_interfaces(cls, obj):
        '''For some given object, get back a bunch of other, related objects.

        Many methods in this test are meant to "trace" whatever object you
        give it, regardless of type. So to ensure full test coverage,
        it's recommended to use this method as much as possible.

        Yields:
            Ways classes to test with.

        '''
        context = ways.api.trace_context(obj)
        finder_ = ways.api.Find(context)
        yield context
        yield context.actions
        yield finder_
        yield ways.api.AssetFinder(finder_, asset=None)

    def test_trace_assignment(self):
        '''Get the assignment of various objects.'''
        context = self._setup_simple_contexts()

        for obj in self._get_object_interfaces(context):
            obj = ways.api.trace_assignment(obj)
            self.assertNotEqual(obj, ways.api.DEFAULT_ASSIGNMENT)

        self.assertEqual(ways.api.trace_assignment('invalid_input'),
                         ways.api.DEFAULT_ASSIGNMENT)

    def test_trace_context(self):
        '''Make sure that we can get the Context of any Ways object.'''
        context = self._setup_simple_contexts()

        for obj in self._get_object_interfaces(context):
            obj = ways.api.trace_context(obj)
            self.assertTrue(isinstance(obj, ways.api.Context))

    def test_trace_hierarchy(self):
        '''Find the hierarchy hidden in any Ways object.'''
        context = self._setup_simple_contexts()

        for obj in self._get_object_interfaces(context):
            obj = ways.api.trace_hierarchy(obj)
            self.assertTrue(obj)

        self.assertFalse(ways.api.trace_hierarchy(['invalid_input']))

    def test_trace_actions(self):
        '''Reasonably try to get actions for any Ways object.

        Not all Ways objects have (should?) have actions associated.

        But technically any Context will have actions so any object
        that contains a Context should theoretically have actions that we get.

        '''
        context = self._setup_simple_contexts()
        _init_actions()

        # TODO : Yield with nose?
        for obj in self._get_object_interfaces(context):
            actions = ways.api.trace_actions(obj, duplicates=False)
            self.assertEqual(len(actions), 2)

    def test_trace_actions_duplicates(self):
        '''Get all actions in a Ways object.'''
        _init_actions()

        context = self._setup_simple_contexts()

        # TODO : Yield with nose?
        for obj in self._get_object_interfaces(context):
            actions = ways.api.trace_actions(obj, duplicates=True)
            self.assertEqual(len(actions), 2)

    def test_trace_action_names(self):
        '''Get the names of every action of a Ways object.'''
        context = self._setup_simple_contexts()
        _init_actions()

        # TODO : Yield with nose?
        for obj in self._get_object_interfaces(context):
            actions = ways.api.trace_action_names(obj)
            self.assertEqual(len(actions), 2)

    def test_trace_action_info(self):
        '''Test to make sure that we can get back all actions, by name.'''
        context = self._setup_simple_contexts()
        _init_actions()

        # TODO : Yield with nose?
        for obj in self._get_object_interfaces(context):
            actions = ways.api.trace_actions_table(obj)
            self.assertTrue(actions)

    def test_get_all_hierarchies(self):
        '''Define a bunch of plugins and then get their hierarchies.'''
        hierarchies = {
            ('foo', ),
            ('foo', 'bar'),
            ('frodo', 'baggins', ),
        }

        for hierarchy in hierarchies:
            common_test.create_plugin(hierarchy=hierarchy)

        self.assertEqual(hierarchies, ways.api.get_all_hierarchies())

    def test_get_child_hierarchies(self):
        '''Get all hierarchies that depend on a given hierarchy.'''
        hierarchies = {
            ('another', ),
            ('another', 'here'),

            ('foo', ),
            ('foo', 'bar'),
            ('foo', 'bar', 'thing'),
            ('foo', 'bar', 'fizz'),
            ('foo', 'bar', 'fizz', 'buzz'),

            ('frodo', 'baggins', ),
        }

        for hierarchy in hierarchies:
            common_test.create_plugin(hierarchy=hierarchy)

        expected_children = {
            ('foo', 'bar', 'fizz'),
            ('foo', 'bar', 'thing'),
            ('foo', 'bar', 'fizz', 'buzz'),
        }
        self.assertEqual(expected_children,
                         set(ways.api.get_child_hierarchies(('foo', 'bar'))))

    def test_get_all_hierarchies_as_dict_full(self):
        '''Print all of the hierarhies as a big dictionary.'''
        _setup_hierarchies()

        expected = {
            ('another', ): {
                ('another', 'here'): {},
            },
            ('foo', ): {
                ('foo', 'bar'): {
                    ('foo', 'bar', 'fizz'): {
                        ('foo', 'bar', 'fizz', 'buzz'): {},
                    },
                    ('foo', 'bar', 'thing'): {},
                },
            },
            ('frodo', ): {
                ('frodo', 'baggins'): {},
            },
        }

        self.assertEqual(expected, ways.api.get_all_hierarchy_trees(full=True))

    def test_get_all_hierarchies_as_dict_full(self):
        '''Print all of the hierarhies as a big dictionary.'''
        _setup_hierarchies()

        expected = {
            ('another', ): {
                ('another', 'here'): {},
            },
            ('foo', ): {
                ('foo', 'bar'): {
                    ('foo', 'bar', 'fizz'): {
                        ('foo', 'bar', 'fizz', 'buzz'): {},
                    },
                    ('foo', 'bar', 'thing'): {},
                },
            },
            ('frodo', ): {
                ('frodo', 'baggins'): {},
            },
        }

        self.assertEqual(expected, ways.api.get_all_hierarchy_trees(full=True))

    def test_get_child_hierarchies_as_dict_part(self):
        '''Print all of the hierarhies at the given hierarchy.'''
        _setup_hierarchies()

        expected = {
            'foo': {
                'bar': {
                    'fizz': {
                        'buzz': {},
                    },
                    'thing': {},
                },
            },
        }

        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(('foo', 'bar'), full=False))

    def test_get_child_hierarchies_as_dict_full(self):
        '''Print all of the hierarhies at the given hierarchy.'''
        _setup_hierarchies()

        expected = {
            ('foo', ): {
                ('foo', 'bar'): {
                    ('foo', 'bar', 'fizz'): {
                        ('foo', 'bar', 'fizz', 'buzz'): {},
                    },
                    ('foo', 'bar', 'thing'): {},
                },
            },
        }

        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(('foo', 'bar'), full=True))


# TODO : Make sure to run tests to make sure that the contents of dir
#        are what we expect
#
#        Also add tests for core - because that makes sense, too
#
class DirTestCase(Common):

    '''Test that methods that rely on Ways object.__dir__ work properly.'''

    def test_get_dir(self):
        '''Test that dir(Context.actions) will return back all available actions.

        This test is tangentially related to trace because it uses trace to
        find the actions.

        Todo:
            This is a weird place for this test. Move it someplace else.

        '''
        _init_actions()

        context = self._setup_simple_contexts()

        expected_actions = ways.api.trace_action_names(context)
        found_context_actions = dir(context.actions)

        common_context_actions = [action for action in expected_actions
                                  if action in found_context_actions]

        asset = ways.api.get_asset({'SHOT_NAME': '0123'}, context='a/context')
        found_asset_actions = dir(asset.actions)
        common_asset_actions = [action for action in expected_actions
                                if action in found_asset_actions]

        self.assertEqual(expected_actions, common_context_actions)
        self.assertEqual(expected_actions, common_asset_actions)


class FailureTestCase(common_test.ContextTestCase):

    '''Test the different ways that Plugins and Descriptors can fail to load.'''

    def test_module_import_failure(self):
        '''Capture a failed plugin that couldn't be imported by Python.'''
        name = 'something_foo'
        hierarchy = ('foo', 'bar')
        contents = textwrap.dedent(
            '''
            import nuke
            from ways import commander

            class SomeAction(ways.api.Action):

                name = '{name}'

                @classmethod
                def get_hierarchy(self):
                    return {hierarchy}

                def __call__(self, *args, **kwargs):
                    pass

            '''
        ).format(name=name, hierarchy=hierarchy)

        temp_folder = tempfile.mkdtemp()
        temp_name = os.path.basename(tempfile.NamedTemporaryFile(suffix='.py', delete=True).name)
        temp_file = os.path.join(temp_folder, temp_name)

        with open(temp_file, 'w') as file_:
            file_.write(contents)

        ways.api.load_plugin(temp_file)

        # Because the module failed to import, the action won't be visible
        action = ways.get_action(name, hierarchy=hierarchy)
        self.assertEqual(action, None)

        # We should at least see some information about this PluginSheet
        results = ways.api.trace_all_plugin_results_info()
        self.assertTrue(temp_file in results)
        info = results.get(temp_file, dict())
        self.assertEqual(info.get('status'), common.FAILURE_KEY)
        self.assertEqual(info.get('reason'), common.IMPORT_FAILURE_KEY)

    def test_module_load_failure(self):
        '''Capture a failed plugin that couldn't be loaded by Python.

        This happens when the file that this plugin was defined in could be
        loaded but something in it main function that we ran created an error.

        '''
        name = 'something_foo'
        hierarchy = ('foo', 'bar')
        contents = textwrap.dedent(
            '''
            import ways.api

            class SomeAction(ways.api.Action):

                name = '{name}'

                @classmethod
                def get_hierarchy(self):
                    return {hierarchy}

                def __call__(self, *args, **kwargs):
                    pass

            def main():
                raise ValueError('Something that went wrong')

            '''
        ).format(name=name, hierarchy=hierarchy)

        temp_folder = tempfile.mkdtemp()
        temp_name = os.path.basename(tempfile.NamedTemporaryFile(suffix='.py', delete=True).name)
        temp_file = os.path.join(temp_folder, temp_name)

        with open(temp_file, 'w') as file_:
            file_.write(contents)

        ways.api.load_plugin(temp_file)

        # The module is importable so we can find out action
        action = ways.get_action(name, hierarchy=hierarchy)
        self.assertNotEqual(action, None)

        # But main() fails, so the plugin is a registered failure
        results = ways.api.trace_all_plugin_results_info()
        self.assertTrue(temp_file in results)
        info = results.get(temp_file, dict())
        self.assertEqual(info.get('status'), common.FAILURE_KEY)
        self.assertEqual(info.get('reason'), common.LOAD_FAILURE_KEY)


def _init_actions():
    '''Create a couple random classes and register them to Ways.'''
    common_test.create_action('another_action_here')
    common_test.create_action('action_here')


def _setup_hierarchies():
    '''A function that just creates a generic set of hierarchies.'''
    hierarchies = {
        ('another', ),
        ('another', 'here'),

        ('foo', ),
        ('foo', 'bar'),
        ('foo', 'bar', 'thing'),
        ('foo', 'bar', 'fizz'),
        ('foo', 'bar', 'fizz', 'buzz'),

        ('frodo', 'baggins', ),
    }

    for hierarchy in hierarchies:
        common_test.create_plugin(hierarchy=hierarchy)
