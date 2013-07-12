"""
memoization function for decoration
"""
import functools

def Memoize(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def helper(*args):
        if args not in cache:
            cache[args] = obj(*args)
        return cache[args]

    return helper