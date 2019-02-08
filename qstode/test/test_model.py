"""
    qstode.test.test_model
    ~~~~~~~~~~~~~~~~~~~~~~

    Model and database related tests.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from . import FlaskTestCase
from .. import db
from ..model.user import User
from ..model.bookmark import Bookmark, Tag
from .model_factory import UserFactory, TagFactory, BookmarkFactory


class ModelTest(FlaskTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()
        self.user1 = UserFactory.create(username="pippo", password="secret")
        self.user2 = UserFactory.create(username="pluto")
        db.Session.commit()

        BookmarkFactory.create(
            user=self.user1, tags=[TagFactory.create(name=w) for w in ("search", "web", "google")]
        )
        db.Session.commit()
        BookmarkFactory.create(
            user=self.user1,
            private=True,
            tags=[TagFactory.create(name=w) for w in ("search", "web", "bing")],
        )
        db.Session.commit()
        BookmarkFactory.create(
            user=self.user2, tags=[TagFactory.create(name=w) for w in ("news", "nerds", "web")]
        )
        db.Session.commit()


class UserTest(ModelTest):
    def test_user_check_password(self):
        user = User.query.filter_by(username="pippo").first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password("secret"))

    def test_is_following(self):
        user1 = User.query.filter_by(username="pippo").first()
        user2 = User.query.filter_by(username="pluto").first()
        user1.watched_users.append(user2)
        db.Session.commit()

        self.assertTrue(user1.is_following(user2.id))
        self.assertFalse(user2.is_following(user1.id))


# REMEMBER: tags with no bookmarks gets deleted automatically!
class TagTest(ModelTest):
    def test_get_many(self):
        names = ["news", "web"]
        tags = Tag.get_many(names)
        self.assertTrue([t.name for t in tags] == ["news", "web"])

    def test_tag_search(self):
        tag = Tag.search("new").first()
        self.assertTrue(tag.name == "news")

    def test_get_or_create(self):
        tag = TagFactory.create(name="search")
        db.Session.commit()
        t = Tag.query.filter_by(name="search").one_or_none()
        self.assertTrue(t is not None)
        self.assertEqual(tag.id, t.id)

        t2 = Tag.get_or_create("search")
        db.Session.commit()
        self.assertEqual(t2.id, tag.id)

    def test_search(self):
        for n in ("programming", "programmers"):
            BookmarkFactory.create(tags=[TagFactory.create(name=n)])
        db.Session.commit()

        result = Tag.search("programm")
        self.assertEqual(result.count(), 2)

    def test_get_related(self):
        result = Tag.get_related(["search"])
        self.assertEqual(result[0].name, "web")


class BookmarkTest(ModelTest):
    def test_by_tags(self):
        # lookup for 'search' must give 1 result, because
        # the other bookmark tagged with 'search' is private
        for tags, count in ((["web"], 2), (["search"], 1)):
            rv = Bookmark.by_tags(tags)
            self.assertEqual(rv.count(), count)

    def test_by_user(self):
        user = User.query.filter_by(username="pippo").first()
        rv = Bookmark.by_user(user.id)
        self.assertEqual(rv.count(), 1)

        rv = Bookmark.by_user(user.id, include_private=True)
        self.assertEqual(rv.count(), 2)

    def test_get_latest(self):
        rv = Bookmark.get_latest()
        self.assertEqual(rv.count(), 2)
