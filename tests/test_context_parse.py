#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test all of the different ways that Context objects can be parsed.'''

# IMPORT STANDARD LIBRARIES
import os
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from . import common_test


class ContextWithParseExpressionTestCase(common_test.ContextTestCase):

    '''A collection of tests for different ways to parse a Context.'''

    def test_plugin_parse(self):
        '''Test that a basic parse expression works correctly.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                z_parse_plugin:
                    hierarchy: 31tt/whatever
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('31tt/whatever')
        parse_regex = context.get_str(resolve_with='regex')
        expected_regex = r'/jobs/{JOB_NAME}_{JOB_ID}/some_kind/of/real_folders'
        self.assertEqual(parse_regex, expected_regex)

    def test_inner_parse_expression(self):
        '''Test that plugins with recursive parse tokens get values correctly.'''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: tt/whatever
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse:
                                glob:
                                    JOB: '*'
                                regex:
                                    JOB: \w+_\d{4}
                        JOB_ID:
                            parse:
                                glob: '*'
                                regex: \d{4}
                        JOB_NAME:
                            parse:
                                glob: '*'
                                regex: \w+
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('tt/whatever')
        parse_regex = context.get_str(resolve_with='regex')

        self.assertEqual(parse_regex,
                         r'/jobs/\w+_\d{4}/some_kind/of/real_folders')

    def test_inner_parse_expression_002(self):
        '''Test that two absolute plugins append to a relative plugin.'''
        # This plugin does nothing to build the final parse_regex.
        # It just exists to give us a couple opportunities for KeyErrors
        # for us to catch and fix. Basically, ignore b_parse_plugin
        # as long as this test passes
        #
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: tt/whatever
                    mapping: '{JOB_NAME}_{JOB_ID}'
                    mapping_details:
                        JOB_ID:
                            parse:
                                glob: '*'
                                regex: \d{4}
                        JOB_NAME:
                            parse:
                                glob: '*'
                                regex: \w+
                b_parse_plugin:
                    hierarchy: tt/whatever
                c_parse_plugin:
                    hierarchy: tt/whatever
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse:
                                glob:
                                    JOB: '*'
                                regex:
                                    JOB: \w+_\d{4}
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('tt/whatever')
        parse_regex = context.get_str(resolve_with='regex')

        self.assertEqual(parse_regex,
                         r'/jobs/\w+_\d{4}/some_kind/of/real_folders')

    def test_parse_env_vars(self):
        '''Resolve a Context object's mapping using environment variables.'''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: yytt/whatever
                    mapping: /jobs/{JOB}/some_kind/of/real_folders/{THING}
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                        THING:
                            parse:
                                regex: \w+
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')
        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('yytt/whatever')

        os.environ['JOB'] = 'some_job'
        parse_regex = context.get_str(resolve_with=('env', 'regex'))
        expected_regex = r'/jobs/some_job/some_kind/of/real_folders/\w+'
        self.assertEqual(parse_regex, expected_regex)

    def test_parse_with_a_set_depth(self):
        '''Attempt to parse a plugin's value to a set depth value.'''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: yytt/whatever
                    mapping: /thing/{JOB}/folders/{THING}
                    mapping_details:
                        ANOTHER:
                            mapping: '{OBJ}{VALUES}'
                            parse:
                                regex: \w+
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                        OBJ:
                            parse:
                                regex: \w
                        THING:
                            mapping: '{ANOTHER}_{TOKEN_SET}'
                        VALUES:
                            parse:
                                regex: (\w*)?
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('yytt/whatever')

        os.environ['JOB'] = 'job'
        parse_regex = context.get_str(resolve_with=('env', 'regex'), depth=1)
        expected_regex = r'/thing/job/folders/\w+_{TOKEN_SET}'
        self.assertEqual(parse_regex, expected_regex)

    def test_set_groups_with_dict(self):
        '''Test that varying input to get_str works as expected.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 31tt/whatever
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('31tt/whatever')
        parse_regex = context.get_str(resolve_with='regex', groups={'JOB_ID': 8})
        expected_regex = r'/jobs/{JOB_NAME}_8/some_kind/of/real_folders'
        self.assertEqual(parse_regex, expected_regex)

    def test_set_groups_with_tuple(self):
        '''Test that varying input to get_str works as expected.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 31tt/whatever
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('31tt/whatever')
        parse_regex = context.get_str(resolve_with='regex',
                                      groups=(('JOB_ID', 8), ))
        expected_regex = r'/jobs/{JOB_NAME}_8/some_kind/of/real_folders'
        self.assertEqual(parse_regex, expected_regex)

    def test_parse_with_invalid_input(self):
        '''Test that invalid input is caught early.

        No tokens that exist in holdout can exist as keys in 'groups'.

        '''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: 31tt/whatever
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                    JOB:
                        mapping: '{JOB_NAME}_{JOB_ID}'
                        parse: {}
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('31tt/whatever')

        with self.assertRaises(ValueError):
            context.get_str(
                resolve_with='regex', groups=(('JOB_ID', 8), ), holdout='JOB_ID')


class ContextParserMethodTestCase(common_test.ContextTestCase):

    '''Test the methods of the ContextParser object.'''

    def test_context_get_tokens(self):
        '''Check that get_tokens runs properly.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: whatever
                    mapping: /jobs/{JOB}/some_kind/of/real_folders/{THING}
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                        THING:
                            mapping: '{WHATEVER}'
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_sheet(contents=contents)

        context = ways.api.get_context('whatever')
        parser = context.get_parser()

        self.assertEqual(set(parser.get_tokens()), {'THING', 'JOB'})
