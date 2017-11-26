#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test for the "plugin_advanced.rst" documentation page.'''

# IMPORT STANDARD LIBRARIES
import os
import tempfile
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from .. import common_test


class PluginAdvancedTestCase(common_test.ContextTestCase):

    '''All tests for the Advanced Context section of Ways's documentation.'''

    def test_plugin_setups(self):
        '''Make sure that a "Hello World" absolute plugin matches relative.

        This method relies on Context.as_dict() to work.

        '''
        absolute = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz/buzz
            ''')
        self._make_plugin_sheet(absolute)
        context = ways.api.get_context('fizz/buzz')
        absolute_info = context.as_dict()

        ways.clear()

        relative = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz
                relative_plugin:
                    hierarchy: '{root}/buzz'
                    uses:
                        - fizz
            ''')
        self._make_plugin_sheet(relative)
        context = ways.api.get_context('fizz/buzz')
        relative_info = context.as_dict()

        self.assertEqual(absolute_info, relative_info)

    def test_invalid_hierarchy(self):
        '''A relative plugin cannot refer to its own hierarchy.'''
        contents = textwrap.dedent(
            '''
            plugins:
                relative:
                    mapping: something
                    hierarchy: some/place
                    uses:
                        - some/place
            ''')

        self._make_plugin_sheet(contents)
        context = ways.api.get_context('some/place')
        self.assertEqual(context, None)

        ways.clear()

        contents = textwrap.dedent(
            '''
            plugins:
                absolute:
                    mapping: whatever
                    hierarchy: foo
                relative:
                    mapping: "{root}/something"
                    hierarchy: "{foo}/bar"
                    uses:
                        - foo/bar
            ''')

        self._make_plugin_sheet(contents)
        context = ways.api.get_context('some/place')
        self.assertEqual(context, None)

    def test_recursive_relative_uses(self):
        '''Make a relative plugin that uses a relative plugin.'''
        contents = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz
                relative_plugin1:
                    hierarchy: '{root}/buzz'
                    uses:
                        - fizz
                relative_plugin2:
                    hierarchy: '{root}/foo'
                    uses:
                        - fizz/buzz
            ''')
        self._make_plugin_sheet(contents)
        context = ways.api.get_context('fizz/buzz/foo')
        self.assertNotEqual(None, context)

    def test_compare_rel_and_abs(self):
        '''Create a setup for absolute and relative that make the same result.'''
        contents = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz
                    mapping: bar

                absolute_plugin1:
                    hierarchy: fizz/buzz
                    mapping: bar/something

                absolute_plugin1_library:
                    hierarchy: fizz/buzz/library
                    mapping: bar/something/library

                absolute_plugin2:
                    hierarchy: fizz/buzz/pop
                    mapping: bar/something/another/thing

                absolute_plugin2_library:
                    hierarchy: fizz/buzz/pop/library
                    mapping: bar/something/another/thing/library

                absolute_plugin3:
                    hierarchy: fizz/buzz/pop/fizz
                    mapping: bar/something/another/thing/sets

                absolute_plugin3_library:
                    hierarchy: fizz/buzz/pop/fizz/library
                    mapping: bar/something/another/thing/sets/library

            ''')
        self._make_plugin_sheet(contents)

        context = ways.api.get_context('fizz/buzz/pop/fizz/library')
        absolute_info = context.as_dict()

        ways.clear()

        contents = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz
                    mapping: bar

                relative_plugin1:
                    hierarchy: '{root}/buzz'
                    mapping: '{root}/something'
                    uses:
                        - fizz

                absolute_plugin2:
                    hierarchy: '{root}/pop'
                    mapping: '{root}/another/thing'
                    uses:
                        - fizz/buzz

                absolute_plugin3:
                    hierarchy: '{root}/fizz'
                    mapping: '{root}/sets'
                    uses:
                        - fizz/buzz/pop

                library:
                    hierarchy: '{root}/library'
                    mapping: '{root}/library'
                    uses:
                        - fizz
                        - fizz/buzz
                        - fizz/buzz/pop
                        - fizz/buzz/pop/fizz
            ''')

        self._make_plugin_sheet(contents)
        context = ways.api.get_context('fizz/buzz/pop/fizz/library')
        relative_info = context.as_dict()

        self.assertEqual(absolute_info, relative_info)

    def test_abs_and_rel_os_plugins(self):
        '''An absolute and relative setup that also have specific platforms.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                linux:
                    mapping: /jobs
                    hierarchy: job
                windows:
                    mapping: \\NETWORK\jobs\someJobName_123\library
                    hierarchy: job
                linux_library:
                    mapping: /jobs/someJobName_123/library
                    hierarchy: job/library
                windows_library:
                    mapping: \\NETWORK\jobs\someJobName_123\library
                    hierarchy: job/library
                linux_library_reference:
                    mapping: /jobs/someJobName_123/library/reference
                    hierarchy: job/library/reference
                windows_library_reference:
                    mapping: \\NETWORK\jobs\someJobName_123\library\reference
                    hierarchy: job/library/reference
            ''')

        self._make_plugin_sheet(contents)
        context = ways.api.get_context('job/library/reference')
        absolute_info = context.as_dict()

        ways.clear()

        contents = textwrap.dedent(
            r'''
            plugins:
                job_root_linux:
                    hierarchy: job
                    mapping: /jobs
                    platforms:
                        - linux

                job_root_windows:
                    hierarchy: job
                    mapping: \\NETWORK\jobs
                    platforms:
                        - windows

                library:
                    hierarchy: '{root}/library'
                    mapping: '{root}/someJobName_123/library'
                    uses:
                        - job

                reference:
                    hierarchy: '{root}/reference'
                    mapping: '{root}/reference'
                    uses:
                        - job/library
            ''')
        self._make_plugin_sheet(contents)
        context = ways.api.get_context('job/library/reference')
        relative_info = context.as_dict()

        self.assertEqual(absolute_info, relative_info)

    def test_abs_and_rel_append(self):
        '''Append to another plugin using the absolute and relative syntax.'''
        key = 'some_data'
        value = 8
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                    mapping: something
                append_plugin:
                    hierarchy: foo/bar
                    data:
                        {key}: {value}
            ''').format(key=key, value=value)
        self._make_plugin_sheet(contents)

        context = ways.api.get_context('foo/bar')
        absolute_info = context.data[key]

        ways.clear()

        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                    mapping: something
                append_plugin:
                    hierarchy: ''
                    data:
                        {key}: {value}
                    uses:
                        - foo/bar
            ''').format(key=key, value=value)
        self._make_plugin_sheet(contents)

        context = ways.api.get_context('foo/bar')
        relative_info = context.data[key]

        self.assertEqual(absolute_info, value)
        self.assertEqual(relative_info, value)

    def test_plugin_file_types(self):
        '''Make directories with different plugin info files and read them.'''
        config = textwrap.dedent(
            '''
            assignment: foo
            recursive: false
            ''')
        root = tempfile.mkdtemp()

        yml = os.path.join(root, ways.api.PLUGIN_INFO_FILE_NAME + '.yml')
        with open(yml, 'w') as file_:
            file_.write(config)

        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: bar
            ''')
        self._make_plugin_sheet(contents, folder=root)

        context = ways.api.get_context('bar', assignment='foo')
        yml_assignment = context.get_assignment()

        ways.clear()

        config = textwrap.dedent(
            '''
            {
                "assignment": "foo",
                "recursive": false,
            }
            ''')
        root = tempfile.mkdtemp()

        jsn_ = os.path.join(root, ways.api.PLUGIN_INFO_FILE_NAME + '.json')
        with open(jsn_, 'w') as file_:
            file_.write(config)

        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: bar
            ''')
        self._make_plugin_sheet(contents, folder=root)

        context = ways.api.get_context('bar', assignment='foo')
        json_assignment = context.get_assignment()

        self.assertEqual('foo', yml_assignment)
        self.assertEqual('foo', json_assignment)

    def test_change_plugin_assignments(self):
        '''Test all 3 ways to assign items to plugins.

        By testing all 3 ways at once, we make sure that assignment priority
        works properly.

        '''
        config = textwrap.dedent(
            '''
            assignment: foo
            recursive: false
            ''')
        root = tempfile.mkdtemp()

        yml = os.path.join(root, ways.api.PLUGIN_INFO_FILE_NAME + '.yml')
        with open(yml, 'w') as file_:
            file_.write(config)

        contents = textwrap.dedent(
            '''
            plugins:
                a_plugin:
                    hierarchy: something
            '''
        )
        self._make_plugin_sheet(contents, folder=root)

        contents = textwrap.dedent(
            '''
            globals:
                assignment: bar
            plugins:
                some_plugin:
                    hierarchy: some/hierarchy
                    mapping: foo
                another_plugin:
                    hierarchy: another/hierarchy
                    mapping: bar
                    assignment: job
            ''')
        self._make_plugin_sheet(contents)
        config_context = ways.api.get_context('something', assignment='foo')
        globals_context = ways.api.get_context('some/hierarchy', assignment='bar')
        plugin_context = ways.api.get_context('another/hierarchy', assignment='job')

        self.assertNotEqual(None, config_context)
        self.assertNotEqual(None, globals_context)
        self.assertNotEqual(None, plugin_context)

    def test_assignment_basic_example(self):
        '''Show how assignments can affect runtime behavior.'''
        os.environ[ways.api.PRIORITY_ENV_VAR] = (os.pathsep).join(['master', 'job'])
        contents = textwrap.dedent(
            '''
            plugins:
                job:
                    hierarchy: job
                    mapping: '/jobs/{JOB}'
                shot:
                    hierarchy: '{root}/shot'
                    mapping: '{root}/{SCENE}/{SHOT}'
                    uses:
                        - job
                plates:
                    hierarchy: '{root}/plates'
                    mapping: '{root}/library/graded/plates'
                    uses:
                        - job/shot
                client_plates:
                    hierarchy: '{root}/client'
                    mapping: '{root}/clientinfo'
                    uses:
                        - job/shot/plates
                compositing:
                    hierarchy: '{root}/comp'
                    mapping: '{root}/compwork'
                    uses:
                        - job/shot/plates
            ''')
        self._make_plugin_sheet(contents)

        contents = textwrap.dedent(
            '''
            globals:
                assignment: job
            plugins:
                job_plugin:
                    hierarchy: '{root}/plates'
                    mapping: '{root}/archive/plates'
                    uses:
                        - job/shot
            ''')
        self._make_plugin_sheet(contents)

        expected = '/jobs/{JOB}/{SCENE}/{SHOT}/archive/plates/clientinfo'
        context = ways.api.get_context('job/shot/plates/client')
        self.assertEqual(expected, context.get_mapping())
