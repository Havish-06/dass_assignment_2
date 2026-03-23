"""
Tests for Support Tickets endpoints.
"""
import pytest
import requests
from utils import BASE_URL, get_headers

SUPPORT_USER = "12"


def _create_ticket(subject="Valid Test Subject", message="This is a valid message"):
    r = requests.post(f"{BASE_URL}/support/ticket", headers=get_headers(user_id=SUPPORT_USER),
                       json={"subject": subject, "message": message})
    return r.json().get("ticket_id") if r.status_code in [200, 201] else None


class TestCreateTicket:
    def test_create_valid(self):
        resp = requests.post(f"{BASE_URL}/support/ticket", headers=get_headers(user_id=SUPPORT_USER),
                             json={"subject": "Valid Subject", "message": "Valid message"})
        assert resp.status_code in [200, 201]
        assert "ticket_id" in resp.json()

    def test_new_ticket_is_open(self):
        tid = _create_ticket()
        if tid:
            tickets = requests.get(f"{BASE_URL}/support/tickets", headers=get_headers(user_id=SUPPORT_USER)).json()
            t = next((t for t in tickets if t["ticket_id"] == tid), None)
            assert t and t["status"] == "OPEN"

    def test_subject_4_chars_rejected(self):
        resp = requests.post(f"{BASE_URL}/support/ticket", headers=get_headers(user_id=SUPPORT_USER),
                             json={"subject": "ABCD", "message": "Valid"})
        assert resp.status_code == 400

    def test_subject_101_chars_rejected(self):
        resp = requests.post(f"{BASE_URL}/support/ticket", headers=get_headers(user_id=SUPPORT_USER),
                             json={"subject": "A" * 101, "message": "Valid"})
        assert resp.status_code == 400

    def test_message_empty_rejected(self):
        resp = requests.post(f"{BASE_URL}/support/ticket", headers=get_headers(user_id=SUPPORT_USER),
                             json={"subject": "Valid Subject", "message": ""})
        assert resp.status_code == 400

    def test_message_501_chars_rejected(self):
        resp = requests.post(f"{BASE_URL}/support/ticket", headers=get_headers(user_id=SUPPORT_USER),
                             json={"subject": "Valid Subject", "message": "A" * 501})
        assert resp.status_code == 400

    def test_missing_subject(self):
        resp = requests.post(f"{BASE_URL}/support/ticket", headers=get_headers(user_id=SUPPORT_USER),
                             json={"message": "Valid"})
        assert resp.status_code == 400


class TestTicketMessagePreservation:
    def test_message_preserved_in_listing(self):
        """BUG: message field is empty/missing when retrieving tickets via GET."""
        msg = "This exact message must be preserved word for word"
        tid = _create_ticket(subject="Preservation Test", message=msg)
        if tid:
            tickets = requests.get(f"{BASE_URL}/support/tickets", headers=get_headers(user_id=SUPPORT_USER)).json()
            t = next((t for t in tickets if t["ticket_id"] == tid), None)
            assert t is not None
            assert t.get("message") == msg, f"Message not preserved: got '{t.get('message', '')}'"


class TestTicketStatusTransitions:
    def test_open_to_in_progress_valid(self):
        tid = _create_ticket()
        if tid:
            assert requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                                json={"status": "IN_PROGRESS"}).status_code == 200

    def test_in_progress_to_closed_valid(self):
        tid = _create_ticket()
        if tid:
            requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                         json={"status": "IN_PROGRESS"})
            assert requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                                json={"status": "CLOSED"}).status_code == 200

    def test_open_to_closed_rejected(self):
        """BUG: skipping IN_PROGRESS allowed."""
        tid = _create_ticket()
        if tid:
            assert requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                                json={"status": "CLOSED"}).status_code == 400

    def test_backward_transition_rejected(self):
        """BUG: IN_PROGRESS → OPEN (backward) allowed."""
        tid = _create_ticket()
        if tid:
            requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                         json={"status": "IN_PROGRESS"})
            assert requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                                json={"status": "OPEN"}).status_code == 400

    def test_closed_to_open_rejected(self):
        """BUG: CLOSED → OPEN (backward) allowed."""
        tid = _create_ticket()
        if tid:
            requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                         json={"status": "IN_PROGRESS"})
            requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                         json={"status": "CLOSED"})
            assert requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                                json={"status": "OPEN"}).status_code == 400

    def test_invalid_status_rejected(self):
        """BUG: arbitrary status values accepted."""
        tid = _create_ticket()
        if tid:
            assert requests.put(f"{BASE_URL}/support/tickets/{tid}", headers=get_headers(user_id=SUPPORT_USER),
                                json={"status": "RESOLVED"}).status_code == 400
