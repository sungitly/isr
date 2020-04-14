# -*- coding: utf-8 -*-
from flask.ext.cache import Cache

cache = Cache()

LONG_CACHE = 86400
SHORT_CACHE = 3600

orig_memoize_kwargs_to_args = Cache._memoize_kwargs_to_args


def fix_memoize_kwargs_to_args(self, f, *args, **kwargs):
    def _uni_type(n):
        if isinstance(n, basestring):
            return unicode(n)
        if isinstance(n, int):
            return long(n)
        if isinstance(n, list):
            return [_uni_type(item) for item in n]
        if isinstance(n, dict):
            return {_uni_type(k): _uni_type(n[k]) for k in n}
        if isinstance(n, tuple):
            return tuple([_uni_type(item) for item in n])
        return n

    fix_args = _uni_type(args)
    fix_kwargs = _uni_type(kwargs)
    return orig_memoize_kwargs_to_args(self, f, *fix_args, **fix_kwargs)


Cache._memoize_kwargs_to_args = fix_memoize_kwargs_to_args
