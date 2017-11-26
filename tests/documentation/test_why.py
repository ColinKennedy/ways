#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tests for all of the "why.rst" documentation page.'''

# IMPORT STANDARD LIBRARIES
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from .. import common_test


class WhyTestCase(common_test.ContextTestCase):

    '''General tests for the why.rst file.'''

    def _setup_basic_plugin_sheet(self):
        '''Create a minimum file and add it to Ways.'''
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
        self._setup_basic_plugin_sheet()

        context = ways.api.get_context('some/hierarchy')
        self.assertNotEqual(None, context)

    def test_get_value(self):
        '''Get a part of a hierarchy in a Plugin Sheet.'''
        self._setup_basic_plugin_sheet()

        path = '/path/to/a/job_name/here'
        asset = ways.api.get_asset(path, context='some/hierarchy')
        self.assertEqual('job_name', asset.get_value('JOB'))
