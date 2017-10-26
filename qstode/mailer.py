# -*- coding: utf-8 -*-
"""
    qstode.mailer
    ~~~~~~~~~~~~~

    Mail sending stuff.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import socket
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from qstode.app import app


class Mailer(object):
    def __init__(self, sender):
        self.sender = sender

    def send(self, to, subject, message_text, message_html):
        server = app.config.get('SMTP_HOST', 'localhost')
        port = app.config.get('SMTP_PORT', 25)

        msg = MIMEMultipart('alternative')
        part_txt = MIMEText(message_text, 'plain', 'utf-8')
        part_html = MIMEText(message_html, 'html', 'utf-8')

        msg['Subject'] = '[QStode] %s' % (subject,)
        msg['From'] = self.sender
        msg['To'] = to

        msg.attach(part_txt)
        msg.attach(part_html)

        try:
            conn = smtplib.SMTP(server, port)
            conn.sendmail(self.sender, [to], msg.as_string())
            conn.quit()
        except (smtplib.SMTPException, socket.error) as ex:
            app.logger.error("Unable to send mail: %s" % str(ex))
            app.logger.exception(ex)
            return False

        return True
