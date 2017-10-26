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

        user_1 = model.User("user1", "user1@example.com", "password")
        user_2 = model.User("user2", "user2@example.com", "password")

        db.Session.add_all([user_1, user_2])
        db.Session.commit()

        b1 = model.Bookmark.create({
            'url': "http://www.python.org",
            'title': "Python",
            'notes': "Python website",
            'tags': ["programming", "python", "guido"],
            'user': user_1,
        })
        db.Session.add(b1)
        db.Session.commit()

        b2 = model.Bookmark.create({
            'url': "https://github.com/piger/qstode",
            'title': "QStode",
            'notes': "QStode source code",
            'tags': ["web", "python", "tags", "flask"],
            'user': user_1,
        })
        db.Session.add(b2)
        db.Session.commit()


class TaglistViewTest(ApiTestBase):
    def test_taglist(self):
        rv = self.client.get(url_for('api_taglist'))
        self.assert200(rv)
        self.assertEqual(rv.mimetype, 'application/json')

        tags = rv.json.get('tags', [])
        first = tags[0]
        self.assertEqual(first['tag'], "python")
        self.assertEqual(len(tags), 6)
