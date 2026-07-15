"""
Custom Decorators

admin_required: restricts a view to users with is_admin=True.
Full implementation added in Phase 6 once the User model exists.
"""

from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    """Restrict access to admin users only. Returns 403 otherwise."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return f(*args, **kwargs)

    return decorated_function
