#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test all things related to the cache.py file.'''

# IMPORT STANDARD LIBRARIES
import os
import json
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from . import common_test


class CacheFindPluginTestCase(common_test.ContextTestCase):

    '''Test the different methods that Ways searches for and creates plugins.'''

    def test_find_plugin_in_path(self):
        '''Add a plugin file and then read its contents.'''
        plugin_file = self._make_plugin_folder_with_plugin()

        ways.api.add_search_path(os.path.dirname(plugin_file))
        plugins = ways.api.get_all_plugins()
        plugin_names = [plugin.__class__.__name__ for plugin in plugins]

        self.assertEqual(plugins[0].sources, (plugin_file, ))
        self.assertEqual(plugin_names, ['DataPlugin'])

    # def test_get_default_path_plugin_info(self):
    #     pass

    # TODO : I need to reimplement these methods so that this test will pass
    # def test_get_path_plugin_info(self):
    #     plugin_file = self._make_plugin_folder_with_plugin('UniqueClass')
    #     plugin_info_file_path = os.path.join(os.path.dirname(plugin_file),
    #                                          descriptor.PLUGIN_INFO_FILE_NAME)

    #     assignment = 'tttzt'
    #     plugin_info = {
    #         'assignment': assignment,
    #         'recursive': True,
    #     }

    #     with open(plugin_info_file_path, 'w') as file_:
    #         json.dump(plugin_info, file_)

    #     info = self.cache.get_plugin_info(plugin_info_file_path)
    #     self.assertEqual(info['assignment'], assignment)

    def test_get_recursive_plugin_true(self):
        '''Test that Plugin Sheets are found/created recursively.'''
        plugin_file = self._make_plugin_folder_with_plugin()
        plugin_folder = os.path.dirname(plugin_file)

        # Make a config file that specifies the folder as recursive
        plugin_config_file = os.path.join(
            plugin_folder, ways.api.PLUGIN_INFO_FILE_NAME + '.json')

        assignment = 'tttzt'
        os.environ[ways.api.PRIORITY_ENV_VAR] = 'tttzt'
        plugin_info = {
            'assignment': assignment,
            'recursive': True,

        }

        with open(plugin_config_file, 'w') as file_:
            json.dump(plugin_info, file_)

        # Make an inner Plugin file
        inner_plugin_file = {
            'globals': {},
            'plugins': {
                'some_unique_plugin_name': {
                    'hierarchy': '/something/whatever',
                    'uuid': '9e9c849b-d98f-4a2e-a295-67f643646c97',
                    'data': {
                        'something': 8,
                    },
                },
            },
        }
        inner_folder = os.path.join(plugin_folder, 'inner_folder')
        if not os.path.isdir(inner_folder):
            os.makedirs(inner_folder)

        with open(os.path.join(inner_folder, 'some_plugin.json'), 'w') as file_:
            json.dump(inner_plugin_file, file_)

        ways.api.add_search_path(plugin_folder)

        context = ways.api.get_context('/something/whatever')
        expected_result = {'something': 8}
        self.assertEqual(expected_result, context.data)

    # def test_pass_a_failed_import(self):
    #     '''Pass files that fail to import.

    #     Say we have a file in the same folder directory that may or may-not
    #     be a file that defines a Plugin. If it fails to import, the cache
    #     should just skip over the file and fail gracefully.

    #     '''
    #     pass

    def test_cache_clear(self):
        '''Test that clearing the cache works properly.'''
        common_test.create_plugin(hierarchy=('foo', 'bar'))

        had_plugins = bool(ways.api.get_all_plugins())
        ways.clear()
        self.assertTrue(not ways.api.get_all_plugins() and had_plugins)


class CacheCreatePlugin(common_test.ContextTestCase):

    '''Test the different ways that the cache creates Plugin objects.'''

    def test_add_plugin_to_cache(self):
        '''Add a generic plugin to the cache.'''
        plugin = common_test.create_plugin(hierarchy=('foo', 'bar'))

        found_classes = \
            [obj.__class__ for obj
             in ways.PLUGIN_CACHE['hierarchy'][plugin.get_hierarchy()]['master']]

        self.assertEqual(found_classes, [plugin])

    def test_add_override_plugin(self):
        '''Add multiple plugins to the same hierarchy in the cache.'''
        plugin1 = common_test.create_plugin(hierarchy=('foo', 'bar'))
        plugin2 = common_test.create_plugin(hierarchy=('foo', 'bar'))

        found_classes = \
            [obj.__class__ for obj
             in ways.PLUGIN_CACHE['hierarchy'][plugin1.get_hierarchy()]['master']]

        self.assertEqual(found_classes, [plugin1, plugin2])

    def test_add_non_default_plugin(self):
        '''Add multiple plugins with different assignments to the cache.'''
        assignment = 'job123'
        plugin = common_test.create_plugin(
            hierarchy=('foo', 'bar'), assignment=assignment)

        found_classes = \
            [obj.__class__ for obj
             in ways.PLUGIN_CACHE['hierarchy'][plugin.get_hierarchy()][assignment]]

        self.assertEqual(found_classes, [plugin])

