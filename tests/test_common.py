#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Make sure that generic functions work exactly as we expect.'''

# IMPORT STANDARD LIBRARIES
import unittest

# IMPORT WAYS LIBRARIES
from ways import common


class ParseTestCase(unittest.TestCase):

    '''Test generic parsing-related functions.'''

    def test_working_0001(self):
        '''Test that correct input for expand_string works as expected.'''
        pattern = '/jobs/{JOB}/some_kind/{THING}/real_folders'
        text = '/jobs/some_job_here/some_kind/of/real_folders'

        expected_output = {'JOB': 'some_job_here', 'THING': 'of'}
        self.assertEqual(expected_output, common.expand_string(pattern, text))

    def test_working_0002(self):
        '''Test that correct input for expand_string works as expected.'''
        shot = 'NAME_010'
        format_string = '{SHOT}_{ID}'
        expected_output = {'SHOT': 'NAME', 'ID': '010'}

        self.assertEqual(expected_output, common.expand_string(format_string, shot))

    def test_expand_string_failure_0001(self):
        '''Force expand_string fails to prevent a bad match from occurring.'''
        text = '/jobs/some_job/some_kind/of/real_folders'
        pattern = '/jobs/{JOB}/some_kind/of/real_folders/inner'

        self.assertFalse(common.expand_string(pattern, text))

    def test_expand_string_failure_0002(self):
        '''Force expand_string fails to prevent a bad match from occurring.'''
        text = '/jobs/some_job/some_kind/of/real_folders'
        pattern = '/jobs/{JOB}/some_kind/{SHOTNAME}/real_folders/inner'

        self.assertFalse(common.expand_string(pattern, text))
