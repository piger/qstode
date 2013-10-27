# -*- coding: utf-8 -*-
"""
    qstode.forms.user
    ~~~~~~~~~~~~~~~~~

    User related forms definitions.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import re
from flask_wtf import Form
from flask_wtf.recaptcha import RecaptchaField
from wtforms import TextField, PasswordField, ValidationError
from wtforms.validators import (DataRequired, Email, EqualTo, Length, Regexp,
                                Optional)
from flask_wtf.html5 import EmailField
from flask_babel import lazy_gettext as _
from .misc import RedirectForm
from qstode.model.user import User


# Length limit for password validation
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 64


def unique_username(form, field):
    if User.query.filter_by(username=field.data).first() is not None:
        raise ValidationError(_(u"Username already exists"))

def unique_email(form, field):
    if User.query.filter_by(email=field.data).first() is not None:
        raise ValidationError(_(u"E-mail already registered"))


# USER FORMS ---
class LoginForm(RedirectForm):
    email = EmailField(_(u'Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_(u'Password'), validators=[DataRequired()])

class PasswordResetForm(Form):
    email = EmailField(_(u'Email'), validators=[DataRequired(), Email()])

class PasswordChangeForm(Form):
    password = PasswordField(
        _(u'New password'),
        validators=[
            DataRequired(),
            Length(
                min=8, max=128,
                message=_(u"Password length must be between %(min)d and %(max)d characters")
            ),
            EqualTo('password_confirm',
                    message=_(u"Passwords must match"))
        ]
    )
    password_confirm = PasswordField(_(u'Confirm new password'))




class RegistrationForm(Form):
    username = TextField(_(u'Username'), validators=[DataRequired(),
                                                     unique_username])
    email = EmailField(_(u'Email'), validators=[DataRequired(), Email(),
                                                unique_email])

    password = PasswordField(
        _(u'Password'),
        validators=[
            DataRequired(),
            Length(
                min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH,
                message=_(u"Password length must be between %(min)d and %(max)d characters" % dict(min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH))
            ),
            EqualTo('password_confirm', message=_(u"Passwords must match"))
        ]
    )
    password_confirm = PasswordField(_(u'Confirm password'),
                                     validators=[DataRequired()])

    recaptcha = RecaptchaField()


username_re = re.compile(r'^[A-Za-z0-9]+$')

class UserDetailsForm(Form):
    username = TextField(_(u'Username'), validators=[
        DataRequired(),
        Length(min=3, max=20),
        Regexp(username_re)
    ])

    password_old = PasswordField('Current password')

    password = PasswordField(
        _(u'Password'),
        validators=[
            Optional(),
            Length(
                min=8, max=128,
                message=_(u"Password length must be between %(min)d and %(max)d characters")
            ),
            EqualTo('password_confirm',
                    message=_(u"Passwords must match"))
        ]
    )
    password_confirm = PasswordField(_(u'Confirm new password'))

class CreateProfileForm(Form):
    username = TextField(_(u'Username'), validators=[
        DataRequired(),
        Length(min=3, max=20),
        Regexp(username_re),
        unique_username,
    ])
    email = EmailField(_(u"Email"), validators=[DataRequired(), Email(),
                                                unique_email])
