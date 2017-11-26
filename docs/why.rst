Why use Ways
============

The problem with writing code isn't actually writing it for the first time.
It's changing code later that causes the most issues.
Project requirements change or I/O can out of hand. Depending on the changes
needed, multiple tools might need to be updated at once.

Dealing with these complexity-scenarios is where Ways truly shines.


Basics
------

Ways is a Python toolkit which is supported by config files called "Plugin Sheets".
This is an example of a relatively simple Plugin Sheet.

.. code-block :: yaml

    plugins:
        some_plugin:
            hierarchy: some/hierarchy
            mapping: /path/to/a/{JOB}/here

This Plugin Sheet is written using YAML but it can written in Python or JSON, too.
The important bit in this Plugin Shet is the "hierarchy" key. The string used
there is what we'll use to get Context and Asset objects in other examples.

.. note ::

    This page will reference "Context" and "Asset" objects a lot.
    (:class:`ways.api.Context` and :class:`ways.api.Asset`).

    They're both explained in other pages so, for now, just know that Context
    objects help get plugins and Asset objects add functionality to Context objects.

To make a Context and Asset from the Plugin Sheet that was written earlier,
you would use :func:`ways.api.get_context` and :func:`ways.api.get_asset`.

::

    path = '/path/to/a/job_name/here'
    asset = ways.api.get_asset(path, context='some/hierarchy')
    asset.get_value('JOB')
    # Result: 'job_name'


.. _creating_actions :

Extend Ways Using Actions
-------------------------

Context and Asset objects have very few methods by default and almost every
method just queries information defined in a Plugin Sheet. To actually write
methods that use a Context or Asset, we need to define an Action for it.

An Action is any callable object, class or function, that takes at least one
argument. The first argument given to an Action will always be the Asset or
Context that called it.

There are two ways to create Action objects. Create a class/function and
"register" it to Ways or subclass :class:`ways.api.Action`, and Ways
will register it for you.

::

    # Method #1: Subclass ways.api.Action
    class SomeAction(ways.api.Action):

        name = 'some_action'

        def __call__(self, context):
            return 8

        @classmethod
        def get_hierarchy(cls):
            return 'some/hierarchy'

    # Method #2: Register a function or class, explicitly
    def some_function(obj):
        return 8

    def main():
        ways.api.add_action(some_function, name='function', hierarchy='some/hierarchy')

    # Actually using the Actions
    context = ways.api.get_context('some/hierarchy')

    context.actions.some_action()
    context.actions.function()

Actions let the user link Contexts together, manipulate data, or
communicate between different APIs.


Mixing Ways with other APIs
---------------------------

Many examples in this page and others use Ways to describe filepaths. This
isn't a requirement for Ways, it's just to keep examples simple. The truth is,
in practice, if you're using Ways only to deal with filepaths, Ways won't be
much better than a database.

But Ways doesn't need to represent paths on disk, Ways can represent anything
as long as it can be broken down into a string.

A common situation that comes up in the VFX industry is that tools need to
communicate with a filesystem, a database, and some third-party Python API at once.

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

    # Get the path of the published texture and add it to the local disk
    version = asset.actions.get_latest_version()
    path = version.actions.get_filepath()

    if not os.path.isfile(path):
        print('Syncing: "{path}" from the database.'.format(path=path))
        version.actions.sync()

    asset.actions.set_path(path)

    # Now we need to find the rig(s) that contain this texture to republish
    rig_sets = []
    for node_ in pm.sets(query=True):
        try:
            if node_.attr('setType') == 'rig':
                rig_sets.append(node_)
        except pm.MayaAttributeError:
            pass

    rigs = []
    for rig_node in rig_sets:
        rig = get_asset(rig_node)

        if not rig:
            continue

        if rig.actions.contains(texture):
            rig.actions.publish(convert_to='geometry_cache')  # Publish the new version


These sort of API mixtures are possible because of the "hierarchy" key
mentioned earlier. Each Context knows about their own hierarchy, the hierarchy
of its parent Context, and all child Contexts by looking through its hierarchy
which you have full control over.

