#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test the creation, registration, and methods of Ways Descriptors.'''

# IMPORT STANDARD LIBRARIES
import os
import sys
import shutil
import tempfile
import textwrap

# IMPORT THIRD-PARTY LIBRARIES
import git
import six

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from . import common_test

six.add_move(six.MovedModule('mock', 'mock', 'unittest.mock'))


class DescriptorContextTestCase(common_test.ContextTestCase):

    '''Test the different ways that Descriptor objects are created and loaded.'''

    def _local_git_repository_test(self, delete):
        '''Create a local git repository and return an example Context.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: ztt/whatever
            ''')

        git_repo_location = tempfile.mkdtemp()

        git_repository = git.Repo.init(git_repo_location)

        # Make a plugin and put it in smoe inner folder
        plugin_file_path = self._make_plugin_folder_with_plugin2(
            contents=contents, folder=git_repo_location)
        inner_folder = os.path.join(os.path.dirname(plugin_file_path), 'plugins')
        os.makedirs(inner_folder)
        new_plugin_path = os.path.join(inner_folder, os.path.basename(plugin_file_path))
        os.rename(plugin_file_path,
                  os.path.join(inner_folder, os.path.basename(plugin_file_path)))

        git_repository.index.add([new_plugin_path])
        git_repository.index.commit('Added a plugin file')

        temp_path = tempfile.mkdtemp()
        if delete:
            shutil.rmtree(temp_path)

        descriptor_info = {
            'create_using': 'ways.api.GitLocalDescriptor',
            'path': git_repo_location,
            'items': (temp_path, ),
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = ways.api.encode(descriptor_info)
        ways.api.add_descriptor(serialized_info)
        return ways.api.get_context('ztt/whatever')

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
        plugin_file_path = self._make_plugin_folder_with_plugin2(
            contents=contents, folder=git_repo_location)
        inner_folder = os.path.join(os.path.dirname(plugin_file_path), 'plugins')
        os.makedirs(inner_folder)
        new_plugin_path = os.path.join(inner_folder, os.path.basename(plugin_file_path))

        inner_path = os.path.join(inner_folder, os.path.basename(plugin_file_path))
        os.rename(plugin_file_path, inner_path)

        git_repository.index.add([new_plugin_path])
        git_repository.index.commit('Added a plugin file')

        descriptor_info = {
            'create_using': 'ways.api.GitLocalDescriptor',
            'path': git_repo_location,
            'items': ('plugins', ),
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = ways.api.encode(descriptor_info)
        ways.api.add_descriptor(serialized_info)
        context = ways.api.get_context('ztt/whatever')
        self.assertNotEqual(context, None)

    def test_exists_absolute_item(self):
        '''Create a local Git repo to absolute folders that exists.'''
        context = self._local_git_repository_test(delete=False)
        self.assertNotEqual(context, None)

    def test_not_exists_absolute_items(self):
        '''Create a local Git repo to absolute folders that do not exist.'''
        context = self._local_git_repository_test(delete=True)
        self.assertNotEqual(context, None)

    # def test_add_local_git_branch_descriptor(self):
    #     '''Gather plugins from a local git repository on a non-master branch.'''

    @six.moves.mock.patch('git.Repo.clone_from')  # pylint: disable=no-member
    def test_add_remote_git(self, clone_from_mock):
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
        plugin_file_path = self._make_plugin_folder_with_plugin2(
            contents=contents, folder=git_repo_location)
        inner_folder = os.path.join(os.path.dirname(plugin_file_path), 'plugins')

        os.makedirs(inner_folder)

        new_plugin_path = os.path.join(inner_folder, os.path.basename(plugin_file_path))

        inner = os.path.join(inner_folder, os.path.basename(plugin_file_path))
        os.rename(plugin_file_path, inner)

        git_repository.index.add([new_plugin_path])
        git_repository.index.commit('Added a plugin file')

        descriptor_info = {
            'create_using': 'ways.api.GitRemoteDescriptor',
            'url': 'https://github.com/Mock/url.git',  # Not a real URL
            'path': git_repo_location,
            'items': ('plugins', ),
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = ways.api.encode(descriptor_info)
        ways.api.add_descriptor(serialized_info)

        # Make a GitRemoteDescriptor class without specifying a path
        descriptor_info = {
            'create_using': 'ways.api.GitRemoteDescriptor',
            'url': 'https://github.com/Mock/url.git',  # Not a real URL
            'items': ('plugins', ),
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = ways.api.encode(descriptor_info)
        ways.api.add_descriptor(serialized_info)

        context = ways.api.get_context('ztt/whatever')
        self.assertNotEqual(context, None)

    def test_no_explicit_class(self):
        '''Adding a Descriptor without specifying 'create_using' should fail.'''
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
        serialized_info = ways.api.encode(descriptor_info)
        ways.api.add_descriptor(serialized_info)

        context = ways.api.get_context('ztt/whatever')
        self.assertNotEqual(context, None)

    def test_with_explicit_class(self):
        '''A generic Descriptor with 'create_using' defined should succeed.

        Note:
            {'create_using': 'ways.api.FolderDescriptor'} is the default
            class so you don't need to actually include it.

        '''
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
        serialized_info = ways.api.encode(descriptor_info)
        ways.api.add_descriptor(serialized_info)

        context = ways.api.get_context('ztt/whatever')
        self.assertNotEqual(context, None)

    # def test_add_remote_git_descriptor(self):
    #     '''Gather plugins from a remote (web) git repository.'''

    # def test_add_remote_git(self):
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

    def test_add_search_path_env_var(self):
        '''Add a Plugin Sheet file path that uses a environment variable.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: 2ff2/whatever
            ''')

        root = tempfile.mkdtemp()
        self.temp_paths.append(root)
        fake = os.path.join(root, '$JOB', 'example_plugin.yml')
        real = os.path.expandvars(fake)

        os.environ['JOB'] = 'foo'

        os.makedirs(os.path.dirname(real))

        with open(real, 'w') as file_:
            file_.write(contents)

        os.environ[ways.api.DESCRIPTORS_ENV_VAR] = fake

        ways.api.init_plugins()

        context = ways.api.get_context('2ff2/whatever')
        self.assertNotEqual(context, None)

    def test_callable_descriptor(self):
        '''Use a callable function/method as a descriptor.'''
        example = textwrap.dedent(
            """\
            class CustomPlugin(object):
                def __init__(self):
                    '''Create the object and keep a reference to the cache.'''
                    super(CustomPlugin, self).__init__()
                    self.data = dict()

                @classmethod
                def get_hierarchy(cls):
                    return ('foo', 'bar')


            class CallableDescriptor(object):
                def __init__(self):
                    '''Just create the object and do nothing else.'''
                    super(CallableDescriptor, self).__init__()

                def __call__(self):
                     return [CustomPlugin()]

            """)

        some_temp_folder = tempfile.mkdtemp()
        module_file_path = os.path.join(some_temp_folder, 'another.py')
        with open(module_file_path, 'w') as file_:
            file_.write(example)

        open(os.path.join(some_temp_folder, '__init__'), 'w').close()

        sys.path.append(some_temp_folder)

        descriptor_info = {
            'create_using': 'another.CallableDescriptor',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = ways.api.encode(descriptor_info)
        ways.api.add_descriptor(serialized_info)

        context = ways.api.get_context('foo/bar')
        self.assertNotEqual(None, context)

    def test_with_mixed_assignment(self):
        '''Make it so that a Descriptor can return a weird mixture of Plugins.

        It's usually best to stick to a single convention (return just a list
        of Plugin objects or return a list of Plugin, assigment pairs) but
        lets make sure we support both at once - because we can.

        '''
        value = 'buzz'
        example = textwrap.dedent(
            """\
            class CustomPlugin(object):
                def __init__(self, data):
                    '''Create the object and keep a reference to the cache.'''
                    super(CustomPlugin, self).__init__()
                    self.data = data

                @classmethod
                def get_hierarchy(cls):
                    return ('foo', 'bar')


            class CallableDescriptor(object):
                def __init__(self):
                    '''Just create the object and do nothing else.'''
                    super(CallableDescriptor, self).__init__()

                def __call__(self):
                    dict1 = dict()
                    dict1['some'] = '8'

                    dict2 = dict()
                    dict2['some'] = '{value}'
                    return [CustomPlugin(dict1), (CustomPlugin(dict2), 'job')]
            """).format(value=value)

        some_temp_folder = tempfile.mkdtemp()
        module_file_path = os.path.join(some_temp_folder, 'another2.py')
        with open(module_file_path, 'w') as file_:
            file_.write(example)

        open(os.path.join(some_temp_folder, '__init__'), 'w').close()

        sys.path.append(some_temp_folder)

        descriptor_info = {
            'create_using': 'another2.CallableDescriptor',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = ways.api.encode(descriptor_info)
        ways.api.add_descriptor(serialized_info)

        context = ways.api.get_context('foo/bar', assignment='job')
        self.assertEqual(value, context.data['some'])


class DescriptorInvalidTestCase(common_test.ContextTestCase):

    '''Test to make sure that invalid Descriptors raise errors properly.'''

    def test_not_importable(self):
        '''Try to create a Descriptor that isn't on the PYTHONPATH.'''
        root = tempfile.mkdtemp()
        self.temp_paths.append(root)
        descriptor_info = {
            'items': root,
            'create_using': 'foo.bar.bad.import.path',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = ways.api.encode(descriptor_info)

        self.assertEqual(ways.api.add_descriptor(serialized_info), None)

        self.assertEqual(
            ways.api.RESOLUTION_FAILURE_KEY,
            list(ways.api.trace_all_load_results()['descriptors'].values())[0]['reason']
        )

    def test_no_callable_method(self):
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
        self.temp_paths.append(some_temp_folder)

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
        serialized_info = ways.api.encode(descriptor_info)
        self.assertEqual(ways.api.add_descriptor(serialized_info), None)

    def test_not_callable_failure(self):
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
        serialized_info = ways.api.encode(descriptor_info)
        self.assertEqual(ways.api.add_descriptor(serialized_info), None)

    def test_bad_resolution(self):
        '''Create a descriptor that isn't able to be created, for some reason.'''
        descriptor_info = {
            'create_using': 'foo.bar.doesnt.exist.and.will.fail',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = ways.api.encode(descriptor_info)
        self.assertEqual(ways.api.add_descriptor(serialized_info), None)
