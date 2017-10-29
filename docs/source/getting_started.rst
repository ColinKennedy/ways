Getting Started
===============

This section assumes that you've read through the :doc:`summary` Page and
that you're ready to start.

First, create a new YAML file, call it whatever you'd like. For this example,
it'll be called "plugin_sheet.yml". Add the path to this file to your
WAYS_DESCRIPTORS environment variable.

Setting your environment variable
---------------------------------

tcsh/csh

.. code-block :: tcsh

    setenv WAYS_DESCRIPTORS /some/path/to/a/plugin_sheet.yml

bash

.. code-block :: bash

    export WAYS_DESCRIPTORS=/some/path/to/a/plugin_sheet.yml

Your specific command will depend on your terminal/setup.

Writing your your first Plugin Sheet
------------------------------------

Now that plugin_sheet.yml exists, lets add a "Hello World!" plugin to it.

::

    > cat /some/path/to/a/plugin_sheet.yml
    plugins:
        foo_plugin:
            hierarchy: 'some/context'

At this point, we've made our first plugin in our first Plugin Sheet.
Now you can open a Python interpreter or another file and use it, as a Context.

Instantiate your new Context
----------------------------

::

    import ways.api
    ways.api.get_context('some/context')

If get_context did not return None, congratulations, Ways is ready to use.

Adding features to Context objects
----------------------------------

From here, we can add data to the Context

::

    > cat /some/path/to/a/plugin_sheet.yml
    plugins:
        foo_plugin:
            hierarchy: 'some/context'
            data:
                some:
                    arbitrary:
                        - info1
                        - info2
                        - 3
                        - bar

::

    import ways.api
    context = ways.api.get_context('some/context')
    context.data['some']['arbitrary']
    # Result: ['info1', 'info2', 3, 'bar']

Here we can add data to the plugin and access it later, though a Context.
Context objects persist everywhere as long as you call them with the
same hierarchy.

::

    context = ways.api.get_context('some/context')
    print(id(context))
    context.data['some']['arbitrary'].append('bar2')

    def some_function():
        a_new_context = ways.api.get_context('some/context')
        print(id(a_new_context))
        print(a_new_context.data['some']['arbitrary'])
        # Result: ['info1', 'info2', 3, 'bar', 'bar2']

In the above example, we have a Context that initializes with some metadata,
we add to the metadata, and then we retrieve it in another function without
passing the Context into it.

There's a lot more to how Plugin objects are defined. Including Context
inheritance, relative plugins, and OS-aware plugins. To know more, Check out
TODO: Finish?
`Creating a Plugin Sheet`.

Asset Objects
-------------

We have a generic description of a path on disk "/some/{JOB}/and/folders" so
now we'll extend it using an Asset object.

If Context objects are branches on a tree, think of Asset objects as the leaves.
Meaning, Context objects describe a range of information and Asset objects are
specific points along that range.

Creating an Asset object is more or less the same as creating a Context. The
main difference is that any part of a Context's mapping that is an unfilled
Token (i.e. in our above example, "{JOB}"), we need to define it while creating
the Asset.

::

    > cat /some/path/to/a/plugin_sheet.yml
    plugins:
        job:
            hierarchy: 'some/context'
            mapping: /jobs/{JOB}/here

::

    # All 3 of these syntaxes create the same Asset object
    asset1 = ways.api.get_asset((('JOB', 'foo'), ), 'some/context')
    asset2 = ways.api.get_asset({'JOB': 'foo'}, 'some/context')
    asset3 = ways.api.get_asset(path, 'some/context')
    print(asset1.get_str())
    # Result: '/jobs/foo/here'
    print(asset1.get_value('JOB'))
    # Result: 'foo'

Asset objects act like dictionaries that have some data and the Context is
what grounds that dictionary in something real (i.e. a filesystem or a
database). Asset objects have a small list of features that you'll learn in other
sections, like token validation (checking if tokens are optional or not),
Context-expansion, recursive value parsing, and API hooks so that you
can swap Asset objects for classes that you may have already written.
TODO : Link to this?
To find out more about that, check out `Asset Object Tricks`.