.. code-block :: yaml

    plugins:
        database_root:
            # get_database_asset, under the hood, fills in the info in mapping
            # and then returns another Ways Asset with its own set of Actions.
            #
            hierarchy: db/asset
            mapping: db.{SHOT}.{ASSET_NAME}

        # filepath-related plugin
        textures_output:
            hierarchy: job/shot/textures/release
            # This is an example filepath to publish our texture to
            mapping: "{JOB}/{SCENE}/{SHOT}/releases/{ASSET}_v{VERSION}/{texture}"

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
            hierarchy: "dcc/maya/nodes/File"

The above example only works with Maya "File" nodes. If we wanted to support
other Maya texture-related nodes, all we'd have to do is add them to this
Plugin Sheet and then implement a "set_path" Action for them.


String Querying
---------------

A basic use of Ways would be to get data from a file path. Normally you might do
something like this to split a path and get its pieces.

::

    def get_parts(path):
        return path.split(os.sep)


    def get_environment_info(path):
        '''Parse a path of format "/jobs/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}".'''
        parts = get_parts(path)

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
            path: true

Add the path to "plugin_sheet.yml", to your WAYS_DESCRIPTORS environment variable.

::

    export WAYS_DESCRIPTORS=/path/to/plugin_sheet.yml

This is what using our plugin in Python would look like

::

    import ways.api

    path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
    asset = ways.api.get_asset(path)
    print(asset.get_value('JOB'))
    # Result: 'someJobName_123'

Now for some bad news - We need our setup to work with Windows. And worse,
the Windows-equivalent path for "/jobs/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}"
has a different number of folders so our old function cannot work for both
("\\\\\\NETWORK\\server1\\jobs\\{JOB}\\{SCENE}\\{SHOT}\\{DISCIPLINE}").

But in Ways, these sort of changes only require a slight change in our Plugin Sheets.

.. code-block :: yaml

    plugins:
        windows_root:
            hierarchy: job
            mapping: "\\\\NETWORK\\jobs"
            path: true
            platforms:
                - windows
        linux_root:
            hierarchy: job
            mapping: /jobs
            path: true
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

    path2 = r'\\NETWORK\jobs\someJobName_123\shot_name-Info\sh01\animation'
    asset2 = ways.api.get_asset(path2)
    print(asset2.get_value('JOB'))
    # Result on Windows: 'someJobName_123'

This works because the "discipline" plugin key uses "job" and "job" is
defined differently for each OS. To support other operating systems, you write
once for each OS and just append any information you need onto it.


String Parsing
++++++++++++++

Now our project needs to be able to query the "Info" part from SCENE because
"Info" is useful to us.

If we're doing a non-Ways solution, like using built-in Python functions or
regex, your solution may look something like this:

::

    def get_scene_info(scene):
        '''str: Get the "Info" part of some scene.'''
        return scene.split('-')[-1]

    path = '/jobs/someJobName_123/shot_name-Info/sh01/animation'
    info = get_environment_info(path)
    print(get_scene_info(info['SCENE']))
    # Result: 'Info'


Using "split('-')" is definitely not ideal because we're forcing a specific
convention on the code that will need to be consistent for all of our other
tools.

We could make "-" a global variable or read in from a config file and that
will help but, either way, getting "Info" becomes a a very granular task.

Imagining what kinds of paths that our program expects without documentation
becomes more difficult, as well.

Lets tackle the same problem, using Ways.

.. code-block :: yaml

    plugins:
        windows_root:
            hierarchy: job
            mapping: "\\\\NETWORK\\jobs"
            path: true
            platforms:
                - windows
        linux_root:
            hierarchy: job
            mapping: /jobs
            path: true
            platforms:
                - linux
        discipline:
            hierarchy: '{root}/shot/discipline'
            mapping: '{root}/{JOB}/{SCENE}/{SHOT}/{DISCIPLINE}'
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


.. code-block :: yaml

    mapping_details:
        SCENE:
            mapping: "{SCENE_PREFIX}-{SCENE_INFO}"

