#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test the basic methods of the Asset class, in a variety of Contexts.'''

# IMPORT STANDARD LIBRARIES
import os
import glob
import tempfile
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
from . import common_test


class AssetCreateTestCase(common_test.ContextTestCase):

    '''The main test for the Asset class.'''

    def test_create_asset_from_string(self):
        '''Create an Asset class, using only a string.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: some/context
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
            ''')

        self._make_plugin_sheet(contents=contents)

        some_path = '/jobs/some_job/some_kind/of/real_folders'
        context = ways.api.get_context('some/context')
        asset = ways.api.get_asset(some_path, context=context)

        self.assertNotEqual(asset, None)

    def test_create_asset_from_string_fail(self):
        '''Try to create an Asset and fail because the paths are different.'''
        contents = {
            'globals': {},
            'plugins': {
                'a_parse_plugin': {
                    'mapping': '/jobs/{JOB}/some_kind/of/real_folders',
                    'mapping_details': {
                        'JOB': {
                            'parse': {
                                'regex': '.+',
                            },
                        },
                    },
                    'hierarchy': 'some/other/context',
                },
            },
        }
        plugin = self._make_plugin_sheet(contents=contents)
        ways.api.add_search_path(os.path.dirname(plugin))

        some_path = '/jobs/some_job/some_other_kind/of/real_folders'
        context = ways.api.get_context('some/other/context')
        asset = ways.api.get_asset(some_path, context=context)

        self.assertEqual(asset, None)

    def test_create_asset_context_from_string(self):
        '''Create an Asset class, giving a Context hierarchy as a string.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: some/other/context
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
                            required: false
            ''')

        self._make_plugin_sheet(contents=contents)

        some_path = '/jobs/some_job/some_kind/of/real_folders'
        asset = ways.api.get_asset(some_path, context='some/other/context')

        self.assertNotEqual(asset, None)


