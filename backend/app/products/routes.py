"""
Products Routes

Three browsing experiences:
  1. "Catalog" mode (/products/, no filters): sectioned by category.
  2. "Category" mode (/products/?category=X, no other filters): a rich
     category landing — hero banner, related collections, then the
     category's own subcategories (e.g. Rings, Chains, Bracelets),
     each shown as its own row with a "View All" link.
  3. "Filtered" mode (search, subcategory, price, or sort active):
     the classic sidebar + paginated grid.
"""

from decimal import Decimal, InvalidOperation

from flask import render_template, request, current_app
from sqlalchemy import or_

from app.products import products_bp
from app.models.product import Product, Category


@products_bp.route("/")
def listing():
    query = request.args.get("q", "").strip()
    category_slug = request.args.get("category", "").strip()
    subcategory = request.args.get("subcategory", "").strip()
    sort = request.args.get("sort", "newest")
    page = request.args.get("page", 1, type=int)
    min_price_raw = request.args.get("min_price", "").strip()
    max_price_raw = request.args.get("max_price", "").strip()

    categories = Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()
    active_category = None
    if category_slug:
        active_category = Category.query.filter_by(slug=category_slug, is_active=True).first()

    no_filters_active = not (query or min_price_raw or max_price_raw or sort != "newest" or subcategory)

    # ---- MODE 1: Full catalog, sectioned by category ----
    if no_filters_active and not category_slug:
        catalog_sections = []
        for cat in categories:
            products = (
                Product.query.filter_by(category_id=cat.id, is_active=True)
                .order_by(Product.created_at.desc())
                .limit(6)
                .all()
            )
            if products:
                catalog_sections.append({"category": cat, "products": products})

        featured_products = (
            Product.query.filter_by(is_featured=True, is_active=True)
            .order_by(Product.created_at.desc())
            .limit(8)
            .all()
        )
        if len(featured_products) < 8:
            # Top up with newest active products so the section never looks sparse
            existing_ids = {p.id for p in featured_products}
            top_up = (
                Product.query.filter(Product.is_active.is_(True), ~Product.id.in_(existing_ids) if existing_ids else True)
                .order_by(Product.created_at.desc())
                .limit(8 - len(featured_products))
                .all()
            )
            featured_products = featured_products + top_up

        return render_template(
            "products/listing.html",
            view_mode="catalog",
            catalog_sections=catalog_sections,
            featured_products=featured_products,
            categories=categories,
            active_category=None,
            query=query, sort=sort, min_price=min_price_raw, max_price=max_price_raw,
        )

    # ---- MODE 2: Category landing, sectioned by subcategory ----
    if no_filters_active and active_category:
        subcats = (
            db_distinct_subcategories(active_category.id)
        )
        subcategory_sections = []
        for subcat_name in subcats:
            products = (
                Product.query.filter_by(category_id=active_category.id, subcategory=subcat_name, is_active=True)
                .order_by(Product.created_at.desc())
                .limit(6)
                .all()
            )
            if products:
                subcategory_sections.append({"name": subcat_name, "products": products})

        # Products with no subcategory assigned, shown in their own row
        uncategorized = (
            Product.query.filter_by(category_id=active_category.id, subcategory=None, is_active=True)
            .order_by(Product.created_at.desc())
            .limit(6)
            .all()
        )
        if uncategorized:
            subcategory_sections.append({"name": "More in " + active_category.name, "products": uncategorized})

        related_categories = [c for c in categories if c.id != active_category.id]

        return render_template(
            "products/listing.html",
            view_mode="category",
            subcategory_sections=subcategory_sections,
            subcategory_names=subcats,
            categories=categories,
            related_categories=related_categories,
            active_category=active_category,
            query=query, sort=sort, min_price=min_price_raw, max_price=max_price_raw,
        )

    # ---- MODE 3: Filtered / searched — sidebar + paginated grid ----
    products_query = Product.query.filter_by(is_active=True)

    if query:
        like_pattern = f"%{query}%"
        products_query = products_query.filter(
            or_(
                Product.name.ilike(like_pattern),
                Product.description.ilike(like_pattern),
                Product.tags.ilike(like_pattern),
            )
        )

    if active_category:
        products_query = products_query.filter(Product.category_id == active_category.id)

    if subcategory:
        products_query = products_query.filter(Product.subcategory == subcategory)

    try:
        if min_price_raw:
            products_query = products_query.filter(Product.price >= Decimal(min_price_raw))
        if max_price_raw:
            products_query = products_query.filter(Product.price <= Decimal(max_price_raw))
    except InvalidOperation:
        pass

    if sort == "price_asc":
        products_query = products_query.order_by(Product.price.asc())
    elif sort == "price_desc":
        products_query = products_query.order_by(Product.price.desc())
    elif sort == "name_asc":
        products_query = products_query.order_by(Product.name.asc())
    else:
        products_query = products_query.order_by(Product.created_at.desc())

    pagination = products_query.paginate(
        page=page, per_page=current_app.config["PRODUCTS_PER_PAGE"], error_out=False
    )

    subcats_for_sidebar = db_distinct_subcategories(active_category.id) if active_category else []
    related_categories = [c for c in categories if not active_category or c.id != active_category.id]

    return render_template(
        "products/listing.html",
        view_mode="filtered",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        related_categories=related_categories,
        active_category=active_category,
        active_subcategory=subcategory,
        subcategory_names=subcats_for_sidebar,
        query=query, sort=sort, min_price=min_price_raw, max_price=max_price_raw,
    )


def db_distinct_subcategories(category_id):
    """Returns the distinct, non-null subcategory names within a category, in a stable order."""
    rows = (
        Product.query.with_entities(Product.subcategory)
        .filter(Product.category_id == category_id, Product.subcategory.isnot(None), Product.is_active.is_(True))
        .distinct()
        .order_by(Product.subcategory.asc())
        .all()
    )
    return [r[0] for r in rows]


@products_bp.route("/<slug>")
def detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()

    related_products = (
        Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.is_active.is_(True),
        )
        .limit(4)
        .all()
    )

    return render_template("products/product_detail.html", product=product, related_products=related_products)
