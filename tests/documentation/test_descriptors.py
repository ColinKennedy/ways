#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORT STANDARD LIBRARIES
import os
import sys
import tempfile
import textwrap

# IMPORT WAYS LIBRARIES
import ways.api
from ways.base import cache
from ways.helper import common

# IMPORT LOCAL LIBRARIES
from .. import common_test


class DescriptorsTestCase(common_test.ContextTestCase):

    '''A mixed set of Descriptor-related tests.

    This class has no real organization - it's just meant for test coverage.

    '''

    def test_descriptor_function_return(self):
        '''Check that our example string creates a proper GitLocalDescriptor.'''
        root = tempfile.mkdtemp()
        folder = 'plugins'
        resolved_path = os.path.join(root, folder)

        os.makedirs(resolved_path)
        self.temp_paths.append(resolved_path)

        descriptor = 'path={root}&create_using=ways.api.GitLocalDescriptor&items=plugins' \
                     '&uuid=some_unique_string-we-can_search_for-later' \
                     ''.format(root=root)

        obj = cache._resolve_descriptor(descriptor)
        self.assertTrue(isinstance(obj, ways.api.GitLocalDescriptor))
        self.assertEqual(obj.path, root)
        self.assertEqual(obj.items, [resolved_path])

    def test_descriptor_rewrite(self):
        '''Change the begining example strings to URL encoded strings.'''
        folder_info = {
            'create_using': 'ways.api.FolderDescriptor',
            'items': ['/tmp/to/plugins/folder'],
        }

        yml_info = {
            'create_using': 'ways.api.FileDescriptor',
            'items': ['/tmp/to/plugin.yml'],
        }

        json_info = {
            'create_using': 'ways.api.FileDescriptor',
            'items': ['/tmp/to/plugin.json'],
        }

        py_info = {
            'create_using': 'ways.api.FileDescriptor',
            'items': ['/tmp/to/plugin.py'],
        }

        composite = [
            (
                folder_info,
                'items=%2Ftmp%2Fto%2Fplugins%2Ffolder&create_using=ways.api.FolderDescriptor',
                ways.api.FolderDescriptor
            ),
            (
                yml_info,
                'items=%2Ftmp%2Fto%2Fplugin.yml&create_using=ways.api.FileDescriptor',
                ways.api.FileDescriptor,
            ),
            (
                json_info,
                'items=%2Ftmp%2Fto%2Fplugin.json&create_using=ways.api.FileDescriptor',
                ways.api.FileDescriptor,
            ),
            (
                py_info,
                'items=%2Ftmp%2Fto%2Fplugin.py&create_using=ways.api.FileDescriptor',
                ways.api.FileDescriptor,
            )
        ]

        # TODO : nose!
        for info, encoding, class_item in composite:
            # Check to make sure the inspected encoding is OK
            details = common.conform_decode(ways.api.decode(encoding))
            self.assertEqual(info, details)
            desc1 = cache._resolve_descriptor(info)
            desc2 = cache._resolve_descriptor(encoding)
            self.assertEqual(desc1, desc2)
            self.assertTrue(isinstance(desc1, class_item))
            self.assertTrue(isinstance(desc2, class_item))

    def test_callable_descriptor(self):
        '''Make a Descriptor that is just a function and then load it.'''
        root = '/tmp/path/'
        sys.path.append(root)

        path = os.path.join(root, 'some_module.py')

        if not os.path.isdir(root):
            os.makedirs(root)

        contents = textwrap.dedent(
            '''
            import ways.api

            def some_function(*args, **kwargs):
                return [ways.api.Plugin()]
            '''
        )

        with open(path, 'w') as file_:
            file_.write(contents)
            self.temp_paths.append(path)

        info = 'path={path}&create_using=some_module.some_function&items=plugins' \
               ''.format(path=path.replace(os.sep, '%2F'))
        os.environ['WAYS_DESCRIPTORS'] = info
        ways.clear()
        ways.api.init_plugins()
        descriptor = cache._resolve_descriptor(info)
        self.assertEqual(1, len(descriptor))


class CustomPlugin(ways.api.Plugin):

    '''A Plugin.'''

    data = {'data': True}

    @classmethod
    def get_hierarchy(cls):
        '''('something', 'here').'''
        return ('something', 'here')


class CustomDescriptor(object):

    '''A Descriptor used for testing.'''

    @classmethod
    def get_plugins(cls):
        '''Get a plugin with an explicit assignment.'''
        return [(CustomPlugin(), 'master')]

    @classmethod
    def get_plugin_info(cls):
        '''Get some plugin info.'''
        return {'assignment': 'master', 'foo': 'bar'}


class CustomDescriptor1(object):

    '''A Descriptor used for testing.'''

    @classmethod
    def get_plugins(cls):
        '''Get a plugin without an explicit assignment.'''
        return [CustomPlugin()]

    @classmethod
    def get_plugin_info(cls):
        '''Get some plugin info.'''
        return {'assignment': 'master', 'foo': 'bar'}
