#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import tempfile
import textwrap
import unittest
import os

# IMPORT LOCAL LIBRARIES
from ways import common
from . import common_test
import ways.api


class ContextAttributeTestCase(common_test.ContextTestCase):
    def test_get_plugins_in_platform(self):
        '''Only get back plugin objects that are OK for the current platform.'''
        common_test.create_plugin(hierarchy=('maya', 'exports'), platforms='linux')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='linux')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='*')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='windows')

        context = ways.api.get_context('maya/exports/thing')

        expected_number_of_plugins = len(
            self.cache.plugin_cache['hierarchy'][('maya', 'exports', 'thing')]['master'])
        expected_number_of_plugins += len(
            self.cache.plugin_cache['hierarchy'][('maya', 'exports')]['master'])

        self.assertEqual(expected_number_of_plugins, 4)
        # This context should be missing at least one plugin
        self.assertTrue(len(context.plugins) != expected_number_of_plugins)

    def test_get_plugins_in_defined_platform(self):
        common_test.create_plugin(hierarchy=('maya', 'exports'), platforms='linux')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='linux')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='*')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='windows')

        os.environ[ways.api.PLATFORMS_ENV_VAR] = 'windows'

        context = ways.api.get_context('maya/exports/thing')

        expected_number_of_plugins = len(
            self.cache.plugin_cache['hierarchy'][('maya', 'exports', 'thing')]['master'])
        expected_number_of_plugins += len(
            self.cache.plugin_cache['hierarchy'][('maya', 'exports')]['master'])

        self.assertEqual(expected_number_of_plugins, 4)
        # This context should be missing at least one plugin
        self.assertEqual(len(context.plugins), 2)


class ContextAliasTestCase(common_test.ContextTestCase):

    '''Test the aliasing features for Context objects.'''

    def test_aliased_context(self):
        '''Create a context that points to another context with an alias.'''
        common_test.create_plugin(hierarchy=('maya', 'scenes'), platforms='*')

        ways.api.register_context_alias('maya_scenes', 'maya/scenes')
        context = ways.api.get_context('maya_scenes')

        self.assertNotEqual(context, None)
        self.assertEqual(context.hierarchy, ('maya_scenes', ))
        self.assertEqual(len(context.plugins), 1)

    def test_recursive_aliased_context(self):
        '''Create a context that points to a context and to another context.'''
        common_test.create_plugin(hierarchy=('maya', 'scenes'), platforms='*')

        ways.api.register_context_alias('maya_scenes', 'maya/scenes')
        ways.api.register_context_alias('scenes', 'maya_scenes')
        context = ways.api.get_context('scenes')

        self.assertNotEqual(context, None)
        self.assertEqual(context.hierarchy, ('scenes', ))
        self.assertEqual(len(context.plugins), 1)

    def test_follow_alias_context(self):
        '''Create a context that finds the original non-aliased context.'''
        common_test.create_plugin(hierarchy=('maya', 'scenes'), platforms='*')

        ways.api.register_context_alias('maya_scenes', 'maya/scenes')
        context = ways.api.get_context('maya_scenes', follow_alias=True)

        self.assertNotEqual(context, None)
        self.assertEqual(context.hierarchy, ('maya', 'scenes', ))
        self.assertEqual(len(context.plugins), 1)

#     def test_alias_part(self):
#         '''Search for single words to replace with a new alias.'''
#         contents = get_generic_job_config()
#         plugin_file = self._make_plugin_folder_with_plugin2(contents=contents)

#         self.cache.add_search_path(os.path.dirname(plugin_file))

#         context = ways.api.get_context('foo/scene')
#         self.assertNotEqual(context, None)

#     def test_alias_multipart(self):
#         '''Resolve an alias that spans more than one part of a hierarchy.'''

#     def test_alias_recursive_multipart(self):
#         '''Resolve a multi-part hierarchy that is more than one layer deep.'''


