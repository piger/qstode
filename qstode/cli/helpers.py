# -*- coding: utf-8 -*-
"""
    qstode.cli.helpers
    ~~~~~~~~~~~~~~~~~~

    Helpers for the command-line utilities.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import iso8601


class ObjectCache(object):
    """A simple cache object that does not interact with the database"""

    # The database Model used to create new items
    model_class = None

    def __init__(self):
        self._cache = {}

    def get(self, key):
        """Get or create an element from the cache"""

        assert self.model_class is not None

        if key not in self._cache:
            item = self.model_class(key)
            self._cache[key] = item

        return self._cache[key]


def parse_datetime(dt):
    """Returns a datetime object parsed from the provided timestamp string
    and strips timezone informations"""

    if dt is not None:
        rv = iso8601.parse_date(dt)
        return rv.replace(tzinfo=None)
    return dt


def unescape(s):
    """Unescape a string containing \' or \" escapings"""

    corrections = (
        ("\\'", "'"),
        ('\\"', '"'))

    for pattern, repl in corrections:
        s = s.replace(pattern, repl)

    return s
