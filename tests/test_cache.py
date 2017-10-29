#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import unittest
import tempfile
import textwrap
import shutil
import json
import os

# IMPORT 'LOCAL' LIBRARIES
from . import common_test
import ways.api


class CacheFindPluginTestCase(common_test.ContextTestCase):
    def test_find_plugin_in_path(self):
        '''Add a plugin file and then read its contents.'''
        plugin_file = self._make_plugin_folder_with_plugin()

        self.cache.add_search_path(os.path.dirname(plugin_file))
        plugins = self.cache.get_all_plugins()
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
        plugin_file = self._make_plugin_folder_with_plugin()
        plugin_folder = os.path.dirname(plugin_file)

        # Make a config file that specifies the folder as recursive
        plugin_config_file = os.path.join(
            plugin_folder, ways.api.PLUGIN_INFO_FILE_NAME + '.json')

        assignment = 'tttzt'
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
                    'hidden': True,
                    'navigatable': False,
                    'selectable': True,
                    'hierarchy': '/something/whatever',
                    'uuid': '9e9c849b-d98f-4a2e-a295-67f643646c97',
                    'id': 'rigs',
                },
            }
        }
        inner_folder = os.path.join(plugin_folder, 'inner_folder')
        if not os.path.isdir(inner_folder):
            os.makedirs(inner_folder)

        with open(os.path.join(inner_folder, 'some_plugin.json'), 'w') as file_:
            json.dump(inner_plugin_file, file_)

        self.cache.add_search_path(plugin_folder)
        plugins = self.cache.get_all_plugins()

        plugin_names = [plugin.get_id() for plugin in plugins]
        self.assertEqual(plugin_names, ['models', 'rigs'])

    # def test_pass_a_failed_import(self):
    #     '''Pass files that fail to import.

    #     Say we have a file in the same folder directory that may or may-not
    #     be a file that defines a Plugin. If it fails to import, the cache
    #     should just skip over the file and fail gracefully.

    #     '''
    #     pass

    def test_cache_clear(self):
        common_test.create_plugin(hierarchy=('foo', 'bar'))

        had_plugins = bool(self.cache.get_all_plugins())
        self.cache.clear()
        self.assertTrue(not self.cache.get_all_plugins() and had_plugins)


class CacheCreatePlugin(common_test.ContextTestCase):
    def test_add_plugin_to_cache(self):
        plugin = common_test.create_plugin(hierarchy=('foo', 'bar'))

        found_classes = \
            [obj.__class__ for obj
             in self.cache.plugin_cache['hierarchy'][plugin.get_hierarchy()]['master']]

        self.assertEqual(found_classes, [plugin])

    def test_add_override_plugin(self):
        plugin1 = common_test.create_plugin(hierarchy=('foo', 'bar'))
        plugin2 = common_test.create_plugin(hierarchy=('foo', 'bar'))

        found_classes = \
            [obj.__class__ for obj
             in self.cache.plugin_cache['hierarchy'][plugin1.get_hierarchy()]['master']]

        self.assertEqual(found_classes, [plugin1, plugin2])

    def test_add_non_default_plugin(self):
        assignment = 'job123'
        plugin = common_test.create_plugin(
            hierarchy=('foo', 'bar'), assignment=assignment)

        found_classes = \
            [obj.__class__ for obj
             in self.cache.plugin_cache['hierarchy'][plugin.get_hierarchy()][assignment]]

        self.assertEqual(found_classes, [plugin])

#     def test_get_all_assignments(self):
#         '''Make a number of plugins with different assignments and return them.

#         The Plugin objects that will be made: A master Plugin, a job Plugin,
#         another job Plugin (or override the previous), and another arbitrary
#         Plugin, and the same arbitrary plugin with a different hierarchy.

#         '''
#         class SomePlugin(plugin.Plugin):
#             def is_hidden(self):
#                 return True

#             def is_navigatable(self):
#                 return False

#             def is_selectable(self):
#                 return False

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

#             def is_hidden(self):
#                 return True

#             def is_navigatable(self):
#                 return False

#             def is_selectable(self):
#                 return False

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

#             def is_hidden(self):
#                 return True

#             def is_navigatable(self):
#                 return False

#             def is_selectable(self):
#                 return False

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

#             def is_hidden(self):
#                 return True

#             def is_navigatable(self):
#                 return False

#             def is_selectable(self):
#                 return False

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

#             def is_hidden(self):
#                 return True

#             def is_navigatable(self):
#                 return False

#             def is_selectable(self):
#                 return False

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

#             def is_hidden(self):
#                 return True

#             def is_navigatable(self):
#                 return False

#             def is_selectable(self):
#                 return False

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

#             def is_hidden(self):
#                 return True

#             def is_navigatable(self):
#                 return False

#             def is_selectable(self):
#                 return False

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
    return textwrap.dedent(
        '''\
        from ways import situation as sit

        class {class_name}(plugin.Plugin):
            def is_hidden(self):
                return True

            def is_navigatable(self):
                return False

            def is_selectable(self):
                return False

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


if __name__ == '__main__':
    print(__doc__)

