Plugin Basics
=============

Plugin Sheets are the backbone of Ways. They define many plugins in very few
lines and drive how Ways will parse your objects.

Because Plugin Sheets have a finite list of keys that it can use,
it's important to know what each of them are called and what each of them do.


All Plugin Sheet Keys
---------------------

This is a "Hello World" Plugin Sheet. It's the absolute minimum information
that every Plugin Sheet has. The only things that are required is a single value
under "plugins" and that value must have a "hierarchy" defined.

.. note ::

    For reference, this is a YAML file. YAML is used in this example because it's
    pretty easy to read and follow but Ways also supports JSON and Python files.

.. code-block :: yaml

    plugins:
        some_plugin:
            hierarchy: example

Here is an example of a very complicated Plugin Sheet. Every key that Ways
uses is in this file. This is a bit like getting thrown into the deep-end of a
pool but don't worry if not everything makes sense immediately. It'll all be
explained in this page and in others.

.. code-block :: yaml

    globals:
        assignment: an_assignment_to_every_plugin
    plugins:
        some_plugin:
            hierarchy: example
            uuid: something_unique

        this_can_be_called_anything:
            hierarchy: example/hierarchy
            mapping: "/jobs/{JOB}"
            uuid: another_unique_uuid
            platforms:
                - linux
            path: true

        window_jobs_plugin:
            hierarchy: example/hierarchy
            mapping: "C:\\Users\\{USER}\\jobs\\{JOB}"
            mapping_details:
                USER:
                    parse:
                        regex: \w+
            platforms:
                - windows
            uuid: windows_job
            path: true

        jobs_details:
            hierarchy: example/hierarchy
            mapping_details:
                JOB:
                    mapping: '{JOB_NAME}_{JOB_ID}'
                JOB_NAME:
                    mapping: '{JOB_NAME_PREFIX}_{JOB_NAME_SUFFIX}'
                JOB_NAME_PREFIX:
                    parse:
                        regex: '\w+'
                JOB_NAME_SUFFIX:
                    parse:
                        regex: 'thing-\w+'
                JOB_ID:
                    parse:
                        regex: '\d{3}'
            uuid: something_unique

        yet_another_plugin:
            hierarchy: example/tree
            mapping: /tree
            uuid: does_not_matter_what_it_is
            path: true

        config_plugin:
            hierarchy: "{root}/config"
            mapping: "{root}/configuration"
            uses:
                - example/hierarchy
                - example/tree
            uuid: as_Long_as_It_is_Different

        some_assigned_plugin:
            assignment: different_assignment
            hierarchy: something
            data:
                important_information: here
            uuid: boo_Did_I_scare_you?


Clearly there is a big difference between a "Hello World" Plugin Sheet and
this one. The good news is, everything in this example optional and you may
not need to ever use it all.

Feel free to use this page as a reference while writing Plugin Sheets.


Required Keys
-------------

plugins
+++++++

This is the only required, top-level key. It is a dictionary that contains all
of the plugins inside the Plugin Sheet. As long as its items are valid dict
keys, anything can be used as a plugin key though it's recommended to use
strings, since they're easy to read. Example plugin keys from above are
"some_plugin", "this_can_be_called_anything", "job_details", and all of the
other defined plugins.


hierarchy
+++++++++

