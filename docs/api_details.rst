API Details
===========

The first thing to know about Ways is that it is not a tool, it is a toolkit.
Ways is not immediately useful. You, the user, make Ways useful for your
pipeline.

If you haven't already, please read the :doc:`summary` page on each of the
main ideas that Ways uses. This document will expand on ideas written there.


Contexts
--------

If you go to :class:`ways.base.situation.Context`, you can read more about the class.

Context objects have

1. a hierarchy
2. a data property which is similar to a ChainMap
3. an actions property which can be used to extend a Context's interface

The Context object is the most important class in Ways because it encompasses
two critical functions.

1. The Context is basically a "hierarchy interface". Everything that Ways
   builds is based on hierarchies that the user has full control over.
   Hierarchies each have their own actions, data, and order of importance and
   the Context lets us write functions around them.
2. The data that a Context uses is loaded exactly when it is queried. This
   means that we can load some plugins, create a Context object, add another
   plugin, and the Context picks up that new data without you doing anything.

Once you've read through the Context object, read :func:`ways.api.get_context`.
You should become familiar with the Flyweight design pattern
(http://sourcemaking.com/design_patterns/flyweight) because that's also an
important part about how Ways creates Context objects.


Plugins
-------

In the :mod:`ways.base.plugin` file, you'll find a couple very basic classes.

Context objects are built out of plugins. There's not much to say about plugins
other than that they wrap around a dict that the user loads.

Two documents that cover all the different Plugin Sheet keyes
are :doc:`plugin_basics` and :doc:`plugin_advanced`.

At this point, it's a good idea to re-read each of Context object's methods
and how those relate to the different plugin keys.


Ways Cache
----------

Now that you understand Context objects, it's important to know how they are
loaded. In the :mod:`ways.base.cache` file, you'll find the functions that are
used to register Contexts and plugins, which we've talked about already, and also
register Descriptors and Actions, which we haven't been explained yet.

When Ways first is imported and used, it gathers plugins that it can see in
the WAYS_PLUGINS and WAYS_DESCRIPTOR environment variables. Once you're
actually in Python, it's best to just use Python functions to add additional
objects.

If you absolutely need to add paths to those environment variables, first ask
yourself why you think you need to. If you still think its necessary, add the
paths with os.environ and the run :func:`ways.api.init_plugins`.

.. warning ::

    This function **will** remove any objects that were added using Python so
    it's not recommended to use. But you can do it.


Descriptors
-----------

Read through :doc:`descriptors` to get the jist about how Descriptor
objects are built as a user. There's not much to say about them other than
they're classes used to load Plugin Sheets. That way, you can load
plugins into Ways from disk, a database, or whatever other method you'd like.

Other than that, they are not special in any way. Everything related to
Descriptors is found in the :mod:`ways.base.descriptor` file. To see how
they're loaded, revisit :mod:`ways.base.cache`.

In particular, two things in cache.py are interesting to maintainers.

1. add_search_path is just an alias to add_descriptor. The user can add plugins
   just by giving a filepath or folder and the Descriptor object needed will be
   built for them. Most of the time, that's all anyone need while using Ways.
2. add_descriptor and add_plugin both try their best to catch errors before
   they happen so the user can review any Descriptor or plugins that didn't
   load. For more information on that, check out :doc:`troubleshooting`.


Actions
-------

Many pages talk about Actions. It's mentioned in :doc:`summary`,
:doc:`why`, :doc:`common_patterns` and even has its own section in
:doc:`troubleshooting`. There's not much point in repeating what has already
been said so lets talk just about how Ways actually exposes Actions to the
user.

When an Action is registered to Ways (using :func:`ways.base.cache.add_action`),
the user specifies a hierarchy for the Action and a name to call it.

This is kept in a dictionary in :class:`ways.ACTION_CACHE`.

When the user calls an action using :class:`ways.api.Context.actions`,
the following happens:

1. Ways looks up to see if that Action/Context has a definition for that
   Action. If there's no definition, look for a default value. If neither,
   raise an AttributeError.
2. If an Action is found, the function is wrapped using funtools.partial. The
   partial function adds the Context/Asset that called it as the first arg.

::

    context = ways.api.get_context('something')
    context.actions.some_action_name()

So by using functools.partial, we eliminate the need for the user to write

::

    context.actions.some_action_name(context)


Any class that inherits from :class:`ways.api.Action` is automatically registered to
Ways, because the :class:`ways.parsing.resource.ActionRegistry` metaclass registers
the class once it's defined.


Assets
------

The Asset object is a simple wrapper around a Context object. Nearly all of its
methods are used for getting data that the user has provided.

All classes and functions are located in the :mod:`ways.parsing.resource` file.

There are a couple functions in particular that are interesting to developers.
The first is :func:`ways.parsing.resource._get_value`. If a user queries a part
of an Asset that exists, the value is returned. But if the value doesn't exist,
Ways is still able to "build" the value based on surrounding information. For the
sake of making it easier to search for, the two methods are called
"Parent-Search" and "Child-Search". All of the functions related to those
search methods are either scoped functions in :func:`ways.parsing.resource._get_value`
or somewhere within :mod:`ways.parsing.resource`.

The other function that's very important is
:func:`ways.parsing.resource._find_context_using_info`.

Basically, if a user tries to run :func:`ways.api.get_asset` without giving a context,
this function will try to "find" a matching Context to use instead. At the risk
of reiterating the same information twice, read through
:func:`ways.parsing.resource._find_context_using_info` and func:`ways.api.get_asset`
docstrings. Both functions go in detail about the common pitfalls of auto-finding Contexts.


api.py
------

This module is where almost every function or class meant to be used by
developers is put. There's nothing really special about it, just know that it's
there and exists for the user's convenience.
