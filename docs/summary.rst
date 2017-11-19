API Summary
===========

Here we will get a high-level summary of how Ways works.

Ways is an API that helps developers define and use Context and Asset objects.
Contexts and Assets aren't defined directly. Instead, they're instead generated
by Ways, automatically, from your input.

Your job as the user is to define plugins which will describe Context objects.
But, if needed, Contexts and Plugins can be defined and registered explicitly.

Plugin Sheets
-------------

Plugins Sheets are files on disk or on a server that describe a Context.
Defining a single plugin in a Plugin Sheet will make a Context available for use.
Adding more plugins will add to the existing Context.

Plugin Sheets can be JSON, YAML, or Python files.

.. _descriptor_summary:

Descriptor Objects
------------------

A Descriptor is an abstraction layer used to load Plugin Sheets. If provided with
a file path or folder, Ways generates Descriptor objects in the background so
the user doesn't need to worry about them. For most people, just knowing that
this functionality exists is enough.

That said, Descriptor objects can also query from databases or be given
some custom functionality. If you need a way to load Plugin Sheets that Ways
doesn't ship with, check out :doc:`descriptors` to learn how they work and
to create your own.

Plugins
-------

Once you've made your Descriptor objects, you will need to make a Plugin Sheet
to actually start writing Context objects. A Plugin Sheet is a file that
contains plugins + any global values for those plugins.

The way that Plugin Sheets are discovered and loaded is completely left up to
the Descriptors that you use. The ones that Ways ship with recognize JSON,
YAML, and Python files but you could easily support your own loading procedure
with a custom Descriptor class/subclass.

Descriptors are evaluated in the order they're added to the WAYS_DESCRIPTORS
environment variable and a Descriptor's Plugin Sheet load order is handled by
each Descriptor. Ways evaluates found Plugin Sheets in alphabetical order, by
default.

Whenever a user tries to create a Context, the Context's Plugin objects are
looked up as read-only data, combined, and then hooked into the Context.

Context Objects
---------------

Context objects are containers of metadata and Plugin information.

Plugins are loaded into a Context on-demand - so you could define a Plugin
Sheet, instantiate a Context object, and then add more Plugin Sheets /
Descriptors in middle of runtime and the original Context you instantiated
will already have the new Plugin settings without you having to do anything.

(It's not recommended to do this, of course, but Ways allows it).

There's a ton of things that you can use Context objects to do but to keep
this page short, the examples will stop here. Go to :doc:`getting_started`
to try it for yourself.

Asset Objects
-------------

TODO WRITE

Action Objects
--------------

Actions are classes or functions that attach to a Context. So two Contexts
could have two Actions called "do_some_action" and do completely different
things. You define the Action, the Context that it's meant to act upon, and that's it.

Head over to `getting_started` to learn about creating Descriptors, Contexts,
Actions, and more.
