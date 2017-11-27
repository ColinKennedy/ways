Changelog
=========

0.1.0 (YYYY-MM-DD)
------------------

* Added documentation
  - Common Patterns And Best Practices
  - Plugin Basics
  - Advanced Plugin Topics
  - Contributors Guide
  - Troubleshooting Ways
  - Fixed module documentation and added unittests
* Reorganized modules
  - The flat list of files have been divided and moved to
    "base", "helper", and "parsing" folders.
* Removed regex requirement from parsing Tokens and added it back in
  as an optional extension
* Added trace methods to use for debugging
* Added demo.py - A file that can be used to test if Ways is working
* Created logic to "auto-find" Context objects whenever the user tries to run
  ways.api.get_asset without an explicit Context set


0.1.0b1 (2017-10-28)
--------------------

* First release on PyPI.
