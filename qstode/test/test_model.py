# -*- coding: utf-8 -*-
"""
    qstode.test.test_model
    ~~~~~~~~~~~~~~~~~~~~~~

    Model and database related tests.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from sqlalchemy import func
from nose.plugins.skip import SkipTest
from qstode.test import FlaskTestCase
from qstode import db
from ..model import User, Bookmark, Tag, Link


sample_bookmarks = [
    {
        'title': u'Le facezie',
        'url': u'http://www.spatof.org',
        'tags': [u'tutorials', u'documentazione', u'zsh', u'internet'],
    },

    {
        'title': u'google',
        'url': u'http://www.google.com',
        'tags': [u'ricerca', u'internet', u'gmail', u'posta'],
    },

    {
        'title': u'Undercore',
        'url': u'http://www.undercoreonline.com',
        'tags': [u'notizie', u'articoli', u'foto', u'musica'],
    },
]

sample_users = (
    (u'pippo', u'pippo@spatof.org', 'foobar'),
    (u'pluto', u'pluto@gmail.com', 'gnagna'),
)


class ModelTest(FlaskTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()
        pippo = User(u"pippo", "pippo@example.com", "secret")
        pluto = User(u"pluto", "pluto@example.com", "secret")
        db.Session.add_all([pippo, pluto])
        db.Session.commit()

        b1 = Bookmark.create({
            'url': u"http://www.google.com",
            'title': u"Google",
            'notes': u"Google search engine",
            'tags': [u"search", u"web", u"google"],
            'user': pippo,
        })
        db.Session.add(b1)
        db.Session.commit()

        # REMEMBER, THIS IS PRIVATE!
        b2 = Bookmark.create({
            'url': u"http://www.bing.com",
            'title': u"Bing",
            'notes': u"Bing search engine",
            'tags': [u"search", u"web", u"bing"],
            'user': pippo,
            'private': True,
        })
        db.Session.add(b2)
        db.Session.commit()

        b3 = Bookmark.create({
            'url': u"http://www.slashdot.org",
            'title': u"Slashdot",
            'notes': u"Slashdot: news for nerds",
            'tags': [u"news", u"nerds", u"web"],
            'user': pluto,
        })
        db.Session.add(b3)
        db.Session.commit()


class UserTest(ModelTest):
    def test_user_creation(self):
        user = User(u"cow-user", u"cow@example.com", "secret")
        db.Session.add(user)
        db.Session.commit()

        user = User.query.filter_by(username=u"cow-user").first()
        assert user is not None
        assert user.check_password('secret') is True
        assert user.is_active() is True

    def test_is_following(self):
        user1 = User.query.filter_by(username=u'pippo').first()
        user2 = User.query.filter_by(username=u'pluto').first()
        user1.watched_users.append(user2)
        db.Session.commit()

        self.assertTrue(user1.is_following(user2.id))
        self.assertFalse(user2.is_following(user1.id))


class TagTest(ModelTest):
    def test_get_many(self):
        names = [u"news", u"web"]
        tags = Tag.get_many(names)
        assert [t.name for t in tags] == [u"news", u"web"]

    def test_tag_search(self):
        tag = Tag.search(u"new").first()
        assert tag.name == u"news"


class BookmarkTest(ModelTest):
    def test_by_tags(self):
        # lookup for 'search' must give 1 result, because
        # the other bookmark tagged with 'search' is private
        for tags, count in (
                ([u'web'], 2),
                ([u'search'], 1),
        ):
            rv = Bookmark.by_tags(tags)
            x = rv.count()
            assert x == count

    def test_by_user(self):
        user = User.query.filter_by(username=u'pippo').first()
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
