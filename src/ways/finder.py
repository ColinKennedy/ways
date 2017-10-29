#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import collections
import functools
import itertools
import sys

# IMPORT LOCAL LIBRARIES
from . import finder_common
from .core import compat
from . import common
from . import trace


# TODO : In general, I regret the name of this module. FIXME


class Find(compat.DirMixIn, object):

    '''A wrapper around a Context object that provides some basic syntax-sugar.

    The syntax of using Context objects is clunky. This class is meant to help.
    See the second and last example, for details.

    Example:
        >>> context = Context('/some/context')
        >>> command = context.get_action('get_assets')
        >>> command()
        >>> # ['/some/asset1.tif', '/some/asset2.tif', '/some/asset2.tif']

    Example:
        >>> # If an action is meant to return back an iterable object and the
        >>> # action that it gets back is None, that can cause immediate problems
        >>> #
        >>> context = Context('/some/context')
        >>> command = context.get_action('get_assets')  # Returns None
        >>> for asset in command():
        >>>     print(asset)
        >>> # The above code will TypeError error if get_action returns None

    Example:
        >>> # The best you can do is this
        >>> context = Context('/some/context')
        >>> command = context.get_action('get_assets') or lambda: []
        >>> for asset in command():
        >>>     print(asset)
        >>> # The above code will not error but it's pretty verbose compared to
        >>> # what we're actually trying to accomplish.

    Example:
        >>> # Here is (IMO) the best solution
        >>> context = Context('/some/context')
        >>> find = finder.Find(context)
        >>> # Returns [] even if get_assets isn't defined
        >>> # because get_assets is listed in Finder(context).defaults
        >>> #
        >>> for asset in find.get_assets():
        >>>     print(asset)

    '''

    _default_key_name = 'default'
    _default_key = (_default_key_name, )
    defaults = collections.defaultdict()
    defaults[_default_key] = dict()

    def __init__(self, context):
        '''Create this object and store the given Context.

        Args:
            context (<ways.api.Context>): The Context to wrap.

        '''
        super(Find, self).__init__()
        self.context = context

    @classmethod
    def add_to_defaults(cls, name, value, hierarchy=None):
        '''Add default value if an Action name is missing.

        Args:
            name (str):
                The name of the Action to add a default value for.
            value:
                The object to add as the default return value for a missing Action.
            hierarchy (:obj:`tuple[str] or str`, optional):
                The location to put these default values.
                If no hierarchy is given, ('default', ) is used, instead.

        '''
        if hierarchy is None:
            hierarchy = cls._default_key_name

        hierarchy = common.split_by_comma(hierarchy)

        cls.defaults[hierarchy][name] = value

    def __getattr__(self, name):
        '''Try to pass missing calls from Finder to the stored Context's actions.

        If the action is missing in Context, try to return a default value
        for the action. If no default is found, just return None like normal.

        '''
        def return_value(arg, *args, **kwargs):
            '''Just return the vaue of the original function.'''
            return arg

        return_none = functools.partial(return_value, None)

        command = self.context.get_action(name)
        if command is None:
            try:
                context_dict = self.defaults[self.context.get_hierarchy()]
            except KeyError:
                message = "AttributeError: '{obj}' has no attribute '{attr}'" \
                          "".format(obj=self.__class__.__name__, attr=name)
                raise AttributeError(message)

            try:
                return functools.partial(return_value, context_dict[name])
            except KeyError:
                return return_none

        return command

    def __dir__(self):
        '''list[str]: Add Action names to the list of return items.'''
        return sorted(
            set(itertools.chain(super(Find, self).__dir__(),
                                self.__dict__.keys(),
                                trace.trace_action_names(self.context))))


find_context = finder_common.find_context


# TODO : Move somewhere more core
def decorate_all_functions(function_decorator):
    '''Make a function decorator into a class decorator.

    This result (a new class decorator) will be applied to all of the
    methods in the decorated class.

    Reference:
        https://stackoverflow.com/questions/25828864

    Args:
        function_decorator: The function(s) of the class to decorate.

    Returns:
        callable: A new function that's been wrapped with function_decorator.

    '''
    def decorator(cls):
        '''Decorate functions with a function that calls function_decorator.'''
        for name, obj in vars(cls).items():
            if callable(obj):
                try:
                    obj = obj.__func__  # unwrap Python 2 unbound method
                except AttributeError:
                    pass  # not needed in Python 3
                setattr(cls, name, function_decorator(obj))
        return cls
    return decorator


if __name__ == '__main__':
    print(__doc__)

