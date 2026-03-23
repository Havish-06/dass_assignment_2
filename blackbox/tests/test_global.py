"""
Tests for global request validation (X-Roll-Number, X-User-ID headers).
"""
import pytest
import requests
from utils import BASE_URL, get_headers


class TestXRollNumberHeader:
    def test_missing_roll_returns_401(self):
        resp = requests.get(f"{BASE_URL}/admin/users")
        assert resp.status_code == 401

    def test_invalid_roll_letters_returns_400(self):
        resp = requests.get(f"{BASE_URL}/admin/users", headers={"X-Roll-Number": "abcd"})
        assert resp.status_code == 400

    def test_invalid_roll_symbols_returns_400(self):
        resp = requests.get(f"{BASE_URL}/admin/users", headers={"X-Roll-Number": "!@#$"})
        assert resp.status_code == 400

    def test_valid_roll_passes(self):
        resp = requests.get(f"{BASE_URL}/admin/users", headers={"X-Roll-Number": "2024101092"})
        assert resp.status_code == 200


class TestXUserIDHeader:
    def test_missing_user_id_returns_400(self):
        resp = requests.get(f"{BASE_URL}/profile", headers={"X-Roll-Number": "2024101092"})
        assert resp.status_code == 400

    def test_invalid_user_id_letters_returns_400(self):
        resp = requests.get(f"{BASE_URL}/profile", headers=get_headers(user_id="abc"))
        assert resp.status_code == 400

    def test_invalid_user_id_zero_returns_400(self):
        resp = requests.get(f"{BASE_URL}/profile", headers=get_headers(user_id="0"))
        assert resp.status_code == 400

    def test_nonexistent_user_returns_400(self):
        """Spec says invalid user → 400. BUG: returns 404."""
        resp = requests.get(f"{BASE_URL}/profile", headers=get_headers(user_id="999999"))
        assert resp.status_code == 400

    def test_admin_no_user_id_needed(self):
        resp = requests.get(f"{BASE_URL}/admin/users", headers={"X-Roll-Number": "2024101092"})
        assert resp.status_code == 200


class TestNonExistentUserAcrossEndpoints:
    """BUG: Non-existent user ID 999999 returns 200 on most user-scoped endpoints."""

    def test_user_scoped_endpoints_reject_nonexistent_user(self):
        """All user-scoped GET endpoints should return 400 for non-existent user."""
        fake_h = get_headers(user_id="999999")
        endpoints = ["/addresses", "/cart", "/wallet", "/loyalty", "/orders", "/support/tickets"]
        for ep in endpoints:
            resp = requests.get(f"{BASE_URL}{ep}", headers=fake_h)
            assert resp.status_code == 400, \
                f"GET {ep} returned {resp.status_code} for non-existent user, expected 400"
