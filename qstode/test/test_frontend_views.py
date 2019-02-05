"""
    qstode.test.test_frontend_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    General views testing.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask import url_for
from qstode.test import FlaskTestCase
from ..model.user import User
from ..model.bookmark import Bookmark
from qstode import db


class FrontendViewsTest(FlaskTestCase):
    def setUp(self):
        super(FrontendViewsTest, self).setUp()
        user_1 = User("user1", "user1@example.com", "password")
        user_2 = User("user2", "user2@example.com", "password")

        db.Session.add_all([user_1, user_2])
        db.Session.commit()

        b1 = Bookmark.create(
            {
                "url": "http://www.python.org",
                "title": "Python",
                "notes": "Python website",
                "tags": ["programming", "python", "guido"],
                "user": user_1,
            }
        )
        db.Session.add(b1)
        db.Session.commit()

        b2 = Bookmark.create(
            {
                "url": "https://github.com/piger/qstode",
                "title": "QStode",
                "notes": "QStode source code",
                "tags": ["web", "python", "tags", "flask"],
                "user": user_1,
            }
        )
        db.Session.add(b2)
        db.Session.commit()

    def test_index_content(self):
        rv = self.client.get(url_for("index"))
        self.assert200(rv)
        assert b"Python website" in rv.data

    def test_login_failure(self):
        form_data = {"user": "not_user", "password": "password", "next": url_for("index")}
        rv = self.client.post(url_for("login"), data=form_data)
        self.assert200(rv)

    def test_login_success(self):
        form_data = {"user": "user1", "password": "password", "next": url_for("index")}
        rv = self.client.post(url_for("login"), data=form_data)
        self.assert_redirects(rv, url_for("index"))

    def test_complete_tags_success(self):
        rv = self.client.get(url_for("complete_tags") + "?term=pyt")
        self.assert200(rv)
        self.assertTrue("results" in rv.json)

        results = rv.json.get("results", [])
        assert len(results) == 1
        assert results[0].get("value", "") == "python"

    def test_complete_tags_empty(self):
        expected = {"results": []}
        rv = self.client.get(url_for("complete_tags") + "?term=foobarbaz")
        self.assert200(rv)
        self.assertEqual(rv.json, expected)
