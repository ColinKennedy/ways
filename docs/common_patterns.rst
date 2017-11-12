Common Patterns And Best Practices
==================================

- Add a UUID to your plugin

Action Patterns
---------------

Actions that don't exist for a Context or Asset will raise an
AttributeError. This is because Ways has no way of knowing knowing what a
good default value should be for an Action.

To get around this, you'll find yourself doing this:

::

    context = ways.api.get_context('foo/bar')

    try:
        items = context.actions.some_action_that_does_not_exist()
    except AttributeError:
        items = []

    for item in items:
        # ...

Yikes, That's horrible. Luckily, there's a better way - Action defaults.

Action defaults are default values that you can define for Actions in advance.

So, for example, in a plugin file, you can write this:

/some/plugin/defaults.py

::

    import ways.api

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

Instead of raising AttributeError, some_action returns the empty list. Also
there's no requirement that says add_action_default needs to be in a separate
file. It's just generally a good idea, to keep things tidy.

.. note ::

    This will add a default value for all actions in all hierarchies.
    If you'd rather have an Action's default value only apply to certain

    hierarchies, just run
    ways.api.add_action_default('some_action', [], hierarchy='foo/bar')
