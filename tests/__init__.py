'''A collection of all of the tests for Ways.

In this module, we set up the mock imports needed to run all of our tests.

'''

# IMPORT THIRD-PARTY LIBRARIES
import six

six.add_move(six.MovedModule('io', 'StringIO', 'io'))
six.add_move(six.MovedModule('mock', 'mock', 'unittest.mock'))
