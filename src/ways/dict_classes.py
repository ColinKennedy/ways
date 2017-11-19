#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Extended dictionary classes.'''

# IMPORT STANDARD LIBRARIES
import collections


class ReadOnlyDict(collections.Mapping, object):

    '''A dictionary whose items can be set to read-only, if need be.'''

    def __init__(self, data=None, settable=False):
        '''Create the object and set it to read or write mode.

        Attributes:
            settable (bool): If the instance has write permissions.

        Args:
            data (:obj:`dict`, optional):
                The information to store. Default is an empty dict.
            settable (:obj:`bool`, optional):
                If True, this instance will be set to write mode. If False,
                it is set to read-only. Default is False.

        '''
        super(ReadOnlyDict, self).__init__()

        self._data = data
        self.settable = settable

    def setdefault(self, key, value):
        '''Add the key to this dictionary if it does not exist.

        Args:
            key: The key to set.
            value: The value to set on our key, if the key does not exist.

        '''
        if not key in self._data:
            self[key] = value

    def __getitem__(self, key):
        '''Get the item at some key.

        Args:
            key: The identifier to get the item of.

        Returns:
            The value of key.

        '''
        return self._data[key]

    def __iter__(self):
        '''tuple: The item pairs in this instance.'''
        return iter(self._data)

    def __len__(self):
        '''int: The number of items in this instance.'''
        return len(self._data)

    def __unsettable_error_message(self):
        '''Raise a message letting us know that we cannot set this class.'''
        raise RuntimeError('Object: "{obj!r}" is in read-only mode and '
                           'cannot be set.'.format(obj=self))

    def __setitem__(self, key, value):
        '''Set the key with item, if the dict is not not in read-only mode.

        Args:
            key: The key to set.
            value: The value to set key with.

        Raises:
            RuntimeError: If the instance is in read-only mode.

        '''
        if not self.settable:
            self.__unsettable_error_message()

        self._data[key] = value


def recursive_default_dict():
    '''Create a recursive collection.defaultdict(dict).'''
    return collections.defaultdict(recursive_default_dict)
