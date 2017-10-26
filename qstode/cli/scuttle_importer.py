# -*- coding: utf-8 -*-
"""
    qstode.cli.scuttle_importer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utility function to import data from a Scuttle json export file

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import json
import codecs
import os
import click
from qstode.model import Bookmark, Tag, Link, User, TAG_MIN, TAG_MAX, tag_name_re
from qstode.app import app, db
from qstode.cli.helpers import ObjectCache, parse_datetime, unescape
from qstode.utils import generate_password


# Constants from Scuttle
SCUTTLE_PRIVATE = 2


# Cache for Tags and Links
class TagCache(ObjectCache):
    model_class = Tag


class LinkCache(ObjectCache):
    model_class = Link


def list_duplicate_emails(data):
    emails = {}
    for user in data['users']:
        email = user.get('email')
        if email:
            emails.setdefault(email, 0)
            emails[email] += 1

    for email, tot in emails.items():
        if tot > 1:
            print(email, tot)


def cleanup_tags(tags):
    """Run some validation on a list of tag names; can return an empty list"""

    rv = []
    for tag in tags:
        # strip commas
        tag = tag.replace(",", "")

        # unescape, strip
        tag = unescape(tag)
        tag = tag.strip()

        # validate
        if len(tag) < TAG_MIN or len(tag) > TAG_MAX:
            continue
        if not tag_name_re.match(tag):
            continue
        rv.append(tag)

    return set([tag.lower() for tag in rv])


@app.cli.command()
@click.argument('filename')
def import_scuttle(filename):
    """Import data from a Scuttle JSON export file"""

    data = None
    tag_cache = TagCache()
    link_cache = LinkCache()
    users = {}
    all_users = []

    with codecs.open(filename, 'r', encoding='utf-8') as fd:
        data = json.load(fd, encoding='utf-8')

    tot = len(data['users'])
    for i, db_user in enumerate(data['users']):
        print("Importing user %d of %d" % (i+1, tot))

        username = db_user.get('username')
        email = db_user.get('email', '').lower()
        name = db_user.get('name', '').strip()
        if not name:
            name = username
        # XXX why do we need to generate/set a new password here?
        password = generate_password()
        if username is None:
            print("Skipping user without username: id=%r" % db_user['id'])
            continue
        elif not email:
            print("Skipping user without email address: id=%r" % db_user['id'])
            continue

        # We merge bookmarks for users with the same e-mail address
        # XXX users in scuttle are identified by their username while their
        # name is the "display_name".
        if not email in users:
            user = User(username, email, password, display_name=name)
            user.password = db_user['password']
            user.created_at = parse_datetime(db_user['created_at'])
            users[email] = user
        else:
            user = users[email]

        for db_bookmark in db_user['bookmarks']:
            title = unescape(db_bookmark['title'])
            private = (db_bookmark['status'] == SCUTTLE_PRIVATE)
            notes = unescape(db_bookmark['description'])
            created_on = parse_datetime(db_bookmark['created_at'])
            modified_on = parse_datetime(db_bookmark['modified_at'])

            bookmark = Bookmark(title, private=private,
                                created_on=created_on,
                                modified_on=modified_on,
                                notes=notes)
            bookmark.link = link_cache.get(db_bookmark['url'])
                     
            tags = cleanup_tags(db_bookmark['tags'])
            for tag_name in tags:
                tag = tag_cache.get(tag_name)
                bookmark.tags.append(tag)

            user.bookmarks.append(bookmark)

        all_users.append(user)

    db.Session.add_all(all_users)
    try:
        db.Session.commit()
    except Exception as e:
        print("Caught exception!")
        print(e)
        db.Session.rollback()
