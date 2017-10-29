#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Any function that needs to exist in more than one of the finder modules.'''

# IMPORT STANDARD LIBRARIES
import glob
import os
import re

# IMPORT LOCAL LIBRARIES
from . import cache


# TODO : This function could use more unittests and a facelift
def find_context(path, sort_with='', resolve_with=('glob', ), search=glob.glob):
    '''Get the best Context object for some path.

    Important:
        This function calls cache.HistoryCache.get_all_contexts(), which is a
        very expensive method because it is instantiating every Context for
        every hierarchy/assignment that is in the cache. Once it is run though,
        this method should be fast because the flyweight factory for each
        Context will just return the instances you already created.

    Args:
        path (str):
            The relative or absolute path to use to find some Context.
        sort_with (:obj:`str`, optional):
            The method for sorting.

            Options are: ('default', 'levenshtein-pre', 'levenshtein')
            Default: 'default'.
        resolve_with (tuple[str]):
            The methods that can be used to resolve this context.

            Options are:
                [('glob', ), ('env', ), ('env', 'glob'), ('glob', 'env')]

            regex matching is not supported, currently.
            Default: ('glob', ).
        search (callable[str]):
            The function that will be run on the resolved Context mapping.
            We search for path in this function's output to figure out if the
            Context and path are a match.

    Raises:
        NotImplementedError:
            If resolve_with gets bad options.
        ValueError:
            If the sort_with parameter did not have a proper implementation or
            if the picked implementation is missing third-party plugins that
            need to be installed.

    Returns:
        <ways.api.Context> or NoneType: The matched Context.

    '''
    def sort_with_levenshtein_before_expand(contexts, path):
        '''Sort all contexts based on how similar their mapping is to path.

        Args:
            contexts (list[<ways.api.Context>]):
                The Context objects to sort.
            path (str):
                The path which will be used as a point of reference for our
                string algorithm.

        Raises:
            ValueError:
                This function requires the python-Levenshtein package
                to be installed.

        Returns:
            list[<ways.api.Context>]: The sorted Context objects.

        '''
        try:
            import Levenshtein
        except ImportError:
            raise ValueError('Cannot use a Levenshtein algorithm. '
                             'It was not installed')

        def levenshtein_sort(context):
            '''Compare the Context mapping to our path.

            Returns:
                float:
                    A ratio, from 0 to 1, of how closely the Context object's
                    mapping resembles the given path.

            '''
            mapping = context.get_mapping()

            # Remove all tokens (example: i/am/a/{TOKEN}/here)
            # so that our results are skewed by any of the token's contents
            #
            mapping_replace = re.sub('({[^{}]*})', mapping, '')
            return Levenshtein.ratio(mapping_replace, path)

        return sorted(contexts, key=levenshtein_sort)

    def do_not_sort(contexts):
        '''Do not sort any Context object and just return them all.'''
        return contexts

    path = os.path.normcase(path)

    resolve_options = [('glob', ), ('env', ), ('env', 'glob'), ('glob', 'env')]
    if resolve_with not in resolve_options:
        raise NotImplementedError('resolve_with: "{res}" is not valid for '
                                  'the find_context method. Options were, '
                                  '"{opt}".'.format(res=resolve_with,
                                                    opt=resolve_options))
        # TODO : I 'could' add 'regex' support but only if I can guarantee
        #        there are required tokens, {}s left to expand. Maybe sometime
        #        later

    if sort_with == '':
        sort_with = 'default'

    sort_types = {
        'default': do_not_sort,
        'levenshtein-pre': sort_with_levenshtein_before_expand,
        'levenshtein': sort_with_levenshtein_before_expand,
    }

    try:
        sort_type = sort_types[sort_with]
    except KeyError:
        raise ValueError('Sort type: "{sort}" is invalid. Options were: "{opt}".'
                         ''.format(sort=sort_with, opt=sort_types.keys()))

    # Process each Context until a proper Context object is found
    history = cache.HistoryCache()
    rearranged_contexts = sort_type(history.get_all_contexts())
    for context in rearranged_contexts:
        found_paths = search(context.get_str(resolve_with=resolve_with))
        if path in found_paths:
            return context


if __name__ == '__main__':
    print(__doc__)

