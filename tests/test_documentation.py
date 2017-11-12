#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=protected-access,invalid-name,too-many-lines

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
from ways import cache
from ways import common

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
                     '&uuid=some_unique_string-we-can_search_for-later' \
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
            details = common.conform_decode(parse.parse_qs(encoding))
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


class PluginBasicsTestCase(common_test.ContextTestCase):

    '''All tests for the Plugin Basics section of Ways's documentation.'''

    def _make_complex_setup(self):
        '''Build a lot of plugins at once, for this TestCase.'''
        contents = textwrap.dedent(
            r'''
            globals:
                assignment: an_assignment_to_every_plugin
            plugins:
                some_plugin:
                    hierarchy: example
                    uuid: something_unique

                this_can_be_called_anything:
                    hierarchy: example/hierarchy
                    mapping: "/jobs/{JOB}"
                    uuid: another_unique_uuid
                    platforms:
                        - linux

                window_jobs_plugin:
                    hierarchy: example/hierarchy
                    mapping: "C:\\Users\\{USER}\\jobs\\{JOB}"
                    mapping_details:
                        USER:
                            parse:
                                regex: \w+
                    platforms:
                        - windows
                    uuid: windows_job

                jobs_details:
                    hierarchy: example/hierarchy
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                        JOB_NAME:
                            mapping: '{JOB_NAME_PREFIX}_{JOB_NAME_SUFFIX}'
                        JOB_NAME_PREFIX:
                            parse:
                                regex: '\w+'
                        JOB_NAME_SUFFIX:
                            parse:
                                regex: 'thing-\w+'
                        JOB_ID:
                            parse:
                                regex: '\d{3}'
                    uuid: something_unique

                yet_another_plugin:
                    hierarchy: example/tree
                    mapping: /tree
                    uuid: does_not_matter_what_it_is

                config_plugin:
                    hierarchy: "{root}/config"
                    mapping: "{root}/configuration"
                    uses:
                        - example/hierarchy
                        - example/hierarchy/tree
                    uuid: as_Long_as_It_is_Different

                some_assigned_plugin:
                    assignment: different_assignment
                    hierarchy: something
                    data:
                        important_information: here
                    uuid: boo
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        os.environ[ways.api.PRIORITY_ENV_VAR] = (os.pathsep).join(
            ['master', 'an_assignment_to_every_plugin'])

    def test_hello_world_yaml(self):
        '''Make sure hello world works. Yes, I know this test is redundant.'''
        contents = textwrap.dedent(
            '''
            plugins:
                some_plugin:
                    hierarchy: example
            ''')

        self._make_plugin_folder_with_plugin2(contents=contents)

        context = ways.api.get_context('example')
        self.assertNotEqual(None, context)

    def test_regular_vs_autofind_context(self):
        '''Defining a Context should create the same result as auto-find.'''
        self._make_complex_setup()

        mapping = '/jobs/job_part_something'

        explicit_asset = ways.api.get_asset(mapping, context='example/hierarchy')
        autofound_asset = ways.api.get_asset(mapping)
        self.assertNotEqual(None, explicit_asset)
        self.assertEqual(explicit_asset, autofound_asset)

    def test_mapping_details_parse(self):
        '''Test that mapping_details gets its parse strings as expected.'''
        self._make_complex_setup()

        context = ways.api.get_context('example/hierarchy')
        os.environ['JOB'] = 'job_thing-something_123'

        expected_env_string = '/jobs/job_thing-something_123'
        self.assertEqual(expected_env_string, context.get_str(resolve_with=('env', 'regex')))

        expected_regex_string = '/jobs/\w+_thing-\w+_\d{3}'
        self.assertEqual(expected_regex_string, context.get_str(resolve_with='regex'))
        self.assertEqual(expected_regex_string, context.get_str(resolve_with=('regex', )))

    def test_mapping_details_get_value(self):
        '''Test that mapping_details Parent-/Child-Search works correctly.'''
        self._make_complex_setup()

        mapping = '/jobs/job_thing-something_123'

        asset = ways.api.get_asset(mapping, context='example/hierarchy')
        expected = 'thing-something'
        self.assertEqual(expected, asset.get_value('JOB_NAME_SUFFIX'))


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


class TroubleshootingTestCase(common_test.ContextTestCase):

    '''A group of tests for the code snippets in the troubleshooting page.'''

    def _make_simple_plugin_tree(self):
        contents = textwrap.dedent(
            '''
            plugins:
                a_plugin_root:
                    hierarchy: foo
                    mapping: /jobs
                another_plugin:
                    hierarchy: foo/bar
                    mapping: /jobs/foo/thing
                yet_another_plugin:
                    hierarchy: foo/bar/buzz
                still_more_plugins:
                    hierarchy: foo/fizz
                did_you_know_camels_have_three_eyelids?:
                    hierarchy: foo/fizz/something
                okay_maybe_you_knew_that:
                    hierarchy: foo/fizz/another
                but_I_thought_it_was_cool:
                    hierarchy: foo/fizz/another/here
            '''
        )

        self._make_plugin_folder_with_plugin2(contents=contents)

    def test_basic_descriptor_with_uuid(self):
        '''Test to make sure that a Descriptor is created as we expect.'''
        uuid_ = "foo_bad_path"
        info = {
            "items": "/some/folder/path",
            "create_using": "foo.bar.bad.import.path",
            "uuid": uuid_,
        }

        descriptor_string = \
            'items=%2Fsome%2Ffolder%2Fpath&create_using=foo.bar.bad.import.path&' \
            'uuid=foo_bad_path'

        os.environ['WAYS_DESCRIPTORS'] = descriptor_string

        descriptor_string = _itemize_seralized_descriptor(descriptor_string)
        output = _itemize_seralized_descriptor(parse.urlencode(info, doseq=True))
        self.assertEqual(descriptor_string, output)

        # Add the Descriptor
        ways.api.init_plugins()

        self.assertEqual(
            ways.api.RESOLUTION_FAILURE_KEY,
            ways.api.trace_all_descriptor_results_info()[uuid_]['reason'])

    def test_basic_descriptor_no_uuid(self):
        '''Test to make sure that a Descriptor is created as we expect.

        The Descriptor result should still exist, just not with any known UUID.

        '''
        info = {
            "items": "/some/folder/path",
            "create_using": "foo.bar.bad.import.path",
        }

        descriptor_string = \
            'items=%2Fsome%2Ffolder%2Fpath&create_using=foo.bar.bad.import.path'

        os.environ['WAYS_DESCRIPTORS'] = descriptor_string

        descriptor_string = _itemize_seralized_descriptor(descriptor_string)
        output = _itemize_seralized_descriptor(parse.urlencode(info, doseq=True))
        self.assertEqual(descriptor_string, output)

        # Add the Descriptor
        ways.api.init_plugins()

        self.assertEqual(
            ways.api.RESOLUTION_FAILURE_KEY,
            ways.api.trace_all_descriptor_results()[0]['reason'])

    def test_not_callable_failure(self):
        '''Create a Descriptor not-callable error matching what the docs.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: 2tt/whatever
            ''')
        self._make_plugin_folder_with_plugin2(contents=contents, register=False)

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
        module_file_path = os.path.join(some_temp_folder, 'module.py')
        with open(module_file_path, 'w') as file_:
            file_.write(example_bad_class)

        sys.path.append(some_temp_folder)

        uuid_ = 'some_uuid'
        descriptor_info = {
            'create_using': 'module.BadDescriptor',
            'uuid': uuid_,
            'items': '/something/here',
        }

        # Create an example serialized descriptor that describes our local repo
        serialized_info = parse.urlencode(descriptor_info, True)
        expected_encoded_string = \
            'items=%2Fsomething%2Fhere&' \
            'create_using=module.BadDescriptor&' \
            'uuid=some_uuid'
        expected_encoded_string = _itemize_seralized_descriptor(expected_encoded_string)
        serialized_info_ = _itemize_seralized_descriptor(serialized_info)

        self.assertEqual(expected_encoded_string, serialized_info_)
        self.assertEqual(ways.api.add_descriptor(serialized_info), None)
        self.assertEqual(ways.api.NOT_CALLABLE_KEY,
                         ways.api.trace_all_descriptor_results_info()[uuid_]['reason'])

    def test_plugin_import_failure(self):
        '''Try to load a Plugin that doesn't exist and report an error.'''
        os.environ['WAYS_PLUGINS'] = '/some/path/that/doesnt/exist.py'

        ways.api.init_plugins()

        self.assertEqual(
            ways.api.IMPORT_FAILURE_KEY,
            ways.api.trace_all_plugin_results()[0]['reason'])

    def test_plugin_main_failure(self):
        '''Try to load a Plugin but stop because the main function is broken.'''
        uuid_ = 'some_uuid_here'
        contents = textwrap.dedent(
            '''
            import ways.api

            WAYS_UUID = '{uuid_}'

            def main():
                raise ValueError('invalid main function')

            ''').format(uuid_=uuid_)

        root = tempfile.mkdtemp()
        self.temp_paths.append(root)

        path = os.path.join(root, 'example_plugin.py')
        with open(path, 'w') as file_:
            file_.write(contents)

        os.environ['WAYS_PLUGINS'] = path

        ways.api.init_plugins()

        self.assertEqual(
            ways.api.LOAD_FAILURE_KEY,
            ways.api.trace_all_plugin_results_info()[uuid_]['reason'])

    def test_get_all_hierarchies(self):
        '''Get all of the hierarchies that Ways is allowed to use.'''
        self._make_simple_plugin_tree()

        expected = {('foo', ), ('foo', 'bar'), ('foo', 'bar', 'buzz'),
                    ('foo', 'fizz'), ('foo', 'fizz', 'something'),
                    ('foo', 'fizz', 'another'), ('foo', 'fizz', 'another', 'here')}

        self.assertEqual(expected, ways.api.get_all_hierarchies())

    def test_get_all_hierarchies_full(self):
        '''Get all of the hierarchies that Ways is allowed to use as a tree.'''
        self._make_simple_plugin_tree()

        expected = \
            {
                ('foo', ):
                {
                    ('foo', 'bar'):
                    {
                        ('foo', 'bar', 'buzz'): {},
                    },
                    ('foo', 'fizz'):
                    {
                        ('foo', 'fizz', 'something'): {},
                        ('foo', 'fizz', 'another'):
                        {
                            ('foo', 'fizz', 'another', 'here'): {}
                        },
                    },
                },
            }

        self.assertEqual(expected, ways.api.get_all_hierarchy_trees(full=True))

    def test_get_all_hierarchies_concise(self):
        '''Get all of the hierarchies that Ways is allowed to use as a tree.'''
        self._make_simple_plugin_tree()

        expected = \
            {
                'foo':
                {
                    'bar':
                    {
                        'buzz': {},
                    },
                    'fizz':
                    {
                        'something': {},
                        'another':
                        {
                            'here': {}
                        },
                    },
                },
            }

        self.assertEqual(expected, ways.api.get_all_hierarchy_trees(full=False))

    def test_get_child_hierarchies(self):
        '''Get the Ways hierarchy starting at a certain point.'''
        # '''Get some children. Wait, that didn't come out right.'''
        self._make_simple_plugin_tree()

        hierarchy = ('foo', 'fizz')
        context = ways.api.get_context(hierarchy)
        asset = ways.api.get_asset({}, context=context)

        expected = {('foo', 'fizz', 'something'), ('foo', 'fizz', 'another'),
                    ('foo', 'fizz', 'another', 'here')}

        self.assertEqual(expected, ways.api.get_child_hierarchies(hierarchy))
        self.assertEqual(expected, ways.api.get_child_hierarchies(context))
        self.assertEqual(expected, ways.api.get_child_hierarchies(asset))

    def test_get_child_hierarchy_tree_full(self):
        '''Get the Ways hierarchy starting at a certain point.'''
        self._make_simple_plugin_tree()

        hierarchy = ('foo', 'fizz')
        context = ways.api.get_context(hierarchy)
        asset = ways.api.get_asset({}, context=context)

        expected = \
            {
                ('foo', 'fizz', 'something'): {},
                ('foo', 'fizz', 'another'):
                {
                    ('foo', 'fizz', 'another', 'here'): {},
                },
            }

        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(hierarchy, full=True))
        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(context, full=True))
        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(asset, full=True))

    def test_get_child_hierarchy_tree_concise(self):
        '''Get the Ways hierarchy starting at a certain point.'''
        self._make_simple_plugin_tree()

        hierarchy = ('foo', 'fizz')
        context = ways.api.get_context(hierarchy)
        asset = ways.api.get_asset({}, context=context)

        expected = \
            {
                'something': {},
                'another':
                {
                    'here': {},
                },
            }

        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(hierarchy, full=False))
        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(context, full=False))
        self.assertEqual(expected, ways.api.get_child_hierarchy_tree(asset, full=False))

    def test_trace_method_resolution_plugins_off(self):
        '''Find out the way a method "resolves" its plugins.'''
        self._make_simple_plugin_tree()

        context = ways.api.get_context('foo/bar')
        expected = ['/jobs', '/jobs/foo/thing']
        self.assertEqual(expected, ways.api.trace_method_resolution(context.get_mapping))

        # This check is to make sure that trace_method_resolution didn't
        # break the original functionality of the Context
        #
        self.assertEqual(expected[-1], context.get_mapping())

    def test_trace_method_resolution_plugins_on(self):
        '''Find out the way a method "resolves" its plugins.'''
        self._make_simple_plugin_tree()

        context = ways.api.get_context('foo/bar')
        expected = [('/jobs', context.plugins[0]),
                    ('/jobs/foo/thing', context.plugins[1])]
        self.assertEqual(
            expected, ways.api.trace_method_resolution(context.get_mapping, plugins=True))

        # This check is to make sure that trace_method_resolution didn't
        # break the original functionality of the Context
        #
        self.assertEqual(expected[-1][0], context.get_mapping())

    def test_get_action_hierarchies(self):
        '''Get the hierarchies that an Action name is attached to.'''
        self._make_simple_plugin_tree()

        _build_action('some_action', hierarchy='foo/bar')
        _build_action('some_action', hierarchy='foo/fizz')

        _build_action('another_action', hierarchy='foo/bar')

        expected = {('foo', 'bar'), ('foo', 'fizz')}
        self.assertEqual(expected, ways.api.get_action_hierarchies('some_action'))

    def test_get_action_hierarchies_from_class(self):
        '''Use an Action class to find the hierachies that it can run on.'''
        self._make_simple_plugin_tree()

        action = _build_action('some_action', hierarchy='foo/bar')
        _build_action('some_action', hierarchy='foo/fizz')

        _build_action('another_action', hierarchy='foo/bar')

        expected = {('foo', 'bar'), }
        self.assertEqual(expected, ways.api.get_action_hierarchies(action))

    def test_get_action_hierarchies_from_function(self):
        '''Use an Action function to find the hierachies that it can run on.'''
        self._make_simple_plugin_tree()

        def some_function():
            '''Do some function.'''
            print('Example function return')

        _build_action('some_action', hierarchy='foo/fizz')

        ways.api.add_action(some_function, name='something', hierarchy='foo/bar')
        expected = {('foo', 'bar'), }
        self.assertEqual(expected, ways.api.get_action_hierarchies(some_function))

    def test_get_all_action_hierarchies(self):
        '''Get every Action name and the hierarchies that can use it.'''
        self._make_simple_plugin_tree()

        _build_action('some_action', hierarchy='foo/bar')
        _build_action('some_action', hierarchy='foo/fizz')

        _build_action('another_action', hierarchy='foo/bar')

        self.assertTrue(ways.api.get_all_action_hierarchies())


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


def _build_action(action, folders=None, hierarchy='some/context'):
    '''Create an Action object and return it.'''
    if folders is None:
        folders = []

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
            return hierarchy

        def __call__(self, obj, folders):
            '''Do something.'''
            return folders

    SomeAction.items = folders
    return SomeAction


def _itemize_seralized_descriptor(descriptor):
    '''set[str]: Break a Descriptor string to its parts.'''
    return set(descriptor.split('&'))
