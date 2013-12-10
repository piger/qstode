# -*- coding: utf-8 -*-
"""
    qstode.cli.backup
    ~~~~~~~~~~~~~~~~~

    Backup command line utility.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import json
import codecs
from .. import model


def backup_db(args):
    users = []

    for user in model.User.query.all():
        user_dict = {
            'username': user.username,
            'email': user.email,
            'password': user.password,
            'created_at': user.created_at.isoformat(),
            'active': user.active,
            'bookmarks': [],
        }

        if hasattr(user, 'roles'):
            user_dict['roles'] = [role.name for role in user.roles]

        query = model.Bookmark.by_user(user.id, include_private=True).\
                order_by(model.Bookmark.created_on.asc())
        for bookmark in query.all():
            bookmark_dict = bookmark.to_dict()
            user_dict['bookmarks'].append(bookmark_dict)

        users.append(user_dict)

    print "Writing backup to: {}".format(args.filename)
    with codecs.open(args.filename, 'w', encoding='utf-8') as fd:
        json.dump(dict(backup=users), fd, ensure_ascii=False, indent=4)
