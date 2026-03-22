import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.game import Game


class TradeAndRentTests(unittest.TestCase):
    """White-box tests for rent and trade branches."""

    def setUp(self):
        self.game = Game(["Seller", "Buyer"])
        self.seller, self.buyer = self.game.players

        # Give seller ownership of the first property.
        self.prop = self.game.board.properties[0]
        self.prop.owner = self.seller
        self.seller.add_property(self.prop)

    def test_pay_rent_ignored_for_mortgaged_property(self):
        """When a property is mortgaged, pay_rent should do nothing."""
        self.prop.is_mortgaged = True
        starting_balance = self.buyer.balance

        self.game.pay_rent(self.buyer, self.prop)

        self.assertEqual(self.buyer.balance, starting_balance)

    def test_trade_fails_when_seller_does_not_own_property(self):
        """Trade must fail if the seller does not actually own the property."""
        self.prop.owner = None

        success = self.game.trade(self.seller, self.buyer, self.prop, 100)

        self.assertFalse(success)
        self.assertIsNone(self.prop.owner)

    def test_trade_fails_when_buyer_cannot_afford(self):
        """Trade must fail if the buyer lacks enough cash."""
        price = 1000
        self.buyer.balance = price - 1

        success = self.game.trade(self.seller, self.buyer, self.prop, price)

        self.assertFalse(success)
        # Balances and ownership unchanged.
        self.assertEqual(self.buyer.balance, price - 1)
        self.assertIs(self.prop.owner, self.seller)

    def test_trade_succeeds_and_transfers_property_and_cash(self):
        """Successful trade transfers property and deducts buyer's cash."""
        price = 200
        self.buyer.balance = 500
        starting_seller_balance = self.seller.balance

        success = self.game.trade(self.seller, self.buyer, self.prop, price)

        self.assertTrue(success)
        self.assertIs(self.prop.owner, self.buyer)
        self.assertIn(self.prop, self.buyer.properties)
        self.assertNotIn(self.prop, self.seller.properties)
        self.assertEqual(self.buyer.balance, 500 - price)
        # Seller's cash does not automatically increase; trade is modelled
        # as a transfer between players without touching the bank.
        self.assertEqual(self.seller.balance, starting_seller_balance)


if __name__ == "__main__":
    unittest.main()