Context Actions
---------------

Great - we have a Context and Asset object. You may have noticed though that
both classes have very few methods. Ways tries to not assume how
you'll use Context and Asset objects and instead lets you to extend the
object's interfaces at runtime, using Actions.

To create an Action for our original example, create a new file - we'll call
ours action.py. Add the path to action.py into the WAYS_PLUGINS environment
variable.

Now just add a new class in action.py, have it inherit from ways.api.Action,
and implement two methods.

plugin_sheet.yml

.. code-block :: yaml

    plugins:
        foo_plugin:
            hierarchy: 'some/context'

action.py

::

    import ways.api

    class SomeAction(ways.api.Action):

        '''A subclass that will automatically be registered by Ways.

        The name of the class (SomeAction) can be anything but the name
        property must be correct. Also, get_hierarchy must match the Context
        hierarchy that this action will apply to.

        '''

        name = 'create'

        @classmethod
        def get_hierarchy(cls):
            return 'some/context'

        def __call__(self):
            '''Do something.'''
            return ['/library', 'library/grades', 'comp', 'anim']

To use the Action that was just created, call it from a Context or Assset.

::

    context = ways.api.get_context('some/context')
    context.actions.create()
    # Results: ['/library', 'library/grades', 'comp', 'anim']

That's all there is to it. If you don't want to write an Action subclass, you
can also use a regular function and register it.

::

    def some_action():
        return ['/library', 'library/grades', 'comp', 'anim']

    context = ways.api.get_context('some/context')
    ways.api.add_action(some_action, hierarchy='some/context')
    context.actions.some_action()

    # If you don't want to use the name of the function, you can give the action
    # a name
    #
    ways.api.add_action(some_action, 'custom_name', hierarchy='some/context')

    context.actions.custom_name()
    # Result: ['/library', 'library/grades', 'comp', 'anim']

It doesn't matter what the order of your objects are defined. Actions that
are defined before Context/Asset objects will work fine too.
All that matters is that both exist by the time you call the Action from a Context.


Context and Asset Actions
-------------------------

We've been using Context.actions this whole time but Asset objects have an
"actions" property, too.

ways.api.Asset.actions behaves differently than ways.api.Context.actions.

Asset.actions will always assume that the Action's first argument will take the
current Asset object. Context.actions doesn't assume anything about an Action's
parameters.

If we have an Action like this:


::

    > cat plugin_sheet.yml
    plugins:
        job:
            hierarchy: 'some/context'
            mapping: /jobs/{JOB}/here

action.py

::

    import ways.api

    class AnotherAction(ways.api.Action):

        '''A subclass that will automatically be registered by Ways.'''

        name = 'get_info'

        @classmethod
        def get_hierarchy(cls):
            return 'some/context'

        def __call__(self, shot=None):
            '''Do something.'''
            return ['/library', 'library/grades', 'comp', 'anim']

To call it from an Asset, all we have to write is this:

::

    asset = ways.api.get_asset({'JOB': 'foo'}, context='some/context')
    asset.actions.get_info()

Notice that AnotherAction.__call__ takes an argument but we call get_info with
no args. That's because the Asset object that calls it is being passed as the
first arg, since we used Asset.actions. With Context.actions, nothing is passed
- your args are left unmodified.

If we want to call get_info from a Context, we still can, it's just more work.

::

    asset = ways.api.get_asset({'JOB': 'something'}, context='some/context')

    # Using the Context object
    context = ways.api.get_context('some/context')
    context.actions.get_info(asset)

    # Using the Context located in the Asset object
    asset.context.actions.get_info(asset)

    # This is still the preferred way, most of the time
    asset.actions.get_info()

The most powerful way to chain Actions together is to have Action objects
return other Context/Asset/Action objects. Actions have very few rules
and can be formatted to your needs easily.

TODO : Still need to write this
Check out `Advanced Actions` to read more.

Now that you've gone through the basics, make sure to read through Common
Patterns And Best Practices to get an idea of how you should be formatting your
code

