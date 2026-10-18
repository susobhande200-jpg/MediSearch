"""Safely integrate the MediSearch profile add-on with the existing Django project.

Run from the project root (the directory containing manage.py) after extracting
this add-on ZIP. Existing files are backed up outside the Git repository before
any edits are written. The installer is idempotent.
"""
from datetime import datetime
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    ROOT / "manage.py",
    ROOT / "config" / "settings.py",
    ROOT / "config" / "urls.py",
    ROOT / "templates" / "base.html",
    ROOT / "profiles" / "apps.py",
    ROOT / "marketplace" / "views.py",
    ROOT / "templates" / "marketplace" / "checkout.html",
    ROOT / "templates" / "marketplace" / "pharmacy_detail.html",
    ROOT / "templates" / "marketplace" / "medicine_detail.html",
]
missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
if missing:
    print("ERROR: Extract the add-on into the inner Django project folder containing manage.py.")
    print("Missing required files:")
    for item in missing:
        print(f"  - {item}")
    sys.exit(1)

FILES = {
    "config/settings.py": ROOT / "config" / "settings.py",
    "config/urls.py": ROOT / "config" / "urls.py",
    "templates/base.html": ROOT / "templates" / "base.html",
    "marketplace/views.py": ROOT / "marketplace" / "views.py",
    "templates/marketplace/checkout.html": ROOT / "templates" / "marketplace" / "checkout.html",
    "templates/marketplace/pharmacy_detail.html": ROOT / "templates" / "marketplace" / "pharmacy_detail.html",
    "templates/marketplace/medicine_detail.html": ROOT / "templates" / "marketplace" / "medicine_detail.html",
}
ORIGINALS = {key: path.read_text(encoding="utf-8") for key, path in FILES.items()}
UPDATED = dict(ORIGINALS)

# 1) Register the add-on Django app.
settings_text = UPDATED["config/settings.py"]
match = re.search(r"(INSTALLED_APPS\s*=\s*\[)(.*?)(\n\])", settings_text, flags=re.S)
if not match:
    raise SystemExit("ERROR: Could not safely locate INSTALLED_APPS in config/settings.py. No files were changed.")
apps_block = match.group(2)
if not re.search(r"[\"']profiles[\"']", apps_block):
    new_block = apps_block.rstrip() + '\n    "profiles",'
    settings_text = settings_text[:match.start()] + match.group(1) + new_block + match.group(3) + settings_text[match.end():]
UPDATED["config/settings.py"] = settings_text

# 2) Mount the profile URLs.
urls_text = UPDATED["config/urls.py"]
if 'include("profiles.urls")' not in urls_text and "include('profiles.urls')" not in urls_text:
    if not re.search(r"from\s+django\.urls\s+import[^\n]*\binclude\b", urls_text):
        import_match = re.search(r"from\s+django\.urls\s+import\s+([^\n]+)", urls_text)
        if not import_match:
            raise SystemExit("ERROR: Could not safely add Django's include import in config/urls.py. No files were changed.")
        imported = import_match.group(1).strip()
        urls_text = urls_text[:import_match.start()] + f"from django.urls import {imported}, include" + urls_text[import_match.end():]
    if "urlpatterns = [" not in urls_text:
        raise SystemExit("ERROR: Could not locate urlpatterns in config/urls.py. No files were changed.")
    urls_text = urls_text.replace("urlpatterns = [", 'urlpatterns = [\n    path("profile/", include("profiles.urls")),', 1)
UPDATED["config/urls.py"] = urls_text

