#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''The purpose of this module is to extend Context objects to be more useful.

Currently, you can use Action objects to interface with a Context and add
extra behavior that would otherwise be impossible.

'''

# IMPORT THIRD-PARTY LIBRARIES
import six

# IMPORT LOCAL LIBRARIES
from . import situation as sit
from . import common
from . import cache


class ActionRegistry(type):

    '''A meteclass registrar that adds new Action objects to a cache.'''

    def __new__(mcs, clsname, bases, attrs):
        '''Add the created class to the Action object cache.'''
        new_class = super(ActionRegistry, mcs).__new__(
            mcs, clsname, bases, attrs)

        # If we explicitly state not to register a plugin, don't register it
        # If add_to_registry isn't defined for this Plugin,
        # assume that we should register it
        #
        try:
            if new_class.__name__ == '_Aktion' or not new_class.add_to_registry:
                return new_class
        except AttributeError:
            return new_class

        # Hold a reference to the plugin registry in each plugin instance
        history_cache = cache.HistoryCache()
        # Register the Plugin into our registry
        try:
            assignment = new_class.get_assignment()
        except AttributeError:
            assignment = common.DEFAULT_ASSIGNMENT

        history_cache.add_action(new_class(), assignment=assignment)

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

    def __init__(self):
        '''Initialize the object and do nothing else.'''
        super(_Aktion, self).__init__()

    @property
    def context(self):
        '''Get a reference to the Context that this instance is attached to.

        Note:
            This is done in a wrapped property for 3 reasons.
            1. So that the returned Context can be made dynamic, assuming
               self.get_hierarchy() or self.get_assignment() needed to change
               at runtime.
            2. To make the property read-only
            3. If the Context isn't defined by the time this object
               is instantiated, self.context would return None. By adding it as
               a wrapped property, we defer the evaluation of context for as
               long as possible, to give Context a chance to be defined.
               Ghetto? Yes. Works well? You bet it does!

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


Action = _Aktion


def add_action(action, name='', hierarchy='', assignment=common.DEFAULT_ASSIGNMENT):
    '''Add a created action to this cache.

    Args:
        action (<ways.api.Action>):
            The action to add. Action objects are objects that act
            upon Context objects to gather some kind of information.
        name (:obj:`str`, optional):
            A name to associate with this action. The name must be unique
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
    history = cache.HistoryCache()
    return history.add_action(
        action=action, name=name, hierarchy=hierarchy, assignment=assignment)


if __name__ == '__main__':
    print(__doc__)

