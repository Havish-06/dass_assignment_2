"""
Tests for Coupon endpoints. Field name is "coupon_code".
"""
import pytest
import requests
from utils import BASE_URL, get_headers, clear_cart, add_to_cart

COUPON_USER = "5"


def _setup_cart_and_apply(coupon_code, product_id=1, qty=10):
    clear_cart(COUPON_USER)
    add_to_cart(product_id, qty, COUPON_USER)
    requests.post(f"{BASE_URL}/coupon/remove", headers=get_headers(user_id=COUPON_USER))
    return requests.post(f"{BASE_URL}/coupon/apply", headers=get_headers(user_id=COUPON_USER), json={"coupon_code": coupon_code})


class TestApplyCoupon:
    def test_expired_coupon_rejected(self):
        assert _setup_cart_and_apply("EXPIRED100").status_code == 400

    def test_min_cart_value_not_met(self):
        """Cart of 30 < min_cart_value of 1000."""
        assert _setup_cart_and_apply("SAVE100", product_id=9, qty=1).status_code == 400

    def test_nonexistent_coupon(self):
        assert _setup_cart_and_apply("NONEXISTENT999").status_code in [400, 404]

    def test_missing_coupon_code_field(self):
        resp = requests.post(f"{BASE_URL}/coupon/apply", headers=get_headers(user_id=COUPON_USER), json={})
        assert resp.status_code == 400

    def test_valid_fixed_coupon_discount(self):
        """SAVE50: FIXED 50, min 500. Cart=1200. Discount should be 50."""
        resp = _setup_cart_and_apply("SAVE50")
        assert resp.status_code == 200
        if "discount" in resp.json():
            assert float(resp.json()["discount"]) == 50.0

    def test_percent_coupon_cap_enforced(self):
        """SUPER10: 10%, max 80. Cart=1200. 10%=120 → capped at 80."""
        resp = _setup_cart_and_apply("SUPER10")
        assert resp.status_code == 200
        if "discount" in resp.json():
            assert float(resp.json()["discount"]) <= 80.0

    def test_percent_discount_math(self):
        """SUPER10: 10%, max 80. Cart with 8×40=320. Expected discount = 32. BUG: gets 10."""
        resp = _setup_cart_and_apply("SUPER10", product_id=3, qty=8)
        assert resp.status_code == 200
        if "discount" in resp.json():
            assert abs(float(resp.json()["discount"]) - 32.0) < 0.01, \
                f"Expected 32, got {resp.json()['discount']}"


class TestRemoveCoupon:
    def test_remove_coupon(self):
        resp = requests.post(f"{BASE_URL}/coupon/remove", headers=get_headers(user_id=COUPON_USER))
        assert resp.status_code in [200, 204]
