# AURA LUXE — Professional Django E-Commerce Application

A full-stack, server-rendered luxury e-commerce application built with **Python 3.14**, **Django 5.2**, **SQLite for development / PostgreSQL for production**, and **Pillow** for local visual product search.

The application is configured around **Indian Rupees (₹)** and Indian checkout defaults while retaining global boutique locations for the store-locator experience.

## Core capabilities

- Product catalog with departments, categories, brands, filters, sorting, pagination, stock visibility, sales pricing, and product variants.
- Session-backed shopping cart with quantity validation, stock validation, live price refresh, coupon codes, shipping calculation, and AJAX mini-cart support.
- Guest and authenticated checkout with shipping-address validation, browser GPS auto-fill, delivery methods, payment-method selection, order creation, and transactional stock deduction.
- Customer accounts, secure login/logout/register flows, saved profile/address information, and wishlist management.
- Order confirmation and order-detail pages protected against unauthorized order-number access.
- Authenticated order cancellation with stock restoration and refund-state handling.
- Delivered-order return requests with validation and return workflow statuses.
- Verified-buyer product reviews with aggregate rating updates.
- Store locator and reverse-geocoding APIs with coordinate validation.
- Local camera/file visual search powered by Pillow dominant-color extraction and product tag matching.
- Django admin management for products, variants, reviews, orders, returns, customers, wishlists, brands, and store locations.
- Production-oriented environment configuration, CSRF settings, secure cookies, HSTS, referrer policy, and explicit PostgreSQL selection.

## Important payment note

The checkout supports payment method selection and records a clear **demo payment state** for card/UPI/wallet methods. It does **not** connect to a real payment gateway. To accept real money, integrate a provider such as Razorpay, Stripe, PayU, or another gateway and verify payment callbacks/webhooks server-side before marking an order as paid.

## Setup on Windows PowerShell

### 1. Create and activate a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and set at least a strong `SECRET_KEY` for production.

For local SQLite development:

```env
DEBUG=True
USE_POSTGRES=False
```

For PostgreSQL:

```env
DEBUG=False
USE_POSTGRES=True
DB_NAME=ecommerce_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=127.0.0.1
DB_PORT=5432
ALLOWED_HOSTS=your-domain.example
CSRF_TRUSTED_ORIGINS=https://your-domain.example
```

### 4. Apply migrations and seed the demo catalog

The application ships with an idempotent demo catalog command. Run it once after migrations so the homepage department links, product grids, variants, store locations, and sample reviews have data to render.

```powershell
python manage.py migrate
python manage.py seed_store
```

### 5. Create an admin account

```powershell
python manage.py createsuperuser
```

### 6. Run the application

```powershell
python manage.py runserver 8080
```

Open `http://127.0.0.1:8080/`.

## Verification commands

Run these locally after dependency installation:

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
```

`check_db` is available for a database connectivity diagnostic:

```powershell
python manage.py check_db
```

## Project structure

```text
E-commerce/
├── ecommerce_core/        # Django settings, URLs, ASGI/WSGI
├── store/                 # Catalog, reviews, visual search, stores
├── cart/                  # Session cart, coupons, shipping
├── orders/                # Checkout, stock, order lifecycle, returns
├── accounts/              # Authentication, profiles, wishlist
├── static/                # CSS, JavaScript, placeholder assets
├── templates/             # Server-rendered pages
├── requirements.txt
├── .env.example
└── manage.py
```

## Production checklist

Set `DEBUG=False`, provide a long random `SECRET_KEY`, configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, use PostgreSQL, serve static/media through a proper web server or object storage, configure HTTPS, and integrate a real payment gateway before accepting live payments.
