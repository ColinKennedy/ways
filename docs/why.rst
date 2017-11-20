Why use Ways
============

The problem with writing code isn't actually writing it for the first time.
It's changing code later that causes the most issues.
Project requirements change or I/O can out of hand, forcing multiple
tools to update with new changes to the code.

Dealing with these complexity-scenarios is where Ways truly shines.


Basics
------

Ways is a Python toolkit that is supported by config files called "Plugin
Sheets". This is an example of a relatively simple Plugin Sheet.

.. code-block :: yaml

    plugins:
        some_plugin:
            hierarchy: some/hierarchy
            mapping: /path/to/a/{JOB}/here

This Plugin Sheet is written using YAML but it can implemented using Python or
JSON, as well. The important bit here is the "hierarchy" key. The string used
there is what we'll use to get Context and Asset objects in other examples.

.. note ::

    Context and Asset objects are written in detail in other pages so, for now,
    just know that Context objects help you get plugin data and Asset objects
    wrap Contexts with extra functionality.

To make a Context and Asset, you would use ways.api.get_context and
ways.api.get_asset.

::

    path = '/path/to/a/job_name/here'
    asset = ways.api.get_asset(path, context='some/hierarchy')
    asset.get_value('JOB')
    # Result: 'job_name'


Extend Ways Using Actions
-------------------------

Context and Asset objects have very few methods by default and almost every
method just queries information defined in a Plugin Sheet.  To actually write
methods that use a Context or Asset, we need to define an Action for it.

An Action is a callable object, class or function, that takes at least one
argument. The first argument given to an Action will always be the Asset or
Context that called it.

::

    # Method #1: Subclass ways.api.Action
    class SomeAction(ways.api.Action):

        name = 'some_action'

        def __callable__(self, context):
            print('Hello, World!')

        @classmethod
        def get_hierarchy(cls):
            return 'some/hierarchy'

    # Method #2: Register a function or class, explicitly
    def some_function():
        print('Hello, World, again!')

    ways.api.register_action(some_function, name='function', context='some/hierarchy')

    # Actually using the Actions
    context = ways.api.get_context('some/hierarchy')

    context.actions.some_action()
    context.actions.some_function()

Actions let the user link Contexts together, manipulate data, or
communicate between different APIs.


Mixing Ways with other APIs
---------------------------

Many examples in this and other pages are for writing tools for filepaths. This
is just to keep the examples easy to understand. The truth is, in practice,
if you're using Ways to deal just with filepaths, it won't provide that many
benefits over just querying values from a database.

But Ways doesn't need to represent paths on disk, Ways can represent anything
as long as it can be broken down into a string.

A common situation that comes up in the VFX industry is that tools frequently
need to be written that deals with a filesystem, a database, and some third-party
Python API at once.

For example, say an artist published a new version of a texture on a job's
database and we wanted to republish a 3D model with those new textures.

(This example assumes a basic understanding of the tools of VFX artists.
Example: Maya is a 3D modeling and animation tool and PyMEL is a Python API
used in Maya)


::

    import pymel.core as pm
    import ways.api


    def get_asset(node):
        '''A function to wrap any supported Maya node into a Ways Asset.'''
        class_name = node.__class__.__name__
        context = 'dcc/maya/{}'.format(class_name)
        return ways.api.get_asset({'uuid': node.get_uuid()}, context=context)


    node = pm.selected()[0]  # Use the Maya API to get our selected texture
    texture = get_asset(node)

    # Now use the database to lookup the published versions of the texture
    asset = texture.actions.get_database_asset()

    # Get the path of the published texture, add it to our local disk, and set it
    version = asset.actions.get_latest_version()
    path = version.actions.get_filepath()

    if not os.path.isfile(path):
        print('Syncing: "{path}" from the database.'.format(path=path))
        version.actions.sync()

    asset.actions.set_path(path)

    # Now we need to find the rig(s) that contain this texture to republish
    rig_sets = [node_ for node_ in pm.sets(query=True)
                if 'setType' in node_.listAttrs() and
                node_.attr('setType') == 'rig']

    rigs = []
    for rig_node in rig_sets:
        rig = get_asset(rig_node)
        if not rig:
            continue

        if rig.actions.contains(texture):
            rig.actions.publish()  # Add back to the database


