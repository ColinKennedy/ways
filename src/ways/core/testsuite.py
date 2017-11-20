#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Discover and run the Python test files in this package.'''

# IMPORT STANDARD LIBRARIES
import unittest


def discover_and_run():
    '''Look in the tests/test_*.py folder for unittests and run them all.'''
    loader = unittest.TestLoader()
    tests = loader.discover('tests')
    runner = unittest.TextTestRunner()
    runner.run(tests)


if __name__ == '__main__':
    discover_and_run()