# 3) Put a profile link into the existing logged-in navbar.
base_text = UPDATED["templates/base.html"]
if "profile_overview" not in base_text:
    marker = '''      <a class="btn btn-light-outline rounded-pill px-3" href="{% url 'prescriptions' %}"><i class="bi bi-file-medical me-1"></i>Prescriptions</a>'''
    if marker not in base_text:
        # Try the existing mobile account menu if this variant of the navbar differs.
        mobile_marker = '''      <li class="nav-item nav-mobile-account d-lg-none"><a class="nav-link" href="{% url 'prescriptions' %}"><i class="bi bi-file-earmark-medical me-1"></i>My prescriptions</a></li>'''
        if mobile_marker not in base_text:
            raise SystemExit("ERROR: Could not locate an existing prescriptions navigation link in templates/base.html. No files were changed.")
        addition = '''      <li class="nav-item nav-mobile-account d-lg-none"><a class="nav-link" href="{% url 'profile_overview' %}"><i class="bi bi-person-circle me-1"></i>My profile</a></li>\n'''
        base_text = base_text.replace(mobile_marker, addition + mobile_marker, 1)
    else:
        addition = '''      <a class="btn btn-light-outline rounded-pill px-3" href="{% url 'profile_overview' %}"><i class="bi bi-person-circle me-1"></i>My profile</a>\n'''
        base_text = base_text.replace(marker, addition + marker, 1)

# Whether the desktop item already exists or not, also ensure the mobile menu has it.
mobile_marker = '''      <li class="nav-item nav-mobile-account d-lg-none"><a class="nav-link" href="{% url 'prescriptions' %}"><i class="bi bi-file-earmark-medical me-1"></i>My prescriptions</a></li>'''
mobile_profile_link_start = '''<li class="nav-item nav-mobile-account d-lg-none"><a class="nav-link" href="{% url 'profile_overview' %}">'''
if mobile_profile_link_start not in base_text and mobile_marker in base_text:
    mobile_addition = '''      <li class="nav-item nav-mobile-account d-lg-none"><a class="nav-link" href="{% url 'profile_overview' %}"><i class="bi bi-person-circle me-1"></i>My profile</a></li>\n'''
    base_text = base_text.replace(mobile_marker, mobile_addition + mobile_marker, 1)
UPDATED["templates/base.html"] = base_text

# 4) Pass saved-state flags into the existing medicine/pharmacy detail pages.
marketplace_views = UPDATED["marketplace/views.py"]
if "saved_medicine_items.filter(product=product)" not in marketplace_views:
    old = '''def medicine_detail(request, pk):
    product = get_object_or_404(MedicineProduct, pk=pk, active=True)
    listings = _public_listings().filter(product=product).order_by("selling_price", "pharmacy__name")
    return render(request, "marketplace/medicine_detail.html", {"product": product, "listings": listings})'''
    new = '''def medicine_detail(request, pk):
    product = get_object_or_404(MedicineProduct, pk=pk, active=True)
    listings = _public_listings().filter(product=product).order_by("selling_price", "pharmacy__name")
    is_saved = request.user.is_authenticated and request.user.saved_medicine_items.filter(product=product).exists()
    return render(request, "marketplace/medicine_detail.html", {"product": product, "listings": listings, "is_saved": is_saved})'''
    if old not in marketplace_views:
        raise SystemExit("ERROR: Could not locate the existing medicine_detail view. No files were changed.")
    marketplace_views = marketplace_views.replace(old, new, 1)
if "saved_pharmacy_items.filter(pharmacy=pharmacy)" not in marketplace_views:
    old = '''def pharmacy_detail(request, slug):
    pharmacy = get_object_or_404(Pharmacy, slug=slug, verification_status=Pharmacy.VerificationStatus.APPROVED)
    listings = _public_listings().filter(pharmacy=pharmacy).order_by("product__brand_name")
    return render(request, "marketplace/pharmacy_detail.html", {"pharmacy": pharmacy, "listings": listings})'''
    new = '''def pharmacy_detail(request, slug):
    pharmacy = get_object_or_404(Pharmacy, slug=slug, verification_status=Pharmacy.VerificationStatus.APPROVED)
    listings = _public_listings().filter(pharmacy=pharmacy).order_by("product__brand_name")
    is_saved = request.user.is_authenticated and request.user.saved_pharmacy_items.filter(pharmacy=pharmacy).exists()
    return render(request, "marketplace/pharmacy_detail.html", {"pharmacy": pharmacy, "listings": listings, "is_saved": is_saved})'''
    if old not in marketplace_views:
        raise SystemExit("ERROR: Could not locate the existing pharmacy_detail view. No files were changed.")
    marketplace_views = marketplace_views.replace(old, new, 1)

