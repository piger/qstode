"""
    qstode.test.test_model
    ~~~~~~~~~~~~~~~~~~~~~~

    Model and database related tests.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from qstode.test import FlaskTestCase
from qstode import db
from ..model.user import User
from ..model.bookmark import Bookmark, Tag


sample_bookmarks = [
    {
        "title": "Le facezie",
        "url": "http://www.spatof.org",
        "tags": ["tutorials", "documentazione", "zsh", "internet"],
    },
    {
        "title": "google",
        "url": "http://www.google.com",
        "tags": ["ricerca", "internet", "gmail", "posta"],
    },
    {
        "title": "Undercore",
        "url": "http://www.undercoreonline.com",
        "tags": ["notizie", "articoli", "foto", "musica"],
    },
]

sample_users = (("pippo", "pippo@spatof.org", "foobar"), ("pluto", "pluto@gmail.com", "gnagna"))


class ModelTest(FlaskTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()
        pippo = User("pippo", "pippo@example.com", "secret")
        pluto = User("pluto", "pluto@example.com", "secret")
        db.Session.add_all([pippo, pluto])
        db.Session.commit()

        b1 = Bookmark.create(
            {
                "url": "http://www.google.com",
                "title": "Google",
                "notes": "Google search engine",
                "tags": ["search", "web", "google"],
                "user": pippo,
            }
        )
        db.Session.add(b1)
        db.Session.commit()

        # REMEMBER, THIS IS PRIVATE!
        b2 = Bookmark.create(
            {
                "url": "http://www.bing.com",
                "title": "Bing",
                "notes": "Bing search engine",
                "tags": ["search", "web", "bing"],
                "user": pippo,
                "private": True,
            }
        )
        db.Session.add(b2)
        db.Session.commit()

        b3 = Bookmark.create(
            {
                "url": "http://www.slashdot.org",
                "title": "Slashdot",
                "notes": "Slashdot: news for nerds",
                "tags": ["news", "nerds", "web"],
                "user": pluto,
            }
        )
        db.Session.add(b3)
        db.Session.commit()


class UserTest(ModelTest):
    def test_user_creation(self):
        user = User("cow-user", "cow@example.com", "secret")
        db.Session.add(user)
        db.Session.commit()

        user = User.query.filter_by(username="cow-user").first()
        assert user is not None
        assert user.check_password("secret") is True
        assert user.is_active is True

    def test_is_following(self):
        user1 = User.query.filter_by(username="pippo").first()
        user2 = User.query.filter_by(username="pluto").first()
        user1.watched_users.append(user2)
        db.Session.commit()

        self.assertTrue(user1.is_following(user2.id))
        self.assertFalse(user2.is_following(user1.id))


class TagTest(ModelTest):
    def test_get_many(self):
        names = ["news", "web"]
        tags = Tag.get_many(names)
        assert [t.name for t in tags] == ["news", "web"]

    def test_tag_search(self):
        tag = Tag.search("new").first()
        assert tag.name == "news"


class BookmarkTest(ModelTest):
    def test_by_tags(self):
        # lookup for 'search' must give 1 result, because
        # the other bookmark tagged with 'search' is private
        for tags, count in ((["web"], 2), (["search"], 1)):
            rv = Bookmark.by_tags(tags)
            x = rv.count()
            assert x == count

    def test_by_user(self):
        user = User.query.filter_by(username="pippo").first()
        rv = Bookmark.by_user(user.id)
        x = rv.count()
        assert x == 1

        rv = Bookmark.by_user(user.id, include_private=True)
        x = rv.count()
        assert x == 2

    def test_get_latest(self):
        rv = Bookmark.get_latest()
        x = rv.count()
        assert x == 2
