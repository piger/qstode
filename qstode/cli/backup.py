"""
    qstode.cli.backup
    ~~~~~~~~~~~~~~~~~

    Backup command line utility.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import sys
import json
import iso8601
import click
from qstode.app import app
from ..model.bookmark import Link, Tag, Bookmark
from ..model.user import User
from qstode import db


# Default password for users
DEFAULT_PASSWORD = "change this password"


class Cache(object):

    instance_class = None

    def __init__(self):
        self.items = {}

    def get_item(self, name):
        if name not in self.items:
            item = self.instance_class(name)
            self.items[name] = item
        return self.items[name]


class LinkCache(Cache):
    instance_class = Link


class TagCache(Cache):
    instance_class = Tag


def _parse_date(d):
    """Parse a ISO8601 datetime string and strips timezone information
    to please MySQL"""
    if d is not None:
        rv = iso8601.parse_date(d)
        return rv.replace(tzinfo=None)
    return d


@app.cli.command()
@click.argument("filename")
def backup(filename):
    users = []

    for user in User.query.all():
        user_dict = {
            "username": user.username,
            "email": user.email,
            "password": user.password,
            "created_at": user.created_at.isoformat(),
            "active": user.active,
            "bookmarks": [],
        }

        if hasattr(user, "roles"):
            user_dict["roles"] = [role.name for role in user.roles]

        query = Bookmark.by_user(user.id, include_private=True).order_by(Bookmark.created_on.asc())
        for bookmark in query.all():
            bookmark_dict = bookmark.to_dict()
            user_dict["bookmarks"].append(bookmark_dict)

        users.append(user_dict)

    click.echo("Writing backup to: {}".format(filename))
    with open(filename, "w", encoding="utf-8") as fd:
        json.dump(dict(backup=users), fd, ensure_ascii=False, indent=4)


@app.cli.command()
@click.argument("filename")
def import_file(filename):
    tag_cache = TagCache()
    link_cache = LinkCache()
    data = None

    with open(filename, "rb", encoding="utf-8") as fd:
        data = json.load(fd)

    if data is None:
        click.echo("Error: Invalid bakcup file")
        sys.exit(1)

    users_data = data.get("backup")
    if users_data is None:
        click.echo("Error: Invalid backup file format")
        sys.exit(1)

    for user_data in users_data:
        user = User.query.filter_by(email=user_data["email"]).first()
        if user is None:
            user = User(user_data["username"], user_data["email"], password=DEFAULT_PASSWORD)
            user.created_at = _parse_date(user_data["created_at"])
            user.active = user_data.get("active", True)
            db.Session.add(user)

        user.password = user_data["password"]

        # roles
        roles = user_data.get("roles", [])
        if "admin" in roles:
            user.admin = True

        # bookmarks
        for bm in user_data["bookmarks"]:
            link = link_cache.get_item(bm["url"])

            if "last_modified" in bm:
                mod_date = _parse_date(bm["last_modified"])
            else:
                mod_date = _parse_date(bm["modified_on"])

            if "creation_date" in bm:
                create_date = _parse_date(bm["creation_date"])
            else:
                create_date = _parse_date(bm["created_on"])

            bookmark = Bookmark(
                title=bm["title"],
                private=bm["private"],
                created_on=create_date,
                modified_on=mod_date,
                notes=bm["notes"],
            )
            bookmark.link = link

            for name in bm["tags"]:
                tag = tag_cache.get_item(name)
                bookmark.tags.append(tag)

            user.bookmarks.append(bookmark)

    db.Session.commit()
