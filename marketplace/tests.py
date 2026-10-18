from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import MedicineCategory, MedicineProduct, Pharmacy, PharmacyListing, CartItem, MarketplaceOrder, MarketplaceOrderItem, MarketplaceAuditLog
from .views import _transition_order


class MarketplaceSmokeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(username="customer1", password="Testpass!123")
        self.owner = User.objects.create_user(username="owner1", password="Testpass!123")
        self.other = User.objects.create_user(username="other1", password="Testpass!123")
        category = MedicineCategory.objects.create(name="Demo Essentials", slug="demo-essentials")
        product = MedicineProduct.objects.create(brand_name="DEMO Paracetamol", generic_name="Demo ingredient", strength="500 mg", dosage_form="tablet", category=category)
        self.pharmacy = Pharmacy.objects.create(owner=self.owner, name="DEMO Verified Pharmacy", phone="0000000000", address="1 Demo Street", city="Sampletown", state="West Bengal", pincode="000000", licence_number="DEMO-LIC", verification_status=Pharmacy.VerificationStatus.APPROVED)
        self.listing = PharmacyListing.objects.create(pharmacy=self.pharmacy, product=product, mrp=Decimal("20.00"), selling_price=Decimal("15.00"), available_quantity=10)

    def test_homepage_is_pharmacy_first(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Find your medicine")
        self.assertContains(response, "MediSearch")

    def test_search_returns_approved_listings(self):
        response = self.client.get(reverse("medicine_search"), {"q": "Paracetamol"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DEMO Paracetamol")


    def test_public_pages_do_not_disclose_exact_stock_counts(self):
        urls = [
            reverse("home"),
            reverse("medicine_search"),
            reverse("medicine_detail", args=[self.listing.product_id]),
            reverse("pharmacy_detail", args=[self.pharmacy.slug]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "10 available")
                self.assertNotContains(response, "10 currently available")

    def test_cart_does_not_disclose_remaining_shop_stock(self):
        self.client.force_login(self.customer)
        CartItem.objects.create(customer=self.customer, listing=self.listing, quantity=1)
        response = self.client.get(reverse("cart_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "10 currently available")

    def test_unapproved_pharmacy_does_not_appear_publicly(self):
        self.pharmacy.verification_status = Pharmacy.VerificationStatus.PENDING
        self.pharmacy.save()
        response = self.client.get(reverse("medicine_search"))
        self.assertNotContains(response, "DEMO Verified Pharmacy")

    def test_checkout_reserves_stock_and_creates_pending_request(self):
        self.client.force_login(self.customer)
        CartItem.objects.create(customer=self.customer, listing=self.listing, quantity=2)
        response = self.client.post(reverse("checkout", args=[self.pharmacy.pk]), {"fulfilment": "pickup", "delivery_address": "", "customer_note": ""}, follow=True)
        self.assertEqual(response.status_code, 200)
        order = MarketplaceOrder.objects.get(customer=self.customer)
        self.listing.refresh_from_db()
        self.assertEqual(order.status, MarketplaceOrder.Status.PENDING)
        self.assertEqual(order.total, Decimal("30.00"))
        self.assertEqual(self.listing.available_quantity, 10)
        self.assertEqual(self.listing.reserved_quantity, 2)
        self.assertFalse(CartItem.objects.filter(customer=self.customer).exists())

    def test_stock_is_consumed_only_when_order_is_completed(self):
        order = MarketplaceOrder.objects.create(customer=self.customer, pharmacy=self.pharmacy, subtotal=Decimal("30.00"), total=Decimal("30.00"))
        MarketplaceOrderItem.objects.create(order=order, listing=self.listing, product_name_snapshot=str(self.listing.product), quantity=2, unit_price=Decimal("15.00"), mrp_snapshot=Decimal("20.00"))
        self.listing.reserved_quantity = 2
        self.listing.save()
        _transition_order(order, MarketplaceOrder.Status.ACCEPTED, self.owner)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.available_quantity, 10)
        self.assertEqual(self.listing.reserved_quantity, 2)
        _transition_order(order, MarketplaceOrder.Status.PROCESSING, self.owner)
        _transition_order(order, MarketplaceOrder.Status.READY, self.owner)
        _transition_order(order, MarketplaceOrder.Status.COMPLETED, self.owner)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.available_quantity, 8)
        self.assertEqual(self.listing.reserved_quantity, 0)
        self.assertTrue(MarketplaceAuditLog.objects.filter(action="order_status_changed", object_id=str(order.pk)).exists())

    def test_user_cannot_edit_other_pharmacy_listing(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("retailer_listing_edit", args=[self.listing.pk]))
        self.assertEqual(response.status_code, 403)

    def test_non_staff_cannot_open_platform_admin_dashboard(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("marketplace_admin_dashboard"))
        self.assertEqual(response.status_code, 302)