class AssetMethodTestCase(common_test.ContextTestCase):

    '''Test the methods on a ways.api.Asset object.'''

    def test_asset_get_missing_required_tokens(self):
        '''Find the tokens that are needed by a Asset/Context.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: some/other/context
                    mapping: /jobs/{JOB}/some_kind/{THING}/real_folders
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
                            required: true
                        THING:
                            parse:
                                regex: .+
                            required: false
            ''')

        self._make_plugin_sheet(contents=contents)

        some_path = '/jobs/some_job_here/some_kind/of/real_folders'
        asset = ways.api.get_asset(some_path, context='some/other/context')
        # Intentionally break this asset for this test
        del asset.info['JOB']

        required_tokens = asset.get_missing_required_tokens()
        self.assertEqual(required_tokens, ['JOB'])

    def test_asset_get_unfilled_required_tokens(self):
        '''Find tokens that don't have info for a Asset/Context.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: some/other/context
                    mapping: /jobs/{JOB}/some_kind/{THING}/real_folders
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
                            required: true
                        THING:
                            parse:
                                regex: .+
                            required: false
            ''')

        self._make_plugin_sheet(contents=contents)

        asset = ways.api.get_asset({'JOB': 'asdf'}, context='some/other/context')

        unfilled_tokens = asset.get_unfilled_tokens()
        self.assertEqual(unfilled_tokens, ['THING'])

    def test_asset_get_tokens(self):
        '''Get the tokens of this Asset of some parse type.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: some/other/context
                    mapping: /jobs/{JOB}/some_kind/{THING}/real_folders
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
                            required: true
                        THING:
                            parse:
                                regex: .+
                            required: false
            ''')

        self._make_plugin_sheet(contents=contents)

        asset = ways.api.get_asset({'JOB': 'asdf', 'THING': '8'}, context='some/other/context')
        tokens = asset.get_token_parse('JOB', 'regex')
        self.assertEqual('.+', tokens)

    def test_asset_set_value(self):
        '''Try to change the value of an Asset, after it has been created.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: some/other/context
                    mapping: /jobs/{JOB}/some_kind/{THING}/real_folders
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
                            required: true
                        THING:
                            parse:
                                regex: .+
                            required: false
            ''')

        self._make_plugin_sheet(contents=contents)

        asset = ways.api.get_asset({'JOB': 'asdf'}, context='some/other/context')
        asset.set_value('THING', '8')
        self.assertEqual(asset.get_value('THING'), '8')

    def test_get_value_with_token_that_has_value(self):
        '''Get the value of a token that is defined.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            parse:
                                regex: .+
            ''')

        self._make_plugin_sheet(contents=contents)

        shot_value = 'asdf'
        asset = ways.api.get_asset({'SHOT_NAME': shot_value}, context='a/context')
        self.assertEqual(asset.get_value('SHOT_NAME'), shot_value)

    def test_get_value_with_token_that_has_parent_value(self):
        '''Build a value for a token, automatically, using its parent.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            mapping: '{SHOT_PREFIX}_{SHOT_ID}'
                        SHOT_PREFIX:
                            parse:
                                regex: '[A-Z]+'
                        SHOT_ID:
                            parse:
                                regex: '[0-9]+'
            ''')

        self._make_plugin_sheet(contents=contents)

        shot_id = '0012'
        shot_name = 'SHOTNAME_' + shot_id
        asset = ways.api.get_asset({'SHOT_NAME': shot_name}, context='a/context')
        value = asset.get_value('SHOT_ID')
        self.assertEqual(value, shot_id)

    def test_get_value_with_token_that_has_child_values(self):
        '''Build a value for a token that has all child tokens defined.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            mapping: '{SHOT_PREFIX}_{SHOT_ID}'
                        SHOT_PREFIX:
                            parse:
                                regex: '[A-Z]+'
                        SHOT_ID:
                            parse:
                                regex: '[0-9]+'
            ''')

        self._make_plugin_sheet(contents=contents)

        shot_id = '010'
        shot_prefix = 'SHOT'
        asset = ways.api.get_asset(
            {'SHOT_PREFIX': shot_prefix, 'SHOT_ID': shot_id}, context='a/context')
        value = asset.get_value('SHOT_NAME')
        self.assertEqual(value, shot_prefix + '_' + shot_id)

    def test_get_value_with_token_that_has_parent_value_recursive(self):
        '''Build a value for a token, automatically, using its parent.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/{JOB}/scene/something/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                        JOB_ID:
                            mapping: '{JOB_SITE}.{JOB_UUID}'
                        JOB_NAME:
                            parse:
                                regex: '[a-zA-Z0-9]+'
                        JOB_SITE:
                            parse:
                                regex: '[123456]'
                        JOB_UUID:
                            parse:
                                regex: '[0-9]{3}'

            ''')

        self._make_plugin_sheet(contents=contents)

        asset = ways.api.get_asset({'JOB': 'fooBar_1.342'}, context='a/context')
        value = asset.get_value('JOB_SITE')
        self.assertEqual(value, '1')

    def test_get_value_from_parent_regex_parser(self):
        '''Use regex to split a parent token and return some value.'''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/{JOB}/scene/something/real_folders
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}{JOB_ID}'
                        JOB_ID:
                            mapping: '{JOB_SITE}.{JOB_UUID}'
                        JOB_NAME:
                            parse:
                                regex: '[a-zA-Z0-9]+'
                        JOB_SITE:
                            parse:
                                regex: '[123456]'
                        JOB_UUID:
                            parse:
                                regex: '[0-9]{3}'

            ''')

        self._make_plugin_sheet(contents=contents)

        asset = ways.api.get_asset({'JOB': 'fooBar1.342'}, context='a/context')
        value = asset.get_value('JOB_SITE')
        self.assertEqual(value, '1')

    def test_get_value_with_token_that_has_child_values_recursive(self):
        '''Build a value for a token that has all child tokens defined.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            mapping: '{SHOT_PREFIX}_{SHOT_ID}'
                        SHOT_PREFIX:
                            mapping: '{SHOT_INNER_PREFIX}.{SHOT_INNER_SUFFIX}'
                        SHOT_INNER_PREFIX:
                            parse:
                                regex: '[A-Z]+'
                        SHOT_INNER_SUFFIX:
                            parse:
                                regex: 't'
                        SHOT_ID:
                            parse:
                                regex: '[0-9]+'
            ''')

        self._make_plugin_sheet(contents=contents)

        shot_id = '010'
        shot_prefix = 'SHOT.t'
        asset = ways.api.get_asset(
            {'SHOT_PREFIX': shot_prefix, 'SHOT_ID': shot_id}, context='a/context')
        value = asset.get_value('SHOT_NAME')
        self.assertEqual(value, shot_prefix + '_' + shot_id)

    def test_find_token_parse(self):
        '''Test for when a token has no parse type but has a mapping which does.'''
        contents = textwrap.dedent(
            r'''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            mapping: "{SOMETHING}"
                        SOMETHING:
                            parse:
                                regex: '\w+'
            ''')

        self._make_plugin_sheet(contents=contents)

        asset = ways.api.get_asset({'SHOT_NAME': 'foo'}, context='a/context')
        value = asset.get_token_parse('SHOT_NAME')
        self.assertEqual(r'\w+', value)

    def test_no_token_parse(self):
        '''Test for when there is not token mapping or parse type.'''
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            arbitrary: info
            ''')

        self._make_plugin_sheet(contents=contents)

        asset = ways.api.get_asset({'SHOT_NAME': 'foo'}, context='a/context')
        value = asset.get_token_parse('SHOT_NAME')
        self.assertFalse(value)

    def test_awkward_token_mappings_0001(self):
        '''If a parent token is missing a value and its child has a bad mappging.

        A user will probably (hopefully) never do this but they may accidentally
        add a mapping a token and forget to add at least one child token.

        For example this is what Ways would expect:

        .. code-block :: yaml

            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            mapping: whatever

        But a user might write:

        .. code-block :: yaml

            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            mapping: "{SOMETHING}"
                        SOMETHING:
                            mapping: whatever

        '''
        contents = textwrap.dedent(
            '''
            plugins:
                a_parse_plugin:
                    hierarchy: a/context
                    mapping: /jobs/some_job/scene/{SHOT_NAME}/real_folders
                    mapping_details:
                        SHOT_NAME:
                            mapping: "{SOMETHING}"
                        SOMETHING:
                            mapping: whatever
            ''')

        self._make_plugin_sheet(contents=contents)

        asset = ways.api.get_asset({'SHOT_NAME': 'foo'}, context='a/context')

        # Remove SHOT_NAME so that get_value has to search through SHOT_NAME's
        # child tokens
        #
        del asset.info['SHOT_NAME']

        value = asset.get_value('SHOT_NAME')
        self.assertFalse(value)

    def test_unfilled_tokens_bugfix_0001_required_tokens_missing(self):
        '''Fixing an issue where get_unfilled_tokens was breaking my scripts.

        This is a reproduction of a larger issue that was found in production
        where the scene Context.actions.get_shots did not return the right values.

        '''
        class JobSceneShotPlugin(ways.api.Action):

            '''A generic Action that returns Asset objects.'''

            name = 'get_shots'

            @classmethod
            def get_hierarchy(cls):
                '''Get a hierarchy for this job/scene Action.'''
                return ('job', 'scene')

            def __call__(self, shot, *args, **kwargs):
                context = ways.api.get_context('job/scene/shot')
                shot_glob = context.get_str(resolve_with=('glob', ), groups=kwargs)

                shots = []
                for shot_ in glob.glob(shot_glob):
                    shots.append(shot_)

                return [ways.api.get_asset(path, context='job/scene/shot')
                        for path in shots]

        def make_fake_job_and_scenes(prefix):
            '''Create some fake job(s) and scene(s).'''
            paths_to_create = [
                os.path.join('anotherJobName_24391231', 'whatever', 'SH_0010'),
                os.path.join('anotherJobName_24391231', 'SOMETHING', 'SH_0010'),
                os.path.join('anotherJobName_24391231', 'SOMETHING', 'SH_0020'),
                os.path.join('anotherJobName_24391231', 'config', 'SH_0010'),
            ]
            paths_to_create = [os.path.join(prefix, path) for path in paths_to_create]

            for path in paths_to_create:
                if not os.path.isdir(path):
                    os.makedirs(path)

        tempdir = tempfile.gettempdir()

        # Define our Contexts
        contents = textwrap.dedent(
            r'''
            plugins:
                a_parse_plugin:
                    hierarchy: job
                    mapping: '{temproot}/{{JOB}}'
                    platforms:
                        - linux
                        - darwin
                    uuid: some_uuid

                windows_parse_plugin:
                    hierarchy: job
                    mapping: '{temproot}\{{JOB}}'
                    platforms:
                        - windows
                    uuid: another_uuid

                a_parse_details_plugin:
                    hierarchy: job
                    mapping_details:
                        JOB:
                            mapping: '{{JOB_NAME}}_{{JOB_ID}}'
                            parse:
                                glob: '*'
                        JOB_NAME:
                            casing: snakecase
                            parse:
                                regex: '[a-z]{{3,}}[a-zA-Z]{{3,}}'
                                glob: '*'
                        JOB_ID:
                            parse:
                                regex: '\d{{3,}}'
                                glob: '*'
                    uuid: 4b3dc3bc-fd9b-40ff-8175-26a5b9223fc7

                scene_base_plugin:
                    hierarchy: '{{root}}/scene'
                    mapping: '{{root}}/{{SCENE}}'
                    mapping_details:
                        SCENE:
                            casing: capscase
                            parse:
                                regex: '[A-Z]{{5,}}'
                                glob: '*'
                    path: true
                    uses:
                        - job
                    uuid: 040a5511-aa53-42ae-9bc3-eb332841616e

                shot_base_plugin:
                    hierarchy: '{{root}}/shot'
                    mapping: '{{root}}/{{SHOT_NAME}}'
                    mapping_details:
                        SHOT_NAME:
                            casing: capscase
                            mapping: '{{SHOT_PREFIX}}_{{SHOT_NUMBER}}'
                            parse:
                                regex: '[A-Z]{{2,}}_0[0-9]{{3}}'
                                glob: '*'
                        SHOT_PREFIX:
                            parse:
                                regex: '[A-Z]{{2,}}'
                        SHOT_NUMBER:
                            parse:
                                regex: '0[0-9]{{4}}'
                    uuid: b9bc2279-14bc-4461-9805-cf0b8969c715
                    uses:
                        - job/scene
            ''').format(temproot=tempdir)

        self._make_plugin_sheet(contents=contents)

        # Set up our fake environment
        make_fake_job_and_scenes(tempdir)

        info = {
            'JOB': 'anotherJobName_24391231',
            'SCENE': 'SOMETHING',
        }
        shot_name_prefix = 'SH'

        scene = ways.api.get_asset(info, context='job/scene')
        shots = [shot for shot in scene.actions.get_shots(**info)
                 if shot.get_value('SHOT_NAME').startswith(shot_name_prefix)]

        created_shots = []
        for shot in shots:
            shot_path = shot.get_str(resolve_with=('env', ), groups=info)
            if os.path.isdir(shot_path):
                created_shots.append(shot)

        self.assertTrue(JobSceneShotPlugin.name in dir(scene.actions))
        self.assertEqual(len(created_shots), 2)
        self.assertTrue(all((isinstance(shot, ways.api.Asset) for shot in created_shots)))

    def test_get_value_builtin(self):
        '''Cast the return of "get_value" into another datatype.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                a_parse_plugin:
                    hierarchy: job
                    mapping: '/tmp/{JOB}'
                    mapping_details:
                        JOB:
                            mapping: '{JOB_NAME}_{JOB_ID}'
                        JOB_ID:
                            before_return:
                                - int
            ''')

        self._make_plugin_sheet(contents)

        asset = ways.api.get_asset({'JOB': 'something_123'}, context='job')
        self.assertEqual(asset.get_value('JOB_ID'), 123)

    def test_get_value_function(self):
        '''Run a function and return its value instead of the original value.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                scene_plugin:
                    hierarchy: job/scene
                    mapping: '/tmp/{JOB}/{SCENE}'
                    mapping_details:
                        SCENE:
                            before_return:
                                - ways.common.get_platforms
                shot_plugin:
                    hierarchy: job/scene/shot
                    mapping: '/tmp/{JOB}/{SCENE}/{SHOT}'
            ''')

        self._make_plugin_sheet(contents)

        shot = ways.api.get_asset(
            {'JOB': 'something_123', 'SCENE': 'foo', 'SHOT': 'bar'},
            context='job/scene/shot')

        scene = shot.get_value('SCENE')
        self.assertEqual(('*', ), scene)

    def test_get_value_multifunction(self):
        '''Run multiple, separate functions before returning "get_value".'''
        contents = textwrap.dedent(
            r'''
            plugins:
                scene_plugin:
                    hierarchy: job/scene
                    mapping: '/tmp/{JOB}/{SCENE}'
                    mapping_details:
                        SCENE:
                            before_return:
                                - ways.helper.common.get_platforms
                                - ways.parsing.trace.trace_assignment
                shot_plugin:
                    hierarchy: job/scene/shot
                    mapping: '/tmp/{JOB}/{SCENE}/{SHOT}'
            ''')

        self._make_plugin_sheet(contents)

        shot = ways.api.get_asset(
            {'JOB': 'something_123', 'SCENE': 'foo', 'SHOT': 'bar'},
            context='job/scene/shot')

        scene = shot.get_value('SCENE')
        self.assertEqual(ways.api.DEFAULT_ASSIGNMENT, scene)

    def test_get_value_single_function(self):
        '''Run a function in "before_value" even if it was not given as a list.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                scene_plugin:
                    hierarchy: job/scene
                    mapping: '/tmp/{JOB}/{SCENE}'
                    mapping_details:
                        SCENE:
                            before_return: ways.common.get_platforms
            ''')

        self._make_plugin_sheet(contents)

        scene = ways.api.get_asset(
            {'JOB': 'something_123', 'SCENE': 'foo'}, context='job/scene')

        scene = scene.get_value('SCENE')
        self.assertEqual(('*', ), scene)

    def test_get_value_real(self):
        '''Force "get_value" to return the original string.'''
        contents = textwrap.dedent(
            r'''
            plugins:
                scene_plugin:
                    hierarchy: job/scene
                    mapping: '/tmp/{JOB}/{SCENE}'
                    mapping_details:
                        SCENE:
                            before_return:
                                - ways.common.get_platforms
            ''')

        self._make_plugin_sheet(contents)

        name = 'foo'
        scene = ways.api.get_asset(
            {'JOB': 'bar', 'SCENE': name}, context='job/scene')

        scene = scene.get_value('SCENE', real=True)
        self.assertEqual(name, scene)


