Contributors Guide
==================

API Details
-----------

The first thing to know about Ways is that it is not a tool, it is a toolkit.
Ways is not immediately useful. You, the user, make Ways useful for your
pipeline.

If you haven't already, please read the :doc:`summary` page on each of the
main ideas that Ways uses. This document will expand on ideas written there.


Contexts
++++++++

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
2. The data that a Context is loaded exactly at the moment it is queried. This
   means that we can load some plugins, create a Context object, add another
   plugin, and the Context picks up that new data without you doing anything.

Once you've read through the Context object, read "get_context".
You should become familiar with the Flyweight design pattern
(http://sourcemaking.com/design_patterns/flyweight) because that's also an
important part about how Ways creates Context objects.


Plugins
+++++++

In the :mod:`ways.base.plugin` file, you'll find a couple very basic classes
for plugins.

Context objects are built out of plugins. There's not much to say about plugins
other than they're basically classes that wrap around a dict that the user
loads. If the user writes their plugins in Python, they can write whatever
they'd like. If they use YAML/JSON to build their plugins, there's a finite
number of keys that they can use. As mentioned in the summary, a YAML/JSON file
is called a "Plugin Sheet". Two great documents that cover the different
options that users can use to create plugins are :doc:`plugin_basics` and
:doc:`plugin_advanced`.

At this point, now that you have read through the Context object and Plugins,
specifically the :doc:`plugin_basics` link, it's a good idea to re-read each
of Context object's methods and how those relate to the different plugin keys.


Ways Cache
++++++++++

Now that you understand Context objects, it's important to know how they are
loaded. In the :mod:`ways.base.cache` file, you'll find the functions that are used to
register Contexts and plugins, which we've talked about already, and also
register Descriptors and Actions, which we haven't touched on yet. Ignore
functions related to those two for now and lets just talk about Contexts and
plugins.

When Ways first is imported and used, it gathers plugins that it can see in
the WAYS_PLUGINS and WAYS_DESCRIPTOR environment variables. Once you're
actually in Python, it's best to just use the Ways functions to add additional
objects. If you absolutely need to add paths to those environment variables,
first ask yourself why you think you need to. If you still think its necessary,
add the paths with os.environ and the run :func:`ways.api.init_plugins`. This
function **will** remove any objects added in Python so it's not recommended to
use. But you can do it.


Descriptors
+++++++++++

Read through :doc:`descriptors` to get the jist about how Descriptor
objects are built as a user. There's not much to say about them other than
they're an abstraction used to load Plugin Sheets. That way, you can load
plugins into Ways from disk, a database, or whatever other method you'd like.

Other than that, they are not special in any way. Everything related to
Descriptors is found in the :mod:`ways.base.descriptor` file. To see how
they're loaded, revisit ways.base.cache. In particular, it's good to notice two
things in :mod:`ways.base.cache`.


1. add_search_path is just an alias to add_descriptor. The user can add plugins
   just by giving a filepath or folder and the Descriptor object needed will be
   built for them. Most of the time, that's all you'll need.
2. add_descriptor and add_plugin both try their best to catch errors before
   they happen so the user can review any Descriptor or plugins that didn't
   load. For more information on that, check out :doc:`troubleshooting`.


Actions
+++++++

Many other pages talk about Actions. It's mentioned in :doc:`summary`,
:doc:`why`, :doc:`common_patterns` and even has its own section in
:doc:`troubleshooting`. There's not much point in repeating what has already
been said so lets talk just about how Ways actually exposes Actions to the
user.

When an Action is registered to Ways (using ways.base.cache.add_action), the user
specifies a hierarchy for the Action and a name to call it.

This is kept in a dictionary in :class:`ways.ACTION_CACHE`.

Context and Asset objects both have an "actions" property. "actions" is
actually an object that uses the current Asset or Context to find the hierarchy
and assignment that the user wants to get Actions of.

Asset's "actions" property is a :class:`ways.parsing.resource.AssetFinder` object
and Context's "actions" property is a ways.base.finder.Find object. Both objects
are basically exactly the same, functionally, with the only difference that
once is meant to work with Asset objects and the other Context objects.

When the user calls an action using "actions", the following happens:

1. Ways looks up to see if that Action/Context has a definition for that
   Action. If it doesn't and the user has aptly given that Action name a
   default value to return, that value is returned. If there's no Action and no
   default value, AttributeError is raised as if the Action were an attribute.
2. If an Action is found, the function is wrapped using funtools.partial. The
   partial function adds the Context/Asset as the first arg to the function.

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
++++++

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

The other function that's very important is :func:`ways.parsing.resource._find_context_using_info`.

Basically, if a user tries to run :func:`ways.api.get_asset` without giving a context,
this function will try to "find" a matching Context to use instead. At the risk
of reiterating the same information twice, read through
_find_context_using_info and get_asset's docstrings to find out the common
problems with trying to auto-find Contexts.


api.py
++++++

This module is where almost every function or class meant to be used by
developers is put. There's nothing really special about it, just know that it's
there and exists for the user's convenience.


Reporting Issues
----------------

Before reporting issues, check to make sure that you've installed Ways
properly. Ways has a fair amount of unitests. It even has unittests for its
documentation. If you're having issues setting it up, it may not be an issue
with Ways but your environment.

If your issue is using Ways, then please do submit issues as you see them. Buf
when you do, please leep this in mind:


Before You Submit The Issue
+++++++++++++++++++++++++++

**Check the docs before reporting an issue**. It may have already been addressed.

**Make sure you're running the latest version of Ways**. The issue may be fixed already.

**Search the issue tracker for similar issues**. If you think your issue is still
important enough to raise, do so, but link to the related tickets, too.


When You Write The Issue
++++++++++++++++++++++++

1. If your problem is involved with an environment set up, please include one
   compressed archive (.zip/.rar/.tar/.etc) containing all of the files needed.
   Also, write steps to reproduce your problem. If it involves the files given,
   write steps for setting those files up too.
2. Add the output of :func:`ways.api.trace_all_descriptor_results_info` and
   :func:`ways.api.trace_all_plugin_results_info` as a text file in the ticket.
3. Write a test case for your issue. It helps a lot while trying to reproduce
   the issue and helps make sure that the issue won't happen again in the future.
4. Include your WAYS_PLATFORMS and WAYS_PLATFORM environment variables, if
   those are explicitly defined, as well as your system OS and OS version.


Maintainer Notes
----------------

If you're considering adding features to Ways, the very first thing to do would
be to clone the main repository. See :doc:`installation` for details.

It's recommended to read all of the documentation here from start to end before
making changes. But at the very least, read :doc:`summary`,
:doc:`getting_started` and :ref:`api_details`.


Repository Structure
++++++++++++++++++++

Ways uses a cookiecutter tox environment. For more details, check out
the GitHub repo that Ways was built from for details:

https://github.com/ionelmc/cookiecutter-pylibrary


Pull Requests
+++++++++++++

Ways follows PEP8. It also does its best to respect pylint rules but exceptions
exist, even in the core database.

1. Write easy to read/maintain code.

    - K.I.S.S. Ways gets by using very few classes and very simple ideas.
      If you're adding a class or a complex system, think about why you think
      you need it, first.
    - Ways has many working parts. It tries its best to not make any assumptions
      about Context mapping strings or anything else. Any OS-dependent changes
      (like adding functions to convert "/" or "\\\\", just as an example) will be
      met with extreme caution.

2. Write tests

    At the time of writing, its coverage is over 90%. Lets keep it that way.

3. Explain why your pull request is needed

   This project was written by a single person, with a very specific pipeline
   in mind. There's bound to be ideas here that aren't going to translate as
   well for your pipeline needs. If you can explain what your change does and
   how it adds value to the codebase, more power to you!

To make sure your changes work correctly, just run

::

    tox

The tox environment that Ways comes with has some commands for pylint,
pydocstyle and the like. If you want to only run those, use

::

    tox -e check

If it runs fine on your machine, make a branch and push a build. If the build
succeeds in travis.ci, feel free to make that pull request. And thanks for
going through the trouble, I really appreciate it!


api.py
++++++

If the pull request contains new functions or classes, consider adding them to
api.py and explain why you think they'd be a good addition.
