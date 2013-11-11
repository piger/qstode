# -*- coding: utf-8 -*-
"""
    qstode.views.user
    ~~~~~~~~~~~~~~~~~

    Flask views related to user authentication and authorization.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import os
from urlparse import urljoin
from flask import session, request, redirect, flash, render_template, url_for
from flask_login import login_user, login_required, logout_user, current_user
from flask_openid import COMMON_PROVIDERS
from flask_babel import gettext
from sqlalchemy.orm import joinedload
from qstode.app import app, login_manager, oid, db
from qstode.model.user import User, ResetToken
from qstode.mailer import Mailer
from qstode.forms import (LoginForm, UserDetailsForm, PasswordResetForm,
                          PasswordChangeForm, CreateProfileForm,
                          RegistrationForm)


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


@login_manager.unauthorized_handler
def unauthorized():
    """Display a page that ask the user to login"""
    return render_template("unauthenticated.html")


def make_external(url):
    return urljoin(request.url_root, url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirects already logged in users to the index page
    if current_user.is_authenticated():
        return redirect(url_for('index'))

    form = LoginForm()
    login_failed = False

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.active and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(gettext(u'Successfully logged in as %(user)s', user=user.email), "success")
            return form.redirect('index')

        login_failed = True
        app.logger.info("Failed login from %s" % form.email.data)

    return render_template('login.html', form=form, login_failed=login_failed)


@app.route('/logout')
def logout():
    logout_user()
    session.pop('openid', None)
    return redirect(url_for('index'))


@app.route('/user/details', methods=['GET', 'POST'])
@login_required
def user_details():
    """Edits personal user informations"""

    form = UserDetailsForm(username=current_user.username)

    if form.validate_on_submit():
        if form.username.data != current_user.username:
            current_user.username = form.username.data

        if form.password.data:
            current_user.set_password(form.password.data)

        db.session.commit()
        flash(gettext(u"Profile successfully updated"), 'success')
        return redirect(url_for('user_details'))

    return render_template('user_details.html', form=form)


@app.route('/user/reset/request', methods=['GET', 'POST'])
def reset_request():
    """Begins the password reset procedure"""

    form = PasswordResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data
        ).options(
            joinedload('reset_token')
        ).first()

        # Even if the user wans't found, redirects to the "done" page
        # to avoid user enumeration.
        # WARNING: this method could suffer from a user enumeration
        # though a timing attack.
        if user is None:
            app.logger.error(
                "PasswordReset requested for an "
                "invalid account: %s" % str(form.email.data)
            )
            return render_template('request_reset_done.html')

        if user.reset_token:
            return render_template('request_reset_done.html',
                                   already_requested=True)

        user.reset_token = ResetToken()
        token = user.reset_token.token

        reset_url = make_external(url_for('reset_password', token=token))
        msg_txt = render_template('password_reset_email.txt',
                                  reset_url=reset_url)
        msg_html = render_template('password_reset_email.html',
                                   reset_url=reset_url)

        reset_sender = app.config.get('MAIL_FROM')
        mailer = Mailer(reset_sender)
        result = mailer.send(user.email, "Password reset", msg_txt, msg_html)

        db.session.commit()
        return render_template('request_reset_done.html')

    return render_template('request_reset.html', form=form)


@app.route('/user/reset/t/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Resets a user password if a valid token is provided"""

    t = ResetToken.query.filter_by(
        token=token
    ).options(
        joinedload('user')
    ).first_or_404()

    user = t.user
    form = PasswordChangeForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        app.logger.info("Password changed form reset for %s" % user.email)
        db.session.delete(user.reset_token)
        db.session.commit()
        return render_template('reset_password_done.html')

    return render_template('request_reset_change.html', form=form)

@app.route("/glogin")
@oid.loginhandler
def glogin():
    """Login a user with OpenID (Only Google is supported at the moment);
    if a user is already logged in we update his profile with the current
    OpenID token.

    WARNING: ALPHA VERSION
    """
    openid_url = COMMON_PROVIDERS["google"]
    return oid.try_login(openid_url, ask_for=["email", "fullname", "nickname"])

@oid.after_login
def create_or_login(resp):
    """Registers a new user or performs authentication with OpenID.

    WARNING: ALPHA VERSION

    If an authenticated users requests this page the application will
    update his profile with the current OpenID token; at the moment
    the application *DOESN'T* check if the email address of a user
    is equal to this OpenID email address!
    """
    if current_user.is_authenticated():
        current_user.openid = resp.identity_url
        db.session.commit()
        flash(gettext(u"OpenID profile updated!"), "info")
        return redirect(url_for("index"))

    # Searches for a registered user with a corresponding OpenID token
    # If the user isn't found the application redirects him to the
    # registration page
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None and user.active:
        login_user(user, remember=True)
        flash(gettext(u'Successfully logged in as %(user)s', user=user.email), "success")
        return redirect(oid.get_next_url())
    else:
        session["openid"] = resp.identity_url
        return redirect(url_for("create_profile", next=oid.get_next_url(),
                                name=resp.fullname or resp.nickname,
                                email=resp.email))

@app.route("/create_profile", methods=["GET", "POST"])
def create_profile():
    """Registers a new user with OpenID

    WARNING: ALPHA VERSION

    New user created from this page are *DISABLED* by default and must
    be "approved" by an administrator.
    """

    if "openid" not in session:
        return redirect(url_for("index"))

    email = request.args.get("email")

    form = CreateProfileForm(email=email)
    if form.validate_on_submit():
        password = os.urandom(24)
        user = User(form.username.data, form.email.data, password,
                    openid=session["openid"])
        user.active = False
        db.session.add(user)
        db.session.commit()

        # db.session.refresh(user)

        # login_user(user)
        #flash(u'Successfully logged in as %s' % user.email, "success")
        #session.permanent = True

        #return redirect(oid.get_next_url())

        session.pop("openid", None)
        flash(gettext(u"User registered, now you must wait for an admin approval"), "info")
        return redirect(url_for("index"))

    return render_template("create_profile.html", next_url=oid.get_next_url(),
                           form=form)

@app.route('/user/register', methods=['GET', 'POST'])
def register_user():
    form = RegistrationForm()
    registration_enabled = app.config.get('USER_REGISTRATION_ENABLED')

    if registration_enabled and form.validate_on_submit():
        user = User(form.username.data, form.email.data, form.password.data)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template(
        'register_user.html', form=form,
        registration_enabled=registration_enabled)


def public_access_handler():
    """Handle public access to the web application, for when PUBLIC_ACCESS
    is set to False.

    NOTE: this handler must be registered after flask-login to correctly see
    the authentication status of a user.
    """
    if current_user.is_authenticated():
        return

    if app.config.get('PUBLIC_ACCESS', True):
        return

    public_endpoints = (
        'login', 'register_user', 'reset_request', 'reset_password', 'static',
    )

    if request.endpoint not in public_endpoints:
        return redirect(url_for('login'))
