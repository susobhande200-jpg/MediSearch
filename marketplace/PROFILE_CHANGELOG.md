# MediSearch Profile Add-on — Change Summary

## New Django app and supporting files

- `profiles/` — role-aware profile views, forms, models, routes, admin registrations, migrations and tests.
- `templates/profiles/` — profile overview, edit profile, address book, saved items, preferences and security screens.
- `static/profiles/profile.css` — responsive profile styling using MediSearch theme variables.
- `static/profiles/profile.js` — client-side avatar preview with size/extension guidance; server validation remains authoritative.
- `apply_profile_addon.py` — idempotent installer and safety backup/manifest generator; provides both desktop and mobile profile navigation links.
- `PROFILE_SETUP.md` — installation, testing, deployment, limitations and Git instructions.
- `ADDON_FILE_MANIFEST.txt` — file inventory for the add-on and existing integration targets.

## Existing files integrated by the installer

1. `config/settings.py` — register the app.
2. `config/urls.py` — include `/profile/` routes.
3. `templates/base.html` — add the existing navbar profile link.
4. `marketplace/views.py` — connect existing detail pages to favorite state; provide saved address options to checkout.
5. `templates/marketplace/checkout.html` — add saved address selector while retaining the original delivery-address field.
6. `templates/marketplace/pharmacy_detail.html` — add authenticated save/remove pharmacy action.
7. `templates/marketplace/medicine_detail.html` — add authenticated save/remove medicine action.

The installer copies exact pre-edit versions of those existing files into a timestamped sibling backup directory outside the project root and writes a path-only project file manifest before it writes the changes.

## Data and security approach

- Reuses Django's current user system and existing pharmacy, prescription and order models.
- Enforces per-user address and saved-item filtering; save/remove operations are POST-only and CSRF-protected.
- Retains the existing private prescription download flow; account export includes prescription metadata only.
- Does not instant-delete accounts, invent prescription approvals, reserve inventory for favorites or claim that unsent notification toggles deliver messages.

## Verification caveat

The installer was tested on a clean extracted copy of the supplied project and on a second run for idempotency. Python syntax compilation passed. Django runtime tests and real browser-based responsive tests still need to be executed in the user's project environment because Django was unavailable in this packaging environment.
