"""
Tests for Profile endpoints (GET/PUT).
name: 2–50 chars, phone: exactly 10 digits.
"""
import pytest
import requests
from utils import BASE_URL, get_headers


class TestGetProfile:
    def test_get_profile(self):
        resp = requests.get(f"{BASE_URL}/profile", headers=get_headers())
        assert resp.status_code == 200
        data = resp.json()
        for f in ["user_id", "name", "email", "phone", "wallet_balance", "loyalty_points"]:
            assert f in data


class TestUpdateProfile:
    def test_valid_update(self):
        resp = requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": "ValidName", "phone": "9876543210"})
        assert resp.status_code == 200

    def test_name_1_char_too_short(self):
        resp = requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": "A", "phone": "9876543210"})
        assert resp.status_code == 400

    def test_name_51_chars_too_long(self):
        resp = requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": "A" * 51, "phone": "9876543210"})
        assert resp.status_code == 400

    def test_phone_9_digits_rejected(self):
        resp = requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": "Test", "phone": "123456789"})
        assert resp.status_code == 400

    def test_phone_11_digits_rejected(self):
        resp = requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": "Test", "phone": "12345678901"})
        assert resp.status_code == 400

    def test_phone_with_letters_rejected(self):
        """Phone must be digits only. BUG: server accepts letters."""
        resp = requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": "Test", "phone": "12345abcde"})
        assert resp.status_code == 400

    def test_name_wrong_type_integer(self):
        resp = requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": 12345, "phone": "1234567890"})
        assert resp.status_code == 400

    def test_missing_name_field(self):
        resp = requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"phone": "1234567890"})
        assert resp.status_code == 400

    def test_missing_phone_field(self):
        resp = requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": "Test User"})
        assert resp.status_code == 400

    def test_data_persists_after_update(self):
        requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": "Persist", "phone": "5555555555"})
        data = requests.get(f"{BASE_URL}/profile", headers=get_headers()).json()
        assert data["name"] == "Persist" and data["phone"] == "5555555555"
        requests.put(f"{BASE_URL}/profile", headers=get_headers(), json={"name": "Test User", "phone": "1234567890"})
