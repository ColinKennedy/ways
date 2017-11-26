#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tests for all of the "why.rst" documentation page.'''

# IMPORT STANDARD LIBRARIES
import os
import platform
import textwrap
import unittest

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from .. import common_test


class PluginAndActionTestCase(common_test.ContextTestCase):

    '''General tests for the why.rst file.'''

    def setUp(self):
        '''Create a minimum file and add it to Ways.'''
        super(PluginAndActionTestCase, self).setUp()

        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: some/hierarchy
                    mapping: /path/to/a/{JOB}/here
            ''')

        self._make_plugin_sheet(contents=contents)

    def test_hello_world_plugin(self):
        '''Create a basic Plugin Sheet.'''
        context = ways.api.get_context('some/hierarchy')
        self.assertNotEqual(None, context)

    def test_get_value(self):
        '''Get a part of a hierarchy in a Plugin Sheet.'''
        path = '/path/to/a/job_name/here'
        asset = ways.api.get_asset(path, context='some/hierarchy')
        self.assertEqual('job_name', asset.get_value('JOB'))

    def test_action_class(self):
        '''Create an Action from a ways.api.Action object.'''
        contents = textwrap.dedent(
            '''
            import ways.api

            class SomeAction(ways.api.Action):

                name = 'some_action'

                def __call__(self, context):
                    return 8

                @classmethod
                def get_hierarchy(cls):
                    return 'some/hierarchy'
            ''')

        self._make_plugin(contents=contents)

        context = ways.api.get_context('some/hierarchy')
        self.assertEqual(8, context.actions.some_action())

    def test_action_function(self):
        '''Create an Action from a function.'''
        contents = textwrap.dedent(
            '''
            import ways.api

            def some_function(obj):
                return 8

            def main():
                ways.api.add_action(some_function, name='function', hierarchy='some/hierarchy')
            ''')

        self._make_plugin(contents=contents)

        context = ways.api.get_context('some/hierarchy')
        self.assertEqual(8, context.actions.function())

    @unittest.skipUnless(platform.system() != 'Windows', 'requires UNIX')
    def test_path_split_basic(self):
        '''Split a path without using Ways.'''
        path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
        info = get_environment_info(path)
        self.assertEqual('someJobName_123', info['JOB'])

    def test_path_split_ways(self):
        '''Split the same path in test_path_split_basic, using Ways.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: job/shot/discipline
                    mapping: /jobs/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}
                    path: true
            ''')

        self._make_plugin_sheet(contents=contents)

        path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
        asset = ways.api.get_asset(path)
        self.assertEqual('someJobName_123', asset.get_value('JOB'))

    def test_os_path_split_ways(self):
        '''Create a way to split a path in Windows and in Linux, using Ways.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                windows_root:
                    hierarchy: job
                    mapping: "\\\\NETWORK\\jobs"
                    path: true
                    platforms:
                        - windows
                linux_root:
                    hierarchy: job
                    mapping: /jobs
                    path: true
                    platforms:
                        - linux
                discipline:
                    hierarchy: '{root}/shot/discipline'
                    mapping: '{root}/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}'
                    uses:
                        - job
            ''')

        self._make_plugin_sheet(contents=contents)

        if platform.system() == 'Windows':
            path = r'\\NETWORK\jobs\someJobName_123\shot_name-Info\sh01\animation'
        else:
            path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'

        asset = ways.api.get_asset(path)

        self.assertEqual('someJobName_123', asset.get_value('JOB'))

    def test_scene_split_basic(self):
        '''Split a SCENE without Ways.'''
        path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
        info = get_environment_info(path)
        self.assertEqual('Info', get_scene_info(info['SCENE']))

    def test_scene_split_ways(self):
        '''Split the SCENE, using Ways.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                windows_root:
                    hierarchy: job
                    mapping: "\\\\NETWORK\\jobs"
                    path: true
                    platforms:
                        - windows
                linux_root:
                    hierarchy: job
                    mapping: /jobs
                    path: true
                    platforms:
                        - linux
                discipline:
                    hierarchy: '{root}/shot/discipline'
                    mapping: '{root}/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}'
                    mapping_details:
                        SCENE:
                            mapping: "{SCENE_PREFIX}-{SCENE_INFO}"
                    uses:
                        - job
            ''')

        self._make_plugin_sheet(contents=contents)

        path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
        asset = ways.api.get_asset(path)
        self.assertEqual('Info', asset.get_value('SCENE_INFO'))


class AssetManagementTestCase(common_test.ContextTestCase):

    '''Test the AMS-related examples in "why.rst".'''


def get_parts(path):
    '''list[str]: Get the parts of a path.'''
    return path.split(os.sep)


def get_environment_info(path):
    '''Parse a path of format "/jobs/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}".'''
    parts = get_parts(path)

    return {
        'JOB': parts[2],
        'SCENE': parts[3],
        'SHOT': parts[4],
        'DISCIPLINE': parts[4],
    }


def get_scene_info(scene):
    '''str: Get the "Info" part of some scene.'''
    return scene.split('-')[-1]