class AssetRegistrationTestCase(common_test.ContextTestCase):

    '''Test the different ways that we can register classes for our assets.'''

    def setUp(self):
        '''Reset the registered Asset classes after each test.'''
        super(AssetRegistrationTestCase, self).setUp()
        ways.clear()

    def test_register_and_create_a_custom_asset(self):
        '''Return back some class other than a default Asset class.'''
        asset_class = _get_asset_class()
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: some/thing/context
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
                            required: false
            ''')

        self._make_plugin_sheet(contents=contents)

        # Create a default Asset
        some_path = '/jobs/some_job/some_kind/of/real_folders'
        asset = ways.api.get_asset(some_path, context='some/thing/context')
        asset_is_default_asset_type = isinstance(asset, ways.api.Asset)

        # Register a new class type for our Context
        context = ways.api.get_context('some/thing/context')
        ways.api.register_asset_class(asset_class, context)

        # Get back our new class type
        asset = ways.api.get_asset(some_path, context='some/thing/context')
        asset_is_not_default_asset_type = not isinstance(asset, ways.api.Asset)
        asset.example_method()

        self.assertNotEqual(None, asset)
        self.assertTrue(asset_is_default_asset_type)
        self.assertTrue(asset_is_not_default_asset_type)

    def test_register_and_create_a_custom_asset_with_init(self):
        '''Create an Asset class that is created with a non-default init.'''
        asset_class = _get_asset_class()

        def a_custom_init_function(info, context, *args, **kwargs):
            '''Purposefully ignore the context that gets passed.'''
            context = 8
            return asset_class(info, context, *args, **kwargs)

        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: some/thing/context
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
                            required: false
            ''')

        self._make_plugin_sheet(contents=contents)

        # Create a default Asset
        some_path = '/jobs/some_job/some_kind/of/real_folders'
        asset = ways.api.get_asset(some_path, context='some/thing/context')
        asset_is_default_asset_type = isinstance(asset, ways.api.Asset)

        # Register a new class type for our Context
        context = ways.api.get_context('some/thing/context')
        ways.api.register_asset_class(
            asset_class, context, init=a_custom_init_function)

        # Get back our new class type
        asset = ways.api.get_asset(some_path, context='some/thing/context')
        asset.example_method()

        asset_is_not_default_asset_type = not isinstance(asset, ways.api.Asset)

        self.assertNotEqual(None, asset)
        self.assertTrue(asset_is_default_asset_type)
        self.assertTrue(asset_is_not_default_asset_type)

    def test_register_and_create_a_custom_asset_with_parent_hierarchy(self):
        '''Call a custom Asset class from a child hierarchy, using its parent.'''
        asset_class = _get_asset_class()
        contents = textwrap.dedent(
            '''
            globals: {}
            plugins:
                a_parse_plugin:
                    hierarchy: some/thing/context
                    mapping: /jobs/{JOB}/some_kind/of/real_folders
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
                            required: false
                b_parse_plugin:
                    hierarchy: some/thing/context/inner
                    mapping: /jobs/{JOB}/some_kind/of/real_folders/inner
                    mapping_details:
                        JOB:
                            parse:
                                regex: .+
                            required: false
            ''')

        self._make_plugin_sheet(contents=contents)

        # Create a default Asset
        some_path = '/jobs/some_job/some_kind/of/real_folders/inner'
        asset = ways.api.get_asset(some_path, context='some/thing/context/inner')
        asset_is_default_asset_type = isinstance(asset, ways.api.Asset)

        # Register a new class type for our Context
        ways.api.register_asset_class(asset_class, 'some/thing/context', children=True)

        # Get back our new class type
        asset = ways.api.get_asset(some_path, context='some/thing/context/inner')
        asset_is_not_default_asset_type = not isinstance(asset, ways.api.Asset)

        self.assertTrue(asset_is_default_asset_type)
        self.assertTrue(asset_is_not_default_asset_type)


def _get_asset_class():
    '''Just make a generic asset class.'''
    class SomeNewAssetClass(object):

        '''Some class that will take the place of our Asset.'''

        def __init__(self, info, context):
            '''Create the object.'''
            super(SomeNewAssetClass, self).__init__()
            self.context = context

        def example_method(self):
            '''Run some method.'''
            return 8

        def another_method(self):
            '''Run another method.'''
            return 'bar'

    return SomeNewAssetClass
