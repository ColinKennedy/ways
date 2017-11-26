#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test for the "plugins_basic.rst" documentation page.'''

# IMPORT STANDARD LIBRARIES
import os
import platform
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from .. import common_test


class PluginBasicsTestCase(common_test.ContextTestCase):

    '''All tests for the Plugin Basics section of Ways's documentation.'''

    def _make_complex_setup(self):
        '''Build a lot of plugins at once, for this TestCase.'''
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
                    path: true

                window_jobs_plugin:
                    hierarchy: example/hierarchy
                    mapping: "C:\\Users\\{USER}\\jobs\\{JOB}"
                    mapping_details:
                        USER:
                            parse:
                                regex: \w+
                    platforms:
                        - windows
                    uuid: windows_job
                    path: true

                jobs_details:
                    hierarchy: example/hierarchy
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                        JOB_NAME:
                            mapping: '{JOB_NAME_PREFIX}_{JOB_NAME_SUFFIX}'
                        JOB_NAME_PREFIX:
                            parse:
                                regex: '\w+'
                        JOB_NAME_SUFFIX:
                            parse:
                                regex: 'thing-\w+'
                        JOB_ID:
                            parse:
                                regex: '\d{3}'
                    uuid: something_unique2

                yet_another_plugin:
                    hierarchy: example/tree
                    mapping: /tree
                    uuid: does_not_matter_what_it_is
                    path: true

                config_plugin:
                    hierarchy: "{root}/config"
                    mapping: "{root}/configuration"
                    uses:
                        - example/hierarchy
                        - example/tree
                    uuid: as_Long_as_It_is_Different

                some_assigned_plugin:
                    assignment: different_assignment
                    hierarchy: something
                    data:
                        important_information: here
                    uuid: boo_Did_I_scare_you?
            ''')

        self._make_plugin_sheet(contents=contents)

        os.environ[ways.api.PRIORITY_ENV_VAR] = (os.pathsep).join(
            ['master', 'an_assignment_to_every_plugin'])

    def test_hello_world_yaml(self):
        '''Make sure hello world works. Yes, I know this test is redundant.'''
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: example
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('example')
        self.assertNotEqual(None, context)

    def test_regular_vs_autofind(self):
        '''Defining a Context should create the same result as auto-find.'''
        self._make_complex_setup()

        if platform.system() == 'Windows':
            mapping = r'C:\Users\some_user\jobs\job_part_something'
        else:
            mapping = '/jobs/job_part_something'

        explicit_asset = ways.api.get_asset(mapping, context='example/hierarchy')
        autofound_asset = ways.api.get_asset(mapping)
        self.assertNotEqual(None, explicit_asset)
        self.assertEqual(explicit_asset, autofound_asset)

    def test_mapping_details_parse(self):
        '''Test that mapping_details gets its parse string as expected.'''
        self._make_complex_setup()

        context = ways.api.get_context('example/hierarchy')
        os.environ['JOB'] = 'job_thing-something_123'
        os.environ['USER'] = 'My_Username'

        if platform.system() == 'Windows':
            expected_env_string = r'C:\Users\My_Username\jobs\job_thing-something_123'
        else:
            expected_env_string = '/jobs/job_thing-something_123'

        self.assertEqual(expected_env_string, context.get_str(resolve_with=('env', 'regex')))

        if platform.system() == 'Windows':
            expected_regex_string = r'C:\Users\\w+\jobs\\w+_thing-\w+_\d{3}'
        else:
            expected_regex_string = r'/jobs/\w+_thing-\w+_\d{3}'

        self.assertEqual(expected_regex_string, context.get_str(resolve_with='regex'))
        self.assertEqual(expected_regex_string, context.get_str(resolve_with=('regex', )))

    def test_mapping_details_get_value(self):
        '''Test that mapping_details Parent-/Child-Search works correctly.'''
        self._make_complex_setup()

        if platform.system() == 'Windows':
            mapping = r'C:\Users\username\jobs\job_thing-something_123'
        else:
            mapping = '/jobs/job_thing-something_123'

        asset = ways.api.get_asset(mapping, context='example/hierarchy')
        expected = 'thing-something'
        self.assertEqual(expected, asset.get_value('JOB_NAME_SUFFIX'))

    def test_platforms(self):
        '''Check that the code snippets used for platforms work correctly.'''
        contents = textwrap.dedent(
            '''
            plugins:
                explicit_star_platform:
                    hierarchy: foo
                    platforms:
                        - '*'
                implicit_star_platform:
                    hierarchy: bar
                some_platforms:
                    hierarchy: fizz
                    platforms:
                        - linux
                        - darwin
            ''')

        os.environ['WAYS_PLATFORM'] = 'linux'
        self._make_plugin_sheet(contents=contents)

        all_platforms = {'windows', 'darwin', 'linux', 'java'}
        self.assertEqual(all_platforms, ways.api.get_context('foo').get_platforms())
        self.assertEqual(all_platforms, ways.api.get_context('bar').get_platforms())
        self.assertEqual({'linux', 'darwin'}, ways.api.get_context('fizz').get_platforms())

    def test_path_problem(self):
        '''Test the block of code that illustrates the path problem.'''
        contents = textwrap.dedent(
            '''
            plugins:
                path_plugin:
                    hierarchy: foo
                    mapping: '/jobs/{JOB}'
                    platforms:
                        - linux
                windows_path_root:
                    hierarchy: foo
                    mapping: 'Z:\jobs\{JOB}'
                    platforms:
                        - windows

                relative_plugin:
                    hierarchy: '{root}/bar'
                    mapping: '{root}/shots'
                    uses:
                        - foo
            ''')

        self._make_plugin_sheet(contents=contents)

        if platform.system() == 'Windows':
            mapping = 'Z:\jobs\{JOB}/shots'
        else:
            mapping = '/jobs/{JOB}/shots'

        context = ways.api.get_context('foo/bar')
        self.assertEqual(mapping, context.get_mapping())

    def test_path_solution(self):
        '''Show how setting "path: true" fixes the path problem.'''
        contents = textwrap.dedent(
            '''
            plugins:
                path_plugin:
                    hierarchy: foo
                    mapping: '/jobs/{JOB}'
                    platforms:
                        - linux
                windows_path_root:
                    hierarchy: foo
                    mapping: 'Z:\jobs\{JOB}'
                    platforms:
                        - windows
                plugin_that_appends_path:
                    hierarchy: foo
                    path: true

                relative_plugin:
                    hierarchy: '{root}/bar'
                    mapping: '{root}/shots'
                    uses:
                        - foo
            ''')

        self._make_plugin_sheet(contents=contents)

        if platform.system() == 'Windows':
            mapping = 'Z:\jobs\{JOB}\shots'
        else:
            mapping = '/jobs/{JOB}/shots'

        context = ways.api.get_context('foo/bar')
        self.assertEqual(mapping, context.get_mapping())
