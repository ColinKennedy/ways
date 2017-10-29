#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import tempfile
import textwrap
import urllib
import sys
import os

# IMPORT THIRD-PARTY LIBRARIES
from six.moves.urllib import parse
import six
six.add_move(six.MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock
import git

# IMPORT 'LOCAL' LIBRARIES
from . import common_test
import ways.api


class DescriptorContextTestCase(common_test.ContextTestCase):
    def test_add_local_git_descriptor(self):
        '''Gather plugins from a local git repository.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: ztt/whatever
            ''')

        git_repo_location = tempfile.mkdtemp()

        git_repository = git.Repo.init(git_repo_location)

        # Make a plugin and put it in smoe inner folder
        plugin_file_path = self._make_plugin_folder_with_plugin2(contents=contents, folder=git_repo_location)
        inner_folder = os.path.join(os.path.dirname(plugin_file_path), 'plugins')
        os.makedirs(inner_folder)
        new_plugin_path = os.path.join(inner_folder, os.path.basename(plugin_file_path))
        os.rename(plugin_file_path, os.path.join(inner_folder, os.path.basename(plugin_file_path)))

        git_repository.index.add([new_plugin_path])
        git_repository.index.commit('Added a plugin file')

        descriptor_info = {
            'create_using': 'ways.api.GitLocalDescriptor',
            'path': git_repo_location,
            'items': ('plugins', ),
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = parse.urlencode(descriptor_info, doseq=True)
        self.cache.add_descriptor(serialized_info)
        context = ways.api.get_context('ztt/whatever')
        self.assertNotEqual(context, None)

    # def test_add_local_git_branch_descriptor(self):
    #     '''Gather plugins from a local git repository on a non-master branch.'''

    @mock.patch('git.Repo.clone_from')
    def test_add_remote_git_branch_descriptor(self, clone_from_mock):
        '''Check that we can pull git plugins from an online repository.'''
        clone_from_mock.return_value = None

        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: ztt/whatever
            ''')

        git_repo_location = tempfile.mkdtemp()

        git_repository = git.Repo.init(git_repo_location)

        # Make a plugin and put it in smoe inner folder
        plugin_file_path = self._make_plugin_folder_with_plugin2(contents=contents, folder=git_repo_location)
        inner_folder = os.path.join(os.path.dirname(plugin_file_path), 'plugins')
        os.makedirs(inner_folder)
        new_plugin_path = os.path.join(inner_folder, os.path.basename(plugin_file_path))
        os.rename(plugin_file_path, os.path.join(inner_folder, os.path.basename(plugin_file_path)))

        git_repository.index.add([new_plugin_path])
        git_repository.index.commit('Added a plugin file')

        descriptor_info = {
            'create_using': 'ways.api.GitRemoteDescriptor',
            'url': 'https://github.com/Mock/url.git',  # Not a real URL
            'path': git_repo_location,
            'items': ('plugins', ),
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = parse.urlencode(descriptor_info, doseq=True)
        self.cache.add_descriptor(serialized_info)
        context = ways.api.get_context('ztt/whatever')
        self.assertNotEqual(context, None)

    def test_add_descriptor_without_an_explicit_class(self):
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: ztt/whatever
            ''')

        plugin_file_path = self._make_plugin_folder_with_plugin2(contents=contents)

        descriptor_info = {
            'items': os.path.dirname(plugin_file_path),
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = parse.urlencode(descriptor_info, doseq=True)
        self.cache.add_descriptor(serialized_info)

        context = ways.api.get_context('ztt/whatever')
        self.assertNotEqual(context, None)

    def test_add_descriptor_with_an_explicit_class(self):
        # '''

        # Note:
        #     {'create_using': 'ways.api.FolderDescriptor'} is the default
        #     class so you don't need to actually include it.

        # '''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: ztt/whatever
            ''')

        plugin_file_path = self._make_plugin_folder_with_plugin2(contents=contents)

        descriptor_info = {
            'items': os.path.dirname(plugin_file_path),
            'create_using': 'ways.api.FolderDescriptor',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = parse.urlencode(descriptor_info, doseq=True)
        self.cache.add_descriptor(serialized_info)

        context = ways.api.get_context('ztt/whatever')
        self.assertNotEqual(context, None)

    # def test_add_remote_git_descriptor(self):
    #     '''Gather plugins from a remote (web) git repository.'''

    # def test_add_remote_git_branch_descriptor(self):
    #     '''Gather plugins from a remote (web) git branch repository.'''

    def test_add_search_path_folder(self):
        '''Add a folder that contains Plugin Sheet files.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: 2tt/whatever
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('2tt/whatever')
        self.assertNotEqual(context, None)

    def test_add_search_path_file(self):
        '''Add a Plugin Sheet file path, directly.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: 2ff2/whatever
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('2ff2/whatever')
        self.assertNotEqual(context, None)

    # def test_add_local_git_branch_descriptor(self):
    #     '''Gather plugins from a local git branch repository.'''

    # def test_add_remote_git_descriptor(self):
    #     '''Gather plugins from a remote (web) git repository.'''

    # def test_add_remote_git_branch_descriptor(self):
    #     '''Gather plugins from a remote (web) git branch repository.'''

    def test_callable_descriptor(self):
        '''Use a callable function/method as a descriptor.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: 2tt/whatever
            ''')

        plugin_file_path = self._make_plugin_folder_with_plugin2(contents=contents)

        example_bad_class = textwrap.dedent(
            """\
            class BadDescriptor(object):

                '''A Descriptor that does not work.'''

                def __init__(self, items):
                    '''Just create the object and do nothing else.'''
                    super(BadDescriptor, self).__init__()

                def __call__(self):
                     return []

            """)

        some_temp_folder = tempfile.mkdtemp()
        module_file_path = os.path.join(some_temp_folder, 'another.py')
        with open(module_file_path, 'w') as file_:
            file_.write(example_bad_class)

        open(os.path.join(some_temp_folder, '__init__'), 'w').close()

        sys.path.append(some_temp_folder)

        descriptor_info = {
            'items': os.path.dirname(plugin_file_path),
            'create_using': 'another.BadDescriptor',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = parse.urlencode(descriptor_info, doseq=True)
        self.cache.add_descriptor(serialized_info)


class DescriptorInvalidTestCase(common_test.ContextTestCase):

    '''Test to make sure that invalid Descriptors raise errors properly.'''

    def test_descriptor_has_no_supported_callable_method(self):
        '''Descriptor has no get_plugin or __call__ method.'''
        contents = textwrap.dedent(
            '''
            plugins:
            a_parse_plugin:
                hierarchy: 2tt/whatever
            ''')
        plugin_file_path = self._make_plugin_folder_with_plugin2(
            contents=contents, register=False)

        example_bad_class = textwrap.dedent(
            """\
            class BadDescriptor(object):

                '''A Descriptor that does not work.'''

                def __init__(self, items):
                    '''Just create the object and do nothing else.'''
                    super(BadDescriptor, self).__init__()
            """)

        some_temp_folder = tempfile.mkdtemp()
        module_file_path = os.path.join(some_temp_folder, 'something.py')
        with open(module_file_path, 'w') as file_:
            file_.write(example_bad_class)

        open(os.path.join(some_temp_folder, '__init__'), 'w').close()

        sys.path.append(some_temp_folder)

        descriptor_info = {
            'items': os.path.dirname(plugin_file_path),
            'create_using': 'something.BadDescriptor',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = parse.urlencode(descriptor_info, doseq=True)
        self.assertEqual(self.cache.add_descriptor(serialized_info), None)

    def test_descriptor_get_plugins_is_not_callable(self):
        '''A Descriptor whose get_plugins name is not a valid method.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: 2tt/whatever
            ''')
        plugin_file_path = self._make_plugin_folder_with_plugin2(
            contents=contents, register=False)

        example_bad_class = textwrap.dedent(
            """\
            class BadDescriptor(object):

                '''A Descriptor that does not work.'''

                def __init__(self, items):
                    '''Just create the object and do nothing else.'''
                    super(BadDescriptor, self).__init__()

                    self.get_plugins = None

            """)

        some_temp_folder = tempfile.mkdtemp()
        module_file_path = os.path.join(some_temp_folder, 'something.py')
        with open(module_file_path, 'w') as file_:
            file_.write(example_bad_class)

        open(os.path.join(some_temp_folder, '__init__'), 'w').close()

        sys.path.append(some_temp_folder)

        descriptor_info = {
            'items': os.path.dirname(plugin_file_path),
            'create_using': 'something.BadDescriptor',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = parse.urlencode(descriptor_info, doseq=True)
        self.assertEqual(self.cache.add_descriptor(serialized_info), None)


if __name__ == '__main__':
    print(__doc__)

