#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test for the "troubleshooting.rst" documentation page.'''

# IMPORT STANDARD LIBRARIES
import os
import sys
import tempfile
import textwrap

# IMPORT THIRD-PARTY LIBRARIES
import ways.api
from ways import descriptor

# IMPORT LOCAL LIBRARIES
from .. import common_test


class TroubleshootingTestCase(common_test.ContextTestCase):

    '''A group of tests for the code snippets in the troubleshooting page.'''

    def _make_simple_plugin_tree(self):
        contents = textwrap.dedent(
            '''
            plugins:
                a_plugin_root:
                    hierarchy: foo
                    mapping: /jobs
                another_plugin:
                    hierarchy: foo/bar
                    mapping: /jobs/foo/thing
                yet_another_plugin:
                    hierarchy: foo/bar/buzz
                still_more_plugins:
                    hierarchy: foo/fizz
                did_you_know_camels_have_three_eyelids?:
                    hierarchy: foo/fizz/something
                okay_maybe_you_knew_that:
                    hierarchy: foo/fizz/another
                but_I_thought_it_was_cool:
                    hierarchy: foo/fizz/another/here
            '''
        )

        self._make_plugin_folder_with_plugin2(contents=contents)

    def test_basic_descriptor_with_uuid(self):
        '''Test to make sure that a Descriptor is created as we expect.'''
        uuid_ = "foo_bad_path"
        info = {
            "items": "/some/folder/path",
            "create_using": "foo.bar.bad.import.path",
            "uuid": uuid_,
        }

        descriptor_string = \
            'items=%2Fsome%2Ffolder%2Fpath&create_using=foo.bar.bad.import.path&' \
            'uuid=foo_bad_path'

        os.environ['WAYS_DESCRIPTORS'] = descriptor_string

        descriptor_string = _itemize_seralized_descriptor(descriptor_string)
        output = _itemize_seralized_descriptor(ways.api.encode(info))
        self.assertEqual(descriptor_string, output)

        # Add the Descriptor
        ways.api.init_plugins()

        self.assertEqual(
            ways.api.RESOLUTION_FAILURE_KEY,
            ways.api.trace_all_load_results()['descriptors'][uuid_]['reason'])

    def test_basic_descriptor_no_uuid(self):
        '''Test to make sure that a Descriptor is created as we expect.

        The Descriptor result should still exist, just not with any known UUID.

        '''
        info = {
            "items": "/some/folder/path",
            "create_using": "foo.bar.bad.import.path",
        }

        descriptor_string = \
            'items=%2Fsome%2Ffolder%2Fpath&create_using=foo.bar.bad.import.path'

        os.environ['WAYS_DESCRIPTORS'] = descriptor_string

        descriptor_string = _itemize_seralized_descriptor(descriptor_string)
        output = _itemize_seralized_descriptor(ways.api.encode(info))
        self.assertEqual(descriptor_string, output)

        # Add the Descriptor
        ways.api.init_plugins()

        self.assertEqual(
            ways.api.RESOLUTION_FAILURE_KEY,
            ways.api.trace_all_descriptor_results()[0]['reason'])

    def test_not_callable_failure(self):
        '''Create a Descriptor not-callable error matching what the docs.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: 2tt/whatever
            ''')
        self._make_plugin_folder_with_plugin2(contents=contents, register=False)

        example_bad_class = textwrap.dedent(
            """\
            class BadDescriptor(object):

                '''A Descriptor that does not work.'''

                def __init__(self, items):
                    '''Just create the object and do nothing else.'''
                    super(BadDescriptor, self).__init__()

                    self.get_plugins = None

            """)

        some_temp_folder = tempfile.mkdtemp()
        module_file_path = os.path.join(some_temp_folder, 'module.py')
        with open(module_file_path, 'w') as file_:
            file_.write(example_bad_class)

        sys.path.append(some_temp_folder)

        uuid_ = 'some_uuid'
        descriptor_info = {
            'create_using': 'module.BadDescriptor',
            'uuid': uuid_,
            'items': '/something/here',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = ways.api.encode(descriptor_info)
        expected_encoded_string = \
            'items=%2Fsomething%2Fhere&' \
            'create_using=module.BadDescriptor&' \
            'uuid=some_uuid'
        expected_encoded_string = _itemize_seralized_descriptor(expected_encoded_string)
        serialized_info_ = _itemize_seralized_descriptor(serialized_info)

        self.assertEqual(expected_encoded_string, serialized_info_)
        self.assertEqual(ways.api.add_descriptor(serialized_info), None)
        self.assertEqual(ways.api.NOT_CALLABLE_KEY,
                         ways.api.trace_all_load_results()['descriptors'][uuid_]['reason'])

    def test_plugin_import_failure(self):
        '''Try to load a Plugin that doesn't exist and report an error.'''
        os.environ['WAYS_PLUGINS'] = '/some/path/that/doesnt/exist.py'

        ways.api.init_plugins()

        self.assertEqual(
            ways.api.IMPORT_FAILURE_KEY,
            ways.api.trace_all_plugin_results()[0]['reason'])

    def test_plugin_main_failure(self):
        '''Try to load a Plugin but stop because the main function is broken.'''
        uuid_ = 'some_uuid_here'
        contents = textwrap.dedent(
            '''
            import ways.api

            WAYS_UUID = '{uuid_}'

            def main():
                raise ValueError('invalid main function')

            ''').format(uuid_=uuid_)

        root = tempfile.mkdtemp()
        self.temp_paths.append(root)

        path = os.path.join(root, 'example_plugin.py')
        with open(path, 'w') as file_:
            file_.write(contents)

        os.environ['WAYS_PLUGINS'] = path

        ways.api.init_plugins()

        self.assertEqual(
            ways.api.LOAD_FAILURE_KEY,
            ways.api.trace_all_load_results()['plugins'][uuid_]['reason'])

    def test_get_all_hierarchies(self):
        '''Get all of the hierarchies that Ways is allowed to use.'''
        self._make_simple_plugin_tree()

        expected = {('foo', ), ('foo', 'bar'), ('foo', 'bar', 'buzz'),
                    ('foo', 'fizz'), ('foo', 'fizz', 'something'),
                    ('foo', 'fizz', 'another'), ('foo', 'fizz', 'another', 'here')}

        self.assertEqual(expected, ways.api.get_all_hierarchies())

    def test_get_all_hierarchies_full(self):
        '''Get all of the hierarchies that Ways is allowed to use as a tree.'''
        self._make_simple_plugin_tree()

        expected = \
            {
                ('foo', ):
                {
                    ('foo', 'bar'):
                    {
                        ('foo', 'bar', 'buzz'): {},
                    },
                    ('foo', 'fizz'):
                    {
                        ('foo', 'fizz', 'something'): {},
                        ('foo', 'fizz', 'another'):
                        {
                            ('foo', 'fizz', 'another', 'here'): {}
                        },
                    },
                },
            }

        self.assertEqual(expected, ways.api.get_all_hierarchy_trees(full=True))

    def test_get_all_hierarchies_concise(self):
        '''Get all of the hierarchies that Ways is allowed to use as a tree.'''
        self._make_simple_plugin_tree()

        expected = \
            {
                'foo':
                {
                    'bar':
                    {
                        'buzz': {},
                    },
                    'fizz':
                    {
                        'something': {},
                        'another':
                        {
                            'here': {}
                        },
                    },
                },
            }

        self.assertEqual(expected, ways.api.get_all_hierarchy_trees(full=False))

    def test_get_child_hierarchies(self):
        '''Get the Ways hierarchy starting at a certain point.'''
        # '''Get some children. Wait, that didn't come out right.'''
        self._make_simple_plugin_tree()

        hierarchy = ('foo', 'fizz')
        context = ways.api.get_context(hierarchy)
        asset = ways.api.get_asset({}, context=context)

        expected = {('foo', 'fizz', 'something'), ('foo', 'fizz', 'another'),
                    ('foo', 'fizz', 'another', 'here')}

        self.assertEqual(expected, ways.api.get_child_hierarchies(hierarchy))
        self.assertEqual(expected, ways.api.get_child_hierarchies(context))
        self.assertEqual(expected, ways.api.get_child_hierarchies(asset))

    def test_get_child_hierarchy_tree_full(self):
        '''Get the Ways hierarchy starting at a certain point.'''
        self._make_simple_plugin_tree()

        hierarchy = ('foo', 'fizz')
        context = ways.api.get_context(hierarchy)
        asset = ways.api.get_asset({}, context=context)

        expected = \
            {
                ('foo', 'fizz', 'something'): {},
                ('foo', 'fizz', 'another'):
                {
                    ('foo', 'fizz', 'another', 'here'): {},
                },
            }

        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(hierarchy, full=True))
        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(context, full=True))
        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(asset, full=True))

    def test_get_child_hierarchy_tree_concise(self):
        '''Get the Ways hierarchy starting at a certain point.'''
        self._make_simple_plugin_tree()

        hierarchy = ('foo', 'fizz')
        context = ways.api.get_context(hierarchy)
        asset = ways.api.get_asset({}, context=context)

        expected = \
            {
                'something': {},
                'another':
                {
                    'here': {},
                },
            }

        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(hierarchy, full=False))
        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(context, full=False))
        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(asset, full=False))

    def test_trace_method_resolution_plugins_off(self):
        '''Find out the way a method "resolves" its plugins.'''
        self._make_simple_plugin_tree()

        context = ways.api.get_context('foo/bar')
        expected = ['/jobs', '/jobs/foo/thing']
        self.assertEqual(expected, ways.api.trace_method_resolution(context.get_mapping))

        # This check is to make sure that trace_method_resolution didn't
        # break the original functionality of the Context
        #
        self.assertEqual(expected[-1], context.get_mapping())

    def test_trace_method_resolution_plugins_on(self):
        '''Find out the way a method "resolves" its plugins.'''
        self._make_simple_plugin_tree()

        context = ways.api.get_context('foo/bar')
        expected = [('/jobs', context.plugins[0]),
                    ('/jobs/foo/thing', context.plugins[1])]
        self.assertEqual(
            expected, ways.api.trace_method_resolution(context.get_mapping, plugins=True))

        # This check is to make sure that trace_method_resolution didn't
        # break the original functionality of the Context
        #
        self.assertEqual(expected[-1][0], context.get_mapping())

    def test_get_action_hierarchies(self):
        '''Get the hierarchies that an Action name is attached to.'''
        self._make_simple_plugin_tree()

        common_test.build_action('some_action', hierarchy='foo/bar')
        common_test.build_action('some_action', hierarchy='foo/fizz')

        common_test.build_action('another_action', hierarchy='foo/bar')

        expected = {('foo', 'bar'), ('foo', 'fizz')}
        self.assertEqual(expected, ways.api.get_action_hierarchies('some_action'))

    def test_get_action_hierarchies_from_class(self):
        '''Use an Action class to find the hierachies that it can run on.'''
        self._make_simple_plugin_tree()

        action = common_test.build_action('some_action', hierarchy='foo/bar')
        common_test.build_action('some_action', hierarchy='foo/fizz')

        common_test.build_action('another_action', hierarchy='foo/bar')

        expected = {('foo', 'bar'), }
        self.assertEqual(expected, ways.api.get_action_hierarchies(action))

    def test_get_action_hierarchies_from_function(self):
        '''Use an Action function to find the hierachies that it can run on.'''
        self._make_simple_plugin_tree()

        def some_function():
            '''Do some function.'''
            print('Example function return')

        common_test.build_action('some_action', hierarchy='foo/fizz')

        ways.api.add_action(some_function, name='something', hierarchy='foo/bar')
        expected = {('foo', 'bar'), }
        self.assertEqual(expected, ways.api.get_action_hierarchies(some_function))

    def test_get_all_action_hierarchies(self):
        '''Get every Action name and the hierarchies that can use it.'''
        self._make_simple_plugin_tree()

        common_test.build_action('some_action', hierarchy='foo/bar')
        common_test.build_action('some_action', hierarchy='foo/fizz')

        common_test.build_action('another_action', hierarchy='foo/bar')

        self.assertTrue(ways.api.get_all_action_hierarchies())


def _itemize_seralized_descriptor(descriptor):
    '''set[str]: Break a Descriptor string to its parts.'''
    return set(descriptor.split('&'))
