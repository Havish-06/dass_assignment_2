import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PROJECT_ROOT, "moneypoly")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from moneypoly.player import Player
from moneypoly.board import Board
from moneypoly.property import PropertySpec, Property, PropertyGroup
from moneypoly.config import JAIL_POSITION


class TestPlayer:
    """Branch-coverage tests for Player helpers and guards."""

    def test_add_and_deduct_negative_amount_raises(self):
        player = Player("P1")
        with pytest.raises(ValueError):
            player.add_money(-10)
        with pytest.raises(ValueError):
            player.deduct_money(-5)

    def test_go_to_jail_sets_position_and_status(self):
        player = Player("P1")
        player.go_to_jail()
        assert player.position == JAIL_POSITION
        assert player.jail.in_jail

    def test_properties_helpers_and_repr_and_status_line(self):
        player = Player("P1")
        spec = PropertySpec("Test", 5, 100, 10)
        prop = Property(spec)

        player.add_property(prop)
        assert player.count_properties() == 1
        assert "P1" in repr(player)

        # Removing a property should decrease the count again.
        player.remove_property(prop)
        assert player.count_properties() == 0

        # Status line should include jailed tag when in jail.
        player.go_to_jail()
        status = player.status_line()
        assert "[JAILED]" in status


class TestPropertyAndGroup:
    """Tests for Property, PropertySpec, and PropertyGroup branches."""

    def test_propertyspec_as_tuple_and_with_group(self):
        group = PropertyGroup("G1", "red")
        spec = PropertySpec("Test", 7, 120, 10)
        spec.group = group

        tup = spec.as_tuple()
        assert tup[0] == "Test"
        assert tup[1] == 7
        assert tup[2] == 120
        assert tup[3] == 10
        assert tup[5] == group

        new_group = PropertyGroup("G2", "blue")
        spec2 = spec.with_group(new_group)
        assert spec2.group is new_group
        assert spec2.group != spec.group

    def test_property_mortgage_unmortgage_and_availability(self):
        group = PropertyGroup("G", "green")
        spec = PropertySpec("Test", 10, 200, 20)
        spec.group = group
        prop = Property(spec)

        # Initially unowned, not mortgaged and available.
        assert prop.is_available()

        # Mortgage pays out mortgage_value and becomes unavailable.
        first_payout = prop.mortgage()
        assert first_payout == prop.mortgage_value
        assert not prop.is_available()
        # Second mortgage attempt yields 0.
        assert prop.mortgage() == 0

        # Unmortgage returns 110% of mortgage value and restores availability.
        cost = prop.unmortgage()
        assert cost == int(prop.mortgage_value * 1.1)
        assert prop.is_available()
        # Second unmortgage attempt yields 0.
        assert prop.unmortgage() == 0

        # When a property is owned, it should no longer be available.
        owner = Player("Owner")
        prop.owner = owner
        assert not prop.is_available()

    def test_group_ownership_rent_and_counts(self):
        group = PropertyGroup("Pair", "yellow")
        spec1 = PropertySpec("A", 1, 100, 10)
        spec2 = PropertySpec("B", 3, 100, 10)
        spec1.group = group
        spec2.group = group
        prop1 = Property(spec1)
        prop2 = Property(spec2)

        # Group should have registered both properties.
        assert group.size() == 2

        owner = Player("Owner")
        prop1.owner = owner
        prop2.owner = None

        # Partial ownership: rent remains base, group not fully owned.
        assert not group.all_owned_by(owner)
        assert prop1.get_rent() == prop1.base_rent

        # Full ownership doubles rent.
        prop2.owner = owner
        assert group.all_owned_by(owner)
        assert prop1.get_rent() == prop1.base_rent * Property.FULL_GROUP_MULTIPLIER

        counts = group.get_owner_counts()
        assert counts.get(owner) == 2
        # Adding property twice via add_property should not duplicate.
        group.add_property(prop1)
        assert group.size() == 2
        assert "PropertyGroup" in repr(group)

        # Mortgaged properties in a full group should charge no rent.
        prop1.is_mortgaged = True
        assert prop1.get_rent() == 0


class TestBoard:
    """Tests for Board helper methods and tile classification."""

    def test_get_property_and_tile_types_and_specials(self):
        board = Board()

        # Known property from board setup.
        mediterranean = board.get_property_at(1)
        assert mediterranean is not None
        assert mediterranean.position == 1

        # Position 0 is Go and not a property.
        assert board.get_property_at(0) is None

        # Non-property position returns None.
        assert board.get_property_at(12) is None

        # Tile types: go, property, jail, blank, and a special tile.
        assert board.get_tile_type(0) == "go"
        assert board.get_tile_type(1) == "property"
        assert board.get_tile_type(JAIL_POSITION) == "jail"
        assert board.get_tile_type(12) == "blank"

        # SPECIAL_TILES are recognised as special.
        from moneypoly.board import SPECIAL_TILES  # pylint: disable=import-outside-toplevel

        for pos in SPECIAL_TILES:
            assert board.is_special_tile(pos)
        assert not board.is_special_tile(12)

    def test_is_purchasable_owned_mortgaged_and_collections(self):
        board = Board()
        prop = board.get_property_at(1)
        assert board.is_purchasable(1)

        # Mortgaged properties are not purchasable.
        prop.is_mortgaged = True
        assert not board.is_purchasable(1)

        # Owned properties are not purchasable.
        prop.is_mortgaged = False
        owner = Player("Owner")
        prop.owner = owner
        assert not board.is_purchasable(1)

        # Non-property tile is not purchasable.
        assert not board.is_purchasable(12)

        owned_by_owner = board.properties_owned_by(owner)
        assert prop in owned_by_owner

        unowned = board.unowned_properties()
        assert prop in board.properties
        assert prop not in unowned

        assert "Board(" in repr(board)
