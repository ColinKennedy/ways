#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tests for auto-finding Ways objects.'''

# IMPORT STANDARD LIBRARIES
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from . import common_test


class FindContextTestCase(common_test.ContextTestCase):

    '''Test for whenever the user tries to get Ways objects without a Context.'''

    def test_string(self):
        '''Get a Context/Asset automatically, using a string.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                version_plugin:
                    hierarchy: job/versioned_asset
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
            ''')

        self._make_plugin_sheet(contents)

        versioned = '/tmp/foo/ttt/8'

        asset = ways.api.get_asset(versioned)
        self.assertNotEqual(None, asset)
        self.assertEqual(('job', 'versioned_asset'), asset.context.get_hierarchy())

    def test_string_tied(self):
        '''Resolve a tie between two Contexts.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                version_plugin:
                    hierarchy: job/library
                    mapping: '/tmp/{JOB}/library'
                another_plugin:
                    hierarchy: job/config
                    mapping: '/tmp/{JOB}/config'
            ''')

        self._make_plugin_sheet(contents)

        self.assertNotEqual(None, ways.api.get_asset('/tmp/foo/library'))

    def test_child_tokens_failure(self):
        '''Raise an exception because all Contexts return bad parse values.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                version_plugin:
                    hierarchy: job/library
                    mapping: '/tmp/{JOB}/{SCENE}/library'
                    mapping_details:
                        SCENE:
                            mapping: '{SCENE_PREFIX}_{SCENE_SUFFIX}'
                        SCENE_SUFFIX:
                            parse:
                                regex: '[a-z]+'
                another_plugin:
                    hierarchy: job/config
                    mapping: '/tmp/{JOB}/{SCENE}/config'
                    mapping_details:
                        SCENE:
                            mapping: '{SCENE_PREFIX}_{SCENE_SUFFIX}'
                        SCENE_SUFFIX:
                            parse:
                                regex: '[a-z]+'
            ''')

        self._make_plugin_sheet(contents)

        info = {
            'JOB': 'foo',
            'SCENE_PREFIX': 'something',
            'SCENE_SUFFIX': '0010',
        }

        with self.assertRaises(ValueError):
            ways.api.get_asset(info)

    def test_child_tokens(self):
        '''Get a Context from an Asset that only has child tokens defined.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                version_plugin:
                    hierarchy: job/library
                    mapping: '/tmp/{JOB}/{SCENE}/library'
                    mapping_details:
                        SCENE:
                            mapping: '{SCENE_PREFIX}_{SCENE_SUFFIX}'
                        SCENE_SUFFIX:
                            parse:
                                regex: '\d+'
                another_plugin:
                    hierarchy: job/config
                    mapping: '/tmp/{JOB}/{SCENE}/config'
                    mapping_details:
                        SCENE:
                            mapping: '{SCENE_PREFIX}_{SCENE_SUFFIX}'
                        SCENE_SUFFIX:
                            parse:
                                regex: '[a-z]+'
            ''')

        self._make_plugin_sheet(contents)

        info = {
            'JOB_NAME': 'foo',
            'JOB_ID': '6',
            'SCENE_PREFIX': 'something',
            'SCENE_SUFFIX': '0010',
        }
        self.assertNotEqual(None, ways.api.get_asset(info))

    def test_string_tied_fails(self):
        '''Raise an error if Ways cannot decide the best Context.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                version_plugin:
                    hierarchy: job/versioned_asset
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
                another_plugin:
                    hierarchy: something/completely/different
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
            ''')

        self._make_plugin_sheet(contents)

        versioned = '/tmp/foo/ttt/8'

        with self.assertRaises(ValueError):
            ways.api.get_asset(versioned)

    def test_string_tie_break(self):
        '''Use a parser to break a tie between two Contexts.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
                    mapping_details:
                        ASSET_VERSION:
                            parse:
                                regex: tttt
                version_plugin:
                    hierarchy: job/versioned_asset
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
                    mapping_details:
                        ASSET_VERSION:
                            parse:
                                regex: \d+
                another_plugin:
                    hierarchy: something/completely/different
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
                    mapping_details:
                        ASSET_VERSION:
                            parse:
                                regex: '[a-z]+'
            ''')

        self._make_plugin_sheet(contents)

        self.assertNotEqual(None, ways.api.get_asset('/tmp/foo/ttt/8'))

    def test_from_dict(self):
        '''Get the correct Context/Asset even if only a dict was given.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                version_plugin:
                    hierarchy: job/versioned_asset
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
            ''')

        self._make_plugin_sheet(contents)

        versioned = {
            'JOB': 'foo',
            'SOMETHING': 'ttt',
            'ASSET_VERSION': '8',
        }

        self.assertNotEqual(None, ways.api.get_asset(versioned))

    def test_tie(self):
        '''Raise an error if Ways cannot decide the best Context.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                version_plugin:
                    hierarchy: job/versioned_asset
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
                another_plugin:
                    hierarchy: something/completely/different
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
            ''')

        self._make_plugin_sheet(contents)

        versioned = {
            'JOB': 'foo',
            'SOMETHING': 'ttt',
            'ASSET_VERSION': '8',
        }

        with self.assertRaises(ValueError):
            ways.api.get_asset(versioned)

    def test_tie_break_dict(self):
        '''Get the correct Context/Asset when two Contexts have the same mapping.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
                    mapping_details:
                        ASSET_VERSION:
                            parse:
                                regex: tttt
                version_plugin:
                    hierarchy: job/versioned_asset
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
                    mapping_details:
                        ASSET_VERSION:
                            parse:
                                regex: \d+
                another_plugin:
                    hierarchy: something/completely/different
                    mapping: '/tmp/{JOB}/{SOMETHING}/{ASSET_VERSION}'
                    mapping_details:
                        ASSET_VERSION:
                            parse:
                                regex: '[a-z]+'
            ''')

        self._make_plugin_sheet(contents)

        versioned = {
            'JOB': 'foo',
            'SOMETHING': 'ttt',
            'ASSET_VERSION': '8',
        }

        self.assertNotEqual(None, ways.api.get_asset(versioned))

    def test_fails_no_mapping_string(self):
        '''If no Context could be found that has a mapping, raise Exception.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                version_plugin:
                    hierarchy: job/versioned_asset
                another_plugin:
                    hierarchy: job/vvvv
            ''')

        self._make_plugin_sheet(contents)

        versioned = '/tmp/thing'

        with self.assertRaises(ValueError):
            ways.api.get_asset(versioned)

    def test_fails_no_mapping(self):
        '''If no Context could be found that has a mapping, raise Exception.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                version_plugin:
                    hierarchy: job/versioned_asset
                another_plugin:
                    hierarchy: job/vvvv
            ''')

        self._make_plugin_sheet(contents)

        versioned = {
            'JOB': 'foo',
            'SOMETHING': 'ttt',
            'ASSET_VERSION': '8',
        }

        with self.assertRaises(ValueError):
            ways.api.get_asset(versioned)