This is the only required key at the plugin-level. The value that's defined for
hierarchy must be a string, separated by "/"s (even if you're using Windows).
The hierarchy is used to create objects so it's important that it is named sensibly.


Optional Keys
-------------

globals
+++++++

This key lives on the same level as the "plugins" key and is a quick way to add
information to every plugin in the file.

In the above example, "assignment" was added to globals. That key/value is
added to every plugin in the file, unless the plugin overrides it. In the above
example, every plugin will have the assignment "an_assignment_to_every_plugin"
except for some_assigned_plugin, which will have an assignment
of "different_assignment".


mapping
+++++++

mapping is just a string that describes a plugin. The complex example above
treats its mapping like it's a filepath but mapping doesn't have to be a file
or folder. It can be anything. For example, mapping can be used to reference
a database, too.

When you begin to use Asset objects (:class:`ways.api.Asset`), the mapping
becomes crucial for "auto-finding" Context (:class:`ways.api.Context`) objects.

::

    mapping = '/jobs/job_part_something'

    explicit_asset = ways.api.get_asset(mapping, context='example/hierarchy')
    autofound_asset = ways.api.get_asset(mapping)
    explicit_context == autofound_context
    # Result: True

the right Context should be, mapping is something necessary. The mapping and
uuid keys are always a good idea to define.

For practical examples on using mapping, see :doc:`common_patterns`.

mapping_details
+++++++++++++++

Anything in "{}" inside of a mapping is called a "Token".
Above, "/jobs/{JOB}" has a "JOB" Token and "C:\\Users\\{USER}\\jobs\\{JOB}" has
"USER" and "JOB" Tokens.

Tokens look like a Python format but have a set of features specific to Ways.

For one thing, Tokens can represent environment variables or parse-engines like
regex and glob.

::

    os.environ['JOB'] = 'job_thing-something_123'

    context = ways.api.get_context('example/hierarchy')
    context.get_str(resolve_with=('env', 'regex'))
    # Result on Windows: "C:\\Users\\My_Username\\jobs\\thing-something"
    # Result on Linux/Mac: "/jobs/thing-something"

    # Both calls, 'regex' and ('regex', ), do the same thing
    context.get_str(resolve_with='regex')
    context.get_str(resolve_with=('regex', ))
    # Result on Windows: "C:\\Users\\\w+\\jobs\\w+_thing-\w+_\d{3}"
    # Result on Linux/Mac: "/jobs/\w+_thing-\w+_\d{3}"

If you've read the :doc:`why` link, this example will look familiar.

Immediately, you should take note of a few things. resolve_with=('env', 'regex')
will try to fill in the mapping with environment variables first, and
then fall back to regex if it can't. Changing resolve_with='regex', makes
get_str ignore any environment variables and grab only regex values.

The second important thing to note is that the regex for "JOB", which is
"\w+_\d{3}", wasn't actually defined in JOB. It was defined in Subtokens,
JOB_NAME_PREFIX and JOB_NAME_SUFFIX and JOB_ID. Ways composed that regex value
for JOB using its Subtokens. Like the name implies, a Subtoken is a Token that
is nested inside of another Token.

In docstrings, we refer to this as a "Child-Search". Ways also has a
"Parent-Search" which is exactly like "Child-Search" but instead of searching
for values down, it looks up at a Subtoken's parents. Both Child-Search and
Parent-Search are recursive.

Search methods like Parent/Child Search matter once you start getting into the
deeper parts of Ways, such as Asset objects. For now, just know that it exists.

::

    mapping = '/jobs/job_thing-something_123'
    asset = ways.api.get_asset(mapping, context='example/context')
    asset.get_value('JOB_NAME_SUFFIX')
    # Result: 'thing-something'

By the way, get_value can work on its own, *with or without regex*.
Regex is good to have but is not required.

Just like how mapping is used to find Contexts automatically when none is
given, mapping_details is used to find values for mapping automatically when
pieces are missing.


uuid
++++

.. code-block :: yaml

    plugins:
        something:
            hierarchy: foo/bar
            uuid: some_string_to_describe_this_plugin

This is just a string that Ways will use to refer to your plugin. It can be an
actual UUID (http://docs.python.org/3/library/uuid.html) or anything else, as
long as it's unique.

If you find yourself needing to troubleshoot a Context or Asset, some of the
tools that Ways has will require a UUID.

There's more information about this in :doc:`common_patterns` and
:doc:`troubleshooting`.


data
++++

data is a regular dictionary that gets loaded onto the Context once it is
first created. It's mostly just a place to store metadata onto and retrieve later.
You can also modify and add to data like a regular dictionary in a live Python
session to an extent.

There's two things you'll want to know about data before you use it.

The first is that there's a separation between "loaded" values and "user"
values. Loaded values come for the the plugin files that are registered to
Ways. These keys/values cannot be removed. Then there are user values, which
are keys that you can edit, add, and remove freely. You can change values from
the loaded plugin data but you cannot delete it.

If you ever need to go back to a Context's initial data, just call
Context.revert().


platforms
+++++++++

platforms refers to the operating system(s) that a plugin is allowed to run on.

Ways has two environment variables related to the "platforms" key,
WAYS_PLATFORM and WAYS_PLATFORMS.

WAYS_PLATFORM
*************

Every plugin has a set of platforms that it's allowed to run on. If one of the
platforms in the plugin matches the WAYS_PLATFORM environment variable, Ways
will use it. If WAYS_PLATFORM isn't defined, Ways will just use the computer's
OS, instead.

::
    plugins:
        explicit_star_platform:
            hierarchy: foo
            platforms:
                - '*'
        implicit_star_platform:
            hierarchy: bar
        some_platforms:
            hierarchy: fizz
            platforms:
                - linux
                - darwin

If "*" is a platform on a plugin, then it is automatically assumed that
the plugin works on everything. Any plugin with no platforms defined,
like "implicit_star_platform" will get "*" by default.

WAYS_PLATFORMS is the list of platforms that Ways knows about. It can be any
string that you'd like, separated by your OS path separator (":" in Linux, ";"
in Windows). If WAYS_PLATFORMS isn't defined, a default set of platforms if
given instead.

TODO : Write a very concise platform example

There's a really good example of how to use platforms in :ref:`crossplatforms`
if you'd like to see another example.


uses
++++

The difference between an absolute plugin and a relative plugin is whether or
not "uses" is defined. There's a lot to talk about when it comes to absolute
vs. relative plugins and it is explained on other pages so, in summary, for now
relative plugins can be explained as "plugins that create plugins". They're a
huge time saver and make Plugin Sheets easier to understand. For more
information on how they're built, check out :doc:`plugin_advanced` for details.


assignment
++++++++++

All plugins have assignments. If no assignment is given to a plugin when it
is first created, the plugin is given a default "master" assignment.

The assignment key is one of the most important keys because it
can drastically change how Ways runs in very little lines. In a single
sentence, assignment has the flexibility of "platforms" and the re-usability of
"uses". For more information on how to use them, check out
:doc:`plugin_advanced` for details.


.. _path_explanation:

path
++++

If you are developing a hierarchy that represents a filepath and you need to
support more than one type of OS (like Linux and Windows), it's best to set this
option to True.

On Linux, setting path forces "\\" in a mapping to "/".  On Windows, it
changes "/" to "\\".

Ways will use the OS you've defined in the WAYS_PLATFORM environment variable.
If that environment variable is not set, Ways will use your system OS.

The path key exists because path-related plugins are difficult to write for
more than one OS at a time. Take the next example. If we got the mapping for
"foo/bar", with the Plugin Sheet below, we get an undesired result on Windows.

.. code-block :: yaml

    plugins:
        path_plugin:
            hierarchy: foo
            mapping: '/jobs/{JOB}'
            platforms:
                - linux
        windows_path_root:
            hierarchy: foo
            mapping: 'Z:\jobs\{JOB}'
            platforms:
                - windows

        relative_plugin:
            hierarchy: '{root}/bar'
            mapping: '{root}/shots'
            uses:
                - foo

::

    context = ways.api.get_context('foo/bar')
    context.get_mapping()
    # Result on Linux: '/jobs/{JOB}/shots'
    # Result on Windows: 'Z:\jobs\{JOB}/shots'

The result on Windows is mixes "\\" and "/" because the relative plugin used "/".
If we include path: true, this isn't a problem.

.. code-block :: yaml

    plugins:
        path_plugin:
            hierarchy: foo
            mapping: '/jobs/{JOB}'
            platforms:
                - linux
        windows_path_root:
            hierarchy: foo
            mapping: 'Z:\jobs\{JOB}'
            platforms:
                - windows
        plugin_that_appends_path:
            hierarchy: foo
            path: true

        relative_plugin:
            hierarchy: '{root}/bar'
            mapping: '{root}/shots'
            uses:
                - foo

::

    context = ways.api.get_context('foo/bar')
    context.get_mapping()
    # Result on Linux: '/jobs/{JOB}/shots'
    # Result on Windows: 'Z:\jobs\{JOB}\shots'

The "foo" hierarchy is set as a path so its child hierarchy, "foo/bar" also
becomes a path. Now things work as we expect.

What Now?
+++++++++
Now that you know the basics of each key, head over to :doc:`plugin_advanced`
or :doc:`common_patterns` to see examples of these keys in examples.
