def marketplace_ui(request):
    cart_count = 0
    has_pharmacy = False
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        try:
            cart_count = sum(request.user.marketplace_cart_items.values_list("quantity", flat=True))
        except Exception:
            cart_count = 0
        try:
            has_pharmacy = request.user.owned_pharmacies.exists()
        except Exception:
            has_pharmacy = False
    return {"marketplace_cart_count": cart_count, "has_owned_pharmacy": has_pharmacy}
