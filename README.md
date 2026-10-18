# MediSearch — Local Pharmacy Marketplace & Inventory Management

MediSearch is a Django-based college-project foundation for discovering listed medicines from participating pharmacies. Customers can search and compare prices, see store-reported availability freshness, maintain a cart, request delivery or pickup, and upload prescriptions privately. Pharmacy owners can submit a store profile for approval, manage medicine listings and process order requests. The project keeps the existing appointment and pharmacy POS modules from the earlier codebase, but the public homepage and navigation are pharmacy-marketplace-first.

> **Important:** This is a development/demo application, not a certified online pharmacy platform. Do not use it for real medicine sales or real patient documents until applicable Indian drug-sale, pharmacy licensing, prescription review, privacy, consumer-protection, payment and delivery requirements have been reviewed and met. Never use fictional demo listings for real healthcare decisions.

## Included functionality

- **Responsive UI:** shared Django templates, Bootstrap 5 grid and utilities, responsive CSS at mobile/tablet/desktop widths, accessible focus styles, collapsible navigation, and persistent light/dark mode. Theme preference is stored in local browser storage and defaults to the device theme when no saved preference exists.
- **Customer discovery:** catalogue categories, search by brand/generic/strength/manufacturer, PIN-code search, delivery/pickup filters, selling-price and discount sorting, medicine detail pages and store profile pages.
- **Public stock privacy:** public medicine listings and the customer cart show an availability status rather than the exact remaining shop quantity. Numeric stock remains in retailer inventory and authorised staff workflows.
- **Saved shortcuts:** customers can save medicine products and verified pharmacies to their profile for quick access later.
- **Pharmacy finder:** public profiles only for approved pharmacies; manual location and PIN-code search; Leaflet/OpenStreetMap map pins when coordinates are available. No browser location permission is requested automatically.
- **Retailer registration and verification:** store and licence fields, pending approval by default, server-side authorization, and a custom admin dashboard for approving, rejecting or suspending pharmacies.
- **Store inventory:** catalogue-linked listings, MRP/selling price validation, quantity and reserved stock, batch and expiry fields, low-stock display and stock-update timestamps. Expired listings are excluded from public search and cannot be accepted in new orders.
- **Cart and order requests:** group cart items by pharmacy, check out one pharmacy at a time, reserve available stock during checkout in a database transaction, track status events, and prevent the same reserved stock from being requested again. Requests are not counted as completed sales.
- **Order workflow:** Pending → Accepted → Processing → Ready for Pickup / Out for Delivery → Completed, with rejection and pending-order cancellation releasing reserved stock. Prescription-required items cannot be accepted until the linked prescription is approved.
- **Prescription workflow:** JPG, PNG and PDF upload (maximum 10 MB), private file paths, owner/reviewer checks for downloads, review notes and audit timestamps. Uploading a prescription does not approve it and OCR/AI is not used to approve prescriptions.
- **Admin controls and audit trail:** Django Admin pages for catalogue, pharmacies, listings, prescriptions, marketplace orders and a read-only marketplace audit log, plus a custom control center with recent sensitive-action activity.
- **Deployment setup:** SQLite for local work, PostgreSQL via `DATABASE_URL`, `requirements.txt`, `.env.example`, `.gitignore`, Render blueprint, WhiteNoise static files, health endpoint, tests, and setup guidance.
- **Existing modules retained:** appointment scheduling, staff dashboards, clinical-document workflows, and the legacy pharmacist inventory/POS remain in the project. Marketplace links are the main navigation; old doctor directory routes remain at `/doctors/`.

## Main URLs

| URL | Purpose |
|---|---|
| `/` | MediSearch homepage |
| `/medicines/` | Medicine search and pharmacy comparison |
| `/medicines/<id>/` | Medicine details and store listings |
| `/pharmacies/` | Approved pharmacy finder and map |
| `/pharmacies/<slug>/` | Public pharmacy details and listings |
| `/accounts/register/` | Customer account registration |
| `/customer/` | Customer orders and prescription overview |
| `/cart/` | Cart grouped by pharmacy |
| `/prescriptions/` | Private prescription list |
| `/retailer/register/` | Submit a pharmacy profile for verification |
| `/retailer/` | Retailer inventory/order dashboard |
| `/retailer/listings/` | Store medicine listings |
| `/retailer/orders/` | Retailer order management |
| `/admin-dashboard/` | Super administrator marketplace overview |
| `/admin/` | Django Admin |
| `/health/` | Health check endpoint |

