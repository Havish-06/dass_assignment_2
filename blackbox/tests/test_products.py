"""
Tests for Products endpoints.
"""
import pytest
import requests
from utils import BASE_URL, get_headers, admin_headers


class TestGetProducts:
    def test_get_products_only_active(self):
        products = requests.get(f"{BASE_URL}/products", headers=get_headers()).json()
        assert isinstance(products, list)
        for p in products:
            assert p.get("is_active") == True

    def test_nonexistent_product_returns_404(self):
        assert requests.get(f"{BASE_URL}/products/999999", headers=get_headers()).status_code == 404


class TestProductFiltering:
    def test_filter_by_category(self):
        for p in requests.get(f"{BASE_URL}/products?category=Fruits", headers=get_headers()).json():
            assert p["category"] == "Fruits"

    def test_search_by_name(self):
        products = requests.get(f"{BASE_URL}/products?search=Apple", headers=get_headers()).json()
        assert len(products) > 0
        for p in products:
            assert "apple" in p["name"].lower()

    def test_sort_price_ascending(self):
        prices = [p["price"] for p in requests.get(f"{BASE_URL}/products?sort=price_asc", headers=get_headers()).json()]
        assert prices == sorted(prices)

    def test_sort_price_descending(self):
        prices = [p["price"] for p in requests.get(f"{BASE_URL}/products?sort=price_desc", headers=get_headers()).json()]
        assert prices == sorted(prices, reverse=True)


class TestProductPriceIntegrity:
    def test_user_prices_match_admin_prices(self):
        """BUG: 154 products have mismatched prices."""
        user_prods = requests.get(f"{BASE_URL}/products", headers=get_headers()).json()
        admin_map = {p["product_id"]: p["price"] for p in requests.get(f"{BASE_URL}/admin/products", headers=admin_headers()).json()}
        mismatches = [f"PID {p['product_id']}: user={p['price']}, admin={admin_map[p['product_id']]}"
                      for p in user_prods if p["product_id"] in admin_map and p["price"] != admin_map[p["product_id"]]]
        assert len(mismatches) == 0, f"Price mismatches: {mismatches[:5]}"
