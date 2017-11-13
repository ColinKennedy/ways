Plugin Basics
=============

Plugin Sheets are the backbone of Ways. They define many plugins in very few
lines and drive how Ways will parse your objects.

Because Plugin Sheets have a finite list of keys that it can use,
it's important to know what each of them are called and what they do.

All Plugin Sheet Keys
---------------------

This is a "Hello World" Plugin Sheet. The only things that are required is a
single value under "plugins" and that value must have a "hierarchy" defined.

.. code-block :: yaml

    plugins:
        some_plugin:
            hierarchy: example

Here is an example of a very complicated Plugin Sheet. The file contains every
key that you can use. This is a bit like getting thrown into the deep-end of a
pool but don't worry if not everything makes sense immediately. It'll all be
explained.

For reference, this is a YAML file. YAML is used in this example because it's
pretty easy to read and follow but Ways also supports JSON and Python files.

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

        config_plugin:
            hierarchy: "{root}/config"
            mapping: "{root}/configuration"
            uses:
                - example/hierarchy
                - example/hierarchy/tree
            uuid: as_Long_as_It_is_Different

        some_assigned_plugin:
            assignment: different_assignment
            hierarchy: something
            data:
                important_information: here
            uuid: boo


Clearly there is a big difference between a "Hello World" Plugin Sheet and
this one. The good news is, everything in the complex sheet is technically
optional so feel free to use this page as a reference as you get more familiar
with how Ways works.

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

This is the only required plugin-level key. The value that's defined for
hierarchy must be a string, separated by "/"s, even if you're using Windows.
The hierarchy is used later to get a Context or Asset so it's important that
this is named sensibly.


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

"mapping" is just a string that describes where this plugin should live. The
complex example above treats its mapping like it's a filepath but mapping can
be anything. For example, it's very common to have some plugins use "/" to
show that a mapping is meant to be a filepath and "." to show that it's meant
to be a database. For practical examples of what this looks like, see
:doc:`common_patterns`.

Once you've moved on from Contexts and start using Asset objects, a Context's
mapping is used to automatically find Context objects.

::

    mapping = '/jobs/job_part_something'

    explicit_asset = ways.api.get_asset(mapping, context='example/hierarchy')
    autofound_asset = ways.api.get_asset(mapping)
    explicit_context == autofound_context
    # Result: True

For situations where all you have is input to an Asset and you don't know what
the right Context should be, mapping is something necessary. The mapping and
uuid keys are always a good idea to define.

mapping_details
+++++++++++++++

Ways likes to call any item in "{}"s within a mapping a "Token".
Above, "/jobs/{JOB}" has a "JOB" Token and "C:\\Users\\{USER}\\jobs\\{JOB}" has
"USER" and "JOB" Tokens.

Tokens look like a regular Python format but behave differently, in Ways.

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
for JOB using its Subtokens. A Subtoken is a Token that is nested inside of
another Token.

In docstrings, this is referred to as a "Child-Search". Ways also has a
"Parent-Search" which is exactly like "Child-Search" but instead of searching
for values down, it looks up at a Subtoken's parents. Both Child-Search and
Parent-Search are recursive.

Search methods like Parent/Child Search matter once you start getting into the
deeper parts of Ways, such as Asset objects.

::

    mapping = '/jobs/job_thing-something_123'
    asset = ways.api.get_asset(mapping, context='example/context')
    asset.get_value('JOB_NAME_SUFFIX')
    # Result: 'thing-something'

We never defined what JOB_NAME_SUFFIX was but we can find it because JOB has a
mapping. By the way, get_value can work on its own, *with or without regex*.
Regex is good to have but is not required to do this.

Just like how mapping is used to find Contexts automatically when none is
given, mapping_details is used to find values for mapping automatically when
pieces are missing.

uuid
++++

This is just a unique string that Ways will use to refer to your plugin. For
example, if you are getting unexpected results from a Context or Asset, it's
good to be able to search for plugins by UUID to find what Descriptor loaded
them and where the issue is happening. It's completely optional but it helps
while debugging. There's more information about this in :doc:`troubleshooting`.

data
++++

data is a regular dictionary that gets loaded onto the Context once it is
first created. It's mostly just a convenience attribute to store metadata onto.
It's useful while working with a Context to have a place to store items onto
the Context and retrieve later. You can also modify and add to data like a
regular dictionary in a live Python session to an extent.

There's two notes about data before you use it.

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

Ways determines which plugins to run based on which plugins match the user's
platform. The platform that Ways uses is set with the WAYS_PLATFORM environment
variable. If nothing is set, Ways will use the system OS returned by
platform.system().lower(). If "*" is a listed platform on a plugin, then it is
automatically assumed that the plugin works on everything. "*" is the default
platform if no platform(s) is given for a plugin.

The defined platforms can be any string you'd like. As long as one of the
plugin's platforms matches the user's platform, Ways will load the plugin.

platforms is very important for dealing with file paths. Say you wanted to make
100 plugins for Windows, Linux, and Mac. If you defined each plugin
absolutely, that'd be 300 plugins and each time one changed, the other two
would need to be changed. Because Ways only recognizes one platform at a time,
it lets the user write 100 relative plugins and 3 absolute, OS-based plugins.
At runtime, 1 of the 3 OS-based plugins are picked and the other 100 relative
plugins append to it.


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
