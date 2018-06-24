========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |requires|
        | |codecov| |codacy|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/ways/badge/?style=flat
    :target: https://readthedocs.org/projects/ways
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/ColinKennedy/ways.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/ColinKennedy/ways

.. |requires| image:: https://requires.io/github/ColinKennedy/ways/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/ColinKennedy/ways/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/ColinKennedy/ways/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/ColinKennedy/ways

.. |codacy| image:: https://api.codacy.com/project/badge/Grade/d1cf59fcfbc54733a7360e2cde26bf20
    :alt: Codacy Code Quality Status
    :target: https://www.codacy.com/app/ColinKennedy/ways?utm_source=github.com&utm_medium=referral&utm_content=ColinKennedy/ways&utm_campaign=badger

.. |version| image:: https://img.shields.io/pypi/v/ways.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/ways

.. |commits-since| image:: https://img.shields.io/github/commits-since/ColinKennedy/ways/v0.1.0b1.svg
    :alt: Commits since latest release
    :target: https://github.com/ColinKennedy/ways/compare/v0.1.0b1...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/ways.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/ways

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/ways.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/ways

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/ways.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/ways


.. end-badges

Ways is a pipeline tool for Python that helps users write code to be more
flexible to change. It was originally designed as a basic asset management
system (AMS) for file paths but now can mix with file paths, databases, and
third party APIs, all at once.

Ways links projects together so that, if a change needs to happen for multiple
projects at once, it can be done concisely, in one place, without the need to
re-deploy.

* Free software: MIT license


Installation
============

::

    pip install ways


Documentation
=============

The main documentation can be found here:

https://ways.readthedocs.io/

In particular, two good pages for newcomers are
https://ways.readthedocs.io/en/latest/summary.html
and
https://ways.readthedocs.io/en/latest/getting_started.html


Example
=======

The following is a (overly-)simplified excerpt from the documentation link, above.
Click https://ways.readthedocs.io to see the full details.

Ways is a Python toolkit which is supported by config files called "Plugin Sheets".
This is an example of a relatively simple Plugin Sheet.

::

    plugins:
        some_plugin:
            hierarchy: some/hierarchy
            mapping: /path/to/a/{JOB}/here

To make a `ways.api.Asset` from the Plugin Sheet that was written earlier,
you would use `ways.api.get_asset`.

::

    path = '/path/to/a/job_name/here'
    asset = ways.api.get_asset(path, context='some/hierarchy')
    # Result: <ways.api.Asset>


Extend Ways Using Actions
-------------------------

Asset objects can have functions added to the using something called "Action" objects

An Action is any callable object, class or function, that takes at least one
argument. The first argument given to an Action will always be the Asset that
called it.

There are two ways to create Action objects. Create a class/function and
"register" it to Ways or subclass `ways.api.Action`, and Ways
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
        ways.api.add_action(some_function, name='function', context='some/hierarchy')

    # Actually using the Actions
    context = ways.api.get_context('some/hierarchy')

    context.actions.some_action()
    context.actions.function()

Actions let the user link Contexts together, manipulate data, or
communicate between different APIs.


Mixing Ways with other APIs
---------------------------

Here's a production example where Ways creates filepaths, writes to disk,
queries paths from a database, and syncs them locally, using a program called
Autodesk Maya (pymel is an API for working with Maya)

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
            if node_.attr('setType').get() == 'rig':
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


Development
===========

To run all tests use::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox

If you're thinking of creating a feature request, file a bug report, or make
changes to the repository, check out ``CONTRIBUTING`` for instructions.
