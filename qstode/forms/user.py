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
from wtforms import (TextField, PasswordField, ValidationError, BooleanField,
                     HiddenField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length, Regexp,
                                Optional)
from flask_wtf.html5 import EmailField
from flask_babel import lazy_gettext as _
from .misc import RedirectForm
from .validators import unique_username, unique_email
from ..model import User


# Length limit for password validation
USERNAME_MIN = 3
USERNAME_MAX = 20
PASSWORD_MIN = 8
PASSWORD_MAX = 64

# username validation regexp
username_re = re.compile(r'^[A-Za-z0-9_-]+$')


class CreateUserForm(Form):
    username = TextField(_(u"Username"), [
        DataRequired(),
        Length(USERNAME_MIN, USERNAME_MAX),
        Regexp(username_re),
        unique_username(),
    ])
    email = EmailField(_(u"Email"), [
        DataRequired(),
        unique_email(),
    ])
    password = PasswordField(_(u"Password"), [
        DataRequired(),
        Length(PASSWORD_MIN, PASSWORD_MAX),
        EqualTo("password_confirm")])
    password_confirm = PasswordField(_(u"Confirm password"), [DataRequired()])
    active = BooleanField(_(u"Active"), default=True)
    admin = BooleanField(_(u"Administrator"), default=False)


class DeleteUserForm(RedirectForm):
    user_id = HiddenField()


class EditUserForm(CreateUserForm):
    """Admin: modify an existing user"""

    # username uniqueness is validated inline
    username = TextField(_(u"Username"), [
        DataRequired(),
        Length(USERNAME_MIN, USERNAME_MAX),
        Regexp(username_re),
    ])
    # email uniqueness is validated inline
    email = EmailField(_(u"Email"), [DataRequired()])
    password = PasswordField(_(u"Password"), [
        Optional(),
        Length(PASSWORD_MIN, PASSWORD_MAX),
        EqualTo("password_confirm")])
    password_confirm = PasswordField(_(u"Confirm password"))

    def __init__(self, username, email, *args, **kwargs):
        self._username = username
        self._email = email
        super(EditUserForm, self).__init__(*args, username=username, email=email,
                                           **kwargs)

    def validate_username(self, field):
        if field.data != self._username:
            if User.query.filter_by(username=field.data).first() is not None:
                raise ValidationError(_(u"Username already taken"))

    def validate_email(self, field):
        if field.data != self._email:
            if User.query.filter_by(email=field.data).first() is not None:
                raise ValidationError(_(u"Email already taken"))


class LoginForm(RedirectForm):
    user = TextField(_(u'User'), [DataRequired()])
    password = PasswordField(_(u'Password'), [DataRequired()])
    remember_me = BooleanField(_(u'Remember me'))


class PasswordResetForm(Form):
    email = EmailField(_(u'Email'), [DataRequired(), Email()])


class PasswordChangeForm(Form):
    password = PasswordField(_(u'New password'), [
        DataRequired(),
        Length(min=PASSWORD_MIN, max=PASSWORD_MAX),
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
        Length(min=PASSWORD_MIN, max=PASSWORD_MAX),
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
        unique_username(include_self=True),
    ])
    password_old = PasswordField('Current password')
    password = PasswordField(_(u'Password'), [
        Optional(),
        Length(min=PASSWORD_MIN, max=PASSWORD_MAX),
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
