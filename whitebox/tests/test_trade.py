import os
import sys
import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.game import Game


class TestTradeAndRent:
    """White-box tests for rent and trade branches."""

    def setup_method(self):
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

        assert self.buyer.balance == starting_balance

    def test_pay_rent_transfers_to_owner(self):
        """When rent is due, it should be transferred to the property's owner."""
        # Ensure property is not mortgaged and owned by seller.
        self.prop.is_mortgaged = False
        rent = self.prop.get_rent()
        starting_buyer = self.buyer.balance
        starting_seller = self.seller.balance

        self.game.pay_rent(self.buyer, self.prop)

        assert self.buyer.balance == starting_buyer - rent
        assert self.seller.balance == starting_seller + rent

    def test_pay_rent_can_bankrupt_tenant(self):
        """If the tenant cannot afford rent, they should go bankrupt and be eliminated."""
        self.prop.is_mortgaged = False
        rent = self.prop.get_rent()
        # Set buyer's balance so that paying rent pushes them below zero.
        self.buyer.balance = rent - 1

        self.game.pay_rent(self.buyer, self.prop)

        # Buyer should now be bankrupt and removed from the game.
        assert self.buyer.is_bankrupt()
        assert self.buyer.is_eliminated
        assert self.buyer not in self.game.players

    def test_trade_fails_when_seller_does_not_own_property(self):
        """Trade must fail if the seller does not actually own the property."""
        self.prop.owner = None

        success = self.game.trade(self.seller, self.buyer, self.prop, 100)

        assert not success
        assert self.prop.owner is None

    def test_trade_fails_when_buyer_cannot_afford(self):
        """Trade must fail if the buyer lacks enough cash."""
        price = 1000
        self.buyer.balance = price - 1

        success = self.game.trade(self.seller, self.buyer, self.prop, price)

        assert not success
        # Balances and ownership unchanged.
        assert self.buyer.balance == price - 1
        assert self.prop.owner is self.seller

    def test_trade_succeeds_and_transfers_property_and_cash(self):
        """Successful trade transfers property and deducts buyer's cash."""
        price = 200
        self.buyer.balance = 500
        starting_seller_balance = self.seller.balance

        success = self.game.trade(self.seller, self.buyer, self.prop, price)

        assert success
        assert self.prop.owner is self.buyer
        assert self.prop in self.buyer.properties
        assert self.prop not in self.seller.properties
        assert self.buyer.balance == 500 - price
        # Seller's cash does not automatically increase; trade is modelled
        # as a transfer between players without touching the bank.
        assert self.seller.balance == starting_seller_balance
