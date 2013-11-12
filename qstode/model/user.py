# -*- coding: utf-8 -*-
"""
    qstode.model.user
    ~~~~~~~~~~~~~~~~~

    SQLAlchemy model definitions for user authentication and authorization.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import os
import hashlib
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import (generate_password_hash, check_password_hash,
                               safe_str_cmp)
from qstode.app import db


watched_users = db.Table(
    'watched_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'),
           primary_key=True),
    db.Column('other_user_id', db.Integer, db.ForeignKey('user.id'),
           primary_key=True))


class User(db.Model, UserMixin):
    """A user for the authentication and authorization backend"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    email = db.Column(db.String(128), index=True, unique=True, nullable=False)
    password = db.Column(db.String(128))
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    active = db.Column(db.Boolean)
    openid = db.Column(db.String(200), nullable=True)
    admin = db.Column(db.Boolean, default=False)

    bookmarks = db.relationship('Bookmark', order_by='Bookmark.creation_date',
                             cascade="all, delete-orphan",
                             backref=db.backref('user', lazy='joined'))

    reset_token = db.relationship('ResetToken', uselist=False, backref='user',
                               cascade="all, delete-orphan")

    watched_users = db.relationship('User', secondary=watched_users,
                                 primaryjoin=id==watched_users.c.user_id,
                                 secondaryjoin=id==watched_users.c.other_user_id)

    def __init__(self, username, email, password, openid=None, admin=False):
        self.username = username
        self.email = email
        self.set_password(password)
        self.active = True
        self.openid = openid
        self.admin = admin

    def set_password(self, password):
        """Set a new password for this user"""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check the parameter `password` for a match with the user's
        password"""
        if self.password.startswith('pbkdf2'):
            return check_password_hash(self.password, password)
        else:
            # handle scuttle passwords (sha1) and migrate if correct
            rv = safe_str_cmp(self.password,
                              hashlib.sha1(password).hexdigest())
            if rv is True:
                self.set_password(password)
                db.session.commit()
            return rv

    def is_active(self):
        """Tell if a user have the active flag set (Flask-Login)"""
        return self.active

    def __repr__(self):
        return '<User(username=%r, email=%r, active=%r)>' % (self.username, self.email, self.active)


class ResetToken(db.Model):
    __tablename__ = 'resettokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(40))
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(self, token=None, created_at=None):
        if token is not None:
            self.token = token
        else:
            self.token = hashlib.sha1(os.urandom(20)).hexdigest()
        if created_at is not None:
            self.created_at = created_at
        else:
            self.created_at = datetime.utcnow()

    def __repr__(self):
        return "<ResetToken(token=%s, created_at=%r)>" % (
            self.token, self.created_at)
