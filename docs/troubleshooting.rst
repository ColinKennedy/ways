Troubleshooting Ways
====================

Loading Descriptors And Plugin Sheets
-------------------------------------

Descriptors aren't guaranteed to always load for a number of reasons.
Depending on the class of the Descriptor and your input, there could be
multiple reasons. Luckily, Ways keeps track of Descriptor objects that it tries
to load so you can review a live session to find out what kind of errors you
have.


Descriptor Failed To Import
+++++++++++++++++++++++++++

Ways is designed to allow users to write custom Descriptor objects if they want.
that. But if the user gives an import string that isn't on the PYTHONPATH,
there's nothing that Ways can do to fix it.

Take a simple Descriptor dict, for example.
If we convert it to a URL-encoded string, it looks like this:

::

    from urllib import parse

    info = {
        "items": "/some/folder/path",
        "create_using": "foo.bar.bad.import.path",
        "uuid": "foo_bad_path"
    }
    parse.urlencode(info, doseq=True)

.. code-block :: bash

    export WAYS_DESCRIPTORS=items=%2Fsome%2Ffolder%2Fpath&create_using=foo.bar.bad.import.path&uuid=foo_bad_path

While this URL string is valid with no syntax errors, it will fail because the
value for "create_using" doesn't exist.

This error can also come up if the URL-encoded string isn't correctly formatted
(example: an encoding syntax error will also raise an error).

If you think your Descriptor failed to load and would like to check, search
for the Descriptor using its UUID.

::

    result = ways.api.trace_all_descriptor_results_info()['my_uuid_here']
    # Result:
    # {
    #     "status": "failed",
    #     "item": "items=%2Fsome%2Ffolder%2Fpath&create_using=foo.bar.bad.import.path&uuid=foo_bad_path",
    #     "reason": "resolution_failure"
    #     'traceback': some_traceback_info_here,
    # }


ways.api.trace_all_descriptor_results_info will only be useful if you defined
UUIDs for your Descriptor. If you don't create a Descriptor with a UUID,
Ways will just create one for you but it will be random each time. You'll
still have to iterate over all of the loaded Descriptors to find the one you want.

::

    for result in ways.api.trace_all_descriptor_results():
        # ... do something to find the Descriptor you wanted

    for result in ways.api.trace_all_descriptor_results().values():
        # ... do something to find the Descriptor you wanted


Descriptor has no method to get plugins
+++++++++++++++++++++++++++++++++++++++

If the Descriptor loads but the object that Ways creates doesn't have a method
for getting plugins, there's a very high chance that the Descriptor is
will break on-load. To be on the safe side, Ways doesn't add the Descriptor
to the system since it isn't sure about it and errors out, instead.

::

    # cat /some/module.py
    class BadDescriptor(object):

        '''A Descriptor that does not work.'''

        def __init__(self, items):
            '''Just create the object and do nothing else.'''
            super(BadDescriptor, self).__init__()

            self.get_plugins = None

Assuming module.py is on the PYTHONPATH, Ways can import it but it won't
work because get_plugins isn't a callable function.

.. code-block :: json

    {
        "create_using": "module.BadDescriptor",
        "uuid": "some_uuid",
        "items": "/something/here"
    }

And finally, that becomes

::

    items=%2Fsomething%2Fhere&create_using=module.BadDescriptor&uuid=some_uuid

In this example, BadDescriptor is not callable and does not have a "get_plugins"
method. Ways has no way of knowing how to get the plugins out of the Descriptor.

See :ref:`descriptor_summary` for details on how to best build Descriptor objects.


Loading Standalone Plugins
--------------------------

Standalone plugins are Python files that load separately from the standard
"Descriptor/Plugin Sheet" process. They're completely open - users can write
whatever they want. But because of that, standalone plugins have more
opportunities to fail.


Plugin Fails to Import
++++++++++++++++++++++

Finding out if Plugin files fail to import has almost the same syntax as
a Descriptor.

.. code-block :: bash

    export WAYS_PLUGINS=/some/path/that/doesnt/exist.py

