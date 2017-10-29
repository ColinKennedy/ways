#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import textwrap
import os

# IMPORT 'LOCAL' LIBRARIES
from . import common_test
import ways.api


class ContextMergeTestCase(common_test.ContextTestCase):

    '''Test the ways that Context objects merge with other Context objects.'''

    def test_make_context_unfindable(self):
        '''Make sure that Contexts can be protected from being queried.'''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                relative_plugin:
                    findable: false
                    hierarchy: some/hierarchy
                    mapping: ./scenes/animation
                    platforms:
                        - Linux
                        - Windows
                        - Darwin
                    uses:
                        - maya_project
                        - houdini_project
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)
        context = ways.api.get_context('some/hierarchy')
        self.assertEqual(context, None)

    def test_merge_context_to_another_context(self):
        '''Add a Context object into another Context object.

        This test is actually testing a lot at once and probably could be
        broken up into individual tests.

        What this method tests:
        - If the relative plugin's hierarchy has a keyword called "{root}",
          when we combine the two Contexts together, the parent Context will
          be substituted in for "{root}".
        - If no "{root}" is given, the hierarchy is just appended to the end
          of the other parent Context
        - The same behavior goes for mapping
        - The combined Context's supported platforms is the OSes that are
          listed in both the parent Context and the child Context

        '''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                base_plugin:
                    hierarchy: maya_project
                    mapping: /jobs/{JOB}/shots/sh01/maya
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse:
                                regex: .+
                    platforms:
                        - linux
                        - darwin
                    max_folder: /jobs/{JOB}/shots
                    uuid: base_thing
                some_plugin_name:
                    hierarchy: maya_project
                    mapping: /jobs/{JOB}/shots/sh01/maya
                    mapping_details:
                        JOB_NAME:
                            parse:
                                regex: \w+
                        JOB_ID:
                            parse:
                                regex: \d+
                    platforms:
                        - linux
                        - darwin
                    uuid: another_plugin_extension
                incompatible_plugin:
                    mapping: Z:\jobs\{JOB}\shots\sh01\houdini
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse:
                                regex: .+
                        JOB_NAME:
                            parse:
                                regex: \w+
                        JOB_ID:
                            parse:
                                regex: \d+
                    hierarchy: houdini_project
                    platforms:
                        - windows
                    uuid: plugin_that_is_not_compatible_with_linux
                another_plugin_name:
                    mapping: /jobs/{JOB}/shots/sh01/houdini
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse:
                                regex: .+
                        JOB_NAME:
                            parse:
                                regex: \w+
                        JOB_ID:
                            parse:
                                regex: \d+
                    hierarchy: houdini_project
                    platforms:
                        - linux
                        - darwin
                    uuid: houdini_plugin
                relative_plugin1:
                    findable: false
                    hierarchy: '{root}/mocap'
                    mapping: '{root}/scenes/mocap'
                    platforms:
                        - linux
                        - windows
                        - darwin
                    uses:
                        - maya_project
                        - houdini_project
                    uuid: some_relative_plugin1
                relative_plugin2:
                    findable: false
                    hierarchy: 'animation'
                    mapping: 'scenes/animation'
                    platforms:
                        - linux
                        - windows
                        - darwin
                    uses:
                        - maya_project
                        - houdini_project
                    max_folder: /./scenes
                    uuid: some_relative_plugin2
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        animation_context = ways.api.get_context('maya_project/animation')
        mocap_context = ways.api.get_context('houdini_project/mocap')

        self.assertNotEqual(animation_context, None)
        self.assertNotEqual(mocap_context, None)

        self.assertEqual(animation_context.get_hierarchy(), ('maya_project', 'animation'))
        self.assertEqual(mocap_context.get_hierarchy(), ('houdini_project', 'mocap'))

        self.assertEqual(animation_context.get_mapping(),
                         '/jobs/{JOB}/shots/sh01/mayascenes/animation')
        self.assertEqual(mocap_context.get_mapping(),
                         '/jobs/{JOB}/shots/sh01/houdini/scenes/mocap')

        expected_mapping_details = {
            'JOB': {
                'mapping': '{JOB_NAME}_{JOB_ID}',
                'parse': {
                    'regex': '.+',
                },
            },
            'JOB_NAME': {
                'parse': {
                    'regex': '\w+',
                },
            },
            'JOB_ID': {
                'parse': {
                    'regex': '\d+',
                },
            },
        }
        self.assertEqual(animation_context.get_mapping_details(),
                         expected_mapping_details)
        self.assertEqual(mocap_context.get_mapping_details(),
                         expected_mapping_details)

        expected_animation_max_folder = '/jobs/{JOB}/shots/sh01/maya/scenes'
        self.assertEqual(expected_animation_max_folder,
                         animation_context.get_max_folder())

    def test_001_merge_context_to_another_context_fail_bad_maps(self):
        '''Two Context objects that have conflicting maps should not merge.'''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                base_plugin:
                    hierarchy: maya_project
                    mapping: /jobs/{JOB}/shots/sh01/maya
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse:
                                regex: .+
                        JOB_NAME:
                            parse:
                                regex: \w+
                        JOB_ID:
                            parse:
                                regex: \d+
                    platforms:
                        - linux
                        - darwin
                    max_folder: /jobs/{JOB}/shots
                relative_plugin1:
                    findable: false
                    hierarchy: '{root}/mocap'
                    mapping: '{root}/scenes/mocap'
                    platforms:
                        - linux
                        - windows
                        - darwin
                    uses:
                        - maya_project
                    uuid: some_relative_plugin1
                relative_plugin2:
                    findable: false
                    hierarchy: '{root}/something'
                    mapping: '{root}/some/folders'
                    platforms:
                        - linux
                        - windows
                        - darwin
                    uses:
                        - maya_project
                    uuid: some_relative_plugin2
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        mocap_context = ways.api.get_context('maya_project/mocap/something')
        self.assertEqual(mocap_context, None)

    def test_merge_context_self_referring_context_fail(self):
        '''Keep a plugin from registering if it 'uses' itself.

        If a plugin refers to itself, it will cause a recursive loop.
        We need to catch this before it causes any mayhem in our system.

        '''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                relative_plugin1:
                    findable: false
                    hierarchy: mocap
                    mapping: '{root}/scenes/mocap'
                    platforms:
                        - linux
                        - windows
                        - darwin
                    uses:
                        - mocap
                    uuid: some_relative_plugin1
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        mocap_context = ways.api.get_context('mocap')
        self.assertEqual(mocap_context, None)

    def test_merge_context_into_merged_context(self):
        '''Make sure that a Context can merge with another merged Context.'''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                base_plugin:
                    hierarchy: maya_project
                    mapping: /jobs/{JOB}/shots/sh01/maya
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse:
                                regex: .+
                        JOB_NAME:
                            parse:
                                regex: \w+
                        JOB_ID:
                            parse:
                                regex: \d+
                    platforms:
                        - linux
                        - darwin
                    max_folder: /jobs/{JOB}/shots
                relative_plugin1:
                    findable: false
                    hierarchy: '{root}/mocap'
                    mapping: '{root}/scenes/mocap'
                    platforms:
                        - linux
                        - windows
                        - darwin
                    uses:
                        - maya_project
                    uuid: some_relative_plugin1
                relative_plugin2:
                    findable: false
                    hierarchy: '{root}/something'
                    mapping: '{root}/some/folders'
                    platforms:
                        - linux
                        - windows
                        - darwin
                    uses:
                        - maya_project/mocap
                    uuid: some_relative_plugin2
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        mocap_context = ways.api.get_context('maya_project/mocap/something')
        self.assertNotEqual(mocap_context, None)

        self.assertEqual(mocap_context.get_hierarchy(),
                         ('maya_project', 'mocap', 'something'))
        self.assertEqual(mocap_context.get_mapping(),
                         '/jobs/{JOB}/shots/sh01/maya/scenes/mocap/some/folders')

        expected_mapping_details = {
            'JOB': {
                'mapping': '{JOB_NAME}_{JOB_ID}',
                'parse': {
                    'regex': '.+',
                },
            },
            'JOB_NAME': {
                'parse': {
                    'regex': '\w+',
                },
            },
            'JOB_ID': {
                'parse': {
                    'regex': '\d+',
                },
            },
        }
        self.assertEqual(mocap_context.get_mapping_details(),
                         expected_mapping_details)

    def test_relative_plugin_append1(self):
        '''Append/Replace information from a relative plugin to another.'''
        key = 'something'
        value = 'here'
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                relative_plugin1:
                    data:
                        {key}: {value}
                    hierarchy: '{{root}}/bar'
                    uses:
                        - foo
            ''').format(key=key, value=value)
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo/bar')
        self.assertEqual(context.data[key], value)

    def test_relative_plugin_append2(self):
        '''Append/Replace information from a relative plugin to another.

        This time, use the alternate relative append syntax.

        '''
        key = 'something'
        value = 'here'
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                relative_plugin1:
                    data:
                        {key}: {value}
                    hierarchy: ''
                    uses:
                        - foo/bar
            ''').format(key=key, value=value)
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo/bar')
        self.assertEqual(context.data[key], value)

    def test_relative_plugin_append3(self):
        '''Append/Replace information from a relative plugin to another.

        This time, mix both append syntaxes together.

        '''
        key = 'something'
        value = 'here'
        key2 = 'ttt'
        value2 = ('asfsd', 8)
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                relative_plugin1:
                    data:
                        {key}: {value}
                    hierarchy: ''
                    uses:
                        - foo/bar
                relative_plugin2:
                    data:
                        {key2}: {value2}
                    hierarchy: '{{root}}/bar'
                    uses:
                        - foo

            ''').format(key=key, value=value, key2=key2, value2=value2)
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo/bar')
        self.assertEqual(context.data[key], value)

    def test_relative_plugin_append_from_assignment(self):
        '''Append/Replace a relative plugin even when assignments differ.'''
        key = 'something'
        value = 'here'
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                relative_plugin1:
                    assignment: job
                    data:
                        {key}: {value}
                    hierarchy: ''
                    uses:
                        - foo/bar
            ''').format(key=key, value=value)
        os.environ[ways.api.PRIORITY_ENV_VAR] = (os.pathsep).join(['master', 'job'])
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo/bar')
        self.assertEqual(context.data[key], value)

    def test_relative_plugin_append_from_assignment2(self):
        '''Same as the previous test, but more thorough.'''
        key = 'something'
        value = 'here'
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                    mapping: /some/thing
                relative_plugin1:
                    assignment: job
                    data:
                        {key}: {value}
                    hierarchy: ''
                    mapping: '{{root}}/else'
                    uses:
                        - foo/bar

            ''').format(key=key, value=value)
        os.environ[ways.api.PRIORITY_ENV_VAR] = (os.pathsep).join(['master', 'job'])
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo/bar')

        self.assertEqual(context.data[key], value)
        mapping = '/some/thing/else'
        self.assertEqual(mapping, context.get_mapping())

    def test_relative_plugin_append_from_assignment3(self):
        '''Same as the previous tests, but more thorough.'''
        key = 'something'
        value = 'here'
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                    mapping: /some/thing
                relative_master_plugin:
                    hierarchy: '{root}/fizz'
                    mapping: '{root}/here'
                    uses:
                        - foo/bar
                relative_job_plugin1:
                    assignment: job
                    hierarchy: '{root}/fizz'
                    mapping: '{root}/else'
                    uses:
                        - foo/bar
            ''')
        os.environ[ways.api.PRIORITY_ENV_VAR] = (os.pathsep).join(['master', 'job'])
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo/bar/fizz')

        mapping = '/some/thing/else'
        self.assertEqual(mapping, context.get_mapping())

    # def test_merge_context_into_tri_merged_context(self):
    #     '''Merge a Context into a merged Context that has unmerged content.'''

    # def test_merge_context_with_context_from_another_assignment(self):
    #     '''Allow a Context to merge into another from a different assignment.

    #     Only allow this though if the child Context's assignment is set to
    #     stack with other assignments.

    #     '''
    #     pass


if __name__ == '__main__':
    print(__doc__)

