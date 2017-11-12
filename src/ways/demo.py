#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Test Ways to make sure that it works.'''

# IMPORT STANDARD LIBRARIES
import tempfile
import textwrap
import os

# IMPORT WAYS LIBRARIES
import ways.api


class ExampleAction(ways.api.Action):

    '''An example Action. It just prints something.'''

    name = 'tryme'

    @classmethod
    def get_hierarchy(cls):
        '''tuple[str]: The hierarchy that this Action will attach itself to.'''
        return ('example', 'hierarchy')

    def __call__(self, obj):
        '''Run something.'''
        print('Hello, World!')
        print('Found object, "{obj}"'.format(obj=obj.__class__.__name__))


def setup_file():
    '''Create a Plugin Sheet file and load it into Ways.

    Note:
        ways.api.add_search_path() is used add paths directly to Ways.
        Normally, we'd never want to do this. It's better to add the Plugin Sheet
        to the WAYS_DESCRIPTORS environment variable and auto-register the path.
        But to keep this demo simple, lets break the rules this one time.

    '''
    contents = textwrap.dedent(
        '''
        plugins:
            a_plugin:
                hierarchy: example/hierarchy

        ''')
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yml') as file_:
        file_.write(contents)

    ways.api.add_search_path(file_.name)

    return file_.name


def main():
    '''Run a quick test for Ways.'''
    sheet = ''

    try:
        sheet = setup_file()
        _main()
    except Exception:
        if sheet:
            # Cleanup the temp file
            os.remove(sheet)
        raise

    if sheet:
        # Cleanup the temp file
        os.remove(sheet)


def _main():
    '''Run a quick test for Ways.'''
    context = ways.api.get_context('example/hierarchy')
    context.actions.tryme()
    if isinstance(context, ways.api.Context):
        print('A Context was found, congrats, Ways was installed correctly!')


if __name__ == '__main__':
    main()

