# -*- coding: utf-8 -*-
"""
    qstode.utils
    ~~~~~~~~~~~~

    Miscellaneous utilities.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import os
import hashlib


def read_config_defaults(parser, path):
    if not os.path.exists(path):
        return
    with open(path, 'r') as fd:
        for linenum, line in enumerate(fd):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                raise SyntaxError("%s, line %d: Syntax Error!" % (
                    path, 1 + linenum))

            tokens = [t.strip() for t in line.split('=', 1)]
            parser.set_default(tokens[0], tokens[1])

def random_token(length=20):
    return hashlib.sha1(os.urandom(length)).hexdigest()
