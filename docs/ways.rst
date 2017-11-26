ways package
============

Ways is split into two main sections. :mod:`ways` and :mod:`ways.api`. Of the two, 99% of
all your work is going to use classes and functions out of :mod:`ways.api` but in
the exceptional case where you need to do something special, You'd use the
parent module's functions.

Main Module
-----------

ways.api is where almost every function and class is added to and contains
everything that you'd need to work with Ways.

.. toctree::
    ways.api <api>

Inner Modules
-------------

.. toctree::
    :maxdepth: 2

    ways.api <api>
    ways.base.cache <cache>
    ways.base.commander <commander>
    ways.base.connection <connection>
    ways.base.descriptor <descriptor>
    ways.base.factory <factory>
    ways.base.finder <finder>
    ways.base.plugin <plugin>
    ways.base.situation <situation>

    ways.helper.common <common>
    ways.helper.dict_classes <dict_classes>

    ways.parsing.engine <engine>
    ways.parsing.parse <parse>
    ways.parsing.registry <registry>
    ways.parsing.resource <resource>
    ways.parsing.trace <trace>
    ways.parsing.tracehelper <tracehelper>

Module contents
---------------

.. automodule:: ways
    :members:
    :undoc-members:
    :show-inheritance:


Subpackages
-----------

.. toctree::

    ways.core

