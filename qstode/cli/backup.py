# -*- coding: utf-8 -*-
"""
    qstode.cli.backup
    ~~~~~~~~~~~~~~~~~

    Backup command line utility.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import sys
import json
import codecs
import iso8601
from .. import model
from .. import db


# Default password for users
DEFAULT_PASSWORD = "change this password"


class Cache(object):

    instance_class = None

    def __init__(self):
        self.items = {}

    def get_item(self, name):
        if not name in self.items:
            item = self.instance_class(name)
            self.items[name] = item
        return self.items[name]

class LinkCache(Cache):
    instance_class = model.Link

class TagCache(Cache):
    instance_class = model.Tag


def _parse_date(d):
    """Parse a ISO8601 datetime string and strips timezone information
    to please MySQL"""
    if d is not None:
        rv = iso8601.parse_date(d)
        return rv.replace(tzinfo=None)
    return d


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


def import_file(args):
    tag_cache = TagCache()
    link_cache = LinkCache()
    data = None

    with codecs.open(args.filename, 'rb', encoding='utf-8') as fd:
        data = json.load(fd)

    if data is None:
        print "Error: Invalid bakcup file"
        sys.exit(1)

    users_data = data.get('backup')
    if users_data is None:
        print "Error: Invalid backup file format"
        sys.exit(1)

    users = []
    for user_data in users_data:
        user = model.User.query.filter_by(email=user_data['email']).first()
        if user is None:
            user = model.User(user_data['username'],
                              user_data['email'],
                              password=DEFAULT_PASSWORD)
            user.created_at = _parse_date(user_data['created_at'])
            user.active = user_data.get('active', True)

        user.password = user_data['password']

        # roles
        roles = user_data.get('roles', [])
        if 'admin' in roles:
            user.admin = True

        # bookmarks
        for bm in user_data['bookmarks']:
            link = link_cache.get_item(bm['url'])

            if 'last_modified' in bm:
                mod_date = _parse_date(bm['last_modified'])
            else:
                mod_date = _parse_date(bm['modified_on'])

            if 'creation_date' in bm:
                create_date = _parse_date(bm['creation_date'])
            else:
                create_date = _parse_date(bm['created_on'])

            bookmark = model.Bookmark(
                title=bm['title'],
                private=bm['private'],
                created_on=create_date,
                modified_on=mod_date,
                notes=bm['notes'])
            bookmark.link = link

            for name in bm['tags']:
                tag = tag_cache.get_item(name)
                bookmark.tags.append(tag)

        user.bookmarks.append(bookmark)
    users.append(user)

    db.Session.add_all(users)
    db.Session.commit()


__all__ = ['backup_db', 'import_file']