# 5) Let checkout render and use only the current user's own saved addresses.
if "saved_address_choices" not in marketplace_views:
    old_start = '    form = CheckoutForm(request.POST or None, customer=request.user, pharmacy=pharmacy)'
    new_start = '''    from profiles.models import CustomerAddress

    saved_addresses = list(CustomerAddress.objects.filter(user=request.user).order_by("-is_default", "-updated_at"))

    def _profile_address_text(address):
        location = ", ".join(part for part in (
            address.address_line1, address.locality, address.city,
            f"{address.state} {address.pincode}".strip(),
        ) if part)
        formatted = f"{address.recipient_name}: {location}; Phone: {address.phone}"
        # The existing Order and CheckoutForm fields are limited to 300 characters.
        return formatted[:300]

    saved_address_choices = [
        {
            "id": str(address.pk),
            "label": f"{address.get_address_type_display()} — {address.city}, {address.pincode}",
            "formatted": _profile_address_text(address),
            "is_default": address.is_default,
        }
        for address in saved_addresses
    ]
    selected_saved_address_id = ""
    initial = None
    if request.method == "GET" and saved_addresses:
        default_address = next((address for address in saved_addresses if address.is_default), saved_addresses[0])
        selected_saved_address_id = str(default_address.pk)
        initial = {"delivery_address": _profile_address_text(default_address)}
    elif request.method == "POST":
        selected_saved_address_id = request.POST.get("saved_address", "")

    form = CheckoutForm(request.POST or None, customer=request.user, pharmacy=pharmacy, initial=initial)'''
    if old_start not in marketplace_views:
        raise SystemExit("ERROR: Could not locate the existing checkout form setup. No files were changed.")
    marketplace_views = marketplace_views.replace(old_start, new_start, 1)
    old_return = '''    return render(request, "marketplace/checkout.html", {"form": form, "pharmacy": pharmacy, "cart_items": cart_items, "subtotal": subtotal})'''
    new_return = '''    return render(request, "marketplace/checkout.html", {
        "form": form, "pharmacy": pharmacy, "cart_items": cart_items, "subtotal": subtotal,
        "saved_address_choices": saved_address_choices,
        "selected_saved_address_id": selected_saved_address_id,
    })'''
    if old_return not in marketplace_views:
        raise SystemExit("ERROR: Could not locate the existing checkout render context. No files were changed.")
    marketplace_views = marketplace_views.replace(old_return, new_return, 1)
UPDATED["marketplace/views.py"] = marketplace_views

# 6) Add a saved-address selector just before the existing delivery address field.
checkout_text = UPDATED["templates/marketplace/checkout.html"]
if "savedAddressSelect" not in checkout_text:
    marker = '<div class="checkout-field"><label class="form-label" for="id_delivery_address">Delivery address</label>{{ form.delivery_address }}'
    addition = '''{% if saved_address_choices %}<div class="checkout-field"><label class="form-label" for="savedAddressSelect">Use a saved address (optional)</label><select class="form-select" id="savedAddressSelect" name="saved_address"><option value="">Choose a saved address</option>{% for saved_address in saved_address_choices %}<option value="{{ saved_address.id }}" data-address="{{ saved_address.formatted }}" {% if saved_address.id|stringformat:"s" == selected_saved_address_id %}selected{% endif %}>{{ saved_address.label }}</option>{% endfor %}</select><small class="form-text">Choose one to fill in the delivery address below. You can edit it for this order.</small></div>{% endif %}'''
    if marker not in checkout_text:
        raise SystemExit("ERROR: Could not locate the delivery address field in checkout.html. No files were changed.")
    checkout_text = checkout_text.replace(marker, addition + marker, 1)
if "profile-saved-address-sync" not in checkout_text:
    script = '''{% if saved_address_choices %}<script id="profile-saved-address-sync">(function(){var select=document.getElementById("savedAddressSelect");var field=document.getElementById("id_delivery_address");if(!select||!field)return;select.addEventListener("change",function(){var option=select.options[select.selectedIndex];if(option&&option.dataset.address){field.value=option.dataset.address;}});})();</script>{% endif %}'''
    if "{% endblock %}" not in checkout_text:
        raise SystemExit("ERROR: Could not locate endblock in checkout.html. No files were changed.")
    before_last_block, marker, after_last_block = checkout_text.rpartition("{% endblock %}")
    if not marker:
        raise SystemExit("ERROR: Could not locate the final content block end in checkout.html. No files were changed.")
    checkout_text = before_last_block + script + "\n{% endblock %}" + after_last_block
