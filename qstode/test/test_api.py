# -*- coding: utf-8 -*-
"""
    qstode.test.test_api
    ~~~~~~~~~~~~~~~~~~~~

    REST API testing.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask import url_for
from qstode.test import FlaskTestCase
from qstode import model
from qstode import db


class ApiTestBase(FlaskTestCase):
    def setUp(self):
        super(ApiTestBase, self).setUp()

        user_1 = model.User(u"user1", "user1@example.com", "password")
        user_2 = model.User(u"user2", "user2@example.com", "password")

        db.Session.add_all([user_1, user_2])
        db.Session.commit()

        b1 = model.Bookmark.create({
            'url': u"http://www.python.org",
            'title': u"Python",
            'notes': u"Python website",
            'tags': [u"programming", u"python", u"guido"],
            'user': user_1,
        })
        db.Session.add(b1)
        db.Session.commit()

        b2 = model.Bookmark.create({
            'url': u"https://github.com/piger/qstode",
            'title': u"QStode",
            'notes': u"QStode source code",
            'tags': [u"web", u"python", u"tags", u"flask"],
            'user': user_1,
        })
        db.Session.add(b2)
        db.Session.commit()


class TaglistViewTest(ApiTestBase):
    def test_taglist(self):
        rv = self.client.get(url_for('api_taglist'))
        self.assert200(rv)
        self.assertEquals(rv.mimetype, 'application/json')

        tags = rv.json.get('tags', [])
        first = tags[0]
        self.assertEquals(first['tag'], u"python")
        self.assertEquals(len(tags), 6)
