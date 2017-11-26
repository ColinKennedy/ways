#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module that contains highly generic singleton classes.'''


class SingletonContainer(type):

    '''A singleton metaclass that can register multiple classes, at once.

    Note:
        Classes given to this registry must be valid dict keys (hashable).

    '''

    _instances = {}

    def __call__(cls, *args, **kwargs):
        '''When the class is invoked, register it in our instances.'''
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonContainer, cls).__call__(
                *args, **kwargs)
        return cls._instances[cls]
