ways package
============

Ways is split into two main sections. "ways" and "ways.api". Of the two, 99% of
all your work is going to use classes and functions out of "ways.api" but in
the exceptional case where you need to do something special, You'd use the
parent module's functions.

Main Module
-----------

ways.api is where you should import from. All other modules add their public
classes and functions into ways.api so it contains almost everything that you'd
need to work.

.. toctree::
    ways.api <api>

Inner Modules
-------------

.. toctree::
    :maxdepth: 2

    ways.api <api>
    ways.cache <cache>
    ways.commander <commander>
    ways.common <common>
    ways.connection <connection>
    ways.descriptor <descriptor>
    ways.dict_classes <dict_classes>
    ways.engine <engine>
    ways.factory <factory>
    ways.finder <finder>
    ways.parse <parse>
    ways.plugin <plugin>
    ways.resource <resource>
    ways.situation <situation>
    ways.trace <trace>


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
    ways.retro

