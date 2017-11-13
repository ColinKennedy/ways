Advanced Plugin Topics
======================

Relative Plugins
----------------

One of the most fundamental ideas about Plugin Sheets is that there are two
types of plugins, relative plugins and absolute plugins.

The most bare-minimum absolute plugin looks like this:

.. code-block :: yaml

    plugins:
        absolute_plugin:
            hierarchy: fizz/buzz

The plugin contains just one item, "hierarchy", which is the position of the
Plugin for when it gets built into a Context.

A bare-minimum relative plugin looks like this

.. code-block :: yaml

    plugins:
        absolute_plugin:
            hierarchy: fizz
        relative_plugin:
            hierarchy: '{root}/buzz'
            uses:
                - fizz

A relative plugin can also refer to another relative plugin recursively,
as long as the end of that chain of plugins is an absolute plugin.

Calling a plugin "relative" is a bit of a inaccurate. Relative plugins are
not single plugins - they're a group of plugins. Each hierarchy listed
under "uses", will create a separate Plugin object.

.. note ::
    {root} is only supported on a plugin's hierarchy and mapping but it is also
    not required. If no {root} is given, Ways will just append the
    relative plugin's mapping and hierarchy to its parent. If you do provide
    {root} though, you get to define different places for the parent's data
    to be inserted, like this: "parent/{root}/library/{root}/hierarchy".

"uses" has a couple details that are important to know before starting.

1. uses should never give a relative plugin its own hierarchy.
   For example, these setups are invalid:

.. code-block :: yaml

    plugins:
        relative:
            mapping: something
            hierarchy: some/place
            uses:
                - some/place

.. code-block :: yaml

    plugins:
        absolute:
            mapping: whatever
            hierarchy: foo
        relative:
            mapping: "{root}/something"
            hierarchy: "{foo}/bar"
            uses:
                - foo/bar

2. Relative plugins can be chained together, as long as one of the plugins
   is tied to an absolute plugin.

.. code-block :: yaml

    plugins:
        absolute_plugin:
            hierarchy: fizz
        relative_plugin1:
            hierarchy: '{root}/buzz'
            uses:
                - fizz
        relative_plugin2:
            hierarchy: '{root}/foo'
            uses:
                - fizz/buzz

The initial setup for relative plugins is a bit verbose but has its advantages.
The main advantage is re-useability.

Here is an example of how absolute plugins and relative plugins differ.

+---------------------------------------------+---------------------------------------------------------------+
| Relative                                    | Absolute                                                      |
+---------------------------------------------+---------------------------------------------------------------+
| .. code-block :: yaml                       | .. code-block :: yaml                                         |
|                                             |                                                               |
|     plugins:                                |     plugins:                                                  |
|         absolute_plugin:                    |         absolute_plugin:                                      |
|             hierarchy: fizz                 |             hierarchy: fizz                                   |
|             mapping: bar                    |             mapping: bar                                      |
|                                             |                                                               |
|         relative_plugin1:                   |         absolute_plugin1:                                     |
|             hierarchy: '{root}/buzz'        |             hierarchy: fizz/buzz                              |
|             mapping: '{root}/something'     |             mapping: bar/something                            |
|             uses:                           |                                                               |
|                 - fizz                      |         absolute_plugin1_library:                             |
|                                             |             hierarchy: fizz/buzz/library                      |
|         absolute_plugin2:                   |             mapping: bar/something/library                    |
|             hierarchy: '{root}/pop'         |                                                               |
|             mapping: '{root}/another/thing' |         absolute_plugin2:                                     |
|             uses:                           |             hierarchy: fizz/buzz/pop                          |
|                 - fizz/buzz                 |             mapping: bar/something/another/thing              |
|                                             |                                                               |
|         absolute_plugin3:                   |         absolute_plugin2_library:                             |
|             hierarchy: '{root}/fizz'        |             hierarchy: fizz/buzz/pop/library                  |
|             mapping: '{root}/sets'          |             mapping: bar/something/another/thing/library      |
|             uses:                           |                                                               |
|                 - fizz/buzz/pop             |         absolute_plugin3:                                     |
|                                             |             hierarchy: fizz/buzz/pop/fizz                     |
|         library:                            |             mapping: bar/something/another/thing/sets         |
|             hierarchy: '{root}/library'     |                                                               |
|             mapping: '{root}/library'       |         absolute_plugin3_library:                             |
|             uses:                           |             hierarchy: fizz/buzz/pop/fizz/library             |
|                 - fizz                      |             mapping: bar/something/another/thing/sets/library |
|                 - fizz/buzz                 |                                                               |
|                 - fizz/buzz/pop             |                                                               |
|                 - fizz/buzz/pop/fizz        |                                                               |
+---------------------------------------------+---------------------------------------------------------------+

