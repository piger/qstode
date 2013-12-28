# -*- coding: utf-8 -*-
"""
    qstode.forms.validators
    ~~~~~~~~~~~~~~~~~~~~~~~

    Validators for WTForms.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.login import current_user
from ..model import User
from wtforms import ValidationError


def unique_username(include_self=False):
    """Ensure the given username is unique in the database"""

    def _unique_username(form, field):
        if include_self and field.data == current_user.username:
            return

        user = User.query.filter_by(username=field.data).first()
        if user is not None:
            raise ValidationError(_(u"Username already taken"))

    return _unique_username


def unique_email(include_self=False):
    """Ensure the given email address is unique in the database"""

    def _unique_email(form, field):
        if include_self and field.data == current_user.email:
            return

        user = User.query.filter_by(email=field.data).first()
        if user is not None:
            raise ValidationError(_(u"Email already taken"))

    return _unique_email
