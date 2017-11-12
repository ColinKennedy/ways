#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test Context-related methods and bugs.

Many other modules have tests that relate to or heavily-rely on Context objects
but this module is here to test to make sure that Context objects will
behave properly in other test modules.

'''

# IMPORT STANDARD LIBRARIES
import os
import tempfile
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from . import common_test


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

    def test_alias_with_starting_sep(self):
        '''Make an alias that uses "/" as the first character.'''
        common_test.create_plugin(hierarchy=('maya', 'scenes'), platforms='*')

        ways.api.register_context_alias('/maya_scenes', 'maya/scenes')
        context = ways.api.get_context('/maya_scenes')
        self.assertNotEqual(context, None)
        self.assertEqual(context.hierarchy, ('/', 'maya_scenes'))
        self.assertEqual(len(context.plugins), 1)

    def test_alias_cannot_be_itself(self):
        '''Try to force an alias to be itself.'''
        common_test.create_plugin(hierarchy=('maya', 'scenes'), platforms='*')

        with self.assertRaises(ValueError):
            ways.api.register_context_alias('maya_scenes', 'maya_scenes')

    def test_alias_already_defined(self):
        '''Error out if the user tries to register an existing alias.'''
        common_test.create_plugin(hierarchy=('maya', 'scenes'), platforms='*')

        ways.api.register_context_alias('maya_scenes', 'maya/scenes')
        with self.assertRaises(ValueError):
            ways.api.register_context_alias('maya_scenes', 'maya/scenes')


class ContextCreateTestCase(common_test.ContextTestCase):

    '''Make sure that Context objects are created properly.'''

    def test_context_set_metadata(self):
        '''Set the metadata on a context and spread its settings to others.'''
        data = {'css': {'background-color': 'red'}}
        common_test.create_plugin(hierarchy=('some', 'context'), platforms='', data=data)

        context1 = ways.api.get_context('some/context')
        context1.data['css']['background-color'] = 'red'
        context2 = ways.api.get_context('some/context')

        self.assertEqual(context1.data['css']['background-color'],
                         context2.data['css']['background-color'])

    def test_context_restore_default(self):
        '''Change a Context's data and then return it to its default.'''
        data = {'css': {'background-color': 'blue'}}
        common_test.create_plugin(hierarchy=('some', 'context'), platforms='', data=data)

        context = ways.api.get_context('some/context')
        context.data['css']['background-color'] = 'red'
        context.revert()

        self.assertEqual(context.data['css']['background-color'], 'blue')

    def test_context_checkout_all(self):
        '''Change from one Context to another, after it is defined.'''
        data = {'css': {'background-color': 'blue'}}
        assignment = 'job'
        common_test.create_plugin(hierarchy=('some', 'context'), platforms='', data=data)
        common_test.create_plugin(
            hierarchy=('some', 'context'), platforms='', assignment=assignment, data=data)

        context = ways.api.get_context('some/context')
        context.data['css']['background-color'] = 'white'
        context = context.checkout(assignment)

        self.assertNotEqual(context.data['css']['background-color'], 'white')

    def test_fails_from_bad_hierarchy(self):
        '''Fail to create a Context because bad characters were given.'''
        common_test.create_plugin(hierarchy=('s^ome', 'context'))

        with self.assertRaises(ValueError):
            ways.api.get_context('s^ome/context')

    def test_fails_from_unknown_assignment(self):
        '''If Ways creates a Context with no plugins, error.

        As far as I've found as of this writing, this only happens due to
        user error - If a person tries to call an assignment

        '''
        contents = textwrap.dedent(
            r'''
            globals:
                assignment: an_assignment_to_every_plugin
            plugins:
                some_plugin:
                    hierarchy: example
                    uuid: something_unique

                this_can_be_called_anything:
                    hierarchy: example/hierarchy
                    mapping: "/jobs/{JOB}"
                    uuid: another_unique_uuid
                    platforms:
                        - linux
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)
        mapping = '/jobs/job_part_something'

        with self.assertRaises(RuntimeError):
            asset = ways.api.get_asset(mapping, context='example/hierarchy')

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

    def test_assignment_from_config(self):
        '''Add assignment to Plugin Sheets using a Ways-supported config file.'''
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

        ways.api.add_search_path(directory)

        context = ways.api.get_context('foo', assignment=assignment)

        self.assertEqual(assignment, context.assignment)

    # pylint: disable=invalid-name
    def test_recursive_config_assignment(self):
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

        ways.api.add_search_path(assignment_directory)

        context = ways.api.get_context('foo', assignment=assignment)

        self.assertEqual(assignment, context.assignment)

    def test_assignment_from_file(self):
        '''Add an assignment to all plugins in a Plugin Sheet, using globals.'''
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
        '''Add an assignment to an individual plugin, inside a Plugin Sheet.'''
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

        ways.api.add_search_path(assignment_directory)

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


class ContextMethodTestCase(common_test.ContextTestCase):

    '''Test the methods of a ways.api.Context object.'''

    def test_get_platforms(self):
        '''Get the platforms of a Context.'''
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo
            ''')
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo')
        self.assertEqual(('*', ), context.get_platforms())

    def test_get_plugins_in_platform(self):
        '''Only get back plugin objects that are OK for the current platform.'''
        common_test.create_plugin(hierarchy=('maya', 'exports'), platforms='linux')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='linux')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='*')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='windows')

        context = ways.api.get_context('maya/exports/thing')

        expected_number_of_plugins = len(
            ways.PLUGIN_CACHE['hierarchy'][('maya', 'exports', 'thing')]['master'])
        expected_number_of_plugins += len(
            ways.PLUGIN_CACHE['hierarchy'][('maya', 'exports')]['master'])

        self.assertEqual(expected_number_of_plugins, 4)
        # This context should be missing at least one plugin
        self.assertTrue(len(context.plugins) != expected_number_of_plugins)

    def test_get_plugins_with_platform(self):
        '''Test a number of plugins that use incompatible platforms with this OS.

        The idea is there are two plugins for Windows and two plugins for Linux.
        Not matter which OS this test is run in, the result should always be
        two plugins back.

        '''
        common_test.create_plugin(hierarchy=('maya', 'exports'), platforms='linux')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='linux')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='windows')
        common_test.create_plugin(hierarchy=('maya', 'exports', 'thing'), platforms='windows')

        context = ways.api.get_context('maya/exports/thing')

        expected_number_of_plugins = len(
            ways.PLUGIN_CACHE['hierarchy'][('maya', 'exports', 'thing')]['master'])
        expected_number_of_plugins += len(
            ways.PLUGIN_CACHE['hierarchy'][('maya', 'exports')]['master'])

        self.assertEqual(expected_number_of_plugins, 4)
        # This context should be missing at least one plugin
        self.assertEqual(len(context.plugins), 2)

    def test_bad_platform(self):
        '''Simulate when a user gives a bad value to PLATFORM_ENV_VAR.'''
        common_test.create_plugin(hierarchy=('maya', 'exports'), platforms='*')
        os.environ[ways.api.PLATFORM_ENV_VAR] = '<bad_platform_name_here>'

        context = ways.api.get_context('maya/exports')

        with self.assertRaises(OSError):
            context.validate_plugin('asfdas')

    def test_get_mapping_tokens(self):
        '''Get the Context's top-level tokens and the tokens from a string.'''
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo
                    mapping: '/jobs/{THING}/another/{HERE}'
                    mapping_details:
                        THING:
                            mapping: '{INNER}_{ITEMS}'
            ''')
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo')

        self.assertEqual(['THING', 'HERE'], context.get_mapping_tokens())
        self.assertEqual(['SOMETHING'], context.get_mapping_tokens('obj{SOMETHING}here'))

    def test_get_all_tokens(self):
        '''Get every token and subtoken that's defined in a Context.'''
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo
                    mapping: '/jobs/{THING}/another/{HERE}'
                    mapping_details:
                        THING:
                            mapping: '{INNER}_{ITEMS}'
            ''')
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo')

        self.assertEqual({'THING', 'HERE', 'INNER', 'ITEMS'}, context.get_all_tokens())


class ContextInheritanceTestCase(common_test.ContextTestCase):

    '''Test the ways the a Context is meant to inherit from Context objects.

    Context objects from others through their hierarchy.
    If a Context exists at a lower hierarchy

    '''

    def test_context_inherit(self):
        '''Create a Context that gets its values from various Plugin objects.'''
        data = {'css': {'background-color': 'blue'}}
        common_test.create_plugin(hierarchy=('some', ), platforms='', data=data)
        common_test.create_plugin(hierarchy=('some', 'kind', 'of', 'context'), platforms='')

        context = ways.api.get_context('some/kind/of/context')

        self.assertEqual(context.data['css']['background-color'], 'blue')


def get_generic_job_config():
    '''str: Make a job YAML config file to use for tests in this module.'''
    return textwrap.dedent(
        r'''
        globals: {}
        plugins:
            alpha_root:
                hierarchy: root
                mapping: ''
                uuid: 3d149cb8-a5fe-43bd-85b4-dcb08238e023

            # Job plugins
            all_plugin_linux:
                hierarchy: '{root}/linux'
                mapping: ''
                platforms:
                    - linux
                uuid: 817f0173-4a5c-42d6-a2a9-60935d26c368
                uses:
                    - root

            all_plugin_windows:
                hierarchy: '{root}/windows'
                mapping: '{DRIVE}\'
                mapping_details:
                    DRIVE:
                        parse:
                            regex: '[zZ]:'
                            glob: 'Z:'
                        required: false
                platforms:
                    - windows
                uuid: c4b20e19-7040-4526-a822-a662c9daf7bf
                uses:
                    - root

            job_base_plugin_linux:
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