.. That table is dedication! You're welcome! :)

Both examples create the same exact Plugins.

So to compare the two examples - the relative plugin example took more lines
to create the absolute plugin version. If this example were longer however,
the relative plugin version would come out shorter because each line in "uses"
is 3 lines in the absolute version.

Also, if we needed to change something in "library", we only need to
change one plugin in the relative system, whereas in an absolute system,
you would need to change it in 3 places.

.. note ::
    When Ways loads Plugins, all Plugins are "resolved" into absolute
    Plugin objects.

Designing For Cross-Platform Use
--------------------------------

If you're using Ways to build Context objects for your filesystem, you
may have to consider supporting multiple operating systems.

Say you have two paths that represent the same place on-disk in Windows and in
Linux: /jobs/someJobName_123/library and
Windows: \\\\NETWORK\\jobs\\someJobName_123\\library.

You might be tempted to write your plugins like this:

.. code-block :: yaml

    plugins:
        linux:
            mapping: /jobs
            hierarchy: job
        windows:
            mapping: \\NETWORK\jobs\someJobName_123\library
            hierarchy: job
        linux_library:
            mapping: /jobs/someJobName_123/library
            hierarchy: job/library
        windows_library:
            mapping: \\NETWORK\jobs\someJobName_123\library
            hierarchy: job/library
        linux_library_reference:
            mapping: /jobs/someJobName_123/library/reference
            hierarchy: job/library/reference
        windows_library_reference:
            mapping: \\NETWORK\jobs\someJobName_123\library\reference
            hierarchy: job/library/reference

This works but you wanted to keep data consistent across both plugins, you'd be
forced to write separate plugins for each OS and each feature.

To make the process easier, just use relative plugins

.. code-block :: yaml

    plugins:
        job_root_linux:
            hierarchy: job
            mapping: /jobs
            platforms:
                - linux

        job_root_windows:
            hierarchy: job
            mapping: \\NETWORK\jobs
            platforms:
                - windows

        library:
            hierarchy: '{root}/library'
            mapping: '{root}/someJobName_123/library'
            uses:
                - job

        reference:
            hierarchy: '{root}/reference'
            mapping: '{root}/reference'
            uses:
                - job/library

When two plugins have the same hierarchy but different platforms, the "correct"
plugin for the user's OS is used. The "correct" plugins is chosen based on the
WAYS_PLATFORM environment variable. If it is not defined, the user's
system OS is used.

.. note ::

    In our previous example, the relative plugin called "library" will make the
    appropriate Plugin object that matches the user's OS. If the OS is Windows,
    the mapping for the plugin will convert "/" to "\\".


Appending To Plugins
--------------------

Say for example you have a plugin in another file that you want to add to. You
have two options to do this, an absolute append or a relative append.

You can do this using a relative plugin, but isn't generally a good idea
because its syntax is harder to follow

.. code-block :: yaml

    plugins:
        some_plugin:
            hierarchy: foo/bar
            mapping: something
        append_plugin:
            hierarchy: ''
            data:
                some_data: 8
            uses:
                - foo/bar

Appending with an absolute plugin is much simpler.

.. code-block :: yaml

    plugins:
        some_plugin:
            hierarchy: foo/bar
            mapping: something
        append_plugin:
            hierarchy: foo/bar
            data:
                some_data: 8

So in conclusion, absolute and relative plugins both have their pros and cons.
Pick the right one for the right job.

Other than plugin platforms, there's one other way to affect the discovery and
runtime of plugins in Ways: assignments.

Using Assignments
-----------------

Whenever a Plugin is defined, its hierarchy is defined and if no assignment is
given, ways.DEFAULT_ASSIGNMENT is used, instead.

Ways assignments allow users to change the way plugins resolve at runtime.

First lets explain the syntax of assignments and then explain how this works in
a live environment.

There are 3 ways to define assignments to a plugin. Each one is a matter of
convenience/preference and is no better than the other.

Assigning To Multiple Plugin Sheets
+++++++++++++++++++++++++++++++++++

With the default Ways Descriptor classes, if you have a file called
".waypoint_plugin_info" in the same directory or above a Plugin Sheet,
any assignment listed is used.

".waypoint_plugin_info" can be JSON or YAML.

Examples:

::

    >>> cat .waypoint_plugin_info.json
    >>> {
    >>>     "assignment": master,
    >>>     "recursive": false
    >>> }

::

    >>> cat .waypoint_plugin_info.yml
    >>> assignment: master
    >>> recursive: false

.. note ::
    "recursive" defines if we will search for Ways Plugin Sheets in
    subfolders. For more information, `seealso environment_setup.rst`

