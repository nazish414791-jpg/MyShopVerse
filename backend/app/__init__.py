"""
Application Factory

This is the central factory that:
  1. Creates the Flask app instance
  2. Loads configuration
  3. Initializes extensions (db, login, csrf, etc.)
  4. Registers all blueprints
  5. Registers error handlers and Jinja context processors

Using the factory pattern (instead of a single global `app` object)
keeps the codebase testable and avoids circular imports.
"""

import os
from flask import Flask, render_template

from config import config
from app.extensions import db, migrate, login_manager, bcrypt, csrf, oauth


def create_app(config_name=None):
    """Application factory — builds and returns a configured Flask app."""

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    # Templates and static assets now live in the sibling `frontend/` folder
    # instead of inside `backend/app/`, so we point Flask at them explicitly.
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend")
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=os.path.join(frontend_dir, "templates"),
        static_folder=os.path.join(frontend_dir, "static"),
    )
    app.config.from_object(config[config_name])

    # Ensure instance/ and uploads/ folders exist (SQLite file + user uploads)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)
    _register_home_route(app)

    return app


def _register_home_route(app):
    """Renders the storefront homepage at the bare domain ('/')."""
    from flask import render_template

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/")
    def index():
        from app.models.product import Product, Category

        featured_products = (
            Product.query.filter_by(is_active=True, is_featured=True)
            .order_by(Product.created_at.desc())
            .limit(8)
            .all()
        )
        # Backfill with recent products if fewer than 8 are marked featured
        if len(featured_products) < 8:
            extra = (
                Product.query.filter_by(is_active=True)
                .filter(Product.id.notin_([p.id for p in featured_products]) if featured_products else True)
                .order_by(Product.created_at.desc())
                .limit(8 - len(featured_products))
                .all()
            )
            featured_products += extra

        # New Arrivals: freshest products, excluding anything already shown in Editor's Picks
        featured_ids = [p.id for p in featured_products]
        new_arrivals = (
            Product.query.filter_by(is_active=True)
            .filter(Product.id.notin_(featured_ids) if featured_ids else True)
            .order_by(Product.created_at.desc())
            .limit(8)
            .all()
        )

        # Most Loved: a further distinct set, excluding anything shown above
        shown_ids = featured_ids + [p.id for p in new_arrivals]
        most_loved = (
            Product.query.filter_by(is_active=True)
            .filter(Product.id.notin_(shown_ids) if shown_ids else True)
            .order_by(Product.price.desc())
            .limit(8)
            .all()
        )
        # If the catalog is small, backfill Most Loved from the featured pool rather than leaving it empty
        if len(most_loved) < 6 and featured_products:
            most_loved += [p for p in featured_products if p not in most_loved][: 6 - len(most_loved)]

        categories = Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()

        return render_template(
            "home.html",
            featured_products=featured_products,
            new_arrivals=new_arrivals,
            most_loved=most_loved,
            categories=categories,
        )


def _register_extensions(app):
    """Bind shared extension instances to this app."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    oauth.init_app(app)
    if app.config.get("GOOGLE_CLIENT_ID") and app.config.get("GOOGLE_CLIENT_SECRET"):
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url=app.config["GOOGLE_DISCOVERY_URL"],
            client_kwargs={"scope": "openid email profile"},
        )

    @login_manager.user_loader
    def load_user(user_id):
        # Imported here (not top-level) to avoid circular imports with models
        from app.models.user import User
        return User.query.get(int(user_id))


def _register_blueprints(app):
    """Register all feature blueprints with the app."""
    from app.auth import auth_bp
    from app.products import products_bp
    from app.cart import cart_bp
    from app.orders import orders_bp
    from app.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)


def _register_error_handlers(app):
    """Custom error pages matching the ShopVerse UI theme."""

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/404.html", error_code=403,
                                message="You don't have permission to view this page."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html", error_code=404,
                                message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()  # roll back any broken transaction
        return render_template("errors/500.html", error_code=500,
                                message="Something went wrong on our end."), 500


def _register_context_processors(app):
    """Make common variables available to every template automatically."""

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        from flask_login import current_user
        cart_count = 0
        if current_user.is_authenticated:
            from app.models.cart import CartItem
            cart_count = (
                db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity), 0))
                .filter(CartItem.user_id == current_user.id)
                .scalar()
            ) or 0
        return {
            "store_name": app.config["STORE_NAME"],
            "currency": app.config["CURRENCY_SYMBOL"],
            "current_year": datetime.utcnow().year,
            "cart_item_count": cart_count,
        }