class ContextCreateTestCase(common_test.ContextTestCase):
    def test_context_set_metadata(self):
        '''Set the metadata on a context and spread its settings to others.'''
        data = { 'css': { 'background-color': 'red', } }
        common_test.create_plugin(hierarchy=('some', 'context'), platforms='', data=data)

        context1 = ways.api.get_context('some/context')
        context1.data['css']['background-color'] = 'red'
        context2 = ways.api.get_context('some/context')

        self.assertEqual(context1.data['css']['background-color'],
                         context2.data['css']['background-color'])

    def test_context_restore_default(self):
        '''Change a Context's data and then return it to its default.'''
        data = { 'css': { 'background-color': 'blue', } }
        common_test.create_plugin(hierarchy=('some', 'context'), platforms='', data=data)

        context = ways.api.get_context('some/context')
        context.data['css']['background-color'] = 'red'
        context.revert()

        self.assertEqual(context.data['css']['background-color'], 'blue')

    def test_context_checkout_all(self):
        '''Change from one Context to another, after it is defined.'''
        data = { 'css': { 'background-color': 'blue', } }
        assignment = 'job'
        common_test.create_plugin(hierarchy=('some', 'context'), platforms='', data=data)
        common_test.create_plugin(
            hierarchy=('some', 'context'), platforms='', assignment=assignment, data=data)

        context = ways.api.get_context('some/context')
        context.data['css']['background-color'] = 'white'
        context = context.checkout(assignment)

        self.assertNotEqual(context.data['css']['background-color'], 'white')

    def test_context_fails_because_of_bad_hierarchy(self):
        '''Fail to create a Context because bad characters were given.'''
        common_test.create_plugin(hierarchy=('s^ome', 'context'))

        with self.assertRaises(ValueError):
            context1 = ways.api.get_context('s^ome/context')

#     def test_context_checkout_override_all2(self):
#         context = ways.api.Context('/some/context')
#         context.data['metadata'].set('background-color', 'white')

#         cache.Brain.checkout('some_job')
#         self.assertNotEqual(context.data['metadata']['background-color'], 'white')

#     def test_context_checkout_override_context(self):
#         context = ways.api.Context('/some/context')
#         context2 = ways.api.Context('/another/context')

#         context.data['metadata'].set('background-color', 'white')
#         context.checkout('some_job')

#         context2 = ways.api.Context('/another/context')
#         context2.data['metadata'].set('background-color', 'white')

