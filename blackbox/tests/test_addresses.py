"""
Tests for Addresses endpoints.
NOTE: The server has an inverted pincode bug (rejects 6-digit, accepts 5-digit).
Non-pincode tests use 5-digit pincodes to isolate the bug they're actually testing.
"""
import pytest
import requests
from utils import BASE_URL, get_headers

ADDR_USER = "3"
# Server accepts 5-digit pincodes (bug), so we use them for non-pincode tests
WORKING_PINCODE = "12345"


def _addr(**overrides):
    base = {"label": "HOME", "street": "123 Main Street", "city": "Bangalore",
            "pincode": WORKING_PINCODE, "is_default": False}
    base.update(overrides)
    return base


class TestGetAddresses:
    def test_get_addresses_returns_200(self):
        resp = requests.get(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestCreateAddress:
    def test_create_valid_address(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr())
        assert resp.status_code in [200, 201]

    # Label enum
    def test_invalid_label_returns_400(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(label="WORK"))
        assert resp.status_code == 400

    def test_lowercase_label_returns_400(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(label="home"))
        assert resp.status_code == 400

    # Street: 5–100 chars
    def test_street_4_chars_too_short(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(street="ABCD"))
        assert resp.status_code == 400

    def test_street_exactly_5_chars(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(street="ABCDE"))
        assert resp.status_code in [200, 201]

    def test_street_101_chars_too_long(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(street="A" * 101))
        assert resp.status_code == 400

    # City: 2–50 chars
    def test_city_1_char_too_short(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(city="A"))
        assert resp.status_code == 400

    def test_city_51_chars_too_long(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(city="A" * 51))
        assert resp.status_code == 400

    # Pincode: must be exactly 6 digits — SERVER BUG: inverted
    def test_pincode_6_digits_should_be_accepted(self):
        """Per spec pincode must be exactly 6 digits. BUG: server rejects 6-digit, accepts 4/5/7-digit."""
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(pincode="123456"))
        assert resp.status_code in [200, 201]

    def test_pincode_with_letters_returns_400(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(pincode="12345a"))
        assert resp.status_code == 400

    # Missing fields
    def test_missing_pincode_returns_400(self):
        """Pincode is required. BUG: server accepts missing pincode."""
        p = _addr()
        del p["pincode"]
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=p)
        assert resp.status_code == 400

    def test_missing_street_returns_400(self):
        p = _addr()
        del p["street"]
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=p)
        assert resp.status_code == 400

    def test_empty_body_returns_400(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json={})
        assert resp.status_code == 400

    # Response structure
    def test_post_returns_full_address_object(self):
        resp = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(street="Response Check"))
        if resp.status_code in [200, 201]:
            addr = resp.json().get("address", resp.json())
            for f in ["address_id", "label", "street", "city", "pincode", "is_default"]:
                assert f in addr, f"Missing field: {f}"


class TestDefaultAddress:
    def test_only_one_default_at_a_time(self):
        """When a new default is added, old defaults must be unset. BUG: multiple defaults allowed."""
        requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(street="Default A", is_default=True))
        requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(street="Default B", label="OFFICE", is_default=True))
        addrs = requests.get(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER)).json()
        defaults = [a for a in addrs if a.get("is_default")]
        assert len(defaults) == 1, f"Expected 1 default, found {len(defaults)}"


class TestUpdateAddress:
    def _create(self):
        r = requests.post(f"{BASE_URL}/addresses", headers=get_headers(user_id=ADDR_USER), json=_addr(street="Update Test St"))
        return r.json().get("address_id") or r.json().get("address", {}).get("address_id")

    def test_update_response_shows_new_data(self):
        aid = self._create()
        if aid:
            resp = requests.put(f"{BASE_URL}/addresses/{aid}", headers=get_headers(user_id=ADDR_USER),
                                json={"street": "Brand New Street", "is_default": True})
            assert resp.status_code == 200
            flat = resp.json().get("address", resp.json())
            assert flat.get("street") == "Brand New Street"
            assert flat.get("is_default") == True

    def test_update_cannot_change_label(self):
        aid = self._create()
        if aid:
            resp = requests.put(f"{BASE_URL}/addresses/{aid}", headers=get_headers(user_id=ADDR_USER),
                                json={"label": "OFFICE", "street": "Same St", "is_default": False})
            if resp.status_code == 200:
                flat = resp.json().get("address", resp.json())
                assert flat.get("label") == "HOME", "Label should NOT be changeable"


class TestDeleteAddress:
    def test_delete_nonexistent_returns_404(self):
        resp = requests.delete(f"{BASE_URL}/addresses/999999", headers=get_headers(user_id=ADDR_USER))
        assert resp.status_code == 404
