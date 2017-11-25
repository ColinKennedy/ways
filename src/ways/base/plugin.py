#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module that holds Plugin classes - objects that combine into a Context.'''

# IMPORT STANDARD LIBRARIES
import uuid

# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT WAYS LIBRARIES
import ways

# IMPORT LOCAL LIBRARIES
from ..core import check
from ..helper import common


class PluginRegistry(type):

    '''A metaclass that adds newly-created Plugin objects to a cache.'''

    def __new__(mcs, clsname, bases, attrs):
        '''Add the created object to the HistoryCache.'''
        new_class = super(PluginRegistry, mcs).__new__(
            mcs, clsname, bases, attrs)

        # TODO : We still need to not be using 'Plugin' ...
        # If we explicitly state not to register a plugin, don't register it
        # If add_to_registry isn't defined for this Plugin,
        # assume that we should register it
        #
        try:
            if new_class.__name__ == 'Plugin' or not new_class.add_to_registry:
                return new_class
        except AttributeError:
            return new_class

        assignment = get_assignment(new_class)

        ways.add_plugin(new_class(), assignment)

        return new_class


# pylint: disable=too-few-public-methods
@six.add_metaclass(PluginRegistry)
class Plugin(object):

    '''An add-on that is later retrieved by Context to gather its data.'''

    add_to_registry = True
    _data = dict()

    @property
    def data(self):
        '''dict[str]: The display properties (like {'color': 'red'}).'''
        return self._data

    @data.setter
    def data(self, value):
        '''Set the data on this instance with whatever value is.

        Args:
            value (dict[str]): The new values for this instance.

        '''
        self._data = value


class DataPlugin(Plugin):

    '''An add-on that was made from a serialized file (JSON/YAML/etc).

    This class behaves exactly like a regular Plugin object and is stored
    in the same space as Plugin objects.

    DataPlugin does not add itself to the cache automatically. It is the
    responsibility of some other class/function to register it to Ways.

    We do this so that we can have better control over the DataPlugin's args
    and its assignment before it hits the cache.

    '''

    add_to_registry = False

    def __init__(self, sources, info, assignment):
        '''Create the object and set its sources.

        Args:
            sources (list[str]): The location(s) that defined this Plugin.
            info (dict[str]): The information that came from a JSON or YAML file
                              which sets the base settings of the object.
            assignment (str): The grouping location where this Plugin will go.
                              This assignment must be the same as the Context
                              that this Plugin is meant for.

        Raises:
            ValueError: If there are missing keys in data that this class needs.

        '''
        missing_required_keys = set(self._required_keys()) - set(info.keys())
        if missing_required_keys:
            raise ValueError('Info: "{info}" is missing keys, "{keys}".'
                             ''.format(info=info, keys=missing_required_keys))

        # Give this plugin a UUID if none was given, for us
        # Data is assumed to be a core.classes.dict_class.ReadOnlyDict so we
        # try to unlock it, here. If it's not a custom dict, just let it pass
        #
        try:
            is_settable = info.settable
            info.settable = True
        except AttributeError:
            pass

        info.setdefault('uuid', str(uuid.uuid4()))

        try:
            info.settable = is_settable
        except AttributeError:
            pass

        self._info = info
        self.sources = tuple(sources)
        self._data = self._info.get('data', dict())
        self.assignment = assignment

        super(DataPlugin, self).__init__()

    @classmethod
    def _required_keys(cls):
        '''tuple[str]: Keys that must be set in our Plugin.'''
        return ('hierarchy', )

    def is_path(self):
        '''bool or NoneType: If the mapping is a filepath or None if unsure.'''
        try:
            return self._info['path']
        except KeyError:
            return

    def get_assignment(self):
        '''str: Where this Plugin lives in Ways, along with its hierarchy.'''
        return self.assignment

    def get_groups(self):
        '''Get the groups that this Plugin evaluates onto.

        Note:
            The term 'groups' is not the same as the assignment of a Plugin.
            They are two different things.

        Returns:
            tuple[str]: The groups.

        '''
        value = check.force_itertype(self._info.get('groups', ('*', )), itertype=tuple)
        is_empty = not [val for val in value if val.strip()]
        if is_empty:
            value = ('*', )
        return value

    def get_hierarchy(self):
        '''tuple[str] or str: The location that this Plugin exists within.'''
        return self._info['hierarchy']

    def get_mapping(self):
        '''str: The physical location of this Plugin (on the filesystem).'''
        try:
            return self._info['mapping']
        except KeyError:
            return ''

    def get_mapping_details(self):
        '''dict[str]: Information about the mapping, if needed.'''
        return self._info.get('mapping_details', dict())

    def get_max_folder(self):
        '''str: The furthest location up that this plugin can navigate to.'''
        return self._info.get('max_folder', '')

    def get_platforms(self):
        '''tuple[str]: The platforms that this Plugin is allowed to run on.'''
        return self._info.get('platforms', ('*', ))

    def get_uses(self):
        '''tuple[str]: The Context hierarchies this instance depends on.'''
        return self._info.get('uses', tuple())

    def get_uuid(self):
        '''str: A unique ID for this plugin.'''
        return self._info.get('uuid', '')

    def __repr__(self):
        '''str: The information needed to reproduce this instance.'''
        return '{cls_}(sources={sources!r}, data={data})'.format(
            cls_=self.__class__.__name__,
            sources=self.sources,
            data=dict(self._info))


def get_assignment(obj):
    '''str: Get an object's assignment or fallback to ways.DEFAULT_ASSIGNMENT.'''
    try:
        return obj.get_assignment()
    except AttributeError:
        return common.DEFAULT_ASSIGNMENT
