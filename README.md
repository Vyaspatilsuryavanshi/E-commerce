# AURA LUXE — Professional Django E-Commerce Application

A full-stack, server-rendered luxury e-commerce application built with **Python 3.14**, **Django 5.2**, **SQLite for development / PostgreSQL for production**, and **Pillow** for local visual product search.

The application is configured around **Indian Rupees (₹)** and Indian checkout defaults while retaining global boutique locations for the store-locator experience.

## Core capabilities

- Product catalog with departments, categories, brands, filters, sorting, pagination, stock visibility, sales pricing, and product variants.
- Session-backed shopping cart with quantity validation, stock validation, live price refresh, coupon codes, shipping calculation, and AJAX mini-cart support.
- Guest and authenticated checkout with shipping-address validation, browser GPS auto-fill, delivery methods, Razorpay payment order creation, server-side payment verification, signed webhook handling, and transactional stock reservation.
- Customer accounts, secure login/logout/register flows, saved profile/address information, and wishlist management.
- Order confirmation and order-detail pages protected against unauthorized order-number access.
- Authenticated order cancellation with stock restoration and refund-state handling.
- Delivered-order return requests with validation and return workflow statuses.
- Verified-buyer product reviews with aggregate rating updates.
- Store locator and reverse-geocoding APIs with coordinate validation.
- Local camera/file visual search powered by Pillow dominant-color extraction and product tag matching.
- Django admin management for products, variants, reviews, orders, returns, customers, wishlists, brands, and store locations.
- Production-oriented environment configuration, CSRF settings, secure cookies, HSTS, referrer policy, and explicit PostgreSQL selection.

## Payment integration (Razorpay)

Online checkout is integrated with Razorpay Checkout. The server creates a Razorpay order using the final INR total, verifies the checkout signature, fetches the payment from Razorpay and checks the order ID, amount, currency and captured status before marking an order paid. The signed `payment.captured` webhook provides a second confirmation path. Unpaid online orders remain in the `pending_payment` state and cannot enter fulfillment.

Start with Razorpay Test Mode credentials. Add these values to your local `.env` and to your hosting provider's secret environment variables:

```env
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

In the Razorpay Dashboard, configure a webhook to:

```text
https://your-domain.example/orders/payment/razorpay/webhook/
```

Subscribe to the `payment.captured` event and use the exact webhook secret configured in `RAZORPAY_WEBHOOK_SECRET`. Never commit real credentials or use live keys before completing test-mode checkout, webhook and refund operations. Cash on Delivery remains available when selected.

**Pending-payment expiry:** the `expire_pending_orders` management command checks aged Razorpay orders against the provider before releasing reserved inventory. It expires unpaid orders after 30 minutes by default, leaves authorized/in-flight payments untouched, reconciles captured payments, and flags amount mismatches for review. If Razorpay is unavailable, the order and stock reservation are left untouched. Set `PENDING_PAYMENT_EXPIRY_MINUTES` to change the grace period. Run this command from a scheduled worker/cron every 5–10 minutes; the command is safe to rerun. Refunds for already-paid orders are not automated; paid orders cannot be cancelled through the customer self-service action.

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

Copy `.env.example` to `.env`. For local development, keep `DEBUG=True`. Set a strong `SECRET_KEY`, production hosts, database credentials and Razorpay Test Mode credentials only when testing online payments.

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

### 7. Expire abandoned unpaid orders

Run this command manually to process online orders that have been unpaid for at least 30 minutes:

```powershell
python manage.py expire_pending_orders
```

Preview eligible orders without changing inventory:

```powershell
python manage.py expire_pending_orders --dry-run
```

For production, schedule `python manage.py expire_pending_orders` every 5–10 minutes using a persistent worker or the host scheduler. Keep the provider credentials configured; if the provider cannot be reached, the command deliberately leaves the order and reserved stock unchanged.

## Project structure

```text
E-commerce/
├── ecommerce_core/        # Django settings, URLs, ASGI/WSGI
├── store/                 # Catalog, reviews, visual search, stores
├── cart/                  # Session cart, coupons, shipping
├── orders/                # Checkout, Razorpay payments, stock, order lifecycle, returns
├── accounts/              # Authentication, profiles, wishlist
├── static/                # CSS, JavaScript, placeholder assets
├── templates/             # Server-rendered pages
├── requirements.txt
├── .env.example
└── manage.py
```

## Production checklist

Set `DEBUG=False`, provide a long random `SECRET_KEY`, configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, use PostgreSQL, serve static/media through a proper web server or object storage, configure HTTPS, add Razorpay live credentials only after successful Test Mode validation, register the signed webhook, and define an automated expiry policy for abandoned pending-payment reservations. Configure a real refund workflow before allowing paid-order returns to be marked refunded.