#     def test_get_all_assignments(self):
#         '''Make a number of plugins with different assignments and return them.

#         The Plugin objects that will be made: A master Plugin, a job Plugin,
#         another job Plugin (or override the previous), and another arbitrary
#         Plugin, and the same arbitrary plugin with a different hierarchy.

#         '''
#         class SomePlugin(plugin.Plugin):
#             def get_groups(self):
#                 return ('', )

#             def get_hierarchy(self):
#                 return ('asdf', 'whatever')

#             def get_id(self):
#                 return ''

#             def get_platforms(self):
#                 return ''

#             def get_uuid(self):
#                 return ''

#         class JobPlugin(plugin.Plugin):

#             assignment = 'someJob_123'

#             def get_groups(self):
#                 return ('', )

#             def get_hierarchy(self):
#                 return ('asdf', 'whatever')

#             def get_id(self):
#                 return ''

#             def get_platforms(self):
#                 return ''

#             def get_uuid(self):
#                 return ''

#         class JobPlugin(plugin.Plugin):

#             assignment = 'someJob_123'

#             def get_groups(self):
#                 return ('', )

#             def get_hierarchy(self):
#                 return ('asdf', 'whatever')

#             def get_id(self):
#                 return ''

#             def get_platforms(self):
#                 return ''

#             def get_uuid(self):
#                 return ''

#         class ArbitraryPlugin(plugin.Plugin):

#             assignment = 'ttttt'

#             def get_groups(self):
#                 return ('', )

#             def get_hierarchy(self):
#                 return ('asdf', 'whatever')

#             def get_id(self):
#                 return ''

#             def get_platforms(self):
#                 return ''

#             def get_uuid(self):
#                 return ''

#         class ArbitraryPlugin(plugin.Plugin):

#             assignment = 'ttttt'

#             def get_groups(self):
#                 return ('', )

#             def get_hierarchy(self):
#                 return ('asdf', 'tttt', 'whatever')

#             def get_id(self):
#                 return ''

#             def get_platforms(self):
#                 return ''

#             def get_uuid(self):
#                 return ''

#         expected_assignments = [SomePlugin.assignment, JobPlugin.assignment,
#                                 ArbitraryPlugin.assignment]

#         self.assertEqual(self.cache.get_all_assignments(), expected_assignments)

#     def test_get_plugins_from_assignment(self):
#         class SomePlugin(plugin.Plugin):

#             assignment = 'some_assignment'

#             def get_groups(self):
#                 return ('', )

#             def get_hierarchy(self):
#                 return ('asdf', 'tttt', 'whatever')

#             def get_id(self):
#                 return ''

#             def get_platforms(self):
#                 return ''

#             def get_uuid(self):
#                 return ''

#         class SomePlugin(plugin.Plugin):

#             assignment = 'asfasdf'

#             def get_groups(self):
#                 return ('', )

#             def get_hierarchy(self):
#                 return ('asdf', 'tttt', 'whatever')

#             def get_id(self):
#                 return ''

#             def get_platforms(self):
#                 return ''

#             def get_uuid(self):
#                 return ''

#         self.assertEqual(self.cache.get_all_plugins(assignment='some_assignment'),
#                          [SomePlugin])

#     # def test_set_assignment_by_file(self):
#     #     plugin_folder = tempfile.mkdtemp()
#     #     plugin_info_file = os.path.join(plugin_folder, 'search_path',
#     #                                    '.waypoint_plugin_info.json')
#     #     os.makedirs(os.path.dirname(plugin_info_file))

#     #     example_plugin_info_with_assignment = {
#     #         'assignment': 'something',
#     #     }
#     #     with open(plugin_info_file, 'w') as file_:
#     #         json.dump(example_plugin_info_with_assignment, file_)

#     #     try:
#     #         self._test_set_assignment_by_file(plugin_info_file)
#     #     except Exception:
#     #         raise
#     #     finally:
#     #         shutil.rmtree(plugin_folder)

#     # def _test_set_assignment_by_file(self, plugin_info_file):
#     #     self.cache.add_search_path(os.path.dirname(plugin_info_file))

#     def test_set_assignment_by_plugin(self):
#         pass

#     def test_set_default_plugin(self):
#         pass

#     def test_get_plugin_history(self):
#         pass


def get_example_plugin_file(name='SomePlugin'):
    '''str: Get the contents for a Plugin object to use for testing.'''
    return textwrap.dedent(
        '''\
        from ways import situation as sit

        class {class_name}(plugin.Plugin):
            def get_groups(self):
                return ('', )

            def get_hierarchy(self):
                return ('asdf', 'whatever')

            def get_id(self):
                return ''

            def get_platforms(self):
                return ''

            def get_uuid(self):
                return ''
        '''.format(class_name=name))
