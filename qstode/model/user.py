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
from sqlalchemy import Table, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy import Boolean
from sqlalchemy.orm import relationship, backref
from .. import db


watched_users = Table(
    'watched_users', db.Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('other_user_id', Integer, ForeignKey('users.id'), primary_key=True))


class User(db.Base, UserMixin):
    """A user for the authentication and authorization backend"""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(128))
    email = Column(String(128), index=True, unique=True, nullable=False)
    password = Column(String(128))
    created_at = Column(DateTime(), default=datetime.utcnow)
    active = Column(Boolean)
    openid = Column(String(200), nullable=True)
    admin = Column(Boolean, default=False)

    bookmarks = relationship('Bookmark', order_by='Bookmark.created_on',
                             cascade="all, delete-orphan",
                             backref=backref('user', lazy='joined'))

    reset_token = relationship('ResetToken', uselist=False, backref='user',
                               cascade="all, delete-orphan")

    watched_users = relationship('User', secondary=watched_users,
                                 primaryjoin=id==watched_users.c.user_id,
                                 secondaryjoin=id==watched_users.c.other_user_id)

    def __init__(self, username, email, password, display_name=None,
                 openid=None, admin=False, active=True):
        self.username = username
        self.email = email
        self.set_password(password)
        self.display_name = display_name
        self.active = active
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
                db.Session.commit()
            return rv

    def is_active(self):
        """Tell if a user have the active flag set (Flask-Login)"""
        return self.active

    def __repr__(self):
        return "<User(username={0}, email={1}, active={2})>".format(
            self.username, self.email, self.active)


class ResetToken(db.Base):
    __tablename__ = 'reset_tokens'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    token = Column(String(40))
    created_at = Column(DateTime(), default=datetime.utcnow)

    def __init__(self, token=None, created_at=None):
        if token is not None:
            self.token = token
        else:
            self.token = hashlib.sha1(os.urandom(20)).hexdigest()
        if created_at is not None:
            self.created_at = created_at

    def __repr__(self):
        return "<ResetToken({0}, {1})>".format(self.token, self.created_at)