#         self.assertNotEqual(context.data['metadata']['background-color'], 'white')
#         self.assertEqual(context.data['metadata']['background-color'], 'white')

    def test_assignment_from_config_file(self):
        assignment = 'job'
        config = textwrap.dedent(
            '''
            assignment: {assignment}
            '''.format(assignment=assignment))

        plugin = textwrap.dedent(
            '''
            plugins:
                something:
                    hierarchy: foo
                    mapping: bar
            ''')
        root = tempfile.mkdtemp()
        directory = os.path.join(root, 'folders', 'here')
        os.makedirs(directory)

        config_file = os.path.join(
            directory, ways.api.PLUGIN_INFO_FILE_NAME + '.yml')

        with open(config_file, 'w') as file_:
            file_.write(config)

        with open(os.path.join(directory, 'sheet.yml'), 'w') as file_:
            file_.write(plugin)

        self.cache.add_search_path(directory)

        context = ways.api.get_context('foo', assignment=assignment)

        self.assertEqual(assignment, context.assignment)

    def test_assignment_from_config_file_recursive(self):
        '''Get plugins (and assignment info) from a folder recursively.'''
        assignment = 'job'
        config = textwrap.dedent(
            '''
            assignment: {assignment}
            recursive: true
            '''.format(assignment=assignment))

        plugin = textwrap.dedent(
            '''
            plugins:
                something:
                    hierarchy: foo
                    mapping: bar
            ''')
        root = tempfile.mkdtemp()
        assignment_directory = os.path.join(root, 'folders', 'here')

        config_file = os.path.join(
            assignment_directory, ways.api.PLUGIN_INFO_FILE_NAME + '.yml')

        directory = os.path.join(assignment_directory, 'something', 'else')
        os.makedirs(directory)

        with open(config_file, 'w') as file_:
            file_.write(config)

        with open(os.path.join(directory, 'sheet.yml'), 'w') as file_:
            file_.write(plugin)

        self.cache.add_search_path(assignment_directory)

        context = ways.api.get_context('foo', assignment=assignment)

        self.assertEqual(assignment, context.assignment)

    def test_assignment_from_file(self):
        assignment = 'job'
        contents = textwrap.dedent(
            '''
            globals:
                assignment: {assignment}
            plugins:
                something:
                    hierarchy: foo
                    mapping: bar
            '''.format(assignment=assignment))

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('foo', assignment=assignment)

        self.assertEqual(assignment, context.assignment)

    def test_assignment_from_plugin(self):
        assignment = 'job'
        contents = textwrap.dedent(
            '''
            plugins:
                something:
                    assignment: {assignment}
                    hierarchy: foo
                    mapping: bar
                another:
                    hierarchy: foo
                    mapping: bar/thing

            '''.format(assignment=assignment))

        self._make_plugin_folder_with_plugin2(contents=contents)

        context1 = ways.api.get_context('foo', assignment=assignment)
        self.assertEqual(assignment, context1.assignment)

        context2 = ways.api.get_context('foo')
        self.assertEqual('', context2.assignment)
        self.assertEqual('bar/thing', context2.get_mapping())

    def test_all_assignments(self):
        '''Test all methods of setting plugin assignment at once.'''
        assignment = 'job'
        config = textwrap.dedent(
            '''
            assignment: {assignment}
            recursive: true
            '''.format(assignment=assignment))

        plugin1 = textwrap.dedent(
            '''
            globals:
                assignment: fizz
            plugins:
                something:
                    hierarchy: foo
                    mapping: from_globals
                local:
                    assignment: buzz
                    hierarchy: foo
                    mapping: from_plugin
            ''')

        plugin2 = textwrap.dedent(
            '''
            plugins:
                another:
                    hierarchy: foo
                    mapping: from_config
            '''
        )

        root = tempfile.mkdtemp()
        assignment_directory = os.path.join(root, 'folders', 'here')

        config_file = os.path.join(
            assignment_directory, ways.api.PLUGIN_INFO_FILE_NAME + '.yml')

        directory = os.path.join(assignment_directory, 'something', 'else')
        os.makedirs(directory)

        with open(config_file, 'w') as file_:
            file_.write(config)

        with open(os.path.join(directory, 'sheet.yml'), 'w') as file_:
            file_.write(plugin1)

        with open(os.path.join(directory, 'sheet2.yml'), 'w') as file_:
            file_.write(plugin2)

        self.cache.add_search_path(assignment_directory)

        context1 = ways.api.get_context('foo', assignment=assignment)
        context2 = ways.api.get_context('foo', assignment='fizz')
        context3 = ways.api.get_context('foo', assignment='buzz')

        self.assertEqual(assignment, context1.get_assignment())
        self.assertEqual('fizz', context2.get_assignment())
        self.assertEqual('buzz', context3.get_assignment())
        self.assertEqual('from_config', context1.get_mapping())
        self.assertEqual('from_globals', context2.get_mapping())
        self.assertEqual('from_plugin', context3.get_mapping())

    def test_find_context_assignment(self):
        '''Test that plugins in a non-default assignment is findable.

        We do this by creating a Context that has no plugins assigned under
        "master", forcing Ways to search for plugins in other assignments.

        '''
        os.environ[ways.api.PRIORITY_ENV_VAR] = (os.pathsep).join(['master', 'job'])

        contents = textwrap.dedent(
            '''
            globals:
                assignment: job
            plugins:
                some_plugin:
                    hierarchy: foo
            ''')
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo')
        self.assertNotEqual(None, context)
        self.assertEqual(('foo', ), context.get_hierarchy())


