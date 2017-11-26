#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test the different ways that Context and Plugin objects merge together.'''

# IMPORT STANDARD LIBRARIES
import os
import platform
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from . import common_test


class ContextMergeTestCase(common_test.ContextTestCase):

    '''Test the ways that Context objects merge with other Context objects.'''

    def test_merge_contexts(self):
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
                    uuid: base_thing
                linux_base:
                    hierarchy: maya_project
                    max_folder: /jobs/{JOB}/shots
                    platforms:
                        - linux
                        - darwin
                windows_base:
                    hierarchy: maya_project
                    max_folder: Z:\jobs\{JOB}\shots
                    platforms:
                        - windows
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
                window_plugin:
                    mapping: Z:\jobs\{JOB}\shots\sh01\maya
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
                    hierarchy: maya_project
                    platforms:
                        - windows
                    uuid: a_window_plugin
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
                    hierarchy: '{root}/mocap'
                    mapping: '{root}/scenes/mocap'
                    path: true
                    uses:
                        - maya_project
                        - houdini_project
                    uuid: some_relative_plugin1
                relative_plugin2:
                    hierarchy: 'animation'
                    mapping: '{root}/scenes/animation'
                    path: true
                    uses:
                        - maya_project
                        - houdini_project
                    uuid: some_relative_plugin2
            ''')

        self._make_plugin_sheet(contents=contents)

        animation_context = ways.api.get_context('maya_project/animation')
        mocap_context = ways.api.get_context('houdini_project/mocap')

        self.assertNotEqual(animation_context, None)
        self.assertNotEqual(mocap_context, None)

        self.assertEqual(animation_context.get_hierarchy(), ('maya_project', 'animation'))
        self.assertEqual(mocap_context.get_hierarchy(), ('houdini_project', 'mocap'))

        if platform.system() == 'Windows':
            animation_mapping = r'Z:\jobs\{JOB}\shots\sh01\maya\scenes\animation'
        else:
            animation_mapping = '/jobs/{JOB}/shots/sh01/maya/scenes/animation'

        if platform.system() == 'Windows':
            mocap_mapping = r'Z:\jobs\{JOB}\shots\sh01\houdini\scenes\mocap'
        else:
            mocap_mapping = '/jobs/{JOB}/shots/sh01/houdini/scenes/mocap'

        self.assertEqual(animation_context.get_mapping(), animation_mapping)
        self.assertEqual(mocap_context.get_mapping(), mocap_mapping)

        expected_mapping_details = {
            'JOB': {
                'mapping': '{JOB_NAME}_{JOB_ID}',
                'parse': {
                    'regex': '.+',
                },
            },
            'JOB_NAME': {
                'parse': {
                    'regex': r'\w+',
                },
            },
            'JOB_ID': {
                'parse': {
                    'regex': r'\d+',
                },
            },
        }
        self.assertEqual(animation_context.get_mapping_details(),
                         expected_mapping_details)
        self.assertEqual(mocap_context.get_mapping_details(),
                         expected_mapping_details)

        if platform.system() == 'Windows':
            expected_max_folder = r'Z:\jobs\{JOB}\shots'
        else:
            expected_max_folder = '/jobs/{JOB}/shots'

        self.assertEqual(expected_max_folder, animation_context.get_max_folder())

    def test_001_merge_fail_bad_maps(self):
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

        self._make_plugin_sheet(contents=contents)

        mocap_context = ways.api.get_context('maya_project/mocap/something')
        self.assertEqual(mocap_context, None)

    def test_cyclic_context_fail(self):
        '''Keep a plugin from registering if it 'uses' itself.

        If a plugin refers to itself, it will cause a recursive loop.
        We need to catch this before it causes any mayhem in our system.

        '''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                relative_plugin1:
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

        self._make_plugin_sheet(contents=contents)

        mocap_context = ways.api.get_context('mocap')
        self.assertEqual(mocap_context, None)

    def test_merge_context_recursive(self):
        '''Make sure that a Context can merge with another merged Context.'''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                base_plugin:
                    hierarchy: maya_project
                    mapping: /jobs/{JOB}/shots/sh01/maya
                    platforms:
                        - linux
                        - darwin
                    max_folder: /jobs/{JOB}/shots

                base_plugin_windows:
                    hierarchy: maya_project
                    mapping: 'Z:\{JOB}'
                    path: true
                    platforms:
                        - windows

                base_details:
                    hierarchy: maya_project
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
                relative_plugin1:
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

        self._make_plugin_sheet(contents=contents)

        mocap_context = ways.api.get_context('maya_project/mocap/something')
        self.assertNotEqual(mocap_context, None)

        self.assertEqual(mocap_context.get_hierarchy(),
                         ('maya_project', 'mocap', 'something'))

        if platform.system() == 'Windows':
            mapping = r'Z:\{JOB}\scenes\mocap\some\folders'
        else:
            mapping = '/jobs/{JOB}/shots/sh01/maya/scenes/mocap/some/folders'

        self.assertEqual(mocap_context.get_mapping(), mapping)

        expected_mapping_details = {
            'JOB': {
                'mapping': '{JOB_NAME}_{JOB_ID}',
                'parse': {
                    'regex': '.+',
                },
            },
            'JOB_NAME': {
                'parse': {
                    'regex': r'\w+',
                },
            },
            'JOB_ID': {
                'parse': {
                    'regex': r'\d+',
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
        self._make_plugin_sheet(contents)

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
        self._make_plugin_sheet(contents)

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
        self._make_plugin_sheet(contents)

        context = ways.api.get_context('foo/bar')
        self.assertEqual(context.data[key], value)

    def test_relative_plugin_append4(self):
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
        self._make_plugin_sheet(contents)

        context = ways.api.get_context('foo/bar')
        self.assertEqual(context.data[key], value)

    def test_relative_plugin_append5(self):
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
        self._make_plugin_sheet(contents)

        context = ways.api.get_context('foo/bar')

        self.assertEqual(context.data[key], value)
        mapping = '/some/thing/else'
        self.assertEqual(mapping, context.get_mapping())

    def test_relative_plugin_append6(self):
        '''Same as the previous tests, but more thorough.'''
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
        self._make_plugin_sheet(contents)

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