These sort of API mixtures are possible because Contexts have a very clearly
defined hierarchy. In the below example, different hierarchies and mapping are
used to describe a database Context, filepath Context, and a Maya-Node Context.

.. code-block :: yaml

    plugins:
        # Maya plugins
        node_object:
            hierarchy: dcc/maya
            mapping: "{uuid}"
            mapping_details:
                uuid:
                    parse:
                        regex: "[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}"

        # Texture-related nodes
        file_node:
            hierarchy: "{root}/nodes/file"
            uses:
                - dcc/maya

        database_root:
            # get_database_asset, under the hood, fills in the info in mapping
            # and then returns another Ways Asset with its own set of Actions.
            #
            hierarchy: db/asset
            mapping: db.{SHOT}.{ASSET_NAME}

The above example only works with Maya "File" nodes. If we wanted to support
other Maya nodes, it'd be as simple adding a plugin for that node under the
"# Texture-related nodes" section and then adding an Action for the hierarchy
called "set_path".

The best way to use Ways, in my experience, is to let Ways "suggest" filepaths
while exporting data from your tools, publish to a database with the same
paths, and then use the database to query those published paths when needed.

String Querying
---------------

A basic use of Ways would be to get data from a file path. Normally you might do
something like this to split a path and get its pieces.

::

    def get_parts(path):
        return path.split(os.sep)


    def get_environment_info(path):
        '''Parse a path of format "/jobs/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}".'''
        parts = os_path_split_asunder(path)

        return {
            'JOB': parts[2],
            'SCENE': parts[3],
            'SHOT': parts[4],
            'DISCIPLINE': parts[4],
        }


::

    path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
    info = get_environment_info(path)
    print(info['JOB'])
    # Result: 'someJobName_123'

Here is the same example, using Ways.
Start by making a Plugin Sheet. We'll call this Plugin Sheet "plugin_sheet.yml".

.. code-block :: yaml

    plugins:
        foo_plugin:
            hierarchy: job/shot/discipline
            mapping: /jobs/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}

Add "plugin_sheet.yml", to your WAYS_DESCRIPTORS environment variable.

::

    export WAYS_DESCRIPTORS=/path/to/plugin_sheet.yml

This is what using our plugin in Python would look like

::

    import ways.api

    path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
    asset = ways.api.get_asset(path)
    print(asset.get_value('JOB'))
    # Result: 'someJobName_123'

Now for some bad news - We need our setups to work with Windows.
Here we're writing code for Windows and Linux.

::

    # Reference: https://stackoverflow.com/questions/4579908
    def os_path_split_asunder(path, debug=False):
        parts = []
        while True:
            newpath, tail = os.path.split(path)
            if debug: print repr(path), (newpath, tail)
            if newpath == path:
                assert not tail
                if path: parts.append(path)
                break
            parts.append(tail)
            path = newpath
        parts.reverse()
        return parts

    def get_environment_info(path):
        '''Parse a path of format "/jobs/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}".'''
        parts = os_path_split_asunder(path)

        return {
            'JOB': parts[2],
            'SCENE': parts[3],
            'SHOT': parts[4],
            'DISCIPLINE': parts[4],
        }

::

    path1 = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
    info1 = get_environment_info(path1)
    print(info1['JOB'])
    # Result on Linux/Mac: 'someJobName_123'

    path2 = r'\\NETWORK\jobs\someJobName_123\shot_name-Info\sh01\animation'
    info2 = get_environment_info(path2)
    print(info2['JOB'])
    # Result on Windows: 'someJobName_123'

This can be done with Ways, too.


.. code-block :: yaml

    plugins:
        windows_root:
            hierarchy: job
            mapping: "Z:\\"
            platforms:
                - windows
        linux_root:
            hierarchy: job
            mapping: /jobs
            platforms:
                - linux
        discipline:
            hierarchy: '{root}/shot/discipline'
            mapping: '{root}/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}'
            uses:
                - job

::

    import ways.api

    path1 = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
    asset1 = ways.api.get_asset(path1)
    print(asset1.get_value('JOB'))
    # Result on Linux: 'someJobName_123'

    path2 = r'Z:\jobs\someJobName_123\shot_name-Info\sh01\animation'
    asset2 = ways.api.get_asset(path2)
    print(asset2.get_value('JOB'))
    # Result on Windows: 'someJobName_123'

