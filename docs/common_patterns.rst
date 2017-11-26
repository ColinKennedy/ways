Common Patterns And Best Practices
==================================

While designing and working with Ways, a few re-occuring ideas would appear in
production code over and over. This page is a collection of some of those
good ideas.


Best Practices
--------------

This section is a series of things to include while writing Ways objects that
are generally good ideas to do.


Writing mapping and mapping_details
+++++++++++++++++++++++++++++++++++

Include a mapping for your plugins whenever possible. If you have some kind
of information, a string or a dict, and you don't know what Context hierarchy
it belongs to, mapping and mapping_details are used to "auto-find" the right
Context.

Auto-find using mapping
***********************

Whenever you have to autofind a Context using :func:`ways.api.get_asset`, it's
best to give a string whenever you can because then Ways can exact-match the
string to a mapping, like this:

.. code-block :: yaml

    plugins:
        something:
            hierarchy: foo
            mapping: /jobs/{JOB}/shots

::

    value = '/jobs/someJobName_12391231/shots'
    asset = ways.api.get_asset(value)

If the mapping of the hierarchy you're looking for has at least one Token, you
can give a dict:

::

    value = {'JOB': 'someJobName_12391231'}
    asset = ways.api.get_asset(value)

There's a pretty obvious problem with that though. If two hierarchies have a
mapping that both use the "JOB" Token, Ways will try to return them both, which
will cause an error.

.. code-block :: yaml

    plugins:
        something:
            hierarchy: foo
            mapping: /jobs/{JOB}/shots
        another:
            hierarchy: bar
            mapping: generic.{JOB}.string.here

::

    value = {'JOB': 'someJobName_12391231'}
    asset = ways.api.get_asset(value)  # Will raise an exception

Both "foo" and "bar" hierarchies use the JOB Token so Ways doesn't know which
one to use.

The good news is, there is a way to distinguish between "foo" and "bar" in this
worst-case scenario. Just describe "JOB" using mapping_details.

.. code-block :: yaml

    plugins:
        something:
            hierarchy: foo
            mapping: /jobs/{JOB}/shots
            mapping_details:
                JOB:
                    parse:
                        regex: '\d+'
        another:
            hierarchy: bar
            mapping: generic.{JOB}.string.here
            mapping_details:
                JOB:
                    parse:
                        regex: '\w+'

::

    value = {'JOB': 'someJobName_12391231'}
    asset = ways.api.get_asset(value)
    asset.get_hierarchy()
    # Result: 'foo'

Because the "foo" hierarchy was defined with regex and it expected some integer,
and "bar" is allowed to have non-digit characters, Ways was able to figure out
which Context to use for our Asset.

In short, it's a good idea to define mapping and mapping_details basically always.


Add a UUID
++++++++++

In Ways, the UUID is an optional string that you can add to every plugin. This
UUID is useful for searching and debugging so it's a good idea to include it
whenever you can.

.. code-block :: yaml

    plugins:
        hierarchy: foo
        uuid: some_string_that_is_not_used_anywhere_else


A UUID must be unique, even in other Ways-related files. If the same UUID comes
up more than once, Ways will raise an exception to let you know.


Filepaths and mapping
+++++++++++++++++++++

If you use Ways for filepaths, make sure to enable the "path" key
to avoid OS-related issues.

::

    plugins:
        path_out:
            hierarchy: foo
            mapping: /etc/some/filepath
            path: true

The reason to do this has explained in
:ref:`path_explanation` so head there if further explanation is needed.


Action Patterns
+++++++++++++++

By now you should know about Actions (If not, read through this :ref:`creating_actions`).
Actions are how Ways extends its objects with additional functions.

Because Actions are applied to certain hierarchies, sometimes you may call an
Action on an Asset or Context that you think exists but doesn't.
When that happens, AttributeError is raised.

.. code-block :: yaml

    plugins:
        foo:
            hierarchy: some/hierarchy
        another:
            hierarchy: action/hierarchy

::

    class ActionOne(ways.api.Action):

        name = 'some_action'

        @classmethod
        def get_hierarchy(cls):
            return 'some/hierarchy'

        def __call__(self, obj):
            return ['t', 'a', 'b', 'z']


    class ActionTwo(ways.api.Action):

        name = 'some_action'

        @classmethod
        def get_hierarchy(cls):
            return 'action/hierarchy'

        def __call__(self, obj):
            return [1, 2, 4, 5.4, 6, -2]

    for hierarchy in ['some/hierarchy', 'action/hierarchy', 'bar']:
        context = ways.api.get_context(hierarchy)
        context.actions.some_action()

This will cause you to want to write lots of code using try/except:

::

    try:
        value = context.actions.some_action()
    except AttributeError:
        value = []

