#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Python 2/3 compatibility classes and functions.

Yes, import six is awesome. This just covers whatever six doesn't.

'''

# IMPORT STANDARD LIBRARIES
import types
import inspect

# IMPORT THIRD-PARTY LIBRARIES
import six


class DirMixIn(object):  # pylint: disable=too-few-public-methods

    ''''Mix-in to make implementing __dir__ method in subclasses simpler.

    In Python 2, you can't call super() in __dir__. This mixin lets you do it.

    Example:
        >>> class Something(object):
        >>>     def __dir__(self):
        >>>         return super(Something, self).__dir__()

        >>> print(dir(Something()))  # Raises AttributeError

        >>> class Something(DirMixIn, object):
        >>>     def __dir__(self):
        >>>         return super(Something, self).__dir__()

        >>> print(dir(Something()))  # Works

    That's all there is to it.

    '''

    def __dir__(self):
        '''Re-implement Python's __dir__ method, for Python 2.

        In Python 3, which actually has support for super().__dir__(), just
        return the super's result.

        Returns:
            list[str]: The __dir__ of this object or class.

        '''
        if six.PY3:
            return super(DirMixIn, self).__dir__()

        # Reference:
        # http://www.quora.com/How-dir-is-implemented-Is-there-any-PEP-related-to-that
        #
        def get_attrs(obj):
            '''list[str]: The attributes on the class + its base classes.'''
            try:
                dict_types = (dict, types.DictProxyType)
            except AttributeError:
                # Python 3.x
                dict_types = dict

            if not hasattr(obj, '__dict__'):
                return []  # slots only
            if not isinstance(obj.__dict__, dict_types):
                raise TypeError("%s.__dict__ is not a dictionary"
                                "" % obj.__name__)

            attrs = set()
            for cls_ in inspect.getmro(obj):
                attrs.update(cls_.__dict__.keys())

            return attrs

        def dir2(obj):
            '''Try to get the object's class and return its attributes.'''
            try:
                obj = obj.__class__
            except AttributeError:
                pass

            return sorted(get_attrs(obj))

        return dir2(self)
