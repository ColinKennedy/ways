#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=protected-access,invalid-name

'''A collection of tests for Ways's documentation.

We make a TestCase per-page and test to make sure that pseudo-code we write
there works.

Also, it lets us copy/paste these files and provide as user-demos

'''

# IMPORT STANDARD LIBRARIES
import os
import sys
import tempfile
import textwrap

# IMPORT THIRD-PARTY LIBRARIES
# pylint: disable=import-error
from six.moves.urllib import parse

# IMPORT WAYS LIBRARIES
import ways.api
import ways.descriptor
from ways import cache

# IMPORT LOCAL LIBRARIES
from . import common_test


class GettingStartedTestCase(common_test.ContextTestCase):

    '''Test the code listed in the getting_started.rst documentation file.'''

    def test_hello_world_yaml(self):
        '''Make the most minimal plugin.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('some/context')
        self.assertNotEqual(context, None)

    def test_yaml_with_metadata(self):
        '''Test loading a YAML file with some metadata.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
                    data:
                        some:
                            arbitrary:
                                - info1
                                - info2
                                - 3
                                - bar
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('some/context')
        data = context.data['some']['arbitrary']
        self.assertEqual(data, ['info1', 'info2', 3, 'bar'])

    def test_persistent_context(self):
        '''Check to make sure that Context objects are Flyweights (persistent).'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
                    data:
                        some:
                            arbitrary:
                                - info1
                                - info2
                                - 3
                                - bar
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('some/context')
        context.data['some']['arbitrary'].append('bar2')

        def some_function():
            '''Do the test using a Context in a different scope.'''
            a_new_context = ways.api.get_context('some/context')
            data = ['info1', 'info2', 3, 'bar', 'bar2']
            self.assertEqual(data, a_new_context.data['some']['arbitrary'])

        some_function()

    def test_asset_initialization(self):
        '''Test to make sure that every way to instantiate an Asset works.'''
        contents = textwrap.dedent(
            '''
            plugins:
                job:
                    hierarchy: 'some/context'
                    mapping: /jobs/{JOB}/here
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        path = '/jobs/foo/here'

        # Test the different ways to initialize this asset
        asset1 = ways.api.get_asset((('JOB', 'foo'), ), 'some/context')
        asset2 = ways.api.get_asset({'JOB': 'foo'}, 'some/context')
        asset3 = ways.api.get_asset(path, 'some/context')

        job = 'foo'
        value = asset3.get_value('JOB')

        self.assertEqual(asset1, asset2, asset3)
        self.assertEqual(path, asset3.get_str())
        self.assertEqual(job, value)

    def test_context_action(self):
        '''Create an Action and register it to a Context.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        folders = ['/library', 'library/grades', 'comp', 'anim']

        _build_action('create', folders)

        context = ways.api.get_context('some/context')
        output = context.actions.create(folders)
        self.assertEqual(folders, output)

    def test_context_action_function(self):
        '''Test that action functions work correctly.'''
        contents = textwrap.dedent(
            '''
            plugins:
                foo_plugin:
                    hierarchy: 'some/context'
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        folders = ['/library', 'library/grades', 'comp', 'anim']

        def some_action(obj):  # pylint: disable=unused-argument
            '''Return our folders.'''
            return folders

        context = ways.api.get_context('some/context')
        ways.api.add_action(some_action, hierarchy='some/context')
        context.actions.some_action()

        # If you don't want to use the name of the function, you can give the action
        # a name
        #
        ways.api.add_action(some_action, 'custom_name', hierarchy='some/context')
        self.assertEqual(folders, context.actions.custom_name())

    def test_context_vs_asset_action(self):
        '''Test the differences between Context.actions and Asset.actions.'''
        contents = textwrap.dedent(
            '''
            plugins:
                job:
                    hierarchy: 'some/context'
                    mapping: /jobs/{JOB}/here
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        folders = ['/library', 'library/grades', 'comp', 'anim']
        _build_action('get_info', folders)

        asset = ways.api.get_asset({'JOB': 'foo'}, context='some/context')
        asset_info = asset.actions.get_info(folders)

        context = ways.api.get_context('some/context')
        standalone_context_info = context.actions.get_info(folders)

        asset_context_info = asset.context.actions.get_info(folders)

        self.assertEqual(folders, asset_info)
        self.assertEqual(folders, standalone_context_info)
        self.assertEqual(folders, asset_context_info)


class DescriptorsTestCase(common_test.ContextTestCase):

    '''A mixed set of Descriptor-related tests.

    This class has no real organization - it's just meant for test coverage.

    '''

    def test_descriptor_function_return(self):
        '''Check that our example string creates a proper GitLocalDescriptor.'''
        root = tempfile.mkdtemp()
        folder = 'plugins'
        resolved_path = os.path.join(root, folder)

        os.makedirs(resolved_path)
        self.temp_paths.append(resolved_path)

        descriptor = 'path={root}&create_using=ways.api.GitLocalDescriptor&items=plugins' \
                     ''.format(root=root)

        obj = cache._resolve_descriptor(descriptor)
        self.assertTrue(isinstance(obj, ways.api.GitLocalDescriptor))
        self.assertEqual(obj.path, root)
        self.assertEqual(obj.items, [resolved_path])

    def test_descriptor_rewrite(self):
        '''Change the begining example strings to URL encoded strings.'''
        folder_info = {
            'create_using': 'ways.api.FolderDescriptor',
            'items': ['/tmp/to/plugins/folder'],
        }

        yml_info = {
            'create_using': 'ways.api.FileDescriptor',
            'items': ['/tmp/to/plugin.yml'],
        }

        json_info = {
            'create_using': 'ways.api.FileDescriptor',
            'items': ['/tmp/to/plugin.json'],
        }

        py_info = {
            'create_using': 'ways.api.FileDescriptor',
            'items': ['/tmp/to/plugin.py'],
        }

        composite = [
            (
                folder_info,
                'items=%2Ftmp%2Fto%2Fplugins%2Ffolder&create_using=ways.api.FolderDescriptor',
                ways.api.FolderDescriptor
            ),
            (
                yml_info,
                'items=%2Ftmp%2Fto%2Fplugin.yml&create_using=ways.api.FileDescriptor',
                ways.api.FileDescriptor,
            ),
            (
                json_info,
                'items=%2Ftmp%2Fto%2Fplugin.json&create_using=ways.api.FileDescriptor',
                ways.api.FileDescriptor,
            ),
            (
                py_info,
                'items=%2Ftmp%2Fto%2Fplugin.py&create_using=ways.api.FileDescriptor',
                ways.api.FileDescriptor,
            )
        ]

        # TODO : nose!
        for info, encoding, class_item in composite:
            # Check to make sure the inspected encoding is OK
            details = ways.descriptor.conform_decode(parse.parse_qs(encoding))
            self.assertEqual(info, details)
            desc1 = cache._resolve_descriptor(info)
            desc2 = cache._resolve_descriptor(encoding)
            self.assertEqual(desc1, desc2)
            self.assertTrue(isinstance(desc1, class_item))
            self.assertTrue(isinstance(desc2, class_item))

    def test_callable_descriptor(self):
        '''Make a Descriptor that is just a function and then load it.'''
        root = '/tmp/path/'
        sys.path.append(root)

        path = os.path.join(root, 'some_module.py')

        if not os.path.isdir(root):
            os.makedirs(root)

        contents = textwrap.dedent(
            '''
            import ways.api

            def some_function(*args, **kwargs):
                return [ways.api.Plugin()]
            '''
        )

        with open(path, 'w') as file_:
            file_.write(contents)
            self.temp_paths.append(path)

        info = 'path={path}&create_using=some_module.some_function&items=plugins' \
               ''.format(path=path.replace(os.sep, '%2F'))
        os.environ['WAYS_DESCRIPTORS'] = info
        ways.clear()
        ways.api.init_plugins()
        descriptor = cache._resolve_descriptor(info)
        self.assertEqual(1, len(descriptor))


class ContextAdvancedTestCase(common_test.ContextTestCase):

    '''All tests for the Advanced Context section of Ways's documentation.'''

    def test_plugin_setups(self):
        '''Make sure that a "Hello World" absolute plugin matches relative.

        This method relies on Context.as_dict() to work.

        '''
        absolute = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz/buzz
            ''')
        self._make_plugin_folder_with_plugin2(absolute)
        context = ways.api.get_context('fizz/buzz')
        absolute_info = context.as_dict()

        ways.clear()

        relative = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz
                relative_plugin:
                    hierarchy: '{root}/buzz'
                    uses:
                        - fizz
            ''')
        self._make_plugin_folder_with_plugin2(relative)
        context = ways.api.get_context('fizz/buzz')
        relative_info = context.as_dict()

        self.assertEqual(absolute_info, relative_info)

    def test_invalid_hierarchy(self):
        '''A relative plugin cannot refer to its own hierarchy.'''
        contents = textwrap.dedent(
            '''
            plugins:
                relative:
                    mapping: something
                    hierarchy: some/place
                    uses:
                        - some/place
            ''')

        self._make_plugin_folder_with_plugin2(contents)
        context = ways.api.get_context('some/place')
        self.assertEqual(context, None)

        ways.clear()

        contents = textwrap.dedent(
            '''
            plugins:
                absolute:
                    mapping: whatever
                    hierarchy: foo
                relative:
                    mapping: "{root}/something"
                    hierarchy: "{foo}/bar"
                    uses:
                        - foo/bar
            ''')

        self._make_plugin_folder_with_plugin2(contents)
        context = ways.api.get_context('some/place')
        self.assertEqual(context, None)

    def test_recursive_relative_uses(self):
        '''Make a relative plugin that uses a relative plugin.'''
        contents = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz
                relative_plugin1:
                    hierarchy: '{root}/buzz'
                    uses:
                        - fizz
                relative_plugin2:
                    hierarchy: '{root}/foo'
                    uses:
                        - fizz/buzz
            ''')
        self._make_plugin_folder_with_plugin2(contents)
        context = ways.api.get_context('fizz/buzz/foo')
        self.assertNotEqual(None, context)

    def test_compare_relative_and_absolutes(self):
        '''Create a setup for absolute and relative that make the same result.'''
        contents = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz
                    mapping: bar

                absolute_plugin1:
                    hierarchy: fizz/buzz
                    mapping: bar/something

                absolute_plugin1_library:
                    hierarchy: fizz/buzz/library
                    mapping: bar/something/library

                absolute_plugin2:
                    hierarchy: fizz/buzz/pop
                    mapping: bar/something/another/thing

                absolute_plugin2_library:
                    hierarchy: fizz/buzz/pop/library
                    mapping: bar/something/another/thing/library

                absolute_plugin3:
                    hierarchy: fizz/buzz/pop/fizz
                    mapping: bar/something/another/thing/sets

                absolute_plugin3_library:
                    hierarchy: fizz/buzz/pop/fizz/library
                    mapping: bar/something/another/thing/sets/library

            ''')
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('fizz/buzz/pop/fizz/library')
        absolute_info = context.as_dict()

        ways.clear()

        contents = textwrap.dedent(
            '''
            plugins:
                absolute_plugin:
                    hierarchy: fizz
                    mapping: bar

                relative_plugin1:
                    hierarchy: '{root}/buzz'
                    mapping: '{root}/something'
                    uses:
                        - fizz

                absolute_plugin2:
                    hierarchy: '{root}/pop'
                    mapping: '{root}/another/thing'
                    uses:
                        - fizz/buzz

                absolute_plugin3:
                    hierarchy: '{root}/fizz'
                    mapping: '{root}/sets'
                    uses:
                        - fizz/buzz/pop

                library:
                    hierarchy: '{root}/library'
                    mapping: '{root}/library'
                    uses:
                        - fizz
                        - fizz/buzz
                        - fizz/buzz/pop
                        - fizz/buzz/pop/fizz
            ''')

        self._make_plugin_folder_with_plugin2(contents)
        context = ways.api.get_context('fizz/buzz/pop/fizz/library')
        relative_info = context.as_dict()

        self.assertEqual(absolute_info, relative_info)

    def test_absolute_and_relative_os_plugins(self):
        '''An absolute and relative setup that also have specific platforms.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                linux:
                    mapping: /jobs
                    hierarchy: job
                windows:
                    mapping: \\NETWORK\jobs\someJobName_123\library
                    hierarchy: job
                linux_library:
                    mapping: /jobs/someJobName_123/library
                    hierarchy: job/library
                windows_library:
                    mapping: \\NETWORK\jobs\someJobName_123\library
                    hierarchy: job/library
                linux_library_reference:
                    mapping: /jobs/someJobName_123/library/reference
                    hierarchy: job/library/reference
                windows_library_reference:
                    mapping: \\NETWORK\jobs\someJobName_123\library\reference
                    hierarchy: job/library/reference
            ''')

        self._make_plugin_folder_with_plugin2(contents)
        context = ways.api.get_context('job/library/reference')
        absolute_info = context.as_dict()

        ways.clear()

        contents = textwrap.dedent(
            r'''
            plugins:
                job_root_linux:
                    hierarchy: job
                    mapping: /jobs
                    platforms:
                        - linux

                job_root_windows:
                    hierarchy: job
                    mapping: \\NETWORK\jobs
                    platforms:
                        - windows

                library:
                    hierarchy: '{root}/library'
                    mapping: '{root}/someJobName_123/library'
                    uses:
                        - job

                reference:
                    hierarchy: '{root}/reference'
                    mapping: '{root}/reference'
                    uses:
                        - job/library
            ''')
        self._make_plugin_folder_with_plugin2(contents)
        context = ways.api.get_context('job/library/reference')
        relative_info = context.as_dict()

        self.assertEqual(absolute_info, relative_info)

    def test_absolute_and_relative_append(self):
        '''Append to another plugin using the absolute and relative syntax.'''
        key = 'some_data'
        value = 8
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                    mapping: something
                append_plugin:
                    hierarchy: foo/bar
                    data:
                        {key}: {value}
            ''').format(key=key, value=value)
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo/bar')
        absolute_info = context.data[key]

        ways.clear()

        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: foo/bar
                    mapping: something
                append_plugin:
                    hierarchy: ''
                    data:
                        {key}: {value}
                    uses:
                        - foo/bar
            ''').format(key=key, value=value)
        self._make_plugin_folder_with_plugin2(contents)

        context = ways.api.get_context('foo/bar')
        relative_info = context.data[key]

        self.assertEqual(absolute_info, value)
        self.assertEqual(relative_info, value)

    def test_plugin_file_types(self):
        '''Make directories with different plugin info files and read them.'''
        config = textwrap.dedent(
            '''
            assignment: foo
            recursive: false
            ''')
        root = tempfile.mkdtemp()

        yml = os.path.join(root, ways.api.PLUGIN_INFO_FILE_NAME + '.yml')
        with open(yml, 'w') as file_:
            file_.write(config)

        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: bar
            ''')
        self._make_plugin_folder_with_plugin2(contents, folder=root)

        context = ways.api.get_context('bar', assignment='foo')
        yml_assignment = context.get_assignment()

        ways.clear()

        config = textwrap.dedent(
            '''
            {
                "assignment": "foo",
                "recursive": false,
            }
            ''')
        root = tempfile.mkdtemp()

        jsn_ = os.path.join(root, ways.api.PLUGIN_INFO_FILE_NAME + '.json')
        with open(jsn_, 'w') as file_:
            file_.write(config)

        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: bar
            ''')
        self._make_plugin_folder_with_plugin2(contents, folder=root)

        context = ways.api.get_context('bar', assignment='foo')
        json_assignment = context.get_assignment()

        self.assertEqual('foo', yml_assignment)
        self.assertEqual('foo', json_assignment)

    def test_change_plugin_assignments(self):
        '''Test all 3 ways to assign items to plugins.

        By testing all 3 ways at once, we make sure that assignment priority
        works properly.

        '''
        config = textwrap.dedent(
            '''
            assignment: foo
            recursive: false
            ''')
        root = tempfile.mkdtemp()

        yml = os.path.join(root, ways.api.PLUGIN_INFO_FILE_NAME + '.yml')
        with open(yml, 'w') as file_:
            file_.write(config)

        contents = textwrap.dedent(
            '''
            plugins:
                a_plugin:
                    hierarchy: something
            '''
        )
        self._make_plugin_folder_with_plugin2(contents, folder=root)

        contents = textwrap.dedent(
            '''
            globals:
                assignment: bar
            plugins:
                some_plugin:
                    hierarchy: some/hierarchy
                    mapping: foo
                another_plugin:
                    hierarchy: another/hierarchy
                    mapping: bar
                    assignment: job
            ''')
        self._make_plugin_folder_with_plugin2(contents)
        config_context = ways.api.get_context('something', assignment='foo')
        globals_context = ways.api.get_context('some/hierarchy', assignment='bar')
        plugin_context = ways.api.get_context('another/hierarchy', assignment='job')

        self.assertNotEqual(None, config_context)
        self.assertNotEqual(None, globals_context)
        self.assertNotEqual(None, plugin_context)

    def test_assignment_basic_example(self):
        '''Show how assignments can affect runtime behavior.'''
        os.environ[ways.api.PRIORITY_ENV_VAR] = (os.pathsep).join(['master', 'job'])
        contents = textwrap.dedent(
            '''
            plugins:
                job:
                    hierarchy: job
                    mapping: '/jobs/{JOB}'
                shot:
                    hierarchy: '{root}/shot'
                    mapping: '{root}/{SCENE}/{SHOT}'
                    uses:
                        - job
                plates:
                    hierarchy: '{root}/plates'
                    mapping: '{root}/library/graded/plates'
                    uses:
                        - job/shot
                client_plates:
                    hierarchy: '{root}/client'
                    mapping: '{root}/clientinfo'
                    uses:
                        - job/shot/plates
                compositing:
                    hierarchy: '{root}/comp'
                    mapping: '{root}/compwork'
                    uses:
                        - job/shot/plates
            ''')
        self._make_plugin_folder_with_plugin2(contents)

        contents = textwrap.dedent(
            '''
            globals:
                assignment: job
            plugins:
                job_plugin:
                    hierarchy: '{root}/plates'
                    mapping: '{root}/archive/plates'
                    uses:
                        - job/shot
            ''')
        self._make_plugin_folder_with_plugin2(contents)

        expected = '/jobs/{JOB}/{SCENE}/{SHOT}/archive/plates/clientinfo'
        context = ways.api.get_context('job/shot/plates/client')
        self.assertEqual(expected, context.get_mapping())


