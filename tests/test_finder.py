#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''test the classes and methods for finder.py.'''

# IMPORT STANDARD LIBRARIES
import tempfile
import textwrap
import os

# IMPORT THIRD-PARTY LIBRARIES
from ways import finder

# IMPORT 'LOCAL' LIBRARIES
from . import common_test


class PathConstructionTestCase(common_test.ContextTestCase):

    '''Test the ways that the Find class can be made and its navigation mode.'''

    def test_find_context_by_glob(self):
        '''Use a Context's glob parse to get a Context for a file path.

        You may be wondering why this test is here, instead of being with the
        other Context tests and the reason is this method for finding Context
        objects is the backbone for how <finder.Path> objects are created.

        '''
        os.environ['JOB'] = 'something'
        temp_folder = tempfile.mkdtemp()
        self.temp_paths.append(temp_folder)

        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: 31tt/whatever
                    mapping: {root}/jobs/{{JOB}}/real_folder
                    mapping_details:
                        JOB:
                            mapping: '{{JOB_NAME}}_{{JOB_ID}}'
                            parse:
                                glob: '*'
            '''.format(root=temp_folder))

        self._make_plugin_folder_with_plugin2(contents=contents, folder=temp_folder)

        # Since this find_context example uses glob to search, the folder we're
        # looking for has to actually exist
        #
        the_path = os.path.join(temp_folder, 'jobs/something/real_folder')
        if not os.path.isdir(the_path):
            os.makedirs(the_path)

        context = finder.find_context(path=the_path, resolve_with=('env', 'glob'))
        self.assertNotEqual(context, None)

    def test_find_context_with_absolute_path(self):
        '''Define a Context with an absolute path and find it.'''
        temp_folder = tempfile.mkdtemp()
        self.temp_paths.append(temp_folder)

        some_file = os.path.join(temp_folder, 'jobs', 'something', 'real_folder', 'file.txt')
        contents = textwrap.dedent(
            '''
            globals: {{}}
            plugins:
                a_parse_plugin:
                    hierarchy: some/file/whatever
                    id: models
                    mapping: {root}/jobs/something/real_folder/file.txt
                    uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
            '''.format(root=temp_folder))

        self._make_plugin_folder_with_plugin2(contents=contents, folder=temp_folder)

        # Since this find_context example uses glob to search, the folder we're
        # looking for has to actually exist
        #
        directory = os.path.dirname(some_file)
        if not os.path.isdir(directory):
            os.makedirs(directory)

        open(some_file, 'w').close()

        context = finder.find_context(path=some_file, resolve_with=('env', 'glob'))

        self.assertEqual(context.get_hierarchy(), ('some', 'file', 'whatever'))

#     def test_paths_with_metadata(self):
#         paths = [
#             '/jobs/someJob_123/something/whatever/file.1001.tif',
#             '/jobs/someJob_123/something/whatever/file.1002.tif',
#             '/jobs/someJob_123/something/whatever/file.1003.tif',
#             '/jobs/someJob_123/something/whatever/file.1004.tif',

#             '/jobs/someJob_123/something/whatever/another/file.1001.tif',
#         ]
#         paths = [finder.Path(path) for path in paths]
#         self.assertTrue(all(path.context['metadata']['color'] == 'red' for path in paths))


# class PathReturnTestCase(unittest.TestCase):
#     def test_full_return(self):
#         pass

#     def test_partial_return(self):
#         pass


# class PathParseTestCase(unittest.TestCase):
#     def test_resolve_with_environment(self):
#         pass

#     def test_resolve_with_regex(self):
#         pass

#     def test_resolve_with_environment_then_regex(self):
#         pass

#     def test_resolve_with_regex_then_environment(self):
#         pass

#     def test_get_piece(self):
#         pass

#     def test_get_piece_recursive(self):
#         pass

#     def test_get_piece_recursive_environment(self):
#         # if a parse type is given, do not allow for any other parse type
#         # to be returned
#         #
#         pass

#     def test_get_piece_max_depth(self):
#         pass

#     def test_get_piece_max_depth_failed(self):
#         pass