There's a lot more to learn about parsing. Ways can handle querying missing
data or integrate other parse engines like regex and glob. Most of those topics
are pretty dense so lets skip it for now.
But, if you want to know more, you can skip ahead to :doc:`parsing`.


Adding Existing AMS
-------------------

Most likely, Ways is not the first AMS (Asset Management System) tool you've used.
Chances are, you have your own AMS that you'd like to keep using. Ways can
partially integrate existing objects into its own code to help tie into
existing systems.

::

    class MyAssetClass(object):

        '''Some class that is part of an existing AMS.'''

        def __init__(self, info, context):
            super(MyAssetClass, self).__init__()
            # ... more code ...

    def main():
        ways.api.register_asset_class(MyAssetClass, context='some/hierarchy')

    asset = ways.api.get_asset({}, context='some/hierarchy')
    # Result: <MyAssetClass>

Now when you run "get_asset", the function will return MyAssetClass.
For more information on register_asset_class, check out :ref:`asset_swapping`.


Dealing With Revised Projects
-----------------------------

Imagine that you're working on a tool that publishes images to a database.
Because you were only working for yourself, you made a function to parse your path:

(Example path:
"/jobs/{JOB}/{SCENE}/{SHOT}/elements/{NAME}/{VERSION}/{LAYER}/{SEQUENCE_NAME}"
"/jobs/fooJob/fooScene/sh01/elements/frame_Render/v001/beauty/file_sequence.####.tif")

::

    def get_sequence_info(path):
        '''Parse a path like get_environment_info.'''
        # ... get the info ...

    def publish(info):
        '''Publish to the database with our info.'''
        # Do the publish to our database ...

    path = "/jobs/{JOB}/{SCENE}/{SHOT}/elements/frame_Render/v001/beauty/file_sequence.####.tif"
    info = get_sequence_info(path)
    info['path'] = path

    publish(info)

Lets just pretend for a moment that this example did everything we
needed to do. Maybe get_sequence_info is some regex or another parser.
The point is that, whatever the solution it, it's good enough for the tool
that you're writing.


If we used Ways, this is what the same example could look like.

.. code-block :: yaml

    plugins:
        linux_root:
            hierarchy: job
            mapping: /jobs
            path: true
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

        def __call__(self, info):
            '''Publish to the database with our info.'''
            # ... do the publish ...

::

    path = '/jobs/fooJob/fooScene/sh01/elements/frame_Render/v001/beauty/file_sequence.####.tif'
    asset = ways.api.get_asset(path)
    asset.actions.publish()

Another developer on your team may have developed a tool that depends on those
published images too but their tool uses very different paths from yours and
you are being asked to accomodate those paths to.

You've been putting files in

"/jobs/{JOB}/{SCENE}/{SHOT}/elements/{NAME}/{VERSION}/{LAYER}/{SEQUENCE_NAME}"

but the other developer has been putting similar files in

"/jobs/{JOB}/{SCENE}/{SHOT}/elements/plates/houdini/{NAME}_{VERSION}/{VERSION}/{LAYER}/file_sequence.####.tif"


Now you're in a bad situation. The other developer is adding files in a
completely different folder with a different number of folders, and a slightly
different naming convention than what your tool expected.

You can't rely on your database to get information from these paths because
neither paths have actually been published yet - just rendered to disk.

In Ways, the same situation can be solved by just writing a new plugin

.. code-block :: yaml

    plugins:
        linux_root:
            hierarchy: job
            mapping: /jobs
            path: true
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
            hierarchy: '{root}/rendered/sequence/houdini'
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

.. note ::

    When no context is given to "get_asset", Ways will guess the "best"
    possible Context for the information you give it.

    If the information was a string and it matches a Context's mapping,
    this guess will always be correct.

    There's more information about this in :ref:`mapping_basics` and :ref:`autofind_pattern`.

Both plugins, "sequence_bit" and "houdini_rendered_plugin", share the same
hierarchy - "job/shot/element". "job/shot/element" has a "publish" Action
defined for it so our new hierarchy in "job/shot/element/rendered/sequence/houdini"
can also reuse the same Action.


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
