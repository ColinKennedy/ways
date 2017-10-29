#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import unittest
import textwrap
import os

# IMPORT 'LOCAL' LIBRARIES
from . import common_test
import ways.api


class ContextWithParseExpressionTestCase(common_test.ContextTestCase):

    '''A collection of tests for different ways to parse a Context.'''

    def test_plugin_with_parse_expression(self):
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                z_parse_plugin:
                    hidden: false
                    hierarchy: 31tt/whatever
                    id: models
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                    navigatable: true
                    selectable: true
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('31tt/whatever')
        parse_regex = context.get_str(resolve_with='regex')
        expected_regex = r'/jobs/{JOB_NAME}_{JOB_ID}/some_kind/of/real_folders'
        self.assertEqual(parse_regex, expected_regex)

    def test_plugin_with_inner_parse_expression(self):
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hidden: false
                    hierarchy: tt/whatever
                    id: models
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
                    navigatable: true
                    selectable: true
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('tt/whatever')
        parse_regex = context.get_str(resolve_with='regex')

        self.assertEqual(parse_regex,
                         r'/jobs/\w+_\d{4}/some_kind/of/real_folders')

    def test_plugins_with_inner_parse_expression(self):
        # This plugin does nothing to build the final parse_regex.
        # It just exists to give us a couple opportunities for KeyErrors
        # for us to catch and fix. Basically, ignore b_parse_plugin
        # as long as this test passes
        #
        contents = textwrap.dedent(
            '''
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

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('tt/whatever')
        parse_regex = context.get_str(resolve_with='regex')

        self.assertEqual(parse_regex,
                         r'/jobs/\w+_\d{4}/some_kind/of/real_folders')

# #     def test_plugin_with_parse_and_inner_descriptions(self):
# #         contents = {
# #             'globals': {},
# #             'plugins': {
# #                 'some_unique_plugin_name': {
# #                     'mapping': '/jobs/{JOB}/some_kind/of/real_folders',
# #                     'mapping_details': {
# #                         'JOB': '{JOB_NAME}_{JOB_ID}',
# #                     }
# #                     'mapping_parse': {
# #                         'glob': {
# #                             'JOB': '*'
# #                         },
# #                         'regex': {
# #                             'JOB': '\w+_\d{4}',
# #                             'JOB_NAME': '{JOB_MASTER_NAME}{JOB_DESCRIPTION}',
# #                             'JOB_INNER_NAME': '[a-z]+[a-z0-9]',
# #                             'JOB_DESCRIPTION': '[A-Z0-9]+',
# #                         },
# #                     },
# #                     'hidden': False,
# #                     'navigatable': True,
# #                     'selectable': True,
# #                     'hierarchy': '/asdf/whatever',
# #                     'uuid': '0d255517-dbbf-4a49-a8d0-285a06b2aa6d',
# #                     'id': 'models',
# #                 },
# #             }
# #         }
# #         self._make_plugin_folder_with_plugin(contents=contents)

    def test_parse_env_vars(self):
        '''Resolve a Context object's mapping using environment variables.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hidden: false
                    hierarchy: yytt/whatever
                    id: models
                    mapping: /jobs/{JOB}/some_kind/of/real_folders/{THING}
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                        THING:
                            parse:
                                regex: \w+
                    navigatable: true
                    selectable: true
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')
        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('yytt/whatever')

        os.environ['JOB'] = 'some_job'
        parse_regex = context.get_str(resolve_with=('env', 'regex'))
        expected_regex = r'/jobs/some_job/some_kind/of/real_folders/\w+'
        self.assertEqual(parse_regex, expected_regex)

    def test_parse_with_a_set_depth(self):
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hidden: false
                    hierarchy: yytt/whatever
                    id: models
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
                    navigatable: true
                    selectable: true
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('yytt/whatever')

        os.environ['JOB'] = 'job'
        parse_regex = context.get_str(resolve_with=('env', 'regex'), depth=1)
        expected_regex = r'/thing/job/folders/\w+_{TOKEN_SET}'
        self.assertEqual(parse_regex, expected_regex)

    def test_set_groups_with_dict(self):
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hidden: false
                    hierarchy: 31tt/whatever
                    id: models
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                    navigatable: true
                    selectable: true
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('31tt/whatever')
        parse_regex = context.get_str(resolve_with='regex', groups={'JOB_ID': 8})
        expected_regex = r'/jobs/{JOB_NAME}_8/some_kind/of/real_folders'
        self.assertEqual(parse_regex, expected_regex)

    def test_set_groups_with_tuple(self):
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hidden: false
                    hierarchy: 31tt/whatever
                    id: models
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                    navigatable: true
                    selectable: true
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('31tt/whatever')
        parse_regex = context.get_str(resolve_with='regex',
                                      groups=(('JOB_ID', 8), ))
        expected_regex = r'/jobs/{JOB_NAME}_8/some_kind/of/real_folders'
        self.assertEqual(parse_regex, expected_regex)

    def test_parse_with_invalid_input(self):
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hidden: false
                    hierarchy: 31tt/whatever
                    id: models
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                    JOB:
                        mapping: '{JOB_NAME}_{JOB_ID}'
                        parse: {}
                    navigatable: true
                    selectable: true
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('31tt/whatever')

        with self.assertRaises(ValueError):
            parse_regex = context.get_str(resolve_with='regex',
                                        groups=(('JOB_ID', 8), ),
                                        holdout='JOB_ID')


class ContextParserMethodTestCase(common_test.ContextTestCase):

    '''Test the methods of the ContextParser object.'''

    def test_context_get_tokens(self):
        '''Check that get_tokens runs properly.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hidden: false
                    hierarchy: whatever
                    id: models
                    mapping: /jobs/{JOB}/some_kind/of/real_folders/{THING}
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                            parse: {}
                        THING:
                            mapping: '{WHATEVER}'
                    navigatable: true
                    selectable: true
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('whatever')
        parser = context.get_parser()

        self.assertEqual(set(parser.get_tokens()), {'THING', 'JOB'})


if __name__ == '__main__':
    print(__doc__)

