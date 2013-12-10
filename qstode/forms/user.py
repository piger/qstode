# -*- coding: utf-8 -*-
"""
    qstode.forms.user
    ~~~~~~~~~~~~~~~~~

    User related forms definitions.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import re
from flask_login import current_user
from flask_wtf import Form
from flask_wtf.recaptcha import RecaptchaField
from wtforms import TextField, PasswordField, ValidationError, BooleanField
from wtforms.validators import (DataRequired, Email, EqualTo, Length, Regexp,
                                Optional)
from flask_wtf.html5 import EmailField
from flask_babel import lazy_gettext as _
from .misc import RedirectForm
from .. import model


# Length limit for password validation
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 64

# username validation regexp
username_re = re.compile(r'^[A-Za-z0-9_-]+$')


def unique_username(form, field):
    """Ensure the given username is unique in the database"""

    user = model.User.query.filter_by(username=field.data).first()
    if user is not None:
        raise ValidationError(_(u"Username already exists"))


def unique_username_or_self(form, field):
    """Ensure the given username is unique in the database or equal
    to the current username of the user requesting the validation"""

    username = field.data
    if username != current_user.username:
        user = model.User.query.filter_by(username=username).first()
        if user is not None:
            raise ValidationError(_(u"Username already exists"))


def unique_email(form, field):
    """Ensure the given email address is unique in the database"""

    user = model.User.query.filter_by(email=field.data).first()
    if user is not None:
        raise ValidationError(_(u"E-mail already registered"))


class LoginForm(RedirectForm):
    email = EmailField(_(u'Email'), [DataRequired(), Email()])
    password = PasswordField(_(u'Password'), [DataRequired()])
    remember_me = BooleanField(_(u'Remember me'))


class PasswordResetForm(Form):
    email = EmailField(_(u'Email'), [DataRequired(), Email()])


class PasswordChangeForm(Form):
    password = PasswordField(_(u'New password'), [
        DataRequired(),
        Length(
            min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH,
            message=_(u"Password length must be between %(min)d and %(max)d characters" % dict(min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH))
        ),
        EqualTo('password_confirm', message=_(u"Passwords must match"))
    ])
    password_confirm = PasswordField(_(u'Confirm new password'))


class RegistrationForm(Form):
    username = TextField(_(u'Username'), [DataRequired(),
                                          Length(min=3, max=20),
                                          Regexp(username_re),
                                          unique_username])
    email = EmailField(_(u'Email'), [DataRequired(), Email(),
                                     unique_email])
    password = PasswordField(_(u'Password'), [
        DataRequired(),
        Length(
            min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH,
            message=_(u"Password length must be between %(min)d and %(max)d characters" % dict(min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH))
        ),
        EqualTo('password_confirm', message=_(u"Passwords must match"))
    ])
    password_confirm = PasswordField(_(u'Confirm password'), [DataRequired()])
    recaptcha = RecaptchaField()


# unique_username ???
class UserDetailsForm(Form):
    username = TextField(_(u'Username'), [
        DataRequired(),
        Length(min=3, max=20),
        Regexp(username_re),
        unique_username_or_self
    ])
    password_old = PasswordField('Current password')
    password = PasswordField(_(u'Password'), [
        Optional(),
        Length(
            min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH,
            message=_(u"Password length must be between %(min)d and %(max)d characters" % dict(min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH))
        ),
        EqualTo('password_confirm', message=_(u"Passwords must match"))
    ])
    password_confirm = PasswordField(_(u'Confirm new password'))


class CreateProfileForm(Form):
    username = TextField(_(u'Username'), [
        DataRequired(),
        Length(min=3, max=20),
        Regexp(username_re),
        unique_username,
    ])
    email = EmailField(_(u"Email"), [DataRequired(), Email(), unique_email])
