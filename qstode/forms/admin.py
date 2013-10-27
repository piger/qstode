# -*- coding: utf-8 -*-
"""
    qstode.forms.admin
    ~~~~~~~~~~~~~~~~~~

    Administration related forms definitions.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import re
from flask_wtf import Form
from wtforms import TextField, PasswordField, validators, BooleanField
from flask_wtf.html5 import EmailField
from flask_babel import lazy_gettext as _


username_re = re.compile(r'^[A-Za-z0-9]+$')


class AdminUserCreationForm(Form):
    username = TextField(_(u'Username'), [
        validators.Required(),
        validators.Length(min=3, max=20),
        validators.Regexp(username_re)
    ])

    email = EmailField(_(u'Email'), [
        validators.Required(),
        validators.Email()
    ])

    password = PasswordField(_(u'Password'), [
        validators.Length(
            min=8, max=128,
            message=u"Password length must be between %(min)d and %(max)d characters")
    ])
    admin = BooleanField(_(u"Administrator"), default=False)
    active = BooleanField(_(u"Active"), default=True)

class AdminUserDetailsForm(Form):
    username = TextField(_(u'Username'), [
        validators.Required(),
        validators.Length(min=3, max=20),
        validators.Regexp(username_re)
    ])

    email = EmailField(_(u'Email'),
                       [validators.Required(), validators.Email()])

    password = PasswordField(
        _(u'Password'),
        [validators.Optional(),
         validators.Length(
             min=8, max=128,
             message=u"Password length must be between %(min)d and %(max)d characters"),
         validators.EqualTo('password_confirm',
                            message=_(u"Passwords must match"))
        ]
    )
    password_confirm = PasswordField(_(u'Confirm new password'))


class AdminModifyUserForm(AdminUserDetailsForm):
    admin = BooleanField(_(u"Admin"))
    active = BooleanField(_(u"Active"))
