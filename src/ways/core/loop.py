#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''For-loop helper methods.'''

# IMPORT THIRD-PARTY LIBRARIES
import six


def last_iter(iterable):
    '''Wrap a loop to determine when the last value of a loop is found.

    Reference:
        https://stackoverflow.com/questions/1630320

    Args:
        iterable (iterable): The objects to move through

    '''
    # Get an iterator and pull the first value.

    iterobj = iter(iterable)
    last = next(iterobj)
    # Run the iterator to exhaustion (starting from the second value).

    for val in iterobj:
        # Report the *previous* value (more to come).
        yield False, last
        last = val
    # Report the last value.
    yield True, last


def walk_items(obj):
    '''Iterate and yield parts of an object.

    Example:
        >>> foo = ('fee', 'fi', 'fo', 'fum')
        >>> print(list(walk_items(foo)))
        >>> # Result: [('foo', ), ('foo', 'fi'), ('foo', 'fi', 'fo'),
        >>> #          ('fee', 'fi', 'fo', 'fum')]

    Note:
        This function requires the object use __len__, and __getitem__.

    Args:
        obj (iterable): Some object to return the parts of.

    Yields:
        Parts of the object.

    '''
    for index in six.moves.range(1, len(obj) + 1):
        yield obj[:index]
