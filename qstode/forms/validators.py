# -*- coding: utf-8 -*-
"""
    qstode.forms.validators
    ~~~~~~~~~~~~~~~~~~~~~~~

    Validators for WTForms.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import re
from flask_login import current_user
from flask_babel import lazy_gettext as _
from wtforms import ValidationError
from ..model import User


def ItemsLength(min_length=1, max_length=100):
    """Validate the length of each str element in a list"""

    def _ItemsLength(form, field):
        assert isinstance(field.data, list) is True, \
            "This validator must be used with a `list` field"

        for item in field.data:
            l = len(item)
            if l < min_length or l > max_length:
                raise ValidationError(_(u"All elements must be between " \
                                        u"%(min)d and %(max)d characters" % {
                                            'min': min_length,
                                            'max': max_length,
                                        }))
    return _ItemsLength


def ListLength(min_length=1, max_length=100):
    """Validate the length of a list of elements"""

    def _ListLength(form, field):
        assert isinstance(field.data, list) is True, \
            "This validator must be used with a `list` field"

        l = len(field.data)
        if l < min_length or l > max_length:
            raise ValidationError(_(u"All elements must be between " \
                                    u"%(min)d and %(max)d characters" % {
                                        'min': min_length,
                                        'max': max_length,
                                    }))
    return _ListLength


def ListRegexp(regex):
    """Validate every item of list with a regex match operation"""

    def _ListRegexp(form, field):
        assert isinstance(field.data, list) is True, \
            "This validator must be used with a `list` field"

        for item in field.data:
            if regex.match(item) is None:
                raise ValidationError(_(u"Invalid characters"))
        
    return _ListRegexp


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
