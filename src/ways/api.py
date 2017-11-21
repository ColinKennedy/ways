#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Expose common functionality.

This module's responsibility to maintain backwards- and forwards-compatibility
so that this package can be refactored without breaking any tools.

It's recommended to always import and use modules, here.

'''

# IMPORT LOCAL LIBRARIES
from .base.cache import load_plugin
from .base.cache import init_plugins
from .base.cache import add_descriptor
from .base.cache import add_search_path
from .base.cache import get_all_plugins
# TODO : rename Find class into "Finder"
from .base.finder import Find
from .base.plugin import Plugin
# High-use classes and functions
from .helper.common import PLUGINS_ENV_VAR
from .helper.common import LOAD_FAILURE_KEY
from .helper.common import NOT_CALLABLE_KEY
from .helper.common import PLATFORM_ENV_VAR
from .helper.common import PRIORITY_ENV_VAR
from .helper.common import PLATFORMS_ENV_VAR
from .helper.common import DEFAULT_ASSIGNMENT
from .helper.common import IMPORT_FAILURE_KEY
from .helper.common import DESCRIPTORS_ENV_VAR
from .helper.common import RESOLUTION_FAILURE_KEY
from .helper.common import ENVIRONMENT_FAILURE_KEY
from .helper.common import decode
from .helper.common import encode
from .parsing.parse import ContextParser
# Lower-level debug functions
from .parsing.trace import trace_actions
from .parsing.trace import trace_context
from .parsing.trace import trace_hierarchy
from .parsing.trace import trace_assignment
from .parsing.trace import trace_action_names
from .parsing.trace import get_all_hierarchies
from .parsing.trace import trace_actions_table
from .parsing.trace import get_child_hierarchies
from .parsing.trace import get_action_hierarchies
from .parsing.trace import trace_all_load_results
from .parsing.trace import get_all_hierarchy_trees
from .parsing.trace import trace_method_resolution
from .parsing.trace import get_child_hierarchy_tree
from .parsing.trace import trace_all_plugin_results
from .parsing.trace import get_all_action_hierarchies
from .parsing.trace import trace_all_descriptor_results
from .base.commander import Action
from .base.commander import add_action
from .base.situation import Context
from .base.situation import get_context
from .base.situation import clear_aliases
from .base.situation import resolve_alias
from .base.situation import clear_contexts
from .base.situation import register_context_alias
# Classes and functions exposed for subclassing and extension
# These classes, functions, and constants are usually accessible in other,
# better ways but are exposed in case you want to use them
#
from .base.descriptor import PLUGIN_INFO_FILE_NAME
from .base.descriptor import FileDescriptor
from .base.descriptor import FolderDescriptor
from .base.descriptor import GitLocalDescriptor
from .base.descriptor import GitRemoteDescriptor
from .parsing.registry import get_asset_info
from .parsing.registry import get_asset_class
from .parsing.registry import reset_asset_classes
from .parsing.registry import register_asset_class
from .parsing.resource import Asset
from .parsing.resource import AssetFinder
from .parsing.resource import get_asset

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
    'register_asset_class',
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
