Common Patterns And Best Practices
==================================


TODO:

    - Show filepath and database plugin examples


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

Designing Plugins
-----------------

- tree types (you can switch filepath types but it's best to try to not)


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

TODO Write something about how to Swap the assets!

Action Patterns
---------------

.. Actions that don't exist for a Context or Asset will raise an
.. AttributeError. This is because Ways has no way of knowing knowing what a
.. good default value should be for an Action.

.. To get around this, you'll find yourself doing this:

.. ::

..     context = ways.api.get_context('foo/bar')

..     try:
..         items = context.actions.some_action_that_does_not_exist()
..     except AttributeError:
..         items = []

..     for item in items:
..         # ...

.. Yikes, That's horrible. Luckily, there's a better way - Action defaults.

.. Action defaults are default values that you can define for Actions in advance.

.. So, for example, in a plugin file, you can write this:

.. /some/plugin/defaults.py

.. ::

..     import ways.api

..     def main():
..         '''Add defaults for actions.'''
..         ways.api.add_action_default('some_action', [])

.. Then add the path to /some/plugin/defaults.py to your WAYS_PLUGINS environment
.. variable.

.. Now, in any file you'd like, you can work as normal.

.. ::

..     import ways.api

..     context = ways.api.get_context('foo/bar')
..     for item in context.actions.some_action():
..         # ...

.. Instead of raising AttributeError, some_action returns the empty list. Also
.. there's no requirement that says add_action_default needs to be in a separate
.. file. It's just generally a good idea, to keep things tidy.

.. .. note ::

..     This will add a default value for all actions in all hierarchies.
..     If you'd rather have an Action's default value only apply to certain

..     hierarchies, just run
..     ways.api.add_action_default('some_action', [], hierarchy='foo/bar')
