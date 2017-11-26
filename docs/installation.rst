How To Install
==============

Install via PyPI
----------------

Installing the deployed versions of Ways is recommended. To install Ways, just
run:

::

    pip install ways


Install Locally
---------------

Run these commands

::

    git clone http://www.github.com/ColinKennedy/ways.git
    python ./ways/setup.py install

Verify that your installation works by running the Ways demo

::

    python -m ways.demo

Output:

::

    Hello, World!
    Found object, "Context"
    A Context was found, congrats, Ways was installed correctly!

Once you see those 3 lines, you're all set to begin.


Developing Locally
------------------

To get Ways to run locally without installing it directly onto the
machine, clone the repo from online.

::

    git clone http://www.github.com/ColinKennedy/ways.git
    cd ways
    git submodule update --init --recursive

Test that the repository cloned successfully by running

::

    tox

There should be a output from a number of environments, with each of them passing.