The "discipline" key uses "job" hierachy and "job" is defined differently
depending on the user's OS.

Lets add some more complexity - Now our project needs to be able to query the
"Info" part from SCENE because "Info" is useful to us.

::

    def get_scene_info(job):
        return job.split('-')[-1]

    path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
    info = get_environment_info(path)
    print(get_scene_info(info['SCENE']))
    # Result: 'Info'


Using "split('-')" is definitely not ideal because we're forcing a specific
convention on the code that would need to be enforced in any other tool. But we
don't have much of a choice. It's either that, use regex or another text
parser.

To make it easier for other tools to follow the same convention, we could
make "-" a global variable or read in from a config file. That will help but,
either way, getting "Info" becomes a a very granular task. Imagining what kinds
of paths that our program expects without documentation becomes more difficult,
as well.

Now again, lets tackle the same problem, using Ways.

.. code-block :: yaml

    plugins:
        windows_root:
            hierarchy: job
            mapping: "Z:\\"
            platforms:
                - windows
        linux_root:
            hierarchy: job
            mapping: /jobs
            platforms:
                - linux
        discipline:
            hierarchy: "{root}/shot/discipline"
            mapping: "{root}/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}"
            mapping_details:
                SCENE:
                    mapping: "{SCENE_PREFIX}-{SCENE_INFO}"
            uses:
                - job

::

    import ways.api

    path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
    asset = ways.api.get_asset(path)
    print(asset.get_value('SCENE_INFO'))
    # Result: 'Info'


Between the previous example and this one, only 3 new lines were added.

::

    mapping_details:
        SCENE:
            mapping: "{SCENE_PREFIX}-{SCENE_INFO}"

The first example required a new function to be added to parse the string.
Ways can do the same thing by adding 3 lines into a YAML file.

There's a lot more to learn about parsing - we haven't talked at all about how
Ways can handle querying missing data or how it integrates other parse engines
like regex and glob. These topics are pretty dense so for now lets skip it.
But, if you need to, you can read all about it in :doc:`parsing`.


Adding Existing AMS
-------------------

Most likely, Ways is not the first AMS solution you've tried. Chances are, you
have your own AMS that you'd ideally like to keep using. Plugins/Contexts are a
very core part of how Ways works but the return value of "get_asset" can be
anything. You can just as well add your AMS objects to Ways and use those,
instead.

::

    class MyAssetClass(object):
        '''Some class that is part of an existing AMS.'''

        def __init__(self, context):
            super(MyAssetClass, self).__init__()
            # ... more code ...

    ways.api.register_asset_class(MyAssetClass, context='some/hierarchy')

Now when you run "get_asset", the function will return MyAssetClass.
For more information on register_asset_class, check out :ref:`asset_swapping`.


Dealing With Revised Projects
-----------------------------

You're working on a tool that publishes rendered images to a database. Because
you were only working for yourself, you made a function to parse your path:

(Example path:
"/jobs/{JOB}/{SCENE}/{SHOT}/elements/{NAME}/{VERSION}/{LAYER}/{SEQUENCE_NAME}"
"/jobs/fooJob/fooScene/sh01/elements/frame_Render/v001/beauty/file_sequence.####.tif")

::

    def get_sequence_info(path):
        '''Parse a path like get_environment_info.'''
        TODO write

    def publish(info):
        '''Publish to the database with our info.'''
        # Do the publish to our database ...

    path = "/jobs/{JOB}/{SCENE}/{SHOT}/elements/frame_Render/v001/beauty/file_sequence.####.tif"
    info = get_sequence_info(path)
    info['path'] = path

    publish(info)

Lets just pretend for a moment that this example suited our needs. Maybe
instead get_sequence_info would actually use some regex or something to make
the paths easier to parse. The point is that, whatever the solution it, it's
good enough for your tool.


If we used Ways, this is what the same example could look like.

.. code-block :: yaml

    plugins:
        linux_root:
            hierarchy: job
            mapping: /jobs
        element:
            hierarchy: '{root}/shot/element'
            mapping: '{root}/{JOB}/{SCENE}/{SHOT}/elements'
            uses:
                - job
        sequence_bit:
            hierarchy: '{root}/rendered/sequence'
            mapping: '{root}/{NAME}/{VERSION}/{LAYER}/{SEQUENCE_NAME}'
            uses:
                - job/shot/element

