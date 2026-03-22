import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.player import Player
from moneypoly.property import PropertySpec, Property, PropertyGroup
from moneypoly.board import Board
from moneypoly.config import JAIL_POSITION


class PlayerTests(unittest.TestCase):
    def test_negative_add_and_deduct_raise(self):
        player = Player("P1", balance=100)
        with self.assertRaises(ValueError):
            player.add_money(-10)
        with self.assertRaises(ValueError):
            player.deduct_money(-5)

    def test_go_to_jail_and_status_line(self):
        player = Player("P2", balance=150)
        player.go_to_jail()
        self.assertEqual(player.position, JAIL_POSITION)
        self.assertTrue(player.jail.in_jail)
        line = player.status_line()
        self.assertIn("P2", line)
        self.assertIn("[JAILED]", line)

    def test_properties_and_count(self):
        player = Player("P3")
        spec = PropertySpec("Test", 1, 100, 10)
        prop = Property(spec)
        player.add_property(prop)
        self.assertEqual(player.count_properties(), 1)
        player.remove_property(prop)
        self.assertEqual(player.count_properties(), 0)


class PropertyAndGroupTests(unittest.TestCase):
    def test_propertyspec_tuple_and_with_group(self):
        spec = PropertySpec("Demo", 5, 200, 20)
        tup = spec.as_tuple()
        self.assertEqual(tup[0], "Demo")
        self.assertEqual(tup[1], 5)
        group = PropertyGroup("G", "color")
        new_spec = spec.with_group(group)
        self.assertIs(new_spec.group, group)
        self.assertEqual(new_spec.name, spec.name)

    def test_get_rent_full_group_and_mortgage(self):
        group = PropertyGroup("TestGroup", "c")
        s1 = PropertySpec("A", 1, 100, 10)
        s2 = PropertySpec("B", 2, 100, 10)
        s1.group = group
        s2.group = group
        p1 = Property(s1)
        p2 = Property(s2)
        owner = Player("Owner")
        p1.owner = owner
        p2.owner = owner

        # When owner has the full group, rent should be doubled.
        base = p1.base_rent
        rent_full = p1.get_rent()
        self.assertEqual(rent_full, base * Property.FULL_GROUP_MULTIPLIER)

        # Mortgaged properties charge no rent.
        p1.is_mortgaged = True
        self.assertEqual(p1.get_rent(), 0)

    def test_mortgage_unmortgage_and_availability(self):
        spec = PropertySpec("MProp", 3, 120, 8)
        prop = Property(spec)

        payout1 = prop.mortgage()
        self.assertEqual(payout1, prop.mortgage_value)
        payout2 = prop.mortgage()
        self.assertEqual(payout2, 0)

        cost0 = prop.unmortgage()
        self.assertGreater(cost0, 0)
        cost1 = prop.unmortgage()
        self.assertEqual(cost1, 0)

        self.assertTrue(prop.is_available())
        owner = Player("Buyer")
        prop.owner = owner
        self.assertFalse(prop.is_available())

    def test_group_ownership_and_counts(self):
        group = PropertyGroup("Group", "c")
        s1 = PropertySpec("A", 1, 100, 10)
        s2 = PropertySpec("B", 2, 100, 10)
        s1.group = group
        s2.group = group
        p1 = Property(s1)
        p2 = Property(s2)
        owner = Player("O")

        # No owner yet.
        self.assertFalse(group.all_owned_by(owner))

        # Only one property owned: should still be False.
        p1.owner = owner
        self.assertFalse(group.all_owned_by(owner))

        # All properties owned: now True.
        p2.owner = owner
        self.assertTrue(group.all_owned_by(owner))

        counts = group.get_owner_counts()
        self.assertEqual(counts.get(owner), 2)
        self.assertEqual(group.size(), 2)


class BoardTests(unittest.TestCase):
    def test_get_property_and_tile_types(self):
        board = Board()
        first_prop = board.properties[0]
        self.assertIs(board.get_property_at(first_prop.position), first_prop)
        self.assertEqual(board.get_property_at(0), None)

        self.assertEqual(board.get_tile_type(first_prop.position), "property")
        self.assertEqual(board.get_tile_type(JAIL_POSITION), "jail")

        # Choose a position that is not a special tile or property.
        # Position 4 is a tax tile in this board layout, so use 12.
        self.assertEqual(board.get_tile_type(12), "blank")

    def test_is_purchasable_and_ownership_helpers(self):
        board = Board()
        prop = board.properties[0]
        player = Player("Buyer")

        self.assertTrue(board.is_purchasable(prop.position))
        prop.is_mortgaged = True
        self.assertFalse(board.is_purchasable(prop.position))
        prop.is_mortgaged = False
        prop.owner = player
        player.add_property(prop)
        self.assertFalse(board.is_purchasable(prop.position))
        self.assertFalse(board.is_purchasable(0))  # non-property

        owned = board.properties_owned_by(player)
        self.assertIn(prop, owned)
        unowned = board.unowned_properties()
        self.assertNotIn(prop, unowned)


if __name__ == "__main__":
    unittest.main()
