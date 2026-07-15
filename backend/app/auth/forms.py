"""
Auth Forms

Flask-WTF forms for registration, login, and profile management.
Validation happens both here (server-side) and via HTML5 attributes
in the templates (client-side UX).
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, ValidationError, Optional, Regexp
)

from app.models.user import User


class RegistrationForm(FlaskForm):
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(message="Please enter your full name."), Length(min=2, max=120)],
    )
    email = StringField(
        "Email Address",
        validators=[DataRequired(message="Email is required."), Email(message="Enter a valid email address.")],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, message="Password must be at least 8 characters long."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords do not match."),
        ],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        existing_user = User.query.filter_by(email=field.data.lower().strip()).first()
        if existing_user:
            raise ValidationError("An account with this email already exists. Try logging in instead.")


class LoginForm(FlaskForm):
    email = StringField(
        "Email Address",
        validators=[DataRequired(message="Email is required."), Email(message="Enter a valid email address.")],
    )
    password = PasswordField("Password", validators=[DataRequired(message="Password is required.")])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log In")


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    phone = StringField(
        "Phone Number",
        validators=[Optional(), Regexp(r"^[0-9+\-\s()]{7,20}$", message="Enter a valid phone number.")],
    )
    address_line = TextAreaField("Address", validators=[Optional(), Length(max=255)])
    city = StringField("City", validators=[Optional(), Length(max=100)])
    postal_code = StringField("Postal Code", validators=[Optional(), Length(max=20)])
    country = StringField("Country", validators=[Optional(), Length(max=100)])
    submit = SubmitField("Save Changes")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters long.")],
    )
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords do not match.")],
    )
    submit = SubmitField("Update Password")
