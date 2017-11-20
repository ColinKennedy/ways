#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Various functions for grouping sequences of integers.'''

# IMPORT STANDARD LIBRARIES
import itertools

# IMPORT THIRD-PARTY LIBRARIES
from six import moves


def has_common_elements(*args):
    '''bool: Tests a variable number of sequences for common elements.'''
    for index, seq in enumerate(args):
        try:
            seq2 = args[index + 1]
        except IndexError:
            break

        try:
            next(index for index in seq if index in seq2)
        except StopIteration:
            return False
    return True


def pairwise(iterable):
    "Change an iterable item in to pairs -> (s0,s1), (s1,s2), (s2, s3), ..."
    first, second = itertools.tee(iterable)
    next(second, None)
    return moves.zip(first, second)


def grouper(obj):
    '''Group a list together by its items.

    Slightly different result than ranges, in cases where outlier items lie
    between two ranges.

    Example:
        >>> list(ranges([0, 1, 2, 3, 4, 7, 10, 12, 14, 16]))
        >>> [xrange(0, 4, 1), xrange(10, 16, 2)]

    Args:
        obj (iterable): The list (or iterable) to process

    Returns:
        list[int or tuple]: The ranges from the given list

    '''
    result = []
    for key, group in itertools.groupby(pairwise(obj), key=lambda x: x[1] - x[0]):
        group = list(group)
        if len(group) > 1:
            if result and group[0][0] == result[-1]:
                del result[-1]
            result.append((group[0][0], group[-1][-1], key))
        else:
            result.append(group[0][-1])
    return result


def ranges(obj, return_range=True):
    '''Get the start and end ranges for a list of discontinuous int ranges.

    Reference: http://stackoverflow.com/questions/39709606/

    Example:

        >>> list(ranges([0, 1, 2, 3, 4  7, 10, 12, 14, 16]))
        >>> [xrange(0, 4, 1), 7, xrange(10, 16, 2)]

    Args:
        obj (list[int]): A list of integers to get the sequence of
        return_range (bool): If you just need an iterable and you don't care
                             about keeping the start/end/step, setting to True
                             is more efficient on memory. If False, returns
                             a tuple with start, end, and step.

    Yields:
        [int or range or tuple]: The ranges from the given list

    '''
    iterobj = iter(obj)
    next(iterobj)  # move to second element for comparison
    grps = itertools.groupby(obj, key=lambda x: (x - next(iterobj, -float("inf"))))
    for _, value in grps:
        index = next(value)
        try:
            step = next(value) - index  # catches single element v or gives us a step
            nxt = list(next(grps)[1])
            if return_range:
                yield moves.range(index, nxt.pop(0), step)
            else:
                yield (index, nxt.pop(0), step)
            # outliers or another group
            if nxt:
                if len(nxt) == 1:
                    yield nxt[0]
                else:
                    output = (nxt[0], next(next(grps)[1]), nxt[1] - nxt[0])
                    if return_range:
                        yield moves.range(*output)
                    else:
                        yield output
        except StopIteration:
            yield index  # no seq


def get_difference(list1, list2):
    '''Get the elements of list1 that are not in list2.

    Note:
        This is NOT a symmetric_difference

    Warning:
        This function will cause you to lose list order of list1 and list2

    Args:
        list1 (list): The list to get the intersection with
        list2 (list): The list to get the intersection against

    Returns:
        list: The combination of list1 and list2

    '''
    return list(set(list1) - set(list2))


def get_ordered_intersection(seq1, seq2, memory_efficient=False):
    '''Get the elements that exist in both given sequences.

    This code will preserve the order of the first sequence given.

    Args:
        seq1 (iterable): The sequence to iterate. Also determines return order.
        seq2 (iterable): The second sequence to compare against the first
        memory_efficient (:obj:`bool, optional):
            If you know that every element in both sequences are small in size,
            enable this option for a potential speed boost.

    Returns:
        iterable[any]: The common elements of the two sequences

    '''
    if memory_efficient:
        seq2 = frozenset(seq1)
    return [value for value in seq1 if value in seq2]


def filter_consecutive_items(obj):
    '''Remove all consecutive elements but keep duplicate items.

    Args:
        obj (iterable): The list (or iterable) to process

    Returns:
        list[int or tuple]: The ranges from the given list

    '''
    result = []
    for key, group in itertools.groupby(pairwise(obj), key=lambda val: val[1] - val[0]):
        group = list(group)
        if len(group) > 1:
            if result and group[0][0] == result[-1]:
                del result[-1]
            result.append((group[0][0], group[-1][-1], key))
        else:
            result.append(group[0][-1])
    return result


def uniquify_list(seq, idfun=None):
    '''Order preserving way to get unique elements in a list.

    This function is a bit dirty but extremely fast (see benchmark).

    Reference: https://www.peterbe.com/plog/uniqifiers-benchmark

    Args:
        seq (list): The list to make unique
        idfun (func): An optional function to run, as part of the uniquifier

    Returns:
        list: The uniquified list

    '''
    if not idfun:
        def _idfun(obj):
            '''Return the original object and do nothing.'''
            return obj
        idfun = _idfun

    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        #
        if marker in seen:
            continue

        seen[marker] = 1
        result.append(item)
    return result


def group_into(seq, maximum):
    '''Break a sequence up in a specified number of groups.

    Example:
        >>> seq = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> maximum = 4
        >>> group_into(seq=seq, maximum=maximum)
        >>> [[1, 4, 7, 10], [2, 5, 8], [3, 6, 9]]

    Args:
        seq (iterable): The sequence to split up
        maximum (int): The number of groups to make

    Returns:
        list[iterable]: Group of the original iterable sequence object

    '''
    return [seq[item::maximum] for item in moves.range(maximum)]


def group_nth(seq, num):
    '''Split the sequence by the given number.

    Example:
        >>> seq = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> maximum = 4
        >>> group_nth(seq=seq, num=maximum)
        >>> [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10]]

    Note:
        The number of groups that will be made is (len(seq) // by) + 1

    Args:
        seq (iterable): The sequence to split up into some groups.
        num (int):
            The size of the groups that will be made from the original seqence.

    Returns:
        list[iterable]: A group of the original iterable sequence object

    '''
    return [seq[value * num:(value * num) + num]
            for value in moves.range((len(seq) // num) + 1)
            if value * num < len(seq)]
