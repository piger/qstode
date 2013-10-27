# -*- coding: utf-8 -*-
"""
    qstode.test.test_forms
    ~~~~~~~~~~~~~~~~~~~~~~

    Unit tests related to forms.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask import url_for
from mock import patch
from wtforms import ValidationError
from qstode.test import FlaskTestCase
from qstode.model.user import User
from qstode.forms.user import unique_username, unique_email
from qstode import model


SAMPLE_DATA = {
    'title': u"A Test title",
    'url': u"http://www.example.com",
    'private': False,
    'tags': u"test, form validation, mordor",
    'notes': u"A couple of notes",
}

class FakeField(object):
    def __init__(self, data):
        self.data = data

class ValidatorsTest(FlaskTestCase):
    def setUp(self):
        super(ValidatorsTest, self).setUp()
        self._load_data([
            User(u'pippo', 'pippo@example.com', 'secret')
        ])

    def test_unique_username(self):
        field = FakeField(u'pippo')
        self.assertRaises(ValidationError, unique_username, None, field)

    def test_unique_email(self):
        field = FakeField(u'pippo@example.com')
        self.assertRaises(ValidationError, unique_email, None, field)

    def test_unique_username_false(self):
        field = FakeField(u'charlie root')
        self.assertIsNone(unique_username(None, field))

    def test_unique_email_false(self):
        field = FakeField(u'charlie@root.com')
        self.assertIsNone(unique_email(None, field))

class BookmarkFormBaseTest(FlaskTestCase):
    def setUp(self):
        super(BookmarkFormBaseTest, self).setUp()
        self._load_data([
            User(u'pippo', 'pippo@example.com', 'secret')
        ])

    def _login(self):
        rv = self.client.post('/login', data={
            "email": u"pippo@example.com",
            "password": "secret"
        }, follow_redirects=False)
        self.assert_redirects(rv, url_for('index'))

class BookmarkFormTest(BookmarkFormBaseTest):

    @patch('qstode.app.whoosh_searcher.add_bookmark')
    def test_submit_bookmark(self, mock_add_bookmark):
        self._login()

        rv = self.client.post('/add', data=SAMPLE_DATA)
        self.assertTrue(rv.status_code in (301, 302), "Got %r instead (%r)" % (rv.status_code, rv.data))
        self.assert_redirects(rv, url_for('index'))
        self.assertTrue(mock_add_bookmark.called)

        b = model.Bookmark.query.filter_by(title=SAMPLE_DATA['title']).first()
        self.assertIsNotNone(b, "Non e' stato creato il Bookmark")
        self.assertEquals(b.href, SAMPLE_DATA['url'])

    def test_missing_fields(self):
        self._login()
        for field in ('tags', 'title', 'url'):
            data = SAMPLE_DATA.copy()
            data.pop(field)
            rv = self.client.post('/add', data=data)
            self.assert200(rv)
            res = "field is required" in rv.data or "Invalid URL" in rv.data
            self.assertTrue(res, rv.data)

class TagListTest(BookmarkFormBaseTest):
    @patch('qstode.app.whoosh_searcher.add_bookmark')
    def test_taglist_duplicates(self, mock_add_bookmark):
        self._login()
        rv = self.client.post('/add', data={
            'title': u'Un titolo',
            'url': u'http://www.google.it',
            'private': False,
            'tags': u"uno, uno, UNO, uNo, UnO",
            'notes': u''
        })
        self.assert_redirects(rv, url_for('index'))

        b = model.Bookmark.query.filter_by(title=u'Un titolo').first()
        self.assertIsNotNone(b, "Non e' stato creato il Bookmark")
        self.assertEquals(b.href, u'http://www.google.it')
        tags = [tag.name for tag in b.tags]
        assert len(tags) == 1
        assert tags[0] == u"uno"

    @patch('qstode.app.whoosh_searcher.add_bookmark')
    def test_length_validator_exceed(self, mock_add_bookmark):
        self._login()
        data = SAMPLE_DATA.copy()
        tags = u', '.join([u"tag-%d" % i for i in xrange(51)])
        data['tags'] = tags
        rv = self.client.post('/add', data=data)
        self.assertEquals(rv.status_code, 200)
        self.assertTrue(u'Field must be between 1 and 50 characters long'
                        in rv.data)

    @patch('qstode.app.whoosh_searcher.add_bookmark')
    def test_length_validator_correct(self, mock_add_bookmark):
        self._login()
        data = SAMPLE_DATA.copy()
        tags = u', '.join([u"tag-%d" % i for i in xrange(49)])
        data['tags'] = tags
        rv = self.client.post('/add', data=data)
        self.assertTrue(rv.status_code in (301, 302), "Got %r instead (%r)" % (rv.status_code, rv.data))
        self.assert_redirects(rv, url_for('index'))
