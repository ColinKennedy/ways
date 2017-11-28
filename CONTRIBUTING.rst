==================
Contributors Guide
==================

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.


Installation
============

To get Ways to run locally, clone the repo from online.

    git clone http://www.github.com/ColinKennedy/ways.git
    cd ways
    git submodule update --init --recursive

Test that the repository cloned successfully by running

::

    tox


The latest commit in the "master" branch should have passing tests.

You can also verify that your installation works by running the Ways demo file.

::

    python -m ways.demo

Output:

::

    Hello, World!
    Found object, "Context"
    A Context was found, congrats, Ways was installed correctly!

Once you see those 3 lines, you're all set to begin.


Reporting Issues
================

Before reporting issues, check to make sure that you've installed Ways and try
to run its unittests. If every unittest passes and you still have your issue,
please `use this URL to submit your issue <https://github.com/ColinKennedy/ways/issues>`_.


Documentation Improvements
==========================

Ways could always use more documentation, whether as part of the
official Ways docs, in docstrings, or even on the web in blog posts,
articles, and such.


Feature Requests And Feedback
=============================

The best way to send feedback is to file an issue at
https://github.com/ColinKennedy/ways/issues.

If you are proposing a new feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)


Before You Submit The Issue
===========================

**Check the docs before reporting an issue**. It may have already been addressed.

**Make sure you're running the latest version of Ways**. The issue may be fixed already.

**Search the issue tracker for similar issues**. If you think your issue is still
important enough to raise, do so, but link to the related tickets, too.


When You Write The Issue
========================

1. If your problem is involved with an environment set up, please include a
   compressed archive (.zip/.rar/.tar/.etc) containing all of the files needed
   and write steps to reproduce your problem.
2. Add the output of gways.api.trace_all_descriptor_results_info` and
   :func:`ways.api.trace_all_plugin_results_info` as a text file or link.
3. Write a test case for your issue. It helps a lot to just pick up a test
   and make that test pass so that the issue won't happen again in the future.
4. Include your WAYS_PLATFORMS and WAYS_PLATFORM environment variables, if
   those environment variables have any information, as well as your OS and OS version.


Maintainer Notes
================

If you're considering adding features to Ways, the very first thing to do would
be to clone the main repository. See ``README`` for details.


Repository Structure
++++++++++++++++++++

Ways uses a cookiecutter tox environment. For more details, check out
the GitHub repo that Ways was built from for details:

https://github.com/ionelmc/cookiecutter-pylibrary


Pull Requests
+++++++++++++

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, keep these things in mind:

1. Write easy to read/maintain code.

    - K.I.S.S. Ways gets by using very few classes and very simple ideas.
      If you're adding a class or a complex system, think about why you think
      you need it, first.
    - Ways has many working parts. It tries its best to not make any assumptions
      about Context mapping strings or anything else. Any OS-dependent changes
      (like adding functions to convert "/" or "\\\\", just as an example) will
      be met with caution.

2. Write tests for your changes

    At the time of writing, its coverage is over 90% so lets keep it up!

3. Explain why your pull request is needed

   This project was written by a single person, with a very specific pipeline
   in mind. There's bound to be ideas here that aren't going to translate as
   well for your pipeline needs. If you can explain what your change does and
   how it adds value, more power to you!

To make sure your changes work with the rest of the Ways environment, run

::

    tox

The tox environment that Ways comes with has some commands for pylint,
pydocstyle and the like. If you want to only run those, use

::

    tox -e check

If tox passes [1]_, you're almost ready.

1. Update documentation when there's new API, functionality etc.
2. Add a note to ``CHANGELOG.rst`` about the changes.
3. Add yourself to ``AUTHORS.rst``.


api.py
++++++

If the pull request contains new functions or classes, consider adding them to
api.py and explain why you think they'd be a good addition.


Tips
----

To run a subset of tests::

    tox -e envname -- py.test -k test_myfeature

To run all the test environments in *parallel* (you need to ``pip install detox``)::

    detox


.. [1] If you don't have all the necessary python versions available locally you can rely on Travis - it will
       for each change you add in the pull request. It will be slower than running locally though ...
