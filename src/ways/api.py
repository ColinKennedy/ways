#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Expose common functionality.

This module's responsibility to maintain backwards- and forwards-compatibility
so that this package can be refactored without breaking any tools.

It's recommended to always import and use modules, here.

'''

# IMPORT LOCAL LIBRARIES
# High-use classes and functions
from .common import DESCRIPTORS_ENV_VAR
from .common import PLATFORM_ENV_VAR
from .common import PLATFORMS_ENV_VAR
from .common import PLUGINS_ENV_VAR
from .common import PRIORITY_ENV_VAR

from .plugin import Plugin

from .situation import Context
from .situation import get_context
from .situation import register_context_alias
from .situation import resolve_alias
from .situation import clear_aliases
from .situation import clear_contexts

from .resource import Asset
from .resource import get_asset
from .resource import register_asset_class
from .resource import reset_asset_classes

from .commander import Action
from .commander import add_action

# Lower-level debug functions
from .trace import trace_all_plugin_results
from .trace import trace_all_plugin_results_info
from .trace import trace_actions
from .trace import trace_action_names
from .trace import trace_actions_table
from .trace import trace_context
from .trace import trace_hierarchy

from .trace import get_all_hierarchies

# Classes and functions exposed for subclassing and extension
# These classes, functions, and constants are usually accessible in other,
# better ways but are exposed in case you want to use them
#
from .descriptor import FileDescriptor
from .descriptor import FolderDescriptor
from .descriptor import GitLocalDescriptor
from .descriptor import GitRemoteDescriptor
from .descriptor import PLUGIN_INFO_FILE_NAME
from .descriptor import serialize

from .parse import ContextParser

from .cache import add_descriptor

# TODO : rename Find class into "Finder"
from .finder import Find

from .resource import AssetFinder

from .finder_common import find_context


__all__ = [
    'DESCRIPTORS_ENV_VAR',
    'PLATFORM_ENV_VAR',
    'PLATFORMS_ENV_VAR',
    'PLUGINS_ENV_VAR',
    'PRIORITY_ENV_VAR',

    'Plugin',

    'Context',
    'get_context',
    'register_context_alias',
    'resolve_alias',

    'clear_aliases',
    'clear_contexts',

    'Asset',
    'get_asset',
    'register_asset_class',
    'reset_asset_classes',

    'Action',
    'add_action',

    'trace_all_plugin_results',
    'trace_all_plugin_results_info',
    'trace_actions',
    'trace_action_names',
    'trace_actions_table',
    'trace_context',
    'trace_hierarchy',

    'get_all_hierarchies',

    'FileDescriptor',
    'FolderDescriptor',
    'GitLocalDescriptor',
    'GitRemoteDescriptor',
    'PLUGIN_INFO_FILE_NAME',

    'serialize',

    'ContextParser',

    'add_descriptor',

    'Find',

    'AssetFinder',

    'find_context',
]
