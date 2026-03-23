"""
Tests for Wallet endpoints.
"""
import pytest
import requests
from utils import BASE_URL, get_headers

WALLET_USER = "7"


class TestWalletAdd:
    def test_add_valid(self):
        assert requests.post(f"{BASE_URL}/wallet/add", headers=get_headers(user_id=WALLET_USER), json={"amount": 100}).status_code == 200

    def test_add_zero_rejected(self):
        assert requests.post(f"{BASE_URL}/wallet/add", headers=get_headers(user_id=WALLET_USER), json={"amount": 0}).status_code == 400

    def test_add_negative_rejected(self):
        assert requests.post(f"{BASE_URL}/wallet/add", headers=get_headers(user_id=WALLET_USER), json={"amount": -50}).status_code == 400

    def test_add_over_100000_rejected(self):
        assert requests.post(f"{BASE_URL}/wallet/add", headers=get_headers(user_id=WALLET_USER), json={"amount": 100001}).status_code == 400

    def test_add_exactly_100000(self):
        assert requests.post(f"{BASE_URL}/wallet/add", headers=get_headers(user_id=WALLET_USER), json={"amount": 100000}).status_code == 200


class TestWalletPay:
    def test_pay_insufficient_balance(self):
        assert requests.post(f"{BASE_URL}/wallet/pay", headers=get_headers(user_id=WALLET_USER), json={"amount": 999999999}).status_code == 400

    def test_pay_zero_rejected(self):
        assert requests.post(f"{BASE_URL}/wallet/pay", headers=get_headers(user_id=WALLET_USER), json={"amount": 0}).status_code == 400

    def test_pay_exact_amount_deducted(self):
        """BUG: wallet deducts ~0.40 extra."""
        requests.post(f"{BASE_URL}/wallet/add", headers=get_headers(user_id=WALLET_USER), json={"amount": 1000})
        before = float(requests.get(f"{BASE_URL}/wallet", headers=get_headers(user_id=WALLET_USER)).json()["wallet_balance"])
        pay_amount = 250.50
        requests.post(f"{BASE_URL}/wallet/pay", headers=get_headers(user_id=WALLET_USER), json={"amount": pay_amount})
        after = float(requests.get(f"{BASE_URL}/wallet", headers=get_headers(user_id=WALLET_USER)).json()["wallet_balance"])
        assert abs((before - pay_amount) - after) < 0.01, f"Expected {before - pay_amount}, got {after}"