The assignment in this file will apply to all plugins in all Plugins Sheets at
the same directory or below the ".waypoint_plugin_info" file.

Assigning To A Plugin Sheet
+++++++++++++++++++++++++++

You can add an assignment to every plugin in a Plugin Sheet, using "globals"

.. code-block :: yaml

    globals:
        assignment: bar
    plugins:
        some_plugin:
            hierarchy: some/hierarchy
        another_plugin:
            hierarchy: another/hierarchy

All plugins listed now have "job" assigned to them. Using "globals" takes
priority over any assignment in a ".waypoint_plugin_info" file.

Assigning To A Plugin
+++++++++++++++++++++

If an assignment is directly applied to a plugin, then it is used over any
other assignment method.

.. code-block :: yaml

    plugins:
        another_plugin:
            hierarchy: another/hierarchy
            assignment: job


Applied Assignments - Live Environments
---------------------------------------

Whenever you call a Context, you must give a hierarchy and an assignment.
If no assignment is given, Ways "searches" for plugins in every assignment
that it knows about, defined in the WAYS_PRIORITY environment variable.

.. code-block :: bash

    export WAYS_PRIORITY=master:shot:job

In the above example, "master" plugins are loaded first, then "job"
plugins, and then "shot" plugins.

To take advantage of this in a live environment, here is a short example.

master.yml

.. code-block :: yaml

    plugins:
        job:
            hierarchy: job
            mapping: '/jobs/{JOB}'
        shot:
            hierarchy: '{root}/shot'
            mapping: '{root}/{SCENE}/{SHOT}'
            uses:
                - job
        plates:
            hierarchy: '{root}/plates'
            mapping: '{root}/library/graded/plates'
            uses:
                - job/shot
        client_plates:
            hierarchy: '{root}/client'
            mapping: '{root}/clientinfo'
            uses:
                - job/shot/plates
        compositing:
            hierarchy: '{root}/comp'
            mapping: '{root}/compwork'
            uses:
                - job/shot/plates


Here, we didn't define an assignment and we have no
".waypoint_plugin_info.(yml|json)" file, so ways.DEFAULT_ASSIGNMENT (master)
is given to every Plugin.

Now define the WAYS_PRIORITY

sh/bash

.. code-block :: bash

    export WAYS_PRIORITY=master:job

csh/tcsh

.. code-block :: tcsh

    setenv WAYS_PRIORITY master:job

Add a folder or file location to the WAYS_DESCRIPTORS environment variable
where we're going to look for "job-specific" Plugin Sheets.

.. code-block :: bash

    export WAYS_DESCRIPTORS=/path/to/master.yml:/path/to/job/plugins

The last step is to add a 'job'-assigned Plugin Sheet to the
/path/to/job/plugins folder.

jobber.yml

.. code-block :: yaml

    globals:
        assignment: job
    plugins:
        job_plugin:
            hierarchy: '{root}/plates'
            mapping: '{root}/archive/plates'
            uses:
                - job/shot


Now let's see this in a live environment

::

    # Both get_context versions do the same thing, because assignment='' by default
    context = ways.api.get_context('job/shot/plates/client', assignment='')
    context = ways.api.get_context('job/shot/plates/client')
    context.get_mapping()
    # Result: "/jobs/{JOB}/{SCENE}/{SHOT}/archive/plates/clientinfo"

Before adding jobber.yml to our system, the mapping was
"/jobs/{JOB}/{SCENE}/{SHOT}/library/graded/plates/clientinfo". Now, it's
"/jobs/{JOB}/{SCENE}/{SHOT}/archive/plates/clientinfo".

This works because the "job_plugin" key in jobber.yml matches the same hierarchy
as the "plates" key in master.yml.

jobber.yml comes after master.yml and its assignment loads after, so it
overwrote the hierarchy plugins in master.yml. All of the relative plugins that
depend on "job/shot/plates" now have a completely different mapping.


Now consider this
+++++++++++++++++

If one project has their WAYS_DESCRIPTORS set to this:

.. code-block :: bash

    export WAYS_DESCRIPTORS=/path/to/master.yml

And another project includes the job-assignment folder:

.. code-block :: bash

    export WAYS_DESCRIPTORS=/path/to/master.yml:/path/to/job/plugins/jobber.yml

The two projects could have completely different runtime behaviors despite
having the exact same Python code.

Or maybe instead of having projects point to different files on disk, you have
a job-based environment like this.

.. code-block :: bash

    export WAYS_DESCRIPTORS=/jobs/$JOB/config/ways

Maybe one job is called "foo" and another is called "bar".

/jobs/foo/config/ways and /jobs/bar/config/ways could have different Plugin
Sheet files customized for each job's needs.

With just a single, 8 line file, Ways's plugin resolution can completely change.