Import failures are notoriously annoying because, even if the plugin has a
uuid defined, Ways can't gather it if the module cannot import. Just like
Descriptors, you'll have to iterate over each plugin result to find the ones
that you're looking for.

::

    failed_plugins = [item for item in ways.api.trace_all_plugin_results() if
                      item.get('reason') == ways.api.IMPORT_FAILURE_KEY]


Plugin "main()" Function is broken
++++++++++++++++++++++++++++++++++

If the Plugin has a "main()" function and running it causes some kind of error,
that is also logged. Though this time, we can grab the Plugin by its uuid
as long as it's defined in the file.

::

    # cat /some/plugin.py
    import ways.api

    WAYS_UUID = 'some_uuid_here'

    def main():
        raise ValueError('invalid main function')


In another file or a live Python session, we can search for this Plugin
file's result.

::

    result = ways.api.trace_all_plugin_results_info()['some_uuid_here']


Working In A Live Session
-------------------------

Depending on how complex your setup becomes or the number of
people on your team, it may get difficult to keep track of the Contexts and
Actions that are available to you while you begin to start working.

In most scenarios, you'll want to know what
hierarchies you can use, what Contexts are available, and the Actions that
those Context objects can use.


Working With Hierarchies
++++++++++++++++++++++++

The first thing you'll want to know while working is what hierarchies that you
can use.

.. note ::

    For the sake of completeness, the rest of the examples on this page will
    all refer to the plugins defined in this Plugin Sheet.


.. code-block :: yaml

    cat some_plugin_sheet.yml

    plugins:
        a_plugin_root:
            hierarchy: foo
            mapping: /jobs
        another_plugin:
            hierarchy: foo/bar
            mapping: /jobs/foo/thing
        yet_another_plugin:
            hierarchy: foo/bar/buzz
        still_more_plugins:
            hierarchy: foo/fizz
        did_you_know_camels_have_three_eyelids?:
            hierarchy: foo/fizz/something
        okay_maybe_you_knew_that:
            hierarchy: foo/fizz/another
        but_I_thought_it_was_cool:
            hierarchy: foo/fizz/another/here


To get all hierarchies

::

    ways.api.get_all_hierarchies()
    # Result: {('foo', ), ('foo', 'bar'), ('foo', 'bar', 'buzz'),
    #          ('foo', 'fizz'), ('foo', 'fizz', 'something'),
    #          ('foo', 'fizz', 'another'), ('foo', 'fizz', 'another', 'here')}

To get hierarchies as a dictionary tree

::

    ways.api.get_all_hierarchy_trees(full=True)
    # Result:
    # {
    #     ('foo', ):
    #     {
    #         ('foo', 'bar'):
    #         {
    #             ('foo', 'bar', 'buzz'): {},
    #         },
    #         ('foo', 'fizz'):
    #         {
    #             ('foo', 'fizz', 'something'): {},
    #             ('foo', 'fizz', 'another'):
    #             {
    #                 ('foo', 'fizz', 'another', 'here'): {}
    #             },
    #         },
    #     },
    # }

Or if you'd prefer a more concise version

::

    ways.api.get_all_hierarchy_trees(full=False)
    # Result:
    # {
    #     'foo':
    #     {
    #         'bar':
    #         {
    #             'buzz': {},
    #         },
    #         'fizz':
    #         {
    #             'something': {},
    #             'another':
    #             {
    #                 'here': {}
    #             },
    #         },
    #     },
    # }


Once you've got a Ways object such as an Asset, Context, or just a simple
hierarchy, you can also query "child" hierarchies from that point. A child
hierarchy is any hierarchy that contains the given hierarchy.


::

    hierarchy = ('foo', 'fizz')
    context = ways.api.get_context(hierarchy)
    asset = ways.api.get_asset({}, context=context)

    # All three functions create the same output
    ways.api.get_child_hierarchies(hierarchy)
    ways.api.get_child_hierarchies(context)
    ways.api.get_child_hierarchies(asset)
    # Result: {('foo', 'fizz', 'something'), ('foo', 'fizz', 'another'),
                    ('foo', 'fizz', 'another', 'here')}

And you can visualize it as a tree, too.

