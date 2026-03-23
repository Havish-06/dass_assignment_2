"""
Tests for Checkout endpoint.
"""
import pytest
import requests
from utils import BASE_URL, get_headers, clear_cart, add_to_cart, checkout, get_cart

CHECKOUT_USER = "6"


class TestCheckoutValidation:
    def test_empty_cart_rejected(self):
        clear_cart(CHECKOUT_USER)
        assert checkout("COD", CHECKOUT_USER).status_code == 400

    def test_invalid_payment_method(self):
        clear_cart(CHECKOUT_USER)
        add_to_cart(3, 1, CHECKOUT_USER)
        assert checkout("BITCOIN", CHECKOUT_USER).status_code == 400

    def test_missing_payment_method(self):
        clear_cart(CHECKOUT_USER)
        add_to_cart(3, 1, CHECKOUT_USER)
        resp = requests.post(f"{BASE_URL}/checkout", headers=get_headers(user_id=CHECKOUT_USER), json={})
        assert resp.status_code == 400

    def test_cod_over_5000_rejected(self):
        clear_cart(CHECKOUT_USER)
        add_to_cart(5, 20, CHECKOUT_USER)  # 250×20=5000, +5%GST=5250
        assert checkout("COD", CHECKOUT_USER).status_code == 400
        clear_cart(CHECKOUT_USER)


class TestPaymentStatus:
    def test_card_starts_as_paid(self):
        clear_cart(CHECKOUT_USER)
        add_to_cart(3, 1, CHECKOUT_USER)
        r = checkout("CARD", CHECKOUT_USER)
        assert r.status_code == 200
        oid = r.json().get("order_id")
        if oid:
            order = requests.get(f"{BASE_URL}/orders/{oid}", headers=get_headers(user_id=CHECKOUT_USER)).json()
            assert order.get("payment_status") == "PAID"

    def test_cod_starts_as_pending(self):
        clear_cart(CHECKOUT_USER)
        add_to_cart(3, 1, CHECKOUT_USER)
        r = checkout("COD", CHECKOUT_USER)
        assert r.status_code == 200
        oid = r.json().get("order_id")
        if oid:
            order = requests.get(f"{BASE_URL}/orders/{oid}", headers=get_headers(user_id=CHECKOUT_USER)).json()
            assert order.get("payment_status") == "PENDING"

    def test_wallet_starts_as_pending(self):
        requests.post(f"{BASE_URL}/wallet/add", headers=get_headers(user_id=CHECKOUT_USER), json={"amount": 10000})
        clear_cart(CHECKOUT_USER)
        add_to_cart(3, 1, CHECKOUT_USER)
        r = checkout("WALLET", CHECKOUT_USER)
        if r.status_code == 200:
            oid = r.json().get("order_id")
            if oid:
                order = requests.get(f"{BASE_URL}/orders/{oid}", headers=get_headers(user_id=CHECKOUT_USER)).json()
                assert order.get("payment_status") == "PENDING"


class TestCheckoutInvoice:
    def test_invoice_total_is_subtotal_plus_gst(self):
        clear_cart(CHECKOUT_USER)
        add_to_cart(2, 1, CHECKOUT_USER)
        r = checkout("CARD", CHECKOUT_USER)
        assert r.status_code == 200
        oid = r.json().get("order_id")
        if oid:
            inv = requests.get(f"{BASE_URL}/orders/{oid}/invoice", headers=get_headers(user_id=CHECKOUT_USER)).json()
            assert abs(float(inv["total_amount"]) - (float(inv["subtotal"]) + float(inv["gst_amount"]))) < 0.02
