import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.player import Player
from moneypoly.board import Board
from moneypoly.property import PropertySpec, Property, PropertyGroup
from moneypoly.config import JAIL_POSITION


class PlayerTests(unittest.TestCase):
    """Branch-coverage tests for Player helpers and guards."""

    def test_add_and_deduct_negative_amount_raises(self):
        player = Player("P1")
        with self.assertRaises(ValueError):
            player.add_money(-10)
        with self.assertRaises(ValueError):
            player.deduct_money(-5)

    def test_go_to_jail_sets_position_and_status(self):
        player = Player("P1")
        player.go_to_jail()
        self.assertEqual(player.position, JAIL_POSITION)
        self.assertTrue(player.jail.in_jail)

    def test_properties_helpers_and_repr_and_status_line(self):
        player = Player("P1")
        spec = PropertySpec("Test", 5, 100, 10)
        prop = Property(spec)

        player.add_property(prop)
        self.assertEqual(player.count_properties(), 1)
        self.assertIn("P1", repr(player))

        # Status line should include jailed tag when in jail.
        player.go_to_jail()
        status = player.status_line()
        self.assertIn("[JAILED]", status)


class PropertyAndGroupTests(unittest.TestCase):
    """Tests for Property, PropertySpec, and PropertyGroup branches."""

    def test_propertyspec_as_tuple_and_with_group(self):
        group = PropertyGroup("G1", "red")
        spec = PropertySpec("Test", 7, 120, 10)
        spec.group = group

        tup = spec.as_tuple()
        self.assertEqual(tup[0], "Test")
        self.assertEqual(tup[1], 7)
        self.assertEqual(tup[2], 120)
        self.assertEqual(tup[3], 10)
        self.assertEqual(tup[5], group)

        new_group = PropertyGroup("G2", "blue")
        spec2 = spec.with_group(new_group)
        self.assertIs(spec2.group, new_group)
        self.assertNotEqual(spec2.group, spec.group)

    def test_property_mortgage_unmortgage_and_availability(self):
        group = PropertyGroup("G", "green")
        spec = PropertySpec("Test", 10, 200, 20)
        spec.group = group
        prop = Property(spec)

        # Initially unowned, not mortgaged and available.
        self.assertTrue(prop.is_available())

        # Mortgage pays out mortgage_value and becomes unavailable.
        first_payout = prop.mortgage()
        self.assertEqual(first_payout, prop.mortgage_value)
        self.assertFalse(prop.is_available())
        # Second mortgage attempt yields 0.
        self.assertEqual(prop.mortgage(), 0)

        # Unmortgage returns 110% of mortgage value and restores availability.
        cost = prop.unmortgage()
        self.assertEqual(cost, int(prop.mortgage_value * 1.1))
        self.assertTrue(prop.is_available())
        # Second unmortgage attempt yields 0.
        self.assertEqual(prop.unmortgage(), 0)

    def test_group_ownership_rent_and_counts(self):
        group = PropertyGroup("Pair", "yellow")
        spec1 = PropertySpec("A", 1, 100, 10)
        spec2 = PropertySpec("B", 3, 100, 10)
        spec1.group = group
        spec2.group = group
        prop1 = Property(spec1)
        prop2 = Property(spec2)

        # Group should have registered both properties.
        self.assertEqual(group.size(), 2)

        owner = Player("Owner")
        prop1.owner = owner
        prop2.owner = None

        # Partial ownership: rent remains base, group not fully owned.
        self.assertFalse(group.all_owned_by(owner))
        self.assertEqual(prop1.get_rent(), prop1.base_rent)

        # Full ownership doubles rent.
        prop2.owner = owner
        self.assertTrue(group.all_owned_by(owner))
        self.assertEqual(
            prop1.get_rent(), prop1.base_rent * Property.FULL_GROUP_MULTIPLIER
        )

        counts = group.get_owner_counts()
        self.assertEqual(counts.get(owner), 2)
        # Adding property twice via add_property should not duplicate.
        group.add_property(prop1)
        self.assertEqual(group.size(), 2)
        self.assertIn("PropertyGroup", repr(group))


class BoardTests(unittest.TestCase):
    """Tests for Board helper methods and tile classification."""

    def test_get_property_and_tile_types_and_specials(self):
        board = Board()

        # Known property from board setup.
        mediterranean = board.get_property_at(1)
        self.assertIsNotNone(mediterranean)
        self.assertEqual(mediterranean.position, 1)

        # Non-property position returns None.
        self.assertIsNone(board.get_property_at(12))

        # Tile types: go, property, blank, and a special tile.
        self.assertEqual(board.get_tile_type(0), "go")
        self.assertEqual(board.get_tile_type(1), "property")
        self.assertEqual(board.get_tile_type(12), "blank")

        # SPECIAL_TILES are recognised as special.
        from moneypoly.board import SPECIAL_TILES  # pylint: disable=import-outside-toplevel

        for pos in SPECIAL_TILES:
            self.assertTrue(board.is_special_tile(pos))
        self.assertFalse(board.is_special_tile(12))

    def test_is_purchasable_owned_mortgaged_and_collections(self):
        board = Board()
        prop = board.get_property_at(1)
        self.assertTrue(board.is_purchasable(1))

        # Mortgaged properties are not purchasable.
        prop.is_mortgaged = True
        self.assertFalse(board.is_purchasable(1))

        # Owned properties are not purchasable.
        prop.is_mortgaged = False
        owner = Player("Owner")
        prop.owner = owner
        self.assertFalse(board.is_purchasable(1))

        # Non-property tile is not purchasable.
        self.assertFalse(board.is_purchasable(12))

        owned_by_owner = board.properties_owned_by(owner)
        self.assertIn(prop, owned_by_owner)

        unowned = board.unowned_properties()
        self.assertIn(prop, board.properties)  # sanity check
        self.assertNotIn(prop, unowned)

        self.assertIn("Board(", repr(board))


if __name__ == "__main__":
    unittest.main()
