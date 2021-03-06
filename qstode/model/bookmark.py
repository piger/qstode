"""
    qstode.model.bookmark
    ~~~~~~~~~~~~~~~~~~~~~

    SQLAlchemy model definitions for bookmark related objects.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import re
import math
from datetime import datetime, timedelta
from typing import List
import sqlalchemy.types
from sqlalchemy import desc, func, and_, not_, or_, cast, distinct
from sqlalchemy import Table, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy import Boolean, event
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql.expression import false, true
from flask_login import current_user
from qstode import db
from qstode.model.user import User, watched_users


# Automatically delete orphan tags on database flush.
# http://stackoverflow.com/questions/9234082/setting-delete-orphan-on-sqlalchemy-relationship-causes-assertionerror-this-att
@event.listens_for(db.Session, "after_flush")
def delete_tag_orphans(session, ctx):
    session.query(Tag).filter(~Tag.bookmarks.any()).delete(synchronize_session=False)


# Many-to-many mapping between Bookmarks and Tags
bookmark_tags = Table(
    "bookmark_tags",
    db.Base.metadata,
    Column(
        "bookmark_id", Integer, ForeignKey("bookmarks.id", ondelete="cascade"), primary_key=True
    ),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="cascade"), primary_key=True),
)


# Tag names must be validated by this regex
tag_name_re = re.compile(r"^\w[\w!?.,$-_ ]*$", re.U)

# Validation for length of each tag
TAG_MIN = 1
TAG_MAX = 35

# Validation for length of the notes field
NOTES_MAX = 2500


class Tag(db.Base):
    """This seemingly harmless class describes the `Tag` model that is the
    most important piece of this application; tag names are stored treated
    always lowercase because otherwise it would be a mess.

    An important consideration must be done regarding MySQL and the
    collation: with the default collation for utf8 (utf8_general_ci)
    names like "perù" and "peru" are considered to be equals; to have
    a literal comparison we should use the collation 'utf8_bin', but
    there is a problem with `MySQL-Python` 1.2.3 (the default shipped
    with Debian 7) where 'utf8_bin' columns will always emit 'str' strings, even
    specifying `convert_unicode=True` in the sql engine configuration.
    Setting the column type to `Unicode` with collation `utf8_bin` doesn't solve
    the problem. The only solution is to upgrade to MySQL-Python 1.2.4
    or to specify a generic collation.

    See also: http://sourceforge.net/p/mysql-python/bugs/289/
    """

    # Uncomment this line to enable the "right" collation for tag names.
    # __table_args__ = {'mysql_collate': 'utf8_bin'}

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(TAG_MAX), nullable=False, index=True, unique=True)

    def __init__(self, name):
        """Create a new Tag, enforcing a lowercase name"""
        self.name = name.lower()

    @classmethod
    def get_or_create(cls, name):
        return super().get_or_create(name=name)

    @classmethod
    def search(cls, term):
        query = cls.query.filter(cls.name.startswith(term)).order_by(cls.name.asc())
        return query

    @classmethod
    def get_related(cls, tags: List[str], max_results=10, user=None):
        """
        Returns a list of tuples (Tag.id, Tag.name, count) for each Tag related
        to `tags`, which is a list of tag names.

        The generated SQL query used to hang MySQL 5.5.46-0+deb7u1.

        SQL query as explained here:
        http://stackoverflow.com/questions/4483357/join-instead-of-subquery-for-related-tags
        """
        assert isinstance(tags, list), "The 'tags' parameter must be a list"

        # enforce lowercase
        tags = [tag.lower() for tag in tags]
        # get the IDs for 'tags'
        tags_ids = [tag.id for tag in Tag.get_many(tags)]

        # build the subquery first: the subquery fetch all the bookmark ids of Bookmarks having
        # (all?)  `tags` among their tags.
        subq = db.Session.query(bookmark_tags.c.bookmark_id).join(
            Bookmark, Bookmark.id == bookmark_tags.c.bookmark_id
        )
        if user is None:
            # Exclude private Bookmarks
            subq = subq.filter(Bookmark.private == false())
        else:
            # Exclude private Bookmarks but include user's bookmarks
            subq = subq.filter(
                or_(
                    Bookmark.private == false(),
                    and_(Bookmark.private == true(), Bookmark.user_id == user.id),
                )
            )

        subq = (
            # Only include Bookmarks which tags matches our `tags`
            subq.filter(bookmark_tags.c.tag_id.in_(tags_ids))
            .group_by(bookmark_tags.c.bookmark_id)
            .having(func.count(bookmark_tags.c.tag_id) == len(tags_ids))
            .subquery()
        )

        # the query does a count() of tags joining the table `bookmark_tags`, only including
        # bookmarks from the subquery, only including tags from `tags`.
        q = (
            db.Session.query(cls.id, cls.name, func.count("*").label("tot"))
            .select_from(bookmark_tags)
            .join(cls, cls.id == bookmark_tags.c.tag_id)
            .join(subq, subq.c.bookmark_id == bookmark_tags.c.bookmark_id)
            .filter(not_(cls.id.in_(tags_ids)))
            .group_by(cls.id)
            .order_by(desc("tot"))
            .limit(max_results)
        )

        return q.all()

    @classmethod
    def get_or_create_many(cls, names):
        """
        Returns a list of Tag objects matching `names` and create Tags
        that can't be found.
        """
        results = []
        names = set([n.lower() for n in names])

        for name in names:
            tag = cls.get_or_create(name)
            results.append(tag)

        return results

    @classmethod
    def get_many(cls, names, match_case=False):
        """
        Returns a list of Tags matching `names`.
        """
        if match_case is False:
            names = set([name.lower() for name in names])

        if not len(names):
            return []

        query = cls.query.filter(Tag.name.in_(names))
        return query

    @classmethod
    def tagcloud(cls, limit=15, min_font_size=2, max_font_size=10, user_id=None):
        """
        Generates a tag cloud.

        Returns a list of dicts with keys:
        - name
        - weight
        - total count
        - (font) size

        for the top `limit` popular Tags.
        """

        query = (
            db.Session.query(Tag, func.count(Tag.id).label("total"))
            .join(Tag.bookmarks)
            .filter(Bookmark.private == false())
        )

        if user_id is not None:
            query = query.join(Bookmark.user).filter(User.id == user_id)

        query = query.group_by(Tag.id).order_by("total DESC").limit(limit)

        tags = query.all()
        if len(tags) < limit:
            return []

        # The total count of the most popular tag
        tot_max = tags[0][1]
        # The total count of the least popular tag
        tot_min = tags[-1][1]

        tag_cloud_weighted = []
        for tag, tag_count in tags:
            log_count = math.log(tag_count) - math.log(tot_min)
            log_max = math.log(tot_max) - math.log(tot_min)
            weight = log_count / log_max
            tag_dict = {
                "name": tag.name,
                "weight": weight,
                "tot": tag_count,
                "size": int(min_font_size + round((max_font_size - min_font_size) * weight)),
            }
            tag_cloud_weighted.append(tag_dict)

        tag_cloud_weighted = sorted(tag_cloud_weighted, key=lambda x: x["name"], reverse=False)

        return tag_cloud_weighted

    @classmethod
    def taglist(cls, max_results=20):
        """
        Returns a list of tuples (Tag object, total count) for the most popular
        tags.
        """

        q = (
            db.Session.query(cls, func.count(bookmark_tags.c.bookmark_id).label("tot"))
            .join(bookmark_tags)
            .join(Bookmark)
            .filter(Bookmark.private == false())
            .group_by(cls)
            .order_by(desc("tot"))
            .limit(max_results)
        )

        return q.all()

    def __repr__(self):
        return "<Tag(%r)>" % self.name


class Link(db.Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    href = Column(String(2000), nullable=False)

    def __init__(self, href):
        self.href = href

    @classmethod
    def get_or_create(cls, href):
        return super().get_or_create(href=href)

    def __repr__(self):
        return "<Link(href={})>".format(self.href)


class Bookmark(db.Base):
    """A bookmark element in the archive. It has several properties and
    related tables (URL, Cateory, Tag, etc.).

    db.DateTime columns must store timestamps as if they where from UTC timezone,
    as the `timezone` info is stored only by PostgreSQL database.
    The best practice is to store UTC timestamps and convert to the user
    timezone in the view.
    """

    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    link = relationship("Link", lazy="joined", backref=backref("bookmarks"))
    link_id = Column(Integer, ForeignKey("links.id"))
    href = association_proxy("link", "href")
    private = Column(Boolean, default=False)

    created_on = Column(DateTime, default=datetime.utcnow)
    modified_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    indexed_on = Column(DateTime)

    tags = relationship(
        "Tag",
        secondary=bookmark_tags,
        backref=backref("bookmarks", lazy="dynamic"),
        order_by="Tag.name",
        lazy="subquery",
    )
    notes = Column(String(NOTES_MAX))

    def __init__(self, title, private=False, created_on=None, modified_on=None, notes=None):
        self.title = title
        self.private = private
        if created_on is not None:
            self.created_on = created_on
        if modified_on is not None:
            self.modified_on = modified_on
        self.notes = notes or ""

    @classmethod
    def get_public(cls):
        """Return a query for the list of latest public Bookmarks, including
        the private bookmarks for the current user"""

        if not current_user.is_authenticated:
            return cls.query.filter(cls.private == false())

        return cls.query.filter(
            or_(and_(cls.private == true(), cls.user_id == current_user.id), cls.private == false())
        )

    @classmethod
    def get_latest(cls):
        query = cls.get_public().order_by(cls.created_on.desc())
        return query

    @classmethod
    def by_user(cls, userid, include_private=False):
        where = cls.user_id == userid
        if not include_private:
            where = where & (cls.private == false())
        return cls.query.filter(where).order_by(cls.created_on.desc())

    @classmethod
    def by_followed(cls):
        """Get the latest bookmarks from the users followed by
        the current user"""

        return (
            cls.query.join(User)
            .outerjoin(watched_users, User.id == watched_users.c.other_user_id)
            .filter(watched_users.c.user_id == current_user.id)
            .filter(cls.private == false())
            .order_by(cls.created_on.desc())
        )

    @classmethod
    def by_tags_user(cls, tags, user_id):
        assert isinstance(tags, list), "`tags` parameter must be a list"

        return (
            cls.query.filter(cls.user_id == user_id)
            .join(cls.tags)
            .filter(Tag.name.in_(tags))
            .group_by(cls.id)
            .having(func.count(cls.id) == len(tags))
            .order_by(cls.created_on.desc())
        )

    @classmethod
    def by_tags(cls, tags, exclude=None, user_id=None):
        """Returns all the Bookmarks tagged with the tag names specified in
        the `tags` parameter.

        The optional parameter `exclude` can be specified to exclude Bookmarks
        tagged with any of the specified tag names.

        :param tags: a list of tag names to include in the results
        :param exclude: an optional list of tag names to exclude from the results
        :param user_id: include only bookmarks owned by `user_id`
        """

        assert isinstance(tags, list), "`tags` parameter must be a list"

        if exclude is None:
            exclude = []

        # enforce lowercase and uniqueness
        tags = set([t.lower() for t in tags])
        exclude = set([t.lower() for t in exclude])

        # If no tags was specified for exclusion we can work out a much
        # simplier SQL query.
        if not exclude:
            query = (
                cls.get_public()
                .join(cls.tags)
                .filter(Tag.name.in_(tags))
                .group_by(cls.id)
                .having(func.count(cls.id) == len(tags))
                .order_by(cls.created_on.desc())
            )

            if user_id is not None:
                query = query.filter(cls.user_id == user_id)

            return query

        exclude_query = (
            db.Session.query(bookmark_tags.c.bookmark_id)
            .join(Tag)
            .filter(Tag.name.in_(exclude))
            .subquery("exclude")
        )

        include_query = (
            db.Session.query(bookmark_tags.c.bookmark_id)
            .join(Tag)
            .filter(Tag.name.in_(tags))
            .group_by(bookmark_tags.c.bookmark_id)
            .having(func.count(distinct(Tag.name)) == len(tags))
            .subquery("include")
        )

        query = (
            cls.get_public()
            .outerjoin(exclude_query, cls.id == exclude_query.c.bookmark_id)
            .join(include_query, cls.id == include_query.c.bookmark_id)
            .filter(exclude_query.c.bookmark_id == None)  # noqa
            .order_by(cls.created_on.desc())
        )

        if user_id is not None:
            query = query.filter(cls.user_id == user_id)

        return query

    # TODO: wat?
    @classmethod
    def by_ids(cls, ids):
        """Returns a list of Bookmarks matching the IDs in `ids`;
        in MySQL the returned list is ordered the same as `ids`.
        """
        # Keep the order from Whoosh with a MySQL specific hack:
        # order_by FIELD() function.
        # http://dev.mysql.com/doc/refman/5.0/en/string-functions.html#function_field
        engine = db.Session.get_bind()
        if engine.driver.startswith("mysql"):
            query = cls.get_public().filter(cls.id.in_(ids)).order_by(func.field(cls.id, *ids))
        else:
            query = cls.get_public().filter(cls.id.in_(ids)).order_by(cls.created_on.desc())
        return query

    @classmethod
    def submit_by_day(cls, days=30):
        date_limit = datetime.now() - timedelta(days)

        # multi-database support (MySQL, PostgreSQL, SQLite) for date conversion
        engine = db.Session.get_bind()
        if "sqlite" in engine.driver:  # could be 'sqlite', or 'pysqlite'
            fn = cast(func.julianday(cls.created_on), Integer)
        elif engine.driver == "postgresql":
            fn = cast(cls.created_on, sqlalchemy.types.Date)
        else:
            fn = func.to_days(cls.created_on)

        query = (
            db.Session.query(fn.label("day"), func.count("*").label("count"))
            .filter(cls.created_on > date_limit)
            .group_by("day")
            .order_by("day ASC")
        )

        results = [row.count for row in query.all()]
        return results

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.href,
            "title": self.title,
            "notes": self.notes,
            "tags": [tag.name for tag in self.tags],
            "private": self.private,
            "created_on": self.created_on.isoformat(),
            "modified_on": self.modified_on.isoformat(),
        }

    def __repr__(self):
        return "<Bookmark(title={0}, created_on={1}, private={2}".format(
            self.title, self.created_on, self.private
        )


# TODO: rename me
def get_stats():
    tot_bookmarks = (
        db.Session.query(func.count(Bookmark.id)).filter(Bookmark.private == false()).scalar()
    )

    tot_tags = (
        db.Session.query(Tag)
        .join(bookmark_tags)
        .join(Bookmark)
        .filter(Bookmark.private == false())
        .group_by(Tag.id)
        .count()
    )

    return (tot_bookmarks, tot_tags)


def create_bookmark(url, title, notes, tags, private=False):
    """Helper for creating new Bookmark objects.

    - url: the bookmark URL (e.g. http://www.example.com/)
    - title: a string with the bookmark title
    - notes: a string with the bookmark notes
    - tags: a list of strings with the bookmark tags
    - private: an optional boolean value to make the bookmark private

    :returns: the bookmark just created
    """

    href = Link.get_or_create(url)
    bookmark = Bookmark(title=title, notes=notes, private=private)
    bookmark.link = href
    for tag in Tag.get_or_create_many(tags):
        bookmark.tags.append(tag)

    return bookmark
