# MediSearch Project Structure

- `config/` — Django settings, root URL configuration, ASGI and WSGI.
- `core/` — retained doctor directory and department models.
- `accounts/` — customer/staff profiles, login, role dashboards and team chat.
- `appointments/` — retained appointment booking, notes, prescription and document workflows.
- `pharmacy/` — retained pharmacist POS/inventory module.
- `marketplace/` — medicine catalogue, pharmacy verification, store listings, cart, order requests, stock reservations, prescription privacy checks, retailer/admin/customer views and demo-data command.
- `templates/base.html` — shared navigation, responsive shell, accessible theme toggle and footer.
- `templates/marketplace/` — public medicine pages, dashboards, order/checkout forms and map.
- `static/css/app.css` — retained UI styles plus MediSearch responsive marketplace design and light/dark tokens.
- `requirements.txt` — Python dependencies.
- `.env.example` — safe environment template without actual credentials.
- `render.yaml` — Render web service and PostgreSQL blueprint.

Marketplace relationships:

- `MedicineCategory` → many `MedicineProduct` records.
- `Pharmacy` → many `PharmacyListing` records; a listing connects one pharmacy with one catalogue product.
- `PharmacyListing` tracks MRP, selling price, total available quantity, reserved quantity and last stock update.
- `CartItem` connects a customer to a listing.
- `MarketplaceOrder` connects a customer to one pharmacy, optional private prescription, fulfilment mode and status history.
- `MarketplaceOrderItem` stores a price/product snapshot and refers to the inventory listing.
- `Prescription` is private-by-default and access-checked before download.
