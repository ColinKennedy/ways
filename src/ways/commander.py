#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''This module adds to a Context object interface using Action objects.

Action objects attach to Contexts and let you change data on the Context or
to run other functions.

'''

# scspell-id: 3c62e4aa-c280-11e7-be2b-382c4ac59cfd
# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT LOCAL LIBRARIES
from . import cache
from . import common
from . import situation as sit


class ActionRegistry(type):

    '''A metaclass that adds new Action objects to a registry-cache.'''

    def __new__(mcs, clsname, bases, attrs):
        '''Add the created class to the Action object cache.'''
        new_class = super(ActionRegistry, mcs).__new__(
            mcs, clsname, bases, attrs)

        # If we state not to register a plugin, don't register it
        #
        # If add_to_registry isn't defined for this Plugin,
        # assume that we should register it
        #
        try:
            if new_class.__name__ == '_Aktion' or not new_class.add_to_registry:
                return new_class
        except AttributeError:
            return new_class

        # Register the Plugin into our registry
        try:
            assignment = new_class.get_assignment()
        except AttributeError:
            assignment = common.DEFAULT_ASSIGNMENT

        cache.add_action(new_class(), assignment=assignment)

        return new_class


# TODO : See if I can combine the ActionRegistry with an abstract class
#        that forces users to implement get_hierarchy and __call__
#
@six.add_metaclass(ActionRegistry)
class _Aktion(object):

    '''A base Action object that is meant to attach Context objects.

    To use this class, you must implement get_hierarchy as a classmethod
    and the __call__ method.

    '''

    add_to_registry = True

    @property
    def context(self):
        '''Get a reference to the Context that this instance is attached to.

        Note:
            This is done in a wrapped property for 3 reasons.
            1. So that the returned Context can be changed at runtime.
            2. To make the property read-only
            3. If the Context isn't defined by the time this object
               is instantiated, self.context would return None. By adding it as
               a wrapped property, we try to avoid loading the context for as
               long as possible. The Context is only needed when the Action
               is called. Ghetto? Yes. Works well? You bet it does!

        Returns:
            <ways.api.Context>:
                The object that this instance will attach itself to.

        '''
        return sit.get_context(
            self.get_hierarchy(), assignment=self.get_assignment())

    @classmethod
    def get_assignment(cls):
        '''str: The group where the Context for this instance lives.'''
        return common.DEFAULT_ASSIGNMENT

    @classmethod
    def get_hierarchy(cls):
        '''tuple[str]: The location of the Context/Asset this object affects.'''
        return tuple()


Action = _Aktion


def add_action(action, name='', hierarchy='', assignment=common.DEFAULT_ASSIGNMENT):
    '''Add a created action to this cache.

    Args:
        action (<ways.api.Action>):
            The action to add. Action objects are objects that get passed
            a Context object and run a function.
        name (:obj:`str`, optional):
            A name to use with this action. The name must be unique
            to this hierarchy/assignment or it risks overriding another
            Action that might already exist at the same location.
            If no name is given, the name on the action is tried, instead.
            Default: ''.
        assignment (:obj:`str`, optional): The group to add this action to,
                                            Default: 'master'.

    Raises:
        RuntimeError: If no hierarchy is given and no hierarchy could be
                        found on the given action.
        RuntimeError: If no name is given and no name could be found
                        on the given action.

    '''
    return cache.add_action(
        action=action, name=name, hierarchy=hierarchy, assignment=assignment)
