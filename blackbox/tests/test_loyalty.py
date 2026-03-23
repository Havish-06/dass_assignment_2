"""
Tests for Loyalty Points endpoints.
"""
import pytest
import requests
from utils import BASE_URL, get_headers

LOYALTY_USER = "8"


class TestLoyalty:
    def test_get_loyalty(self):
        resp = requests.get(f"{BASE_URL}/loyalty", headers=get_headers(user_id=LOYALTY_USER))
        assert resp.status_code == 200 and "loyalty_points" in resp.json()

    def test_redeem_zero_rejected(self):
        assert requests.post(f"{BASE_URL}/loyalty/redeem", headers=get_headers(user_id=LOYALTY_USER), json={"points": 0}).status_code == 400

    def test_redeem_more_than_balance_rejected(self):
        assert requests.post(f"{BASE_URL}/loyalty/redeem", headers=get_headers(user_id=LOYALTY_USER), json={"points": 999999}).status_code == 400

    def test_redeem_valid(self):
        pts = requests.get(f"{BASE_URL}/loyalty", headers=get_headers(user_id=LOYALTY_USER)).json().get("loyalty_points", 0)
        if pts >= 1:
            assert requests.post(f"{BASE_URL}/loyalty/redeem", headers=get_headers(user_id=LOYALTY_USER), json={"points": 1}).status_code == 200

    def test_redeem_missing_field(self):
        assert requests.post(f"{BASE_URL}/loyalty/redeem", headers=get_headers(user_id=LOYALTY_USER), json={}).status_code == 400
