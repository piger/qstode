# -*- coding: utf-8 -*-
"""
    qstode.test.test_frontend_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    General views testing.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from nose.plugins.skip import SkipTest
from qstode.test import FlaskTestCase
from qstode import model


class FrontendViewsTest(FlaskTestCase):
    def setUp(self):
        super(FrontendViewsTest, self).setUp()
        self._load_data([
            model.User(u'pippo', 'pippo@example.com', 'password'),
            model.Tag(u'prova'),
            model.Tag(u'internet'),
            model.Tag(u'intranet'),
            model.Tag(u'debug'),
            model.Tag(u'testing')
        ])

    def test_index(self):
        rv = self.client.get('/')
        self.assert200(rv)

    def test_about(self):
        rv = self.client.get('/about')
        self.assert200(rv)

    def test_help(self):
        rv = self.client.get('/help')
        self.assert200(rv)

    def test_login(self):
        rv = self.client.get('/login')
        self.assert200(rv)

    def test_login_failure(self):
        rv = self.client.post('/login', data=dict(
            email='fakeuser@google.it',
            password='password'
        ), follow_redirects=True)
        self.assert200(rv)
        assert 'Authentication failed' in rv.data

    def test_login_success(self):
        rv = self.client.post('/login', data=dict(
            email='pippo@example.com',
            password='password'
        ), follow_redirects=True)
        self.assert200(rv)
        print rv.data
        assert 'Successfully logged in' in rv.data

    def test_complete_tags_success(self):
        raise SkipTest("Must be updated to support orphan tag deletion")

        rv = self.client.get('/_complete/tags?term=int')
        self.assert200(rv)
        self.assertTrue('results' in rv.json)
        results = rv.json.get('results', [])
        self.assertEquals(len(results), 2, "results size must be 2")
        self.assertEquals(results[0].get('value', ''), u'internet')
        self.assertEquals(results[1].get('value', ''), u'intranet')

    def test_complete_tags_empty(self):
        expected = {
            'results': [],
        }
        rv = self.client.get('/_complete/tags?term=foobarbaz')
        self.assert200(rv)
        self.assertEquals(rv.json, expected)
