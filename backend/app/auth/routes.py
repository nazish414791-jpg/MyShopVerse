"""
Auth Routes

Handles registration, login, logout, and profile management (view +
edit details + change password).
"""

from datetime import datetime

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.auth import auth_bp
from app.auth.forms import RegistrationForm, LoginForm, ProfileForm, ChangePasswordForm
from app.extensions import db, oauth
from app.models.user import User


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("auth.profile"))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please log in to continue.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.profile"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user is None or not user.check_password(form.password.data):
            flash("Incorrect email or password. Please try again.", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_active:
            flash("This account has been deactivated. Please contact support.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember_me.data)
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        flash(f"Welcome back, {user.full_name.split()[0]}!", "success")

        next_page = request.args.get("next")
        # Security: only redirect to relative paths (prevents open-redirect attacks)
        if next_page and next_page.startswith("/"):
            return redirect(next_page)

        if user.is_admin:
            # NOTE: admin.dashboard is built in Phase 6 — falls back to profile until then
            try:
                return redirect(url_for("admin.dashboard"))
            except Exception:
                return redirect(url_for("auth.profile"))
        return redirect(url_for("auth.profile"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/login/google")
def google_login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.profile"))

    if not current_app.config.get("GOOGLE_CLIENT_ID") or not hasattr(oauth, "google"):
        flash("Google sign-in isn't set up yet. Please contact the site admin.", "danger")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/login/google/callback")
def google_callback():
    if not hasattr(oauth, "google"):
        flash("Google sign-in isn't set up yet. Please contact the site admin.", "danger")
        return redirect(url_for("auth.login"))

    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo")
        if not user_info:
            user_info = oauth.google.parse_id_token(token, nonce=None)
    except Exception:
        flash("Google sign-in failed or was cancelled. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    google_id = user_info.get("sub")
    email = (user_info.get("email") or "").lower().strip()

    if not google_id or not email:
        flash("Google didn't share the details we need to sign you in.", "danger")
        return redirect(url_for("auth.login"))

    full_name = user_info.get("name") or email.split("@")[0]

    # Match by google_id first, then fall back to an existing email/password account
    # (so someone who registered manually can still use "Continue with Google" later)
    user = User.query.filter_by(google_id=google_id).first()
    if user is None:
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(full_name=full_name, email=email, google_id=google_id, is_active=True)
            db.session.add(user)
        else:
            user.google_id = google_id

    if not user.is_active:
        flash("This account has been deactivated. Please contact support.", "danger")
        return redirect(url_for("auth.login"))

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    login_user(user)
    flash(f"Welcome, {user.full_name.split()[0]}!", "success")

    if user.is_admin:
        try:
            return redirect(url_for("admin.dashboard"))
        except Exception:
            return redirect(url_for("auth.profile"))
    return redirect(url_for("auth.profile"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data
        current_user.address_line = form.address_line.data
        current_user.city = form.city.data
        current_user.postal_code = form.postal_code.data
        current_user.country = form.country.data
        db.session.commit()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    # Recent orders + wishlist for the profile page (matches the mockup layout)
    recent_orders = current_user.orders[:6] if current_user.orders else []
    wishlist = current_user.wishlist_items[:6] if current_user.wishlist_items else []

    return render_template(
        "auth/profile.html",
        form=form,
        recent_orders=recent_orders,
        wishlist=wishlist,
    )


@auth_bp.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template("auth/change_password.html", form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()

        flash("Password updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/change_password.html", form=form)
