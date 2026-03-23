"""
Tests for Admin / Data Inspection endpoints.
"""
import pytest
import requests
from utils import BASE_URL, admin_headers


class TestAdminEndpoints:
    def test_get_users(self):
        resp = requests.get(f"{BASE_URL}/admin/users", headers=admin_headers())
        assert resp.status_code == 200
        users = resp.json()
        assert isinstance(users, list) and len(users) > 0
        assert "wallet_balance" in users[0] and "loyalty_points" in users[0]

    def test_get_single_user(self):
        resp = requests.get(f"{BASE_URL}/admin/users/1", headers=admin_headers())
        assert resp.status_code == 200
        assert resp.json()["user_id"] == 1

    def test_get_nonexistent_user(self):
        resp = requests.get(f"{BASE_URL}/admin/users/999999", headers=admin_headers())
        assert resp.status_code == 404

    def test_get_carts(self):
        resp = requests.get(f"{BASE_URL}/admin/carts", headers=admin_headers())
        assert resp.status_code == 200

    def test_get_orders(self):
        resp = requests.get(f"{BASE_URL}/admin/orders", headers=admin_headers())
        assert resp.status_code == 200

    def test_get_products_includes_inactive(self):
        resp = requests.get(f"{BASE_URL}/admin/products", headers=admin_headers())
        assert resp.status_code == 200
        products = resp.json()
        inactive = [p for p in products if not p.get("is_active")]
        assert len(inactive) > 0

    def test_get_coupons_includes_expired(self):
        resp = requests.get(f"{BASE_URL}/admin/coupons", headers=admin_headers())
        assert resp.status_code == 200
        codes = [c["coupon_code"] for c in resp.json()]
        assert "EXPIRED100" in codes or "EXPIRED50" in codes

    def test_get_tickets(self):
        resp = requests.get(f"{BASE_URL}/admin/tickets", headers=admin_headers())
        assert resp.status_code == 200

    def test_get_addresses(self):
        resp = requests.get(f"{BASE_URL}/admin/addresses", headers=admin_headers())
        assert resp.status_code == 200
