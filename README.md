# ShopVerse

**Developed by Vishma Noor**

A full-stack e-commerce web application built with Flask. ShopVerse provides
a complete online storefront experience — product browsing, cart and
checkout with real card payments, order tracking, and account management on
the customer side, plus a full admin dashboard for managing the catalog,
orders, and customers.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Environment Variables](#environment-variables)
6. [Database](#database)
7. [Admin Access](#admin-access)
8. [Payments (Stripe)](#payments-stripe)
9. [Google Sign-In](#google-sign-in)
10. [Deployment Notes](#deployment-notes)
11. [Author](#author)

---

## Features

**Storefront**
- Product catalog with categories, subcategories, search, sorting, and pagination
- Product detail pages with image gallery, specifications, and customer reviews
- Shopping cart and wishlist
- Checkout with Cash on Delivery or secure card payment via Stripe
- Order confirmation, order history, and per-order tracking
- Customer accounts with email/password login or "Continue with Google"
- Editable profile and password management

**Admin Dashboard**
- Sales analytics overview
- Product management (create, edit, delete, stock and pricing control)
- Category management
- Order management with status updates (Pending → Shipped → Delivered / Cancelled)
- Customer management with order history per customer

**Design**
- Fully responsive, custom-designed UI (no off-the-shelf admin theme)
- Light/warm luxury brand aesthetic used consistently across every page

## Tech Stack

| Layer            | Technology                          |
|-------------------|--------------------------------------|
| Backend           | Python, Flask (application factory + blueprints) |
| Database          | SQLite (via SQLAlchemy ORM)          |
| Auth              | Flask-Login, Flask-Bcrypt, Authlib (Google OAuth) |
| Forms             | Flask-WTF, WTForms                   |
| Payments          | Stripe                                |
| Frontend          | Jinja2 templates, Tailwind CSS (CDN), vanilla JS |
| Migrations        | Flask-Migrate (optional, not yet initialized) |

## Project Structure

```
ShopVerse/
├── backend/                       # All Python / application logic
│   ├── app/
│   │   ├── admin/                 # Admin dashboard blueprint (routes, forms)
│   │   ├── auth/                  # Login, registration, profile, Google OAuth
│   │   ├── cart/                  # Cart, checkout, wishlist, Stripe payment flow
│   │   ├── orders/                # Customer-facing order history
│   │   ├── products/              # Product listing & detail pages
│   │   ├── models/                # SQLAlchemy models: User, Product, Order, Cart
│   │   ├── utils/                 # Shared helpers, decorators, Stripe client
│   │   ├── extensions.py          # Shared Flask extension instances
│   │   └── __init__.py            # Application factory (points to ../frontend for templates/static)
│   ├── instance/                  # Local SQLite database (created at runtime, git-ignored)
│   ├── config.py                  # Environment-based configuration classes
│   ├── seed.py                    # Populates the database with demo data
│   ├── run.py                     # Application entry point
│   ├── requirements.txt           # Python dependencies
│   └── .env                       # Local environment variables (git-ignored)
├── frontend/                      # All templates & static assets
│   ├── templates/                 # Jinja2 templates for every page
│   └── static/                    # CSS, images, favicons, uploaded files
├── .gitignore
└── README.md
```

> **Note:** This is a server-rendered Flask app (Jinja2, not a separate JS
> frontend), so `frontend/` and `backend/` are an organizational split only —
> Flask (in `backend/`) is configured to read templates and static files
> straight out of `frontend/`. All commands below are still run from
> `backend/`.

## Getting Started

**0. Move into the backend folder** (all commands below run from here)
```bash
cd backend
```

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure environment variables**

A `.env` file is already included with safe local defaults. At minimum,
review and update:
- `SECRET_KEY` — replace with your own random string before deploying
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` — the admin account created on first seed

See [Environment Variables](#environment-variables) below for the full list.

**3. Seed the database**
```bash
python seed.py
```
This creates all database tables and populates them with demo products,
categories, customers, and one admin account.

**4. Run the app**
```bash
python run.py
```
Then open **http://localhost:5000** in your browser.

## Environment Variables

All variables live in `.env` (already git-ignored, never commit real secrets).

| Variable | Purpose |
|---|---|
| `FLASK_APP` / `FLASK_ENV` | Standard Flask entry point / environment |
| `SECRET_KEY` | Signs sessions and CSRF tokens — must be unique in production |
| `DATABASE_URL` | Database connection string (defaults to local SQLite) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Credentials for the admin account created by `seed.py` |
| `MAX_CONTENT_LENGTH` / `UPLOAD_FOLDER` | File upload limits and destination |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Enables "Continue with Google" — see below |
| `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_CURRENCY` | Enables real card payments at checkout — see below |

## Database

ShopVerse uses SQLite by default (file created at `instance/shopverse.db`).
Running `python seed.py` will:
1. Create all tables based on the models in `app/models/`
2. Insert demo categories and products
3. Create demo customer accounts
4. Create one admin account using `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env`

Re-running `seed.py` is safe to use for a fresh demo dataset; back up
`instance/shopverse.db` first if you want to keep existing data.

## Admin Access

After seeding, log in at `/auth/login` using the `ADMIN_EMAIL` and
`ADMIN_PASSWORD` values set in your `.env` file, then visit `/admin` for the
dashboard. Change these credentials before deploying anywhere public.

## Payments (Stripe)

Card payments at checkout are powered by Stripe.
1. Create a free account at https://dashboard.stripe.com/register
2. Copy your **test** keys from https://dashboard.stripe.com/test/apikeys into
   `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` to try it out risk-free
3. (Optional) Create a webhook at https://dashboard.stripe.com/webhooks
   pointing to `<your-domain>/cart/checkout/stripe/webhook`, listening for
   `checkout.session.completed`, and paste its signing secret into
   `STRIPE_WEBHOOK_SECRET`
4. Switch to live keys only when ready to accept real payments

Without Stripe keys configured, customers can still check out using Cash on
Delivery.

## Google Sign-In

"Continue with Google" on the login page requires your own OAuth credentials:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create an **OAuth client ID** of type **Web application**
3. Add this Authorized redirect URI: `http://localhost:5000/auth/google/callback`
   (replace with your real domain once deployed)
4. Paste the generated Client ID / Secret into `GOOGLE_CLIENT_ID` /
   `GOOGLE_CLIENT_SECRET` in `.env`

Without these set, the Google button will show a friendly "not configured"
message instead of failing — email/password login is unaffected.

## Deployment Notes

- Set `FLASK_ENV=production` and provide a strong, unique `SECRET_KEY`
- Use a production-grade database (e.g. PostgreSQL) via `DATABASE_URL` instead
  of SQLite for anything beyond a demo
- Serve the app behind a WSGI server (e.g. Gunicorn) and a reverse proxy,
  not the built-in Flask development server
- Ensure `SESSION_COOKIE_SECURE` is respected by running behind HTTPS

## Author

**Vishma Noor**
Email: vishmanoor9@gmail.com