class ContextInheritanceTestCase(unittest.TestCase):

    '''Test the ways the a Context is meant to inherit from Context objects.

    Context objects from others through their hierarchy.
    If a Context exists at a lower hierarchy

    '''

    def test_context_inherit(self):
        '''Create a Context that gets its values from various Plugin objects.'''
        data = { 'css': { 'background-color': 'blue', } }
        common_test.create_plugin(hierarchy=('some', ), platforms='', data=data)
        common_test.create_plugin(hierarchy=('some', 'kind', 'of', 'context'), platforms='')

        context = ways.api.get_context('some/kind/of/context')

        self.assertEqual(context.data['css']['background-color'], 'blue')


def get_generic_job_config():
    return textwrap.dedent(
        '''
        globals: {}
        plugins:
            alpha_root:
                findable: false
                hierarchy: root
                mapping: ''
                uuid: 3d149cb8-a5fe-43bd-85b4-dcb08238e023

            # Job plugins
            all_plugin_linux:
                findable: false
                hidden: false
                hierarchy: '{root}/linux'
                mapping: ''
                navigatable: true
                platforms:
                    - linux
                selectable: true
                uuid: 817f0173-4a5c-42d6-a2a9-60935d26c368
                uses:
                    - root

            all_plugin_windows:
                findable: false
                hidden: false
                hierarchy: '{root}/windows'
                mapping: '{DRIVE}\'
                mapping_details:
                    DRIVE:
                        parse:
                            regex: '[zZ]:'
                            glob: 'Z:'
                        required: false
                navigatable: true
                platforms:
                    - windows
                selectable: true
                uuid: c4b20e19-7040-4526-a822-a662c9daf7bf
                uses:
                    - root

            job_base_plugin_linux:
                findable: true
                hierarchy: '{root}/job'
                mapping: '{root}/jobs/{JOB}'
                mapping_details:
                    JOB:
                        mapping: '{JOB_NAME}_{JOB_ID}'
                        parse:
                            glob: '*'
                    JOB_NAME:
                        casing: snakecase
                        parse:
                            regex: '[a-z]{3,}[a-zA-Z]{3,}'
                            glob: '*'
                    JOB_ID:
                        parse:
                            regex: \d{3,}
                            glob: '*'
                uuid: 4b3dc3bc-fd9b-40ff-8175-26a5b9223fc7
                uses:
                    - root/linux

            job_base_plugin_windows:
                findable: true
                hierarchy: '{root}/job'
                mapping: '{root}\{JOB}'
                mapping_details:
                    JOB:
                        mapping: '{JOB_NAME}_{JOB_ID}'
                        parse:
                            glob: '*'
                    JOB_NAME:
                        casing: snakecase
                        parse:
                            regex: '[a-z]{3,}[a-zA-Z]{3,}'
                            glob: '*'
                    JOB_ID:
                        parse:
                            regex: '\d{3,}'
                            glob: '*'
                uuid: 4b3dc3bc-fd9b-40ff-8175-26a5b9223fc7
                uses:
                    - root/windows

            scene_base_plugin_linux:
                hierarchy: '{root}/scene'
                mapping: '{root}/{SCENE}'
                mapping_details:
                    SCENE:
                        casing: capscase
                        parse:
                            regex: '[A-Z]{5,}'
                            glob: '*'
                platforms:
                    - linux
                    - darwin
                uses:
                    - /job
                uuid: 040a5511-aa53-42ae-9bc3-eb332841616e

            scene_base_plugin_windows:
                hierarchy: '{root}/scene'
                mapping: '{root}\\{SCENE}'
                mapping_details:
                    SCENE:
                        casing: capscase
                        parse:
                            regex: '[A-Z]{5,}'
                            glob: '*'
                platforms:
                    - windows
                uses:
                    - /job
                uuid: 040a5511-aa53-42ae-9bc3-eb332841616e

        ''')


if __name__ == '__main__':
    import unittest
    unittest.main()
    # print(__doc__)

