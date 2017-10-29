========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/ways/badge/?style=flat
    :target: https://readthedocs.org/projects/ways
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/ColinKennedy/ways.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/ColinKennedy/ways

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/ColinKennedy/ways?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/ColinKennedy/ways

.. |requires| image:: https://requires.io/github/ColinKennedy/ways/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/ColinKennedy/ways/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/ColinKennedy/ways/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/ColinKennedy/ways

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

An string-based AMS toolkit for Python

* Free software: MIT license

Installation
============

::

    pip install ways

Documentation
=============

https://ways.readthedocs.io/

Development
===========

To run the all tests run::

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
