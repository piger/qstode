# -*- coding: utf-8 -*-
"""
    qstode.views.user
    ~~~~~~~~~~~~~~~~~

    Flask views related to user authentication and authorization.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from urlparse import urljoin
from flask import session, request, redirect, flash, render_template, url_for
from flask_login import login_user, login_required, logout_user, current_user
from flask_babel import gettext
from sqlalchemy.orm import joinedload
from qstode.app import app, login_manager
from qstode.mailer import Mailer
from qstode import db
from ..model import User
from qstode import forms


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

    form = forms.LoginForm()
    login_failed = False

    if form.validate_on_submit():
        if u'@' in form.user.data:
            user = User.query.filter_by(email=form.user.data).first()
        else:
            user = User.query.filter_by(username=form.user.data).first()

        if user and user.active and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(gettext(u"Successfully logged in as %(user)s", user=user.username), "success")
            return form.redirect('index')

        login_failed = True
        app.logger.info("Failed login from %s" % form.user.data)

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

    form = forms.UserDetailsForm(username=current_user.username)

    if form.validate_on_submit():
        if form.username.data != current_user.username:
            current_user.username = form.username.data

        if form.password.data:
            current_user.set_password(form.password.data)

        db.Session.commit()
        flash(gettext(u"Profile successfully updated"), 'success')
        return redirect(url_for('user_details'))

    return render_template('user_details.html', form=form)


@app.route('/user/reset/request', methods=['GET', 'POST'])
def reset_request():
    """Begins the password reset procedure"""

    form = forms.PasswordResetForm()

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

        user.reset_token = model.ResetToken()
        token = user.reset_token.token

        reset_url = make_external(url_for('reset_password', token=token))
        msg_txt = render_template('password_reset_email.txt',
                                  reset_url=reset_url)
        msg_html = render_template('password_reset_email.html',
                                   reset_url=reset_url)

        reset_sender = app.config.get('MAIL_FROM')
        mailer = Mailer(reset_sender)
        result = mailer.send(user.email, "Password reset", msg_txt, msg_html)

        db.Session.commit()
        return render_template('request_reset_done.html')

    return render_template('request_reset.html', form=form)


@app.route('/user/reset/t/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Resets a user password if a valid token is provided"""

    t = model.ResetToken.query.filter_by(
        token=token
    ).options(
        joinedload('user')
    ).first_or_404()

    user = t.user
    form = forms.PasswordChangeForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        app.logger.info("Password changed form reset for %s" % user.email)
        db.Session.delete(user.reset_token)
        db.Session.commit()
        return render_template('reset_password_done.html')

    return render_template('request_reset_change.html', form=form)


@app.route('/user/register', methods=['GET', 'POST'])
def register_user():
    form = forms.RegistrationForm()
    registration_enabled = app.config.get('USER_REGISTRATION_ENABLED')

    if registration_enabled and form.validate_on_submit():
        user = User(form.username.data, form.email.data, form.password.data)
        db.Session.add(user)
        db.Session.commit()

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