A better way is to assign a default value for your Action.
This value will get returned whenever you call a missing Action.

In a plugin file, you can write this:

/some/plugin/defaults.py

::

    import ways.api

    class ActionTwo(ways.api.Action):

        name = 'some_action'

        @classmethod
        def get_hierarchy(cls):
            return 'action/hierarchy'

        def __call__(self, obj):
            return [1, 2, 4, 5.4, 6, -2]

    def main():
        '''Add defaults for actions.'''
        ways.api.add_action_default('some_action', [])

Then add the path to /some/plugin/defaults.py to your WAYS_PLUGINS environment
variable.

Now, in any file you'd like, you can work as normal.

::

    import ways.api

    context = ways.api.get_context('foo/bar')
    for item in context.actions.some_action():
        # ...

To summarize, it's usually a good idea to define a default value in the same
file that defines Actions. That way there is always a fallback value.

.. note ::

    If you want certain hierarchies to have different default values, specify
    a hierarchy while you define your default value.

    ways.api.add_action_default('some_action', [], hierarchy='foo/bar')


Designing Plugins
-----------------

Appending vs Defining
+++++++++++++++++++++

It's mentioned in several other pages such as :ref:`path_explanation` and
:ref:`appending_plugins` but you have 3 options to add information to
hierarchies. You can either just add the information to the original plugin or
append to it, using another absolute plugin or a relative plugin.

.. code-block :: yaml

    plugins:
        root:
            hierarchy: foo
        another:
            hierarchy: bar
            mapping: a_mapping
        absolute_append:
            hierarchy: foo
            data:
                something_to_add: here
        relative_append:
            hierarchy: ''
            mapping: something
            path: true
            uses:
                - foo
                - bar

In this example, the "absolute_append" plugin will append to "root" and
"relative_append" appends to "root" and "another" at once. If you need better
control over your plugins, using absolute appends will tend to be a very clear,
simple way to do it. If you need to make a broad change to many plugins at
once, relative appends make more sense to do since you can specify many plugins
and add information all in one plugin.

Relative appends have one problem though - you can't customize what gets
appended to both hierarchies.

In the above example, mapping and path are both appending onto "root" and "another".
But say for example you only wanted mapping to append to "root" and not to
"another"? It's not possible - you'd have to split the relative plugin into
two relative plugins. At that point, you might as well use absolute appends.

It's a balancing act and you'll find yourself gravitating to one style or another.

.. _asset_swapping:

Asset Swapping
--------------

Ways comes with an object called Asset (:class:`ways.api.Asset`) that is used
for basic asset management. If you have your own classes that you'd prefer to
use instead, adding those objects to Ways is fairly simple.

Register A Custom Class
+++++++++++++++++++++++

An generic Ways Asset expects at least two arguments, the object that
represents the information to pass to the Asset and the Context that does with
that that information. The Context is optional, as mentioned before.

::

    info = {'foo': 'bar'}
    context = 'some/thing/context'
    ways.api.get_asset(info, context)

If you have a class that takes two or more arguments, you can use that class
directly in place of an Asset.

::

    import ways.api

    class SomeNewAssetClass(object):

        '''Some class that will take the place of our Asset.'''

        def __init__(self, info, context):
            '''Create the object.'''
            super(SomeNewAssetClass, self).__init__()
            self.context = context

        def example_method(self):
            '''Run some method.'''
            return 8

        def another_method(self):
            '''Run another method.'''
            return 'bar'
    context = ways.api.get_context('some/thing/context')
    ways.api.register_asset_class(SomeNewAssetClass, context)
    asset = ways.api.get_asset({'JOB': 'something'}, context='some/thing/context')
    asset.example_method()
    # Result: 8

If the class isn't designed to work with Ways or takes 0 or 1 arguments, you
can still use it. Just add an init function:

::

    import ways.api

    class SomeNewAssetClass(object):

        '''Some class that will take the place of our Asset.'''

        def __init__(self):
            '''Create the object.'''
            super(SomeNewAssetClass, self).__init__()

    def custom_init(*args, **kwargs):
        return SomeNewAssetClass()

    def main():
        '''Register a default Asset class for 'some/thing/context.'''
        context = ways.api.get_context('some/thing/context')
        ways.api.register_asset_class(
            SomeNewAssetClass, context=context, init=custom_init)

By default, you will need to register a class/init function for every hierarchy
that you want to swap. So if you had hierarchies like this, "some",
"some/other", "some/other/child", and "some/other/child/hierarchy" then you'd
need to register the custom class for all 4 hierarchies individually. If you're
prefer to register them for "this hierarchy and all its subhierarchies", set
children to True.

::

    ways.api.register_asset_class(SomeNewAssetClass, context='some', children=True)
