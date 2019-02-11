"""
    qstode.forms.user
    ~~~~~~~~~~~~~~~~~

    User related forms definitions.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import re
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import StringField, PasswordField, ValidationError, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, Optional
from wtforms.fields.html5 import EmailField
from flask_babel import lazy_gettext as _
from qstode.forms.misc import RedirectForm
from qstode.forms.validators import unique_username, unique_email, friendly_email
from ..model.user import User


# Length limit for password validation
USERNAME_MIN = 3
USERNAME_MAX = 20
PASSWORD_MIN = 8
PASSWORD_MAX = 64

# username validation regexp
username_re = re.compile(r"^[A-Za-z0-9_-]+$")


class CreateUserForm(FlaskForm):
    username = StringField(
        _("Username"),
        [
            DataRequired(),
            Length(USERNAME_MIN, USERNAME_MAX),
            Regexp(username_re),
            unique_username(),
        ],
    )
    display_name = StringField(_("Display name"), [DataRequired(), Length(1, 128)])
    email = EmailField(_("Email"), [DataRequired(), unique_email()])
    password = PasswordField(
        _("Password"),
        [DataRequired(), Length(PASSWORD_MIN, PASSWORD_MAX), EqualTo("password_confirm")],
    )
    password_confirm = PasswordField(_("Confirm password"), [DataRequired()])
    active = BooleanField(_("Active"), default=True)
    admin = BooleanField(_("Administrator"), default=False)


class DeleteUserForm(RedirectForm):
    user_id = HiddenField()


class EditUserForm(CreateUserForm):
    """Admin: modify an existing user"""

    # username uniqueness is validated inline
    username = StringField(
        _("Username"), [DataRequired(), Length(USERNAME_MIN, USERNAME_MAX), Regexp(username_re)]
    )
    # email uniqueness is validated inline
    email = EmailField(_("Email"), [DataRequired()])
    password = PasswordField(
        _("Password"), [Optional(), Length(PASSWORD_MIN, PASSWORD_MAX), EqualTo("password_confirm")]
    )
    password_confirm = PasswordField(_("Confirm password"))

    def __init__(self, username, email, *args, **kwargs):
        self._username = username
        self._email = email
        super(EditUserForm, self).__init__(*args, username=username, email=email, **kwargs)

    def validate_username(self, field):
        if field.data != self._username:
            if User.query.filter_by(username=field.data).first() is not None:
                raise ValidationError(_("Username already taken"))

    def validate_email(self, field):
        if field.data != self._email:
            if User.query.filter_by(email=field.data).first() is not None:
                raise ValidationError(_("Email already taken"))


class LoginForm(FlaskForm):
    user = StringField(_("User"), [DataRequired()])
    password = PasswordField(_("Password"), [DataRequired()])
    remember_me = BooleanField(_("Remember me"))


class PasswordResetForm(FlaskForm):
    email = EmailField(_("Email"), [DataRequired(), Email()])


class PasswordChangeForm(FlaskForm):
    password = PasswordField(
        _("New password"),
        [
            DataRequired(),
            Length(min=PASSWORD_MIN, max=PASSWORD_MAX),
            EqualTo("password_confirm", message=_("Passwords must match")),
        ],
    )
    password_confirm = PasswordField(_("Confirm new password"))


class RegistrationForm(FlaskForm):
    display_name = StringField(_("Display name"), [DataRequired(), Length(1, 128)])
    username = StringField(
        _("Username"),
        [DataRequired(), Length(min=3, max=20), Regexp(username_re), unique_username()],
    )
    email = EmailField(_("Email"), [DataRequired(), Email(), friendly_email(), unique_email()])
    password = PasswordField(
        _("Password"),
        [
            DataRequired(),
            Length(min=PASSWORD_MIN, max=PASSWORD_MAX),
            EqualTo("password_confirm", message=_("Passwords must match")),
        ],
    )
    password_confirm = PasswordField(_("Confirm password"), [DataRequired()])


class RecaptchaRegistrationForm(RegistrationForm):
    recaptcha = RecaptchaField()


# unique_username ???
class UserDetailsForm(FlaskForm):
    display_name = StringField(_("Display name"), [DataRequired(), Length(1, 128)])
    password_old = PasswordField(_("Current password"))
    password = PasswordField(
        _("Password"),
        [
            Optional(),
            Length(min=PASSWORD_MIN, max=PASSWORD_MAX),
            EqualTo("password_confirm", message=_("Passwords must match")),
        ],
    )
    password_confirm = PasswordField(_("Confirm new password"))

    def validate(self):
        """Additional validation for `password_old` and `password` fields"""

        success = super(UserDetailsForm, self).validate()

        # If both a new password and the old password was specified
        if self.password.data and self.password_old.data:
            if not current_user.check_password(self.password_old.data):
                self.password_old.errors.append(_("Invalid current password"))
                success = False

        # If only the new password was specified
        elif self.password.data and not self.password_old.data:
            self.password_old.errors.append(_("You must specify your current password"))
            success = False

        return success


class CreateProfileForm(FlaskForm):
    username = StringField(
        _("Username"), [DataRequired(), Length(min=3, max=20), Regexp(username_re), unique_username]
    )
    email = EmailField(_("Email"), [DataRequired(), Email(), unique_email])
