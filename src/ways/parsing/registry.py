#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''Responsible for giving users the ability to swap Assets with other objects.

Attributes:
    ASSET_FACTORY (dict[tuple[str]: dict[str]]:
        This dict should not be changed directly. You should use
        the functions in this module, instead.

        It is a global dictionary that stores classes that are meant to swap
        for an Asset object. ASSET_FACTORY's key is the hierarchy of the Context
        and its value is another dict, which looks like this:

        'class': The class to swap for.
        'init': A custom inititialization function for the class (if needed).
        'children': If True, the class is used for all hierarchies that build
        off of the given hierarchy. If False, the class is only added to the
        given hierarchy.

'''

# IMPORT STANDARD LIBRARIES
import functools

# IMPORT STANDARD LIBRARIES
from ..base import situation as sit

ASSET_FACTORY = dict()


def get_asset_class(hierarchy):
    '''Get the class that is registered for a Context hierarchy.'''
    return get_asset_info(hierarchy)[0]


def get_asset_info(hierarchy):
    '''Get the class and initialization function for a Context hierarchy.

    Args:
        hierarchy (tuple[str] or str):
            The hierarchy to get the asset information of.

    Returns:
        tuple[classobj, callable]:
            The class type and the function that is used to instantiate it.

    '''
    class_type = None
    init = None

    # Try to find a class type from one of our parent hierarchies
    for index in reversed(range(len(hierarchy) + 1)):
        hierarchy_piece = tuple(hierarchy[:index])

        hierarchy_info = ASSET_FACTORY.get(hierarchy_piece, dict())

        try:
            class_type_ = ASSET_FACTORY[hierarchy_piece]['class']
            init_ = ASSET_FACTORY[hierarchy_piece]['init']
        except KeyError:
            continue

        if hierarchy_piece == hierarchy or hierarchy_info.get('children', False):
            class_type = class_type_
            init = init_
            break

    if class_type is None:
        return (None, None)

    return (class_type, init)


def register_asset_class(class_type, context, init=None, children=False):
    '''Change get_asset to return a different class, instead of an Asset.

    The Asset class is useful but it may be too basic for some people's purposes.
    If you have an existing class that you'd like to use with Ways,

    Args:
        class_type (classobj):
            The new class to use, instead.
            context (str or :class:`ways.api.Context`):
            The Context to apply our new class to.
        init (:obj:`callable`, optional):
            A function that will be used to create an instance of class_type.
            This variable is useful if you need to customize your class_type's
            __init__ in a way that isn't normal (A common example: If you want
            to create a class_type that does not pass context into its __init__,
            you can use this variable to catch and handle that).
        children (:obj:`bool`, optional):
            If True, this new class_type will be applied to child hierarchies
            as well as the given Context's hierarchy. If False, it will only be
            applied for this Context. Default is False.

    '''
    if init is None:
        init = make_default_init(class_type)

    context = sit.get_context(context, force=True)

    ASSET_FACTORY[context.get_hierarchy()] = dict()
    ASSET_FACTORY[context.get_hierarchy()]['class'] = class_type
    ASSET_FACTORY[context.get_hierarchy()]['init'] = init
    ASSET_FACTORY[context.get_hierarchy()]['children'] = children


def make_default_init(class_type, *args, **kwargs):
    '''Just make the class type, normally.'''
    return functools.partial(class_type, *args, **kwargs)


def reset_asset_classes(hierarchies=tuple()):
    '''Clear out the class(es) that is registered under a given hierarchy.

    Args:
        hierarchies (iter[tuple[str]]):
            All of the hierarchies to remove custom Asset classes for.
            If nothing is given, all hierarchies will be cleared.

    '''
    if not hierarchies:
        hierarchies = ASSET_FACTORY.keys()

    for key in hierarchies:
        if key not in ASSET_FACTORY:
            continue

        # Reset the key
        ASSET_FACTORY[key] = ASSET_FACTORY[key].__class__()