Now that we've made the plugins needed for our path, we make an Action object
to do the publish.

::

    class PublishAction(ways.api.Action):

        name = 'publish'

        @classmethod
        def get_hierarchy(cls):
            return 'job/shot/element'

        def __callable__(info):
            '''Publish to the database with our info.'''
            # Do the publish to our database ...

::

    path = '/jobs/fooJob/fooScene/sh01/elements/frame_Render/v001/beauty/file_sequence.####.tif'
    asset = ways.api.get_asset(path)
    asset.actions.publish()

Another developer on your team developed a tool that depends on published images
too but their tool uses very different paths and your tool from earlier needs to
accomodate those paths.

You've been putting files in

"/jobs/{JOB}/{SCENE}/{SHOT}/elements/{NAME}/{VERSION}/{LAYER}/{SEQUENCE_NAME}"

but the other developer has been putting similar files in

"/jobs/{JOB}/{SCENE}/{SHOT}/elements/plates/houdini/{NAME}_{VERSION}/{VERSION}/{LAYER}/file_sequence.####.tif"


Now you're in a bad situation. The other developer is adding files in a
completely different folder with a different number of folders, and a slightly
different naming convention than your tool expected.

You can't rely on your database to get information from these paths because
neither paths have actually been published yet - just rendered to disk.

TODO Write a fix for this "situation"

In Ways, the same situation can be solved by just writing a new plugin

.. code-block :: yaml

    plugins:
        linux_root:
            hierarchy: job
            mapping: /jobs
        element:
            hierarchy: '{root}/shot/element'
            mapping: '{root}/{JOB}/{SCENE}/{SHOT}/elements'
            uses:
                - job
        sequence_bit:
            hierarchy: '{root}/rendered/sequence'
            mapping: '{root}/{NAME}/{VERSION}/{LAYER}/{SEQUENCE_NAME}'
            uses:
                - job/shot/element
        houdini_rendered_plugin:
            hierarchy: '{root}'/rendered/sequence/houdini'
            mapping: '{root}/plates/houdini/{NAME}_{VERSION}/{VERSION}/{LAYER}/file_sequence.####.tif'
            uses:
                - job/shot/element

.. code-block :: yaml

    houdini_rendered_plugin:
        hierarchy: '{root}'/rendered/sequence/houdini'
        mapping: '{root}/plates/houdini/{NAME}_{VERSION}/{VERSION}/{LAYER}/file_sequence.####.tif'
        uses:
            - job/shot/element

Adding houdini_rendered_plugin was all we needed to do.
Now we can publish those paths without changing anything else.

::

    path1 = "/jobs/fooJob/fooScene/sh01/elements/frame_Render/v001/beauty/file_sequence.####.tif"
    path2 = "/jobs/{JOB}/{SCENE}/{SHOT}/elements/plates/houdini/frame_render_001/v1/rgba/file_sequence.####.tif"
    asset1 = ways.api.get_asset(path1)
    asset2 = ways.api.get_asset(path2)

    asset1.actions.publish()
    asset2.actions.publish()

When no context is given to "get_asset", Ways will guess the "best"
possible Context for whatever information you do give it. If the information
was a string like in our example and the string matches a Context's mapping,
this guess will always be correct. So even though all we have is a path to some
sequence on disk, Ways gets the right Context and the right Asset for us and we
don't have to care about the path's structure and just "publish" like normal.

Both plugins, "sequence_bit" and "houdini_rendered_plugin" share the same root
hierarchy, "job/shot/element". That root hierarchy has a "publish" action
defined so its child hierarchies also get the same Action.

Our new edit was only 5 extra lines in the config file and nothing else needed
to be changed to support that other developer's tools.


Split Deployment
----------------

Sometimes even the perfect tool must change. Maybe the client has a special job
that needs to ingest filepaths from a different location.

So normally, your tool would point to one filepath, "/some/filepath/here" but
for one specific setup, it needs to "/some/other/path/here". And both setups
are in use at the same time.

Depending on your environment's setup, this may not be trivial to do.
Thankfully though, it is trivial to do in Ways, by using something that Ways
calls "plugin assignment". It's an advanced feature that isn't often used.

A couple sections in another page, :ref:`assignments_basics` is dedicated to
show how to do this so, if you're curious how it works, check it out there.


String Searching
----------------

TODO write!
.. When you've found yourself stuck