::

    ways.api.get_child_hierarchy_tree(('foo', 'fizz'), full=True)
    # Result:
    #    {
    #        ('foo', 'fizz', 'something'): {},
    #        ('foo', 'fizz', 'another'):
    #        {
    #            ('foo', 'fizz', 'another', 'here'): {},
    #        },
    #    }


.. note ::

    The hierarchies that these functions return can be used to create Context
    objects assuming that there's at least one valid plugin in each hierarchy.


Working With Contexts
+++++++++++++++++++++

Context objects have different ways for resolving its Plugin objects.
For example, get_mapping_details resolves completely differently than
get_platforms or get_mapping or eve get_max_folder.

When you get back a value that you didn't expect, it's always one of two
problems. Either the Context didn't load the plugins that you expected or
the plugins that were loaded didn't resolve the way you expected.


Checking The Loaded Context Plugins
***********************************

Getting every Plugin that is loaded into Ways is a single command.

::

    ways.api.get_all_plugins()

If you don't see the plugin that you're looking for in that list, it's possible
that it was not found by the Descriptor that you thought it was. Once it's
clear that all the Plugin objects needed are loaded into Ways, the last step is
just to make sure that your Context is loading your Plugins.

Not all Plugin objects are loaded by a Context. For example, if a Plugin's
"get_platform" method doesn't return the current user's platform, it is
excluded. This Plugin-filtering lets Ways have Plugins with the same
hierarchy but conflicting mappings coexist. It also lets the user define
relative plugins so that Plugins meant for MacOS aren't loaded on Windows.

To get the raw list of Plugins that a Context can choose from, there is the
get_all_plugins method

::

    context = ways.api.get_context('foo/bar')
    raw_plugins = context.get_all_plugins()
    plugins = context.plugins
    unused_plugins = [plugin for plugin in raw_plugins if plugin not in plugins]


get_all_plugins shows you every Plugin that a Context can use. The "plugins"
property shows you which of those Plugins were actually used and you can get
the unused Plugin list by taking the difference between the two.


Checking Method Resolution
**************************

This section assumes that you've read
:doc:`plugin_basics`. It's important to know how
Context objects resolve their plugins before starting to
troubleshoot values that you may not expect.

::

    context = ways.api.get_context('foo/bar')
    ways.api.trace_method_resolution(context.get_mapping)
    # Result: ['/jobs', '/jobs/foo/thing']

    # To include the Plugins that created some output, use plugins=True
    ways.api.trace_method_resolution(context, 'get_platforms' plugins=True)
    # Result: [('/jobs', DataPlugin('etc' 'etc')),
    #          ('/jobs/foo/thing', DataPlugin('etc', 'etc', 'etc'))]


trace_method_resolution works by taking the Context from its first plugin,
running the given method, then uses the first 2 plugins and runs the given
method again until every plugin that the Context sees has been run.

That way, it's obvious which plugin was loaded at what point and that plugin's
effect on the method.


Working With Actions
++++++++++++++++++++

Depending on what information you're working with, Actions can be queried in a
few ways.

If you have a Context and you want to know what Actions that it is allowed to
use, all you have to do is "dir" the "actions" property.

::

    context = ways.api.get_context('foo/bar')
    dir(context.actions)
    # Result: ['action_names', 'here', 'and', 'functions', 'you', 'can', 'use']

    # Assets work the same way
    asset = ways.api.get_asset({'INFO': 'HERE'}, 'foo/bar')
    dir(asset.actions)
    # Result: ['action_names', 'here', 'and', 'functions', 'you', 'can', 'use']

Sometimes all you have is the name of an Action and aren't sure what
hierarchies can use it.

::

    # Get all of the hierarchies that allowed to use "some_action_name"
    hierarchies = ways.api.get_action_hierarchies('some_action_name')

    # To get the hierarchies for every action, use get_all_action_hierarchies
    everything = ways.api.get_all_action_hierarchies()


.. note ::
    get_action_hierarchies will return every Action that matches the given
    Action name. So if multiple classes/functions are all registered
    under the same name, then every hierarchy that those Actions use will be
    returned. However, if a object like a function or class that was
    registered, only that object's hierarchies will be returned.