UPDATED["templates/marketplace/checkout.html"] = checkout_text

# 7) Add POST-only save/unsave controls to the current detail templates.
pharmacy_template = UPDATED["templates/marketplace/pharmacy_detail.html"]
if "profile_save_pharmacy" not in pharmacy_template:
    pattern = r'</section>\s*<section class="mk-section">'
    replacement = '''</section>
{% if user.is_authenticated %}<div class="container py-3"><form method="post" action="{% url 'profile_save_pharmacy' pharmacy.pk %}">{% csrf_token %}<input type="hidden" name="next" value="{% url 'pharmacy_detail' pharmacy.slug %}"><button type="submit" class="btn btn-outline-primary rounded-pill"><i class="bi bi-heart me-1"></i>{% if is_saved %}Remove saved pharmacy{% else %}Save pharmacy{% endif %}</button></form></div>{% endif %}
<section class="mk-section">'''
    pharmacy_template, count = re.subn(pattern, replacement, pharmacy_template, count=1)
    if count != 1:
        raise SystemExit("ERROR: Could not locate the pharmacy detail header/listing boundary. No files were changed.")
UPDATED["templates/marketplace/pharmacy_detail.html"] = pharmacy_template

medicine_template = UPDATED["templates/marketplace/medicine_detail.html"]
if "profile_save_medicine" not in medicine_template:
    pattern = r'</section>\s*<section class="mk-section">'
    replacement = '''</section>
{% if user.is_authenticated %}<div class="container py-3"><form method="post" action="{% url 'profile_save_medicine' product.pk %}">{% csrf_token %}<input type="hidden" name="next" value="{% url 'medicine_detail' product.pk %}"><button type="submit" class="btn btn-outline-primary rounded-pill"><i class="bi bi-heart me-1"></i>{% if is_saved %}Remove saved medicine{% else %}Save medicine{% endif %}</button></form></div>{% endif %}
<section class="mk-section">'''
    medicine_template, count = re.subn(pattern, replacement, medicine_template, count=1)
    if count != 1:
        raise SystemExit("ERROR: Could not locate the medicine detail header/listing boundary. No files were changed.")
UPDATED["templates/marketplace/medicine_detail.html"] = medicine_template

changed = [key for key in FILES if UPDATED[key] != ORIGINALS[key]]
if not changed:
    print("MediSearch profile add-on is already registered. No integration edits were necessary.")
    print("Next: python manage.py check && python manage.py migrate")
    sys.exit(0)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = ROOT.parent / f"{ROOT.name}_PROFILE_BACKUP_{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
# Store a path-only manifest of the source tree and backups of the actual pre-edit
# copies. Skip generated folders so the manifest stays useful and compact.
ignored_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache"}
manifest_paths = []
for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    relative = path.relative_to(ROOT)
    if any(part in ignored_dirs for part in relative.parts):
        continue
    manifest_paths.append(relative.as_posix())
manifest_text = "MediSearch project file manifest before profile add-on integration\n"
manifest_text += "Generated: " + stamp + "\n\n"
manifest_text += "\n".join(sorted(manifest_paths)) + "\n\n"
manifest_text += "Files copied into this backup directory before modification:\n"
manifest_text += "\n".join("  - " + key for key in changed) + "\n"
(backup_dir / "PROJECT_FILE_MANIFEST.txt").write_text(manifest_text, encoding="utf-8", newline="\n")

for key in changed:
    destination = backup_dir / key
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FILES[key], destination)
for key in changed:
    FILES[key].write_text(UPDATED[key], encoding="utf-8", newline="\n")

print("MediSearch profile integration complete.")
print("Modified existing files:")
for key in changed:
    print(f"  - {key}")
print(f"Original backups saved outside the project: {backup_dir}")
print("\nNext commands:")
print("  python manage.py check")
print("  python manage.py migrate")
print("  python manage.py test profiles")
print("  git status")
