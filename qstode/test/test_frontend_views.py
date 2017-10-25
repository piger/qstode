# -*- coding: utf-8 -*-
"""
    qstode.test.test_frontend_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    General views testing.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask import url_for
from qstode.test import FlaskTestCase
from qstode import model
from qstode import db


class FrontendViewsTest(FlaskTestCase):
    def setUp(self):
        super(FrontendViewsTest, self).setUp()
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

    def test_index_content(self):
        rv = self.client.get(url_for('index'))
        self.assert200(rv)
        assert u"Python website" in rv.data

    def test_login_failure(self):
        form_data = {
            'user': u"not_user",
            'password': u"password",
            'next': url_for('index'),
        }
        rv = self.client.post(url_for('login'), data=form_data)
        self.assert200(rv)

    def test_login_success(self):
        form_data = {
            'user': u"user1",
            'password': u"password",
            'next': url_for('index'),
        }
        rv = self.client.post(url_for('login'), data=form_data)
        self.assert_redirects(rv, url_for('index'))

    def test_complete_tags_success(self):
        rv = self.client.get(url_for('complete_tags') + '?term=pyt')
        self.assert200(rv)
        self.assertTrue('results' in rv.json)

        results = rv.json.get('results', [])
        assert len(results) == 1
        assert results[0].get('value', '') == u'python'

    def test_complete_tags_empty(self):
        expected = { 'results': [] }
        rv = self.client.get(url_for('complete_tags') + '?term=foobarbaz')
        self.assert200(rv)
        self.assertEquals(rv.json, expected)
