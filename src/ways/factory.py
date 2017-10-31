#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''The main class that is used to create and store Context instances.

This setup is what makes ways.api.Context objects into flyweight objects.

TODO:
    Remove this class. It could just be a list with functions.

'''

# IMPORT STANDARD LIBRARIES
import collections

# IMPOR WAYS LIBRARIES
import ways

# IMPORT LOCAL LIBRARIES
from . import common


class _AssignmentFactory(object):

    '''A Flyweight factory used to create and hold onto Context instances.'''

    def __init__(self, class_type):
        '''Create the factory that registers a specific class type of object.

        Args:
            class_type (classobj): The class to instantiate with this factory.

        '''
        super(_AssignmentFactory, self).__init__()
        self._class_type = class_type
        self._instances = collections.defaultdict(dict)

    def get_instance(self, hierarchy, assignment, force=False):
        '''Get an instance of our class if it exists and make it if does not.

        Args:
            hierarchy (tuple[str] or str):
                The position where all the plugins for our instance would live.
            assignment (str): The category/grouping of the instance.
            force (:obj:`bool`, optional):
                If False and the Context has no plugins, return None.
                If True, return the empty Context. Default is False.

        Returns:
            class_type or NoneType:
                An instance of our stored class. If the Context that is
                queried doesn't have any Plugin objects defined for it, it's
                considered 'empty'. To avoid faults in our code,
                we return None, in this case.

        '''
        if isinstance(hierarchy, self._class_type):
            # A Context object was passed, by mistake. Just return it
            return hierarchy

        # Get our instance, if there is one
        try:
            return self._instances[hierarchy][assignment]
        except KeyError:
            pass

        # Make our instance
        return self._make_and_store_new_instance(hierarchy, assignment, force=force)

    def _make_and_store_new_instance(self, hierarchy, assignment, force=False):
        '''Create and store our new class instance.

        Args:
            hierarchy (tuple[str] or str):
                The position where all the plugins for our instance would live.
            assignment (str):
                The priority mapping for this instance's plugins.
            force (:obj:`bool`, optional):
                If False and the Context has no plugins, return None.
                If True, return the empty Context. Default is False.

        Returns:
            A new instance of our class type.

        '''
        def make_and_store_instance(hierarchy, assignment):
            '''A syntax-sugar method that makes the instance and caches it.'''
            instance = self._class_type(hierarchy, assignment=assignment)
            self._instances[hierarchy][assignment] = instance
            return instance

        hierarchy = common.split_hierarchy(hierarchy)
        # If no plugins were defined or if the plugins are specifically stated
        # as "not findable" (like an incomplete Context Plugin)
        # we return None to avoid making an undefined Context
        #
        try:
            if not ways.PLUGIN_CACHE['hierarchy'][hierarchy][assignment]:
                raise KeyError
        except KeyError:
            # Is the user specified a null assignment (aka they want all plugins
            # from every assignment) and there are plugins, just pass it through
            #
            is_forcible = (not assignment and ways.PLUGIN_CACHE['hierarchy'].get(hierarchy))

            if force or is_forcible:
                # Register the context, even though it doesn't have plugins
                return make_and_store_instance(hierarchy, assignment)

            # Return nothing, no Plugin objects were found so no Context
            # will be built
            #
            return

        plugins = []

        # Add any Context objects that these plugins depend on
        hierarchies = []
        for plugin in ways.PLUGIN_CACHE['hierarchy'][hierarchy][assignment]:
            try:
                used = plugin.get_uses()
            except AttributeError:
                used = []
            hierarchies.extend(used)

        for uses in hierarchies:
            plugins.append(
                self.get_instance(uses, assignment=assignment, force=True))

        for plugin in ways.PLUGIN_CACHE['hierarchy'][hierarchy][assignment]:
            try:
                if plugin.is_findable():
                    plugins.append(plugin)
            except AttributeError:
                # If the plugin doesn't say whether it is findable, just assume
                # that the information was just omitted and that it is findable
                #
                plugins.append(plugin)

        if not force and not plugins:
            return

        return make_and_store_instance(hierarchy, assignment)

    def clear(self):
        '''Remove every Context instance that this object knows about.

        If a Context is re-queried after this method is run, a new instance
        for the Context will be created and returned.

        Running this method is not recommended because it messes with the
        internals of Ways.

        '''
        self._instances.clear()


class AliasAssignmentFactory(_AssignmentFactory):

    '''Extend the _AssignmentFactory object to include Context aliases.'''

    def __init__(self, class_type):
        '''Create this object and our empty alias dictionary.

        Args:
            class_type (classobj): The class to instantiate with this factory.

        '''
        super(AliasAssignmentFactory, self).__init__(class_type=class_type)
        self.aliases = dict()

    def is_aliased(self, hierarchy):
        '''bool: If this hierarchy is an alias for another hierarchy.'''
        return hierarchy in self.aliases and self.aliases.get(hierarchy) != hierarchy

    def resolve_alias(self, hierarchy):
        '''Assuming that the given hierarchy is an alias, follow the alias.

        Args:
            hierarchy (tuple[str] or str):
                The location to look for our instance. In this method,
                hierarchy is expectex to be an alias for another hierarchy
                so we look for the real hierarchy, here.

        Returns:
            tuple[str]:
                The base hierarchy that this alias is meant to represent.

        '''
        current = tuple()

        while current != hierarchy:
            # On the first run, current will be empty so we just assign it
            # to hierarchy straightaway - so that the try/except will start
            #
            if current == tuple():
                current = hierarchy

            # Keep following the aliases until we get to the real hierachy
            try:
                current = self.aliases[current]
            except KeyError:
                break

        resolved_hierarchy = common.split_hierarchy(current)
        return resolved_hierarchy

    def get_instance(self, hierarchy, assignment, follow_alias=False, force=False):
        '''Get an instance of our class if it exists and make it if does not.

        Args:
            hierarchy (tuple[str] or str):
                The location to look for our instance.
            assignment (str):
                The category/grouping of the instance.
            follow_alias (:obj:`bool`, optional):
                If True, the instance's hierarchy is assumed to be an alias
                for another hierarchy and the returned instance will use
                the "real" hierachy. If False, the instance will stay as
                the aliased hierarchy, completely unmodified.
                Default is False.
            force (:obj:`bool`, optional):
                If False and the Context has no plugins, return None.
                If True, an empty Context is returned. Default is False.

        Returns:
            self._class_type() or NoneType:
                An instance of our preferred class. If the Context that is
                queried doesn't have any Plugin objects defined for it, it's
                considered 'empty'. To avoid faults in our code,
                we return None, by default.

        '''
        if isinstance(hierarchy, self._class_type):
            # A Context object was passed, by mistake. Just return it again
            return hierarchy

        hierarchy = common.split_hierarchy(hierarchy)

        instance = super(AliasAssignmentFactory, self).get_instance(
            hierarchy=hierarchy, assignment=assignment, force=force)

        if not self.is_aliased(hierarchy):
            return instance

        resolved_hierarchy = self.resolve_alias(hierarchy)

        if not follow_alias:
            return instance

        # Follow the alias to get a Context with the 'real' hierarchy
        return super(AliasAssignmentFactory, self).get_instance(
            hierarchy=resolved_hierarchy, assignment=assignment, force=force)

    def clear(self):
        '''Remove all the stored aliases in this instance.'''
        super(AliasAssignmentFactory, self).clear()
        self.aliases = dict()
