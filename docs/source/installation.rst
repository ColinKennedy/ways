How To Install
==============

Run these commands

::

    set location=/some/folder/ways
    git clone http://www.github.com/ColinKennedy/ways.git $location
    cd $location
    git submodule init
    git submodule update --recursive
    pip install docs/source/rtfd-requirements.txt

Verify that your installation works by running the Ways demo

::

    python ways.demo

That's it.

