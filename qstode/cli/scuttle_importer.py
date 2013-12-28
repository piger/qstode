# -*- coding: utf-8 -*-
"""Utility function to import data from a Scuttle json export file"""

import json
import codecs
import os
import iso8601
import re
from qstode.model import Bookmark, Tag, Link, User
from qstode.app import db


__all__ = ['import_scuttle']


class Cache(object):
    """A simple cache object that does not interact with the database"""
    MODEL = None

    def __init__(self):
        self._cache = {}

    def get(self, key):
        if not key in self._cache:
            item = self.MODEL(key)
            self._cache[key] = item
        return self._cache[key]

class TagCache(Cache):
    MODEL = Tag

class LinkCache(Cache):
    MODEL = Link


def parse_date(d):
    """Parse a ISO8601 datetime string and strips timezone information
    to please MySQL"""
    if d is not None:
        rv = iso8601.parse_date(d)
        return rv.replace(tzinfo=None)
    return d

def list_duplicate_emails(data):
    emails = {}
    for user in data['users']:
        email = user.get('email')
        if email:
            emails.setdefault(email, 0)
            emails[email] += 1

    for email, tot in emails.iteritems():
        if tot > 1:
            print email, tot

def fix_escaping(s):
    for pattern, repl in (
            (u"\\'", u"'"),
            (u'\\"', u'"')):
        s = s.replace(pattern, repl)
    return s

MAX_TAG_LEN = 50
def sanitize_name(name):
    name.replace(u',', u'')
    name = fix_escaping(name)
    name = name.strip()
    return name
    # return name[:MAX_TAG_LEN]


def import_scuttle(args):
    """Import data from a Scuttle JSON export file"""

    data = None
    tag_cache = TagCache()
    url_cache = LinkCache()
    users = {}
    emails = {}
    all_users = []

    with codecs.open(args.filename, 'r', encoding='utf-8') as fd:
        data = json.load(fd, encoding='utf-8')

    tot = len(data['users'])
    for i, db_user in enumerate(data['users']):
        print "Importing user %d of %d" % (i+1, tot)

        email = db_user.get('email', '').lower()
        if not email:
            print "Skipping user without email address: id=%r" % db_user['id']
            continue

        # We merge bookmarks for users with the same e-mail address
        # XXX users in scuttle are identified by their username while their
        # name is the "display_name".
        if not email in users:
            user = User(db_user['username'], db_user['email'], 'secret')
            user.password = db_user['password']
            user.created_at = parse_date(db_user['created_at'])
            user.username = db_user['username'] or db_user['name'] or u''
            users[email] = user
        else:
            user = users[email]

        for db_bookmark in db_user['bookmarks']:
            is_private = db_bookmark['status'] == 2
            url = url_cache.get(db_bookmark['url'])
            title = fix_escaping(db_bookmark['title'])
            notes = fix_escaping(db_bookmark['description'])
            content_date = iso8601.parse_date(db_bookmark['created_at']).date()

            bookmark = Bookmark(
                title, private=is_private,
                created_on=parse_date(db_bookmark['created_at']),
                modified_on=parse_date(db_bookmark['modified_at']),
                notes=notes)
            bookmark.link = url_cache.get(db_bookmark['url'])
                                
            tags = []
            tag_names = set([t.lower() for t in db_bookmark['tags']])
            for tag_name in tag_names:
                # tag_name = fix_escaping(tag_name)
                tag_name = sanitize_name(tag_name)
                tag = tag_cache.get(tag_name)
                # tags.append(tag)
                bookmark.tags.append(tag)
            # bookmark.tags = tags

            user.bookmarks.append(bookmark)

        all_users.append(user)

    db.Session.add_all(all_users)
    try:
        db.Session.commit()
    except Exception, e:
        print "Caught exception!"
        print e
        db.Session.rollback()


def main():
    from optparse import OptionParser
    from qstode.main import create_app

    parser = OptionParser()
    parser.add_option('-c', '--config')
    (opts, args) = parser.parse_args()
    if not args:
        parser.error("You must specify a json export file")
    if not opts.config:
        parser.error("You must specify a configuration file")

    os.environ['APP_CONFIG'] = os.path.abspath(opts.config)

    app = create_app()
    import_scuttle(args[0])


if __name__ == '__main__':
    main()
