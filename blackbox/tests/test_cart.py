"""
Tests for Cart endpoints.
"""
import pytest
import requests
from utils import BASE_URL, get_headers, admin_headers, clear_cart, add_to_cart, get_cart

CART_USER = "4"


class TestAddToCart:
    def test_add_valid_item(self):
        clear_cart(CART_USER)
        assert add_to_cart(1, 1, CART_USER).status_code == 200

    def test_add_qty_zero_rejected(self):
        """BUG: server accepts qty=0."""
        assert add_to_cart(1, 0, CART_USER).status_code == 400

    def test_add_negative_qty_rejected(self):
        assert add_to_cart(1, -1, CART_USER).status_code == 400

    def test_add_nonexistent_product(self):
        assert add_to_cart(999999, 1, CART_USER).status_code == 404

    def test_add_exceeding_stock(self):
        clear_cart(CART_USER)
        assert add_to_cart(1, 999999, CART_USER).status_code == 400

    def test_add_inactive_product_rejected(self):
        """BUG: server allows adding inactive product 90."""
        clear_cart(CART_USER)
        assert add_to_cart(90, 1, CART_USER).status_code in [400, 404]

    def test_add_same_product_sums_quantities(self):
        clear_cart(CART_USER)
        add_to_cart(1, 2, CART_USER)
        add_to_cart(1, 3, CART_USER)
        items = get_cart(CART_USER).json().get("items", [])
        p1 = [i for i in items if i.get("product_id") == 1]
        assert len(p1) == 1 and p1[0]["quantity"] == 5


class TestCartMath:
    def test_subtotal_equals_qty_times_price(self):
        """BUG: subtotals are wrong (e.g., 3×120=104 instead of 360)."""
        clear_cart(CART_USER)
        add_to_cart(1, 3, CART_USER)
        cart = get_cart(CART_USER).json()
        admin_map = {p["product_id"]: p["price"] for p in requests.get(f"{BASE_URL}/admin/products", headers=admin_headers()).json()}
        for item in cart.get("items", []):
            expected = item["quantity"] * admin_map.get(item["product_id"], 0)
            assert item["subtotal"] == expected, f"Product {item['product_id']}: subtotal {item['subtotal']} != {item['quantity']}×{admin_map.get(item['product_id'])}={expected}"

    def test_total_equals_sum_of_subtotals(self):
        """BUG: total ≠ sum of subtotals."""
        clear_cart(CART_USER)
        add_to_cart(1, 2, CART_USER)
        add_to_cart(2, 3, CART_USER)
        cart = get_cart(CART_USER).json()
        computed = sum(i.get("subtotal", 0) for i in cart.get("items", []))
        assert float(cart["total"]) == float(computed), f"total {cart['total']} != sum {computed}"


class TestUpdateRemoveClear:
    def test_update_qty_zero_rejected(self):
        clear_cart(CART_USER)
        add_to_cart(1, 2, CART_USER)
        resp = requests.post(f"{BASE_URL}/cart/update", headers=get_headers(user_id=CART_USER), json={"product_id": 1, "quantity": 0})
        assert resp.status_code == 400

    def test_remove_missing_product(self):
        clear_cart(CART_USER)
        resp = requests.post(f"{BASE_URL}/cart/remove", headers=get_headers(user_id=CART_USER), json={"product_id": 999999})
        assert resp.status_code == 404

    def test_clear_cart(self):
        add_to_cart(1, 1, CART_USER)
        requests.delete(f"{BASE_URL}/cart/clear", headers=get_headers(user_id=CART_USER))
        cart = get_cart(CART_USER).json()
        assert cart["total"] == 0 and len(cart.get("items", [])) == 0
