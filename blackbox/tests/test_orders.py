"""
Tests for Orders endpoints.
NOTE: GST test is in test_checkout.py only (not duplicated here).
"""
import pytest
import requests
from utils import BASE_URL, get_headers, admin_headers, clear_cart, add_to_cart, checkout

ORDERS_USER = "9"


class TestGetOrders:
    def test_get_orders(self):
        assert requests.get(f"{BASE_URL}/orders", headers=get_headers(user_id=ORDERS_USER)).status_code == 200

    def test_nonexistent_order(self):
        assert requests.get(f"{BASE_URL}/orders/999999", headers=get_headers(user_id=ORDERS_USER)).status_code == 404


class TestCancelOrder:
    def test_cancel_nonexistent(self):
        assert requests.post(f"{BASE_URL}/orders/999999/cancel", headers=get_headers(user_id=ORDERS_USER)).status_code == 404

    def test_cancellation_restores_stock(self):
        """BUG: stock not restored after cancellation."""
        admin_prods = requests.get(f"{BASE_URL}/admin/products", headers=admin_headers()).json()
        p3 = next(p for p in admin_prods if p["product_id"] == 3)
        initial_stock = p3["stock_quantity"]

        clear_cart(ORDERS_USER)
        add_to_cart(3, 2, ORDERS_USER)
        r = checkout("CARD", ORDERS_USER)
        if r.status_code == 200:
            oid = r.json().get("order_id")
            requests.post(f"{BASE_URL}/orders/{oid}/cancel", headers=get_headers(user_id=ORDERS_USER))

            final_stock = next(p for p in requests.get(f"{BASE_URL}/admin/products", headers=admin_headers()).json()
                               if p["product_id"] == 3)["stock_quantity"]
            assert final_stock == initial_stock, f"Stock not restored: {final_stock} != {initial_stock}"


class TestInvoice:
    def test_invoice_nonexistent(self):
        assert requests.get(f"{BASE_URL}/orders/999999/invoice", headers=get_headers(user_id=ORDERS_USER)).status_code == 404

    def test_invoice_math(self):
        """subtotal + gst = total, and total matches order total."""
        clear_cart(ORDERS_USER)
        add_to_cart(1, 3, ORDERS_USER)
        r = checkout("CARD", ORDERS_USER)
        if r.status_code == 200:
            oid = r.json().get("order_id")
            inv = requests.get(f"{BASE_URL}/orders/{oid}/invoice", headers=get_headers(user_id=ORDERS_USER)).json()
            subtotal, gst, total = float(inv["subtotal"]), float(inv["gst_amount"]), float(inv["total_amount"])
            assert abs(total - (subtotal + gst)) < 0.02

            order_total = float(requests.get(f"{BASE_URL}/orders/{oid}", headers=get_headers(user_id=ORDERS_USER)).json()["total_amount"])
            assert total == order_total
