# -*- coding: utf-8 -*-
"""
    qstode.views.helpers
    ~~~~~~~~~~~~~~~~~~~~

    Helper utilities for the web views.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""


def validate_page(page):
    """Validate a page number"""

    try:
        rv = int(page)
    except (ValueError, TypeError):
        rv = 1

    return rv
