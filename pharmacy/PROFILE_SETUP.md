# MediSearch Profile Management Add-on

This is an **add-on patch** for the existing MediSearch Django project. It does not replace the whole website. It adds a reusable `profiles` app and a safe, repeatable installer. The installer registers the app and URLs, adds a profile link, connects save/unsave actions to the existing medicine/pharmacy detail pages, and lets checkout fill its existing delivery-address field from the current user's saved address book. It backs up every existing file it changes into a timestamped sibling folder outside the Git repository.

## Included functionality

- Role-aware profile overview for customer accounts, existing pharmacy owners, existing `StaffProfile` users and administrators.
- Edit name, email, personal phone, optional date of birth and profile picture.
- Profile picture preview before save, plus server-side content validation (JPEG/PNG/WebP only; 2 MB limit) and an authenticated image endpoint.
- Retailer profile editing using the existing `marketplace.Pharmacy` record. Pharmacy verification status and licence fields remain administrator-controlled.
- Customer address book with ownership checks, default address selection, and create/edit/delete actions; checkout can fill the existing delivery-address field from one of the signed-in customer's own saved addresses.
- Customer order/prescription summaries using existing marketplace models; prescription file access remains through the existing secure download view.
- Saved medicine and verified pharmacy lists, with CSRF-protected save/remove actions on the existing product and pharmacy detail pages. Saved items do not reserve stock, prescribe medication or place orders.
- Store language, preferred fulfilment and notification preferences.
- Password change using Django's built-in `PasswordChangeForm`, retaining the current session after success.
- Download of account/order/address/prescription metadata as a private JSON export.
- Account deletion request for administrator review. This deliberately does **not** instantly delete the user or legal transaction records.
- Profile/address/deletion/security changes are recorded through the existing `MarketplaceAuditLog` without logging passwords or uploaded file content.
- Responsive layout styled to match MediSearch and its existing light/dark theme variables.
- Starter tests for login gating, address ownership, default addresses, export privacy and preference persistence.

## Install on Windows / VS Code

1. Make a backup/commit of the current repository before applying the add-on.
2. Download this ZIP and extract it **into the inner project folder containing `manage.py`**, normally:

   `C:\Users\susob\OneDrive\Desktop\MediSearch\MediSearch`

   It should add `profiles/`, `templates/profiles/`, `static/profiles/`, `apply_profile_addon.py`, `PROFILE_SETUP.md`, `PROFILE_CHANGELOG.md` and `ADDON_FILE_MANIFEST.txt`. Do not extract into `C:\Users\susob` or the outer `Desktop\MediSearch` folder.
3. Open PowerShell in that project folder and run:

   ```powershell
   python apply_profile_addon.py
   python manage.py check
   python manage.py migrate
   python manage.py test profiles
   python manage.py runserver
   ```

   The installer saves backups of all integration files it changes in a timestamped sibling folder **outside the Git repository**. It is safe to run again; it detects existing routes, navigation links, favorite controls and address selectors to avoid duplication.
4. Sign in and open `http://127.0.0.1:8000/profile/`. The authenticated navigation also gains a **My profile** link.
5. Test `/profile/edit/`, `/profile/addresses/`, `/profile/saved/`, `/profile/preferences/`, `/profile/security/` and `/profile/export/` on mobile and desktop widths. Also test saving/removing an item from an existing medicine detail page and pharmacy detail page, and selecting a saved address at checkout.

## Commit only the add-on and its integration changes

First inspect the files:

```powershell
git status
```

Ensure no `.env`, credentials, local database, prescription uploads or other private files are staged. Then stage only the expected files:

```powershell
git add profiles templates/profiles static/profiles apply_profile_addon.py PROFILE_SETUP.md PROFILE_CHANGELOG.md ADDON_FILE_MANIFEST.txt config/settings.py config/urls.py templates/base.html marketplace/views.py templates/marketplace/checkout.html templates/marketplace/pharmacy_detail.html templates/marketplace/medicine_detail.html
git status
git commit -m "Add role-aware profile management"
git push origin main
```

Render should deploy the commit if the GitHub repository and auto-deploy are connected. Otherwise trigger **Manual Deploy → Deploy latest commit** from Render.

## Existing project data reused

This app reuses Django's existing user model; `accounts.PatientProfile` and `accounts.StaffProfile`; `marketplace.Pharmacy`, `PharmacyListing`, `MarketplaceOrder`, `Prescription` and `MarketplaceAuditLog`. It creates only supporting models for supplemental personal preferences, customer addresses, account-deletion requests and the user's saved pharmacy/medicine list. Historical migrations are not edited.

## Important limitations to review before production

- This add-on integrates profile operations with existing models, but does not implement every optional item from the master prompt. The current source has no dedicated pharmacy-staff membership/permission model or platform notification-delivery backend. The staff page uses the existing clinic `StaffProfile`; it does not invent a pharmacy assignment. Notification toggles save preferences but do not send email/SMS/in-app notifications themselves.
- The retailer form only edits a pharmacy owned by the current user; if the account owns multiple pharmacies, select the intended store in the form. Verification status and licence approval remain administrator-controlled.
- Checkout can preload and fill the existing delivery-address text field from a saved address belonging to the signed-in user. The order keeps its current text snapshot rather than a foreign-key link to the address, so changing/removing an address later does not rewrite historical orders.
- Email-change verification reuses the existing account verification route only when the account had a verified `PatientProfile`. SMTP must be configured for email to be delivered.
- Avatar files use Django's configured default media storage and are returned through an authenticated endpoint. A typical Render instance has ephemeral local storage; configure persistent disk/object storage before relying on uploaded avatars across redeployments. Keep private prescriptions in the existing private download flow and do not expose them through a public media URL.
- Two-factor authentication, active-session enumeration/revocation, phone OTP verification, deletion execution, support tickets and notification delivery are not implemented by this add-on. Deletion requests require manual administrator review.

## Verification status

Python source files are syntax-compiled when this archive is built. Django runtime checks and the included test suite still need to be run inside your project environment after extracting and installing the add-on, since the packaging environment does not have Django installed.

## Existing files the installer changes

The installer makes the smallest integration edits it can identify safely. It backs up the actual pre-edit copies and creates a path-only `PROJECT_FILE_MANIFEST.txt` in a timestamped sibling backup folder before writing any changes.

| Existing file | Reason for change |
|---|---|
| `config/settings.py` | Register the new `profiles` Django app. |
| `config/urls.py` | Mount profile routes below `/profile/`. |
| `templates/base.html` | Add a profile entry to the existing logged-in navigation. |
| `marketplace/views.py` | Supply saved-state flags to existing detail pages and provide the current user's saved addresses to checkout. |
| `templates/marketplace/checkout.html` | Add a selector that fills the existing delivery-address field from a saved address. |
| `templates/marketplace/pharmacy_detail.html` | Add a CSRF-protected Save/Remove pharmacy control for authenticated users. |
| `templates/marketplace/medicine_detail.html` | Add a CSRF-protected Save/Remove medicine control for authenticated users. |

The new models are introduced through `profiles/migrations/0001_initial.py` and `profiles/migrations/0002_saveditems.py`. No pre-existing migration is edited.
