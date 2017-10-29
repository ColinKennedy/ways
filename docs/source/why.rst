Why use Ways
================

The problem with writing code isn't actually writing it for the first time.
It's changing the code later that causes the most issues.
Over time, project requirements change. Dealing with these complexity-scenarios
is where Ways truly shines.

Anything that can be represented as a string can used with Ways.
Using Ways objects, the API can query data over a database,
build file paths, or even interface with other APIs.

Here are some immediate and practical examples that Ways can help you. If you
have ever written a tool that ...

- Read/Saves files to a specific location that needed to change later
- Parses information from a path or generic string to get back data
- Writes to disk in different places for varying deployments / environments
- Needed to stay consistent while working with other APIs
- Used a third-party API that later needed to be completely changed

A Basic Example - Parsing a file path
-------------------------------------

Without getting too deep into how to set up Ways just yet, lets just look at
how Ways can be used in a simple example.

Imagine you have a Ways Plugin Sheet file that looks like this:


plugin_sheet.yml

.. code-block :: yaml

    globals: {}
    plugins:
        foo_plugin:
            mapping: '/foo/{JOB}/bar/{SHOT}'
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
                        regex: 'part_\w+'
                JOB_ID:
                    parse:
                        regex: '\d{3}'
            hierarchy': 'some/context'

In this example, the keys below "mapping_details" are called Tokens. Tokens
can be named anything and contain any information. Tokens can also
contain other tokens. In the previous example, JOB contains JOB_NAME and JOB_ID.
JOB_NAME contains JOB_NAME_PREFIX and JOB_NAME_SUFFIX.

The most important item is "hierarchy". The hierarchy defines where
"foo_plugin" lives and the Context that will see thing plugin.

Using this file, Ways can get some patterns back for this Context.

::

    import ways.api
    context = ways.api.get_context('some/context')
    regex_pattern = context.get_str('JOB_NAME', 'regex')
    # Result: '\w+part_\w+'

Note: JOB_NAME doesn't have any regex rules, it just has a mapping.
But JOB_NAME has child Tokens in its mapping and each child Token has a regex
rule so we were able to get a value back for JOB_NAME, by building it.

.. note ::

    If you want to get information about a missing Token and that Token is a
    child of some parent Token which does, Ways can get the information needed
    by parsing the parent token. Ways can also build values for a parent Token
    if all of its child Tokens have values. These search types,
    (Child-Search and Parent-Search) work recursively for any number of Tokens.

Context and Asset Objects
-------------------------

This plugin and Context is nice but its description is too generic to be
useful. To make apply instance-specific data onto a Context, Ways comes with
Asset objects.

::

    path = '/foo/some_part_JobName_123/bar'
    asset = resource.get_asset(path, 'some/context')
    asset.get_value('JOB_NAME_SUFFIX')
    # Result: 'part_JobName'

    asset.get_value('JOB_ID')
    # Result: '123'

    # And we can still get the regex information back, too
    asset.get_token('JOB_ID')
    # Result: '\d{3}'

Asset objects are basically dicts that communicate with a Context's mapping.
This lets you store per-instance data on an Asset and still get all the power
of the Asset being "in-Context".

Actions
-------

There's Context and Asset objects but we still have no way of using them
in functions. To get the most out of these two classes, Action objects can be
defined which hook onto any Context or Asset object.

Like the name implies, an Action object can do anything and be anything, as
long as the object is callable.

TODO : remember ot mention and show that You can also define Actions ahead of plugins.

Defining an Action is a bit verbose so lets save the details for another
section. But just to give an impression of what they look like when used,
heres an example of Action objects in practice.

::

    # IMPORT THIRD-PARTY LIBRARIES
    import ways.api


    # Remember, anything that can be a string can be a Context - so lets make
    # a Context from a user-provided list
    #
    asset_information = ['some_job', 'shots', 'sh01', 'maya', 'animation', 'rnr010_Character_Running', '1']
    asset_path = '|'.join(asset_information)

    file_asset = ways.api.get_asset(asset_path)
    # Imagine that this points to a binary Maya file
    # Example: '/some/path/to/binary/file/with/assets/inside.mb'

    if not file_asset.actions.is_local():
        # get our asset from an external database
        file_asset.actions.sync(wait=True)

    new_asset.actions.increment_version()

    # Our file_asset only knows about file systems. To publish 'inside.mb',
    # we need to actually open the file to get its contents.
    #
    # Luckily, in this example, we have another Context which we can use.
    #
    maya_asset = file_asset.actions.read()
    for rig in maya_asset.actions.get_light_rigs(asset=True):
        maya_asset.actions.increment()
        rig.actions.publish(maya_asset)

    maya_asset.close()

In the above example, we went from having only a list of a user's GUI input to
querying a database for the missing asset, syncing it locally, opening a binary
file using a third-party API, and publishing a new version to the database in
only a few lines.

Of course, this example assumes that you've written functions for each Action
but the point is that Ways has a flexible enough to provide the tools to do that.

