"""
Tests for Reviews endpoints.
"""
import pytest
import requests
from utils import BASE_URL, get_headers

REVIEW_USER_1 = "10"
REVIEW_USER_2 = "11"


class TestPostReview:
    def test_valid_review(self):
        resp = requests.post(f"{BASE_URL}/products/1/reviews", headers=get_headers(user_id=REVIEW_USER_1),
                             json={"rating": 4, "comment": "Great!"})
        assert resp.status_code in [200, 201]

    def test_rating_0_rejected(self):
        resp = requests.post(f"{BASE_URL}/products/1/reviews", headers=get_headers(user_id=REVIEW_USER_1),
                             json={"rating": 0, "comment": "Bad"})
        assert resp.status_code == 400

    def test_rating_6_rejected(self):
        resp = requests.post(f"{BASE_URL}/products/1/reviews", headers=get_headers(user_id=REVIEW_USER_1),
                             json={"rating": 6, "comment": "Too high"})
        assert resp.status_code == 400

    def test_empty_comment_rejected(self):
        resp = requests.post(f"{BASE_URL}/products/1/reviews", headers=get_headers(user_id=REVIEW_USER_1),
                             json={"rating": 3, "comment": ""})
        assert resp.status_code == 400

    def test_comment_201_chars_rejected(self):
        resp = requests.post(f"{BASE_URL}/products/1/reviews", headers=get_headers(user_id=REVIEW_USER_1),
                             json={"rating": 3, "comment": "A" * 201})
        assert resp.status_code == 400

    def test_missing_rating(self):
        resp = requests.post(f"{BASE_URL}/products/1/reviews", headers=get_headers(user_id=REVIEW_USER_1),
                             json={"comment": "No rating"})
        assert resp.status_code == 400


class TestAverageRating:
    def test_average_is_proper_decimal(self):
        """BUG: average_rating is truncated to integer (e.g., 3 instead of 3.5)."""
        pid = 8
        requests.post(f"{BASE_URL}/products/{pid}/reviews", headers=get_headers(user_id=REVIEW_USER_1),
                       json={"rating": 5, "comment": "Excellent"})
        requests.post(f"{BASE_URL}/products/{pid}/reviews", headers=get_headers(user_id=REVIEW_USER_2),
                       json={"rating": 2, "comment": "Not great"})

        data = requests.get(f"{BASE_URL}/products/{pid}/reviews", headers=get_headers()).json()
        avg = data.get("average_rating")
        reviews = data.get("reviews", [])
        if len(reviews) >= 2:
            expected = sum(r["rating"] for r in reviews) / len(reviews)
            assert abs(float(avg) - expected) < 0.01, \
                f"Average {avg} != expected {expected} (integer truncation?)"
