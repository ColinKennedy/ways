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
Now you can open a Python interpreter or import it into another file and use
it as a ways.api.Context.

Create your new Context
-----------------------

::

    import ways.api
    context = ways.api.get_context('some/context')

If context is not None, congratulations, Ways is ready to use.

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
we add to the metadata, and then we call the same hierarchy in another
function. The Context in "some_function" already has the data that was
appended, earlier. You're allowed to write anything in a Context's data.

There's a lot more to how Plugin objects are defined. Including Context
inheritance, relative plugins, and OS-aware plugins. To know more, Check out
:doc:`plugin_basics` and :doc:`plugin_advanced`.


Asset Objects
-------------

We have a generic description of a path on disk "/some/{JOB}/and/folders" so
now we'll extend it using an Asset object.

If Context objects are branches on a tree, think of Asset objects as the leaves.
Meaning, Context objects describe a range of information and Asset objects are
specific points along that range. There can only be 1 of any Context but there
could be any number of Asset objects.

Creating an Asset object is more or less the same as creating a Context. The
main difference is that any part of a Context's mapping that is an unfilled
Token (in our above example "{JOB}" is unfilled), we need to define it.

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
    asset3 = ways.api.get_asset('/jobs/foo/here', 'some/context')
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
To find out more about that, check out `Asset Object Tricks`.

Context Actions
---------------

Great - we have a Context and Asset object. You may have noticed though that
both classes have very few methods. Ways tries to not assume how
you'll use Context and Asset objects and instead lets you to extend the
object's interfaces at runtime, using Actions.

To create an Action for our original example, create a new file name anything -
we'll call ours action.py. Add the path to action.py into the WAYS_PLUGINS
environment variable.

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

        def __call__(self, obj):
            '''Do something.'''
            return ['/library', 'library/grades', 'comp', 'anim']

Note: __call__ takes at least one arg - the Context or Asset that called the
Action. Ways will pass the caller object to this variable before any of the
user's args/kwargs.

To use the Action that was just created, call it from a Context or Asset.

::

    context = ways.api.get_context('some/context')
    context.actions.create()
    # Results: ['/library', 'library/grades', 'comp', 'anim']

That's all there is to it. If you don't want to write an Action subclass, you
can also use a regular function and register it.

::

    def some_action(obj):
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

Actions called from an Asset object behave the same a Context objects. The only
difference is that the first arg that get's passed to the Actions object will
be the instance of Asset that called it, not the Context.

If we want to call get_info from an Asset instance and pass it the Context,
we still can.

::

    asset = ways.api.get_asset({'JOB': 'something'}, context='some/context')

    # Using the Context object
    context = ways.api.get_context('some/context')
    context.actions.get_info()  # get_info will pass 'context'

    # Using the Context located in the Asset object
    asset.context.actions.get_info()  # get_info will pass 'asset.Context'

    # This is still the preferred way, most of the time
    asset.actions.get_info()  # get_info will pass 'asset'

The most powerful way to chain Actions together is to have Action objects
return other Context/Asset/Action objects. Actions have very few rules
and can be formatted to your needs easily.

TODO : Still need to write this
Check out `Advanced Actions` to read more.

Now that you've gone through the basics, make sure to read through Common
Patterns And Best Practices to get an idea of how you should be formatting your
code

