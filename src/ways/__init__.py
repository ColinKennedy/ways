#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import collections


__version__ = "0.1.0b1"


ACTION_CACHE = collections.OrderedDict()
PLUGIN_CACHE = collections.OrderedDict()
PLUGIN_CACHE['hierarchy'] = collections.OrderedDict()
PLUGIN_CACHE['all_plugins'] = []


# IMPORT LOCAL LIBRARIES
# TODO : ugh this import is bad. FIXME
#        It's only used so that we can clear our Context instances
#        Find a better way to do this. Maybe store the instances here, too?
#
from . import situation as sit


def add_plugin(plugin, assignment='master'):
    # Set defaults (if needed)
    hierarchy = plugin.get_hierarchy()

    PLUGIN_CACHE['hierarchy'].setdefault(hierarchy, collections.OrderedDict())
    PLUGIN_CACHE['hierarchy'][hierarchy].setdefault(assignment, [])

    # Add the plugin if it doesn't already exist
    all_plugins = PLUGIN_CACHE['all_plugins']
    if plugin not in all_plugins:
        PLUGIN_CACHE['hierarchy'][plugin.get_hierarchy()][assignment].append(plugin)
        all_plugins.append(plugin)


def clear():
    ACTION_CACHE.clear()
    PLUGIN_CACHE.clear()
    PLUGIN_CACHE['hierarchy'] = collections.OrderedDict()
    PLUGIN_CACHE['all_plugins'] = []
    sit.clear_aliases()
    sit.clear_contexts()


if __name__ == '__main__':
    print(__doc__)