## Local setup (Windows PowerShell)

Use Python 3.12 or 3.13 for compatibility with common dependencies.

```powershell
cd MediSearch
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `DJANGO_DEBUG=True` in `.env` for local development, then run:

```powershell
python manage.py makemigrations marketplace
python manage.py migrate
python manage.py check
python manage.py test
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

For Command Prompt instead of PowerShell, activate the environment with `.venv\Scripts\activate.bat`.

## Add demo data

To add fictional product categories and catalogue items only:

```powershell
python manage.py seed_marketplace_demo
```

To also create two fictional verified demo stores and sample listings for local UI/workflow testing:

```powershell
python manage.py seed_marketplace_demo --create-demo-users
```

The second command creates demo store-owner accounts with generated temporary passwords and prints them once in the terminal. Keep the credentials local, do not share them, and do not run the demo-user option on a production deployment. Store names, addresses, licence numbers, products, phone numbers, prices and stock are all fictional sample data.

To use the existing appointment demo-data command as well, run `python manage.py seed_demo`.

## Production environment

Copy `.env.example` and set environment variables on the host rather than committing secrets:

- `DJANGO_SECRET_KEY`: long random secret.
- `DJANGO_DEBUG=False`.
- `DJANGO_ALLOWED_HOSTS`: exact comma-separated deployment hostnames.
- `DATABASE_URL`: managed PostgreSQL connection string.
- Email SMTP variables only if email delivery is configured.

The included `render.yaml` defines a Django web service and PostgreSQL database. The build command installs dependencies, collects static files and runs migrations; the start command runs Gunicorn. After deployment, visit `/health/`.

Uploaded prescription files on local disk are not automatically persistent on an ephemeral host. Before production use, configure private durable object storage, encryption/backup policies, retention/deletion handling, audit monitoring and a tested access-control design.

## Current scope boundaries — read before real deployment

This ZIP is a substantial working foundation, but **it does not implement every feature in the master specification**. In particular:

- Payments are not processed online; no live payment gateway or automated refund API is configured.
- A cart checkout is submitted to one pharmacy at a time. Customer delivery is a request workflow; delivery tracking/dispatch integrations are not included.
- Store discovery filters by address/city/PIN and displays map pins only for configured coordinates. Geospatial radius queries, true distance sorting, route optimisation and device GPS permission workflows are not implemented.
- The catalogue uses manually managed records and seed data; there is no live external drug catalogue, automatic therapeutic substitution, or medical recommendation engine.
- The basic staff permission model from the retained clinic codebase is not a full per-action permission matrix for each marketplace staff position.
- Advanced notifications, SMS/WhatsApp integration, customer reviews and complaints, full CSV import/export, supplier purchasing, automated expiry jobs, scheduled reservation expiry, analytics exports and complete compliance audit reporting still need further work.
- File validation checks the filename extension, reported content type, size and basic JPG/PNG/PDF signatures; a production deployment should add malware scanning, robust file-content inspection and private object-storage policies.

The marketplace pages use demo/sample data only when you explicitly seed it. Do not claim inventory is live unless the retailer keeps it current; the UI displays a stock update time and flags stale information. Do not enable real prescription sales until licensing and professional review requirements are verified by the operator.

## GitHub workflow

```bash
git init
git add .
git commit -m "Initial MediSearch pharmacy marketplace"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/medisearch.git
git push -u origin main
```

Never commit `.env`, `db.sqlite3`, private uploaded documents, generated passwords or production credentials. The supplied `.gitignore` excludes the most common local secret/data files.

## Manual responsive QA checklist

Use browser DevTools responsive mode or real devices to inspect **320, 375, 576, 768, 992, 1200 and 1440 CSS-pixel widths**. Check the home page, search filters, pharmacy map, medicine detail/comparison, login/registration, prescription upload, cart, checkout, customer dashboard, retailer tables/forms/orders and admin dashboard. Rotate tablets/phones, resize the browser, verify no horizontal overflow or clipped action buttons, and test keyboard focus and light/dark mode.
