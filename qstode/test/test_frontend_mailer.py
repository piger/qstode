# -*- coding: utf-8 -*-
"""
    qstode.test.test_frontend_mailer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Mail sending tests.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import mock
from qstode.test import FlaskTestCase
from qstode.mailer import Mailer


class MailerTestCase(FlaskTestCase):
    def test_sendmail(self):
        with mock.patch('smtplib.SMTP') as MockSMTP:
            instance = MockSMTP.return_value

            mailer = Mailer('sender@example.com')
            rv = mailer.send('recipient@example.com',
                             'test mail', 'test body', 'test body html')

            assert rv
            assert instance.sendmail.called
            assert instance.quit.called
