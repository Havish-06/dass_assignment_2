import requests

BASE_URL = "http://localhost:8080/api/v1"
ROLL = "2024101092"

def get_headers(user_id="1", roll=ROLL):
    """Build request headers. Pass user_id=None for admin-only endpoints."""
    h = {}
    if roll is not None:
        h["X-Roll-Number"] = str(roll)
    if user_id is not None:
        h["X-User-ID"] = str(user_id)
    return h

def admin_headers():
    """Headers for admin endpoints (no X-User-ID)."""
    return {"X-Roll-Number": ROLL}

def clear_cart(user_id="1"):
    """Utility to clear a user's cart."""
    requests.delete(f"{BASE_URL}/cart/clear", headers=get_headers(user_id=user_id))

def add_to_cart(product_id, quantity, user_id="1"):
    """Utility to add a product to cart."""
    return requests.post(
        f"{BASE_URL}/cart/add",
        headers=get_headers(user_id=user_id),
        json={"product_id": product_id, "quantity": quantity}
    )

def get_cart(user_id="1"):
    """Utility to get cart."""
    return requests.get(f"{BASE_URL}/cart", headers=get_headers(user_id=user_id))

def checkout(payment_method, user_id="1"):
    """Utility to checkout."""
    return requests.post(
        f"{BASE_URL}/checkout",
        headers=get_headers(user_id=user_id),
        json={"payment_method": payment_method}
    )
