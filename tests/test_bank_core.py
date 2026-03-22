import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.bank import Bank
from moneypoly.config import BANK_STARTING_FUNDS


class BankCoreTests(unittest.TestCase):
    """White-box tests for Bank core methods and edge cases."""

    def setUp(self):
        self.bank = Bank()

    def test_collect_positive_amount_increases_funds(self):
        """Collecting a positive amount should increase bank funds."""
        self.bank.collect(100)
        self.assertEqual(self.bank.get_balance(), BANK_STARTING_FUNDS + 100)

    def test_collect_negative_amount_is_ignored(self):
        """Docstring says negative amounts are ignored; balance should not drop."""
        self.bank.collect(-50)
        self.assertEqual(self.bank.get_balance(), BANK_STARTING_FUNDS)

    def test_pay_out_zero_or_negative_returns_zero_without_change(self):
        """pay_out should return 0 and not change funds for non-positive input."""
        start = self.bank.get_balance()
        self.assertEqual(self.bank.pay_out(0), 0)
        self.assertEqual(self.bank.get_balance(), start)
        self.assertEqual(self.bank.pay_out(-10), 0)
        self.assertEqual(self.bank.get_balance(), start)

    def test_pay_out_more_than_funds_raises(self):
        """pay_out should raise ValueError if amount exceeds available funds."""
        with self.assertRaises(ValueError):
            self.bank.pay_out(self.bank.get_balance() + 1)

    def test_give_loan_ignores_non_positive_amount(self):
        """give_loan should ignore zero or negative amounts."""
        start_funds = self.bank.get_balance()
        self.bank.give_loan(type("P", (), {"name": "X", "add_money": lambda self, amt: None})(), 0)
        self.assertEqual(self.bank.get_balance(), start_funds)

    def test_give_loan_positive_records_and_reduces_funds(self):
        """Positive loans should reduce bank funds and be tracked in summaries."""
        class DummyPlayer:
            def __init__(self):
                self.name = "Y"
                self.balance = 0

            def add_money(self, amount):
                self.balance += amount

        borrower = DummyPlayer()
        start_funds = self.bank.get_balance()
        self.bank.give_loan(borrower, 100)

        self.assertEqual(borrower.balance, 100)
        # Docstring says the bank's funds are reduced accordingly.
        self.assertEqual(self.bank.get_balance(), start_funds - 100)
        self.assertEqual(self.bank.loan_count(), 1)
        self.assertEqual(self.bank.total_loans_issued(), 100)

    def test_give_loan_positive_amount_records_and_summarises(self):
        """Positive loans reduce bank funds, record loans, and appear in summary helpers."""

        class DummyPlayer:
            def __init__(self):
                self.name = "Borrower"
                self.received = 0

            def add_money(self, amount):
                self.received += amount

        player = DummyPlayer()
        start_funds = self.bank.get_balance()
        self.bank.give_loan(player, 100)

        # Bank funds reduced, player credited.
        self.assertEqual(player.received, 100)
        self.assertEqual(self.bank.get_balance(), start_funds - 100)

        # Loan helpers reflect the issued loan.
        self.assertEqual(self.bank.loan_count(), 1)
        self.assertEqual(self.bank.total_loans_issued(), 100)

        # summary() and __repr__ should be callable without error, both
        # before and after any loans are issued.
        fresh_bank = Bank()
        _ = repr(fresh_bank)
        fresh_bank.summary()

        _ = repr(self.bank)
        self.bank.summary()


if __name__ == "__main__":
    unittest.main()
