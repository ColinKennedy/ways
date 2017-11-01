#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Ways uses a few techniques to automatically load its objects.

Plugin Sheets, Desctiptors, and Python plugin files all have different ways
of being added to the Ways cache so we'll test these methods, in this module.

'''

# IMPORT STANDARD LIBRARIES
import os
import tempfile
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api

# IMPORT LOCAL LIBRARIES
# IMPORT 'LOCAL' LIBRARIES
from . import common_test


class AutoloadTestCase(common_test.ContextTestCase):

    '''Test to that Plugins and Descriptors load in the HistoryCache.'''

    def test_plugins_from_env_file(self):
        '''Mimic a user adding plugins to a pathfinder environment variable.'''
        plugin_file_contents = textwrap.dedent(
            """\
            # IMPORT STANDARD LIBRARIES
            import tempfile
            import json
            import os

            # IMPORT THIRD-PARTY LIBRARIES
            from ways import cache
            import ways.api


            def main():
                class SomeNewAssetClass(object):

                    '''Some class that will take the place of our Asset.'''

                    def __init__(self, info):
                        '''Create the object.'''
                        super(SomeNewAssetClass, self).__init__()
                        self.context = context

                def a_custom_init_function(info, context, *args, **kwargs):
                    '''Purposefully ignore the context that gets passed.'''
                    return SomeNewAssetClass(info, *args, **kwargs)

                def make_plugin_folder_with_plugin_load(contents):
                    '''str: Make a folder and put a plugin inside of it.'''
                    folder = tempfile.mkdtemp()

                    plugin_file = os.path.join(folder, 'example_plugin' + '.json')

                    with open(plugin_file, 'w') as file_:
                        json.dump(contents, file_)

                    return plugin_file

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
                                    'required': False,
                                },
                            },
                            'hierarchy': 'some/thing2/context',
                        },
                    },
                }

                path = make_plugin_folder_with_plugin_load(contents)
                ways.api.add_search_path(path)

                # Create a default Asset
                some_path = '/jobs/some_job/some_kind/of/real_folders'
                asset = ways.api.get_asset(some_path, context='some/thing2/context')
                asset_is_default_asset_type = isinstance(asset, ways.api.Asset)

                # Register a new class type for our Context
                context = ways.api.get_context('some/thing2/context')
                ways.api.register_asset_info(
                    SomeNewAssetClass, context, init=a_custom_init_function)

            """)

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)

        with temp_file as file_:
            file_.write(plugin_file_contents)

        os.environ[ways.api.PLUGINS_ENV_VAR] = temp_file.name

        # Note: This method normally runs on init but because of other tests
        #       instantiating the HistoryCache, we just re-add our plugins
        #
        ways.api.init_plugins()

        path = '/jobs/some_job/some_kind/of/real_folders'
        self.assertFalse(
            isinstance(ways.api.get_asset(info=path, context='some/thing2/context'),
                       ways.api.Asset))

    def test_plugins_from_env_folder(self):
        '''Mimic a user adding plugin folders to a pathfinder env var.'''
        temp_directory = tempfile.mkdtemp()

        plugin_file_contents = textwrap.dedent(
            """\
            # IMPORT STANDARD LIBRARIES
            import tempfile
            import json
            import os

            # IMPORT THIRD-PARTY LIBRARIES
            import ways.api


            def main():
                class SomeNewAssetClass(object):

                    '''Some class that will take the place of our Asset.'''

                    def __init__(self, info):
                        '''Create the object.'''
                        super(SomeNewAssetClass, self).__init__()
                        self.context = context

                def a_custom_init_function(info, context, *args, **kwargs):
                    '''Purposefully ignore the context that gets passed.'''
                    return SomeNewAssetClass(info, *args, **kwargs)

                def make_plugin_folder_with_plugin_load(contents):
                    '''str: Make a folder and put a plugin inside of it.'''
                    folder = tempfile.mkdtemp()

                    plugin_file = os.path.join(folder, 'example_plugin' + '.json')

                    with open(plugin_file, 'w') as file_:
                        json.dump(contents, file_)

                    return plugin_file

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
                                    'required': False,
                                },
                            },
                            'hierarchy': 'some/thing2/context',
                        },
                    },
                }

                plugin_file = make_plugin_folder_with_plugin_load(contents=contents)
                folder = os.path.dirname(plugin_file)
                ways.api.add_search_path(folder)

                # Create a default Asset
                some_path = '/jobs/some_job/some_kind/of/real_folders'
                asset = ways.api.get_asset(some_path, context='some/thing2/context')
                asset_is_default_asset_type = isinstance(asset, ways.api.Asset)

                # Register a new class type for our Context
                context = ways.api.get_context('some/thing2/context')
                ways.api.register_asset_info(
                    SomeNewAssetClass, context, init=a_custom_init_function)

            """)

        temp_file = tempfile.NamedTemporaryFile(suffix='.py').name
        with open(os.path.join(temp_directory, os.path.basename(temp_file)), 'w') as file_:
            file_.write(plugin_file_contents)

        # Add the path to our env var
        os.environ[ways.api.PLUGINS_ENV_VAR] = temp_directory

        # Note: This method normally runs on init but because of other tests
        #       instantiating the HistoryCache, we just re-add our plugins
        #
        ways.api.init_plugins()

        path = '/jobs/some_job/some_kind/of/real_folders'

        self.assertFalse(
            isinstance(ways.api.get_asset(info=path, context='some/thing2/context'),
                       ways.api.Asset))

    # TODO : Make this test pass, again
    # def test_load_descriptors_from_env_var(self):
    #     '''Mimic a user adding descriptors to our environment variable.'''
    #     contents = textwrap.dedent(
    #         '''
    #         globals: {}
    #         plugins:
    #             a_parse_plugin:
    #                 hidden: false
    #                 hierarchy: 2tt/whatever
    #                 id: models
    #                 mapping: /jobs/whatever/some_kind/of/real_folders
    #                 navigatable: true
    #                 selectable: true
    #                 uuid: 0d255517-dbbf-4a49-a8d0-285a06b2aa6d
    #         ''')

    #     # plugin_file = common_test.make_folder_plugin(
    #     #     'AnotherClass', contents=contents)
    #     plugin_file = self._make_plugin_folder_with_plugin2(
    #         contents=contents, ending='.json')

    #     # Add the path to our env var
    #     plugin_env_var = 'WAYS_DESCRIPTORS'
    #     os.environ.setdefault(plugin_env_var, '')
    #     stored_plugins = os.environ[plugin_env_var]

    #     if stored_plugins:
    #         stored_plugins += os.pathsep
    #     stored_plugins += plugin_file
    #     os.environ[plugin_env_var] = stored_plugins

    #     history = self.cache

    #     # Note: This method normally runs on init but because of other tests
    #     #       instantiating the HistoryCache, we just re-add our plugins
    #     #
    #     history.init_plugins()

    #     context = ways.api.get_context('2tt/whatever')
    #     self.assertNotEqual(context, None)
