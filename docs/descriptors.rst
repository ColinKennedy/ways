Descriptors
===========

This section assumes that you've at least read through the Descriptor section
in the `Summary` page.

Basic setup
-----------

When Ways initializes, it gathers all of the Descriptor objects it can
find, using your environment.

The most basic Descriptor is usually a path to a folder or file.
All descriptors added to the WAYS_DESCRIPTORS environment variable are
loaded into Ways, by default.

Example:

TODO : Right now these docs are incorrect. A Python file needs to be added to
WAYS_PLUGINS. Not WAYS_DESCRIPTORS. In retrospect, I don't see the
need for both env vars because it caused even me some confusion earlier.
Maybe this should be made into one env var. OR NOT

TODOID : 5152

::
    export WAYS_DESCRIPTORS=/tmp/to/plugins/folder:/tmp/to/plugin.yml:/tmp/to/plugin.json:/tmp/to/plugin.py

The above example is 4 different ways to load a Plugin Sheet or file.
In each case, Ways will convert those paths to Descriptor objects and
then load the plugins that those objects find.

Descriptors Under The Hood
--------------------------

Custom Descriptors still use the WAYS_DESCRIPTORS environment variable the
same as a path-based Descriptor like we defined earlier but the string is a
standard URL encoding instead of a place on-disk.
For those who don't know, URL encoding is just way to serialize a dictionary
into a string, similar to JSON or YAML.

.. code-block :: json

    {
        "key1": "value1",
        "key2": "value2"
    }

Converts to

::

    key1=value1&key2=value2

Here's a real example of what a Ways custom Descriptor looks like:

::

    path=%2Fsome%2Fpath%2Fon%2Fdisk&class_type=ways.api.GitLocalDescriptor&items=plugins

This example string describes a local git repository.

when our cache unpacks this descriptor string, the result is a dict

::

    descriptor_info = {
        'create_using': 'ways.api.GitLocalDescriptor',
        'path': '/some/path/on/disk',
        'items': ('plugins', ),
    }

"create_using" is a the only reserved key in our dict. Ways uses
"create_using" to import the Descriptor object.
All other key/value pairs are passed to the Descriptor, directly.
It's worth noting that create_using can be any callable Python object. It could
be a function or a class, for example.

Knowing what you now know about Descriptors, the previous example with the 4
different ways to load Descriptors could technically be rewritten as URL strings.

::

    /tmp/to/plugins/folder
    items=%2Ftmp%2Fto%2Fplugins%2Ffolder&create_using=ways.api.FolderDescriptor

::

    /tmp/to/plugin.yml
    items=%2Ftmp%2Fto%2Fplugin.yml&create_using=ways.api.FileDescriptor

::

    /tmp/to/plugin.json
    items=%2Ftmp%2Fto%2Fplugin.json&create_using=ways.api.FileDescriptor

::

    /tmp/to/plugin.py
    items=%2Ftmp%2Fto%2Fplugin.py&create_using=ways.api.FileDescriptor

::

    export WAYS_DESCRIPTORS=/path/to/plugins/folder:/path/to/plugin.yml:/path/to/plugin.json:/path/to/plugin.py:/path/to/plugin/folder
    export WAYS_DESCRIPTORS=items=%2Ftmp%2Fto%2Fplugins%2Ffolder&create_using=ways.api.FolderDescriptor:items=%2Ftmp%2Fto%2Fplugin.yml&create_using=ways.api.FileDescriptor:items=%2Ftmp%2Fto%2Fplugin.json&create_using=ways.api.FileDescriptor:items=%2Ftmp%2Fto%2Fplugin.py&create_using=ways.api.FileDescriptor

It should be pretty obvious that the former syntax is easier to read than the
URL-encoding method. But the URL-encoding method is useful for whenever you need
a custom Descriptor load behavior.

Database Descriptors
--------------------

It was hinted at in the previous section that Ways supports reading
Git repositories directly, instead of using the filesystem. If storing Plugin
Sheet files locally isn't an option, reading from server is an alternative.

TODO Make an example repository and point to it, in this example.

Any callable object can be a Descriptor
+++++++++++++++++++++++++++++++++++++++

Any object that is callable (functions, methods, classes) can be a Descriptor.

::

    path=%2Ftmp%2Fpath%2Fsome_module.py&create_using=some_module.some_function&items=plugins

/tmp/path/some_module.py

::

    def some_function(*args, **kwargs):
        return [ways.api.Plugin()]

Ways will try to assume that the Descriptor object passed is a
class and run "get_plugins". If that fails, Ways tries to call the object,
directly, as though it was a function.

Custom Descriptors
++++++++++++++++++

If you have your own I/O requirements that Ways doesn't handle out of the
box, you can write your own Descriptor and use it.

Descriptors requires two methods to be supported by Ways:
One method to get Plugin objects and another method to display those objects's
information.

Ways expects and looks for a method named "get_plugins". If the Descriptor
object doesn't have a "get_plugins" method, then it must be callable. Either
way, the method's return should be a list of Plugin Objects. Every plugin found
will be given the assignment "master" by default unless you specify otherwise.

Here is an example of a custom Descriptor.

::

    class CustomDescriptor(object):
        def get_plugins(self):
            return [CustomPlugin()]

In this example, the Descriptor will always return one plugin, CustomPlugin().
This Plugin object will be given the assignment of "master" (or whatever
ways.api.DEFAULT_ASSIGNMENT is). If you need the Plugin to go to a different
assignment, just specify it in get_plugins.

::

    class CustomDescriptor(object):
        def get_plugins(self):
            return [(CustomPlugin(), 'foo')]

The method used to display objects's information is optional but highly
recommended because it's needed for some of Ways's more advanced features.
It should be called "get_plugin_info" and return a dict with any data about the
Plugins that can't be stored on the Plugins, themselves. For example,
the default implementation of Ways looks for a file called
".ways_plugin_info" in directories on or above wherever Plugin Sheets
are loaded.

::

    import ways.api

    class CustomPlugin(ways.api.Plugin):

        data = {'data': True}

        @classmethod
        def get_hierarchy(cls):
            return ('something', 'here')

    class CustomDescriptor(object):
        def get_plugins(self):
            return [(CustomPlugin(), 'master')]

        def get_plugin_info(self):
            return {'assignment': 'master', 'foo': 'bar'}

The last things to do are to make sure that CustomDescriptor is importable on
the PYTHONPATH and it can be used like any other Descriptor.

Custom descriptors can be called using URL syntax using WAYS_DESCRIPTORS or
by including a python file in WAYS_PLUGINS and registering the descriptor,
directly. Either method will work.

::

    info = {
        'create_using': 'ways.tests.test_documentation.CustomDescriptor',
    }
    ways.api.add_descriptor(info)
    context = ways.api.get_context('something/here')
    print(context.data['data'])
    # Result: {'data': True}

