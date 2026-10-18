from django.contrib import admin
from .models import (
    MedicineCategory, MedicineProduct, Pharmacy, PharmacyListing, Prescription,
    CartItem, MarketplaceOrder, MarketplaceOrderItem, OrderStatusEvent, MarketplaceAuditLog,
)


@admin.register(MedicineCategory)
class MedicineCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("active",)


@admin.register(MedicineProduct)
class MedicineProductAdmin(admin.ModelAdmin):
    list_display = ("brand_name", "generic_name", "strength", "dosage_form", "category", "requires_prescription", "active")
    search_fields = ("brand_name", "generic_name", "manufacturer")
    list_filter = ("category", "dosage_form", "requires_prescription", "active")


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "city", "pincode", "verification_status", "offers_delivery", "offers_pickup")
    list_filter = ("verification_status", "city", "offers_delivery", "offers_pickup")
    search_fields = ("name", "owner__username", "licence_number", "pincode")
    readonly_fields = ("created_at", "updated_at", "verified_at")


@admin.register(PharmacyListing)
class PharmacyListingAdmin(admin.ModelAdmin):
    list_display = ("product", "pharmacy", "mrp", "selling_price", "available_quantity", "reserved_quantity", "expiry_date", "active", "last_stock_update")
    list_filter = ("active", "pharmacy__verification_status", "product__category")
    search_fields = ("product__brand_name", "product__generic_name", "pharmacy__name", "batch_number")
    readonly_fields = ("last_stock_update", "created_at", "updated_at")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "status", "reviewed_by", "reviewed_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("owner__username", "owner__email")
    readonly_fields = ("created_at", "reviewed_at")


class MarketplaceOrderItemInline(admin.TabularInline):
    model = MarketplaceOrderItem
    extra = 0
    readonly_fields = ("product_name_snapshot", "quantity", "unit_price", "mrp_snapshot")


@admin.register(MarketplaceOrder)
class MarketplaceOrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer", "pharmacy", "status", "fulfilment", "total", "created_at")
    list_filter = ("status", "fulfilment", "created_at")
    search_fields = ("reference", "customer__username", "pharmacy__name")
    readonly_fields = ("reference", "subtotal", "delivery_fee", "total", "created_at", "updated_at")
    inlines = (MarketplaceOrderItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("customer", "listing", "quantity", "added_at")
    search_fields = ("customer__username", "listing__product__brand_name")


@admin.register(OrderStatusEvent)
class OrderStatusEventAdmin(admin.ModelAdmin):
    list_display = ("order", "actor", "old_status", "new_status", "created_at")
    list_filter = ("new_status", "created_at")
    readonly_fields = ("order", "actor", "old_status", "new_status", "note", "created_at")


@admin.register(MarketplaceAuditLog)
class MarketplaceAuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "object_type", "object_id")
    list_filter = ("action", "created_at")
    search_fields = ("actor__username", "object_type", "object_id", "details")
    readonly_fields = ("actor", "action", "object_type", "object_id", "details", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