class CustomPlugin(ways.api.Plugin):

    '''A Plugin.'''

    data = {'data': True}

    @classmethod
    def get_hierarchy(cls):
        '''('something', 'here').'''
        return ('something', 'here')


class CustomDescriptor(object):

    '''A Descriptor used for testing.'''

    @classmethod
    def get_plugins(cls):
        '''Get a plugin with an explicit assignment.'''
        return [(CustomPlugin(), 'master')]

    @classmethod
    def get_plugin_info(cls):
        '''Get some plugin info.'''
        return {'assignment': 'master', 'foo': 'bar'}


class CustomDescriptor1(object):

    '''A Descriptor used for testing.'''

    @classmethod
    def get_plugins(cls):
        '''Get a plugin without an explicit assignment.'''
        return [CustomPlugin()]

    @classmethod
    def get_plugin_info(cls):
        '''Get some plugin info.'''
        return {'assignment': 'master', 'foo': 'bar'}


def _build_action(action, folders):
    '''Create an Action object and return it.'''
    class SomeAction(ways.api.Action):  # pylint: disable=unused-variable

        '''A subclass that will automatically be registered by Ways.

        The name of the class (SomeAction) can be anything but the name
        property must be correct. Also, get_hierarchy must match the Context
        hierarchy that this action will apply to.

        '''

        name = action
        items = []

        @classmethod
        def get_hierarchy(cls):
            return 'some/context'

        def __call__(self, obj, folders):
            '''Do something.'''
            return folders

    SomeAction.items = folders
    return SomeAction
