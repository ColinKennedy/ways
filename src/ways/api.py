#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Expose common functionality.

This module's responsibility to maintain backwards- and forwards-compatibility
so that this package can be refactored without breaking any tools.

It's recommended to always import and use modules, here.

'''

# IMPORT LOCAL LIBRARIES
from .cache import load_plugin
from .cache import init_plugins
from .cache import add_descriptor
from .cache import add_search_path
from .cache import get_all_plugins
from .parse import ContextParser
# Lower-level debug functions
from .trace import trace_actions
from .trace import trace_context
from .trace import trace_hierarchy
from .trace import trace_assignment
from .trace import trace_action_names
from .trace import get_all_hierarchies
from .trace import trace_actions_table
from .trace import get_child_hierarchies
from .trace import get_action_hierarchies
from .trace import get_all_hierarchy_trees
from .trace import trace_all_load_results
from .trace import trace_method_resolution
from .trace import get_child_hierarchy_tree
from .trace import trace_all_plugin_results
from .trace import get_all_action_hierarchies
from .trace import trace_all_descriptor_results
# High-use classes and functions
from .common import decode
from .common import encode
from .common import PLUGINS_ENV_VAR
from .common import LOAD_FAILURE_KEY
from .common import NOT_CALLABLE_KEY
from .common import PLATFORM_ENV_VAR
from .common import PRIORITY_ENV_VAR
from .common import PLATFORMS_ENV_VAR
from .common import DEFAULT_ASSIGNMENT
from .common import IMPORT_FAILURE_KEY
from .common import DESCRIPTORS_ENV_VAR
from .common import RESOLUTION_FAILURE_KEY
from .common import ENVIRONMENT_FAILURE_KEY
# TODO : rename Find class into "Finder"
from .finder import Find
from .plugin import Plugin
from .resource import Asset
from .resource import AssetFinder
from .resource import get_asset
from .resource import get_asset_info
from .resource import get_asset_class
from .resource import register_asset_info
from .resource import reset_asset_classes
from .commander import Action
from .commander import add_action
from .situation import Context
from .situation import get_context
from .situation import clear_aliases
from .situation import resolve_alias
from .situation import clear_contexts
from .situation import register_context_alias
# Classes and functions exposed for subclassing and extension
# These classes, functions, and constants are usually accessible in other,
# better ways but are exposed in case you want to use them
#
from .descriptor import PLUGIN_INFO_FILE_NAME
from .descriptor import FileDescriptor
from .descriptor import FolderDescriptor
from .descriptor import GitLocalDescriptor
from .descriptor import GitRemoteDescriptor

add_action_default = Find.add_to_defaults  # pylint: disable=invalid-name

__all__ = [
    'decode',
    'encode',

    'DESCRIPTORS_ENV_VAR',
    'PLATFORM_ENV_VAR',
    'PLATFORMS_ENV_VAR',
    'PLUGINS_ENV_VAR',
    'PRIORITY_ENV_VAR',

    'ENVIRONMENT_FAILURE_KEY',
    'IMPORT_FAILURE_KEY',
    'LOAD_FAILURE_KEY',
    'NOT_CALLABLE_KEY',

    'RESOLUTION_FAILURE_KEY',

    'DEFAULT_ASSIGNMENT',

    'Plugin',

    'Context',
    'get_context',
    'register_context_alias',
    'resolve_alias',

    'clear_aliases',
    'clear_contexts',

    'Asset',
    'get_asset',
    'get_asset_class',
    'get_asset_info',
    'register_asset_info',
    'reset_asset_classes',

    'Action',
    'add_action',

    'trace_all_load_results',

    'trace_actions',
    'trace_action_names',
    'trace_method_resolution',

    'trace_actions_table',
    'trace_assignment',
    'trace_context',
    'trace_hierarchy',

    'get_action_hierarchies',
    'get_all_action_hierarchies',

    'get_all_hierarchies',
    'get_child_hierarchies',
    'get_child_hierarchy_tree',
    'get_all_hierarchy_trees',

    'FileDescriptor',
    'FolderDescriptor',
    'GitLocalDescriptor',
    'GitRemoteDescriptor',
    'PLUGIN_INFO_FILE_NAME',

    'ContextParser',

    'add_descriptor',
    'add_search_path',
    'load_plugin',
    'get_all_plugins',
    'init_plugins',

    'Find',
    'add_action_default',

    'AssetFinder',
]
