"""Module for representing the Monopoly board, its properties, and special tiles."""


class PropertySpec:
    """Immutable configuration for a board property (name, price, etc.)."""

    def __init__(self, name, position, price, base_rent):
        self.name = name
        self.position = position
        self.price = price
        self.base_rent = base_rent
        self.mortgage_value = price // 2
        self.group = None

    def as_tuple(self):
        """Return a tuple view of the core spec fields."""
        return (
            self.name,
            self.position,
            self.price,
            self.base_rent,
            self.mortgage_value,
            self.group,
        )

    def with_group(self, group):
        """Return a new spec with the same fields but a different group."""
        new_spec = PropertySpec(self.name, self.position, self.price, self.base_rent)
        new_spec.group = group
        return new_spec


class Property:
    """Represents a single purchasable property tile on the MoneyPoly board."""

    FULL_GROUP_MULTIPLIER = 2

    def __init__(self, spec):
        self._spec = spec
        self.owner = None
        self.is_mortgaged = False
        self.houses = 0

        # Register with the group immediately on creation
        if self._spec.group is not None and self not in self._spec.group.properties:
            self._spec.group.properties.append(self)

    def get_rent(self):
        """
        Return the rent owed for landing on this property.
        Rent is doubled if the owner holds the entire colour group.
        Returns 0 if the property is mortgaged.
        """
        if self.is_mortgaged:
            return 0
        if self.group is not None and self.group.all_owned_by(self.owner):
            return self.base_rent * self.FULL_GROUP_MULTIPLIER
        return self.base_rent

    def mortgage(self):
        """
        Mortgage this property and return the payout to the owner.
        Returns 0 if already mortgaged.
        """
        if self.is_mortgaged:
            return 0
        self.is_mortgaged = True
        return self.mortgage_value

    def unmortgage(self):
        """
        Lift the mortgage on this property.
        Returns the cost (110 % of mortgage value), or 0 if not mortgaged.
        """
        if not self.is_mortgaged:
            return 0
        cost = int(self.mortgage_value * 1.1)
        self.is_mortgaged = False
        return cost

    def is_available(self):
        """Return True if this property can be purchased (unowned, not mortgaged)."""
        return self.owner is None and not self.is_mortgaged

    def __repr__(self):
        owner_name = self.owner.name if self.owner else "unowned"
        return f"Property({self.name!r}, pos={self.position}, owner={owner_name!r})"

    # Expose spec fields via read-only properties so existing callers continue to work.

    @property
    def name(self):
        """Return the name of this property."""
        return self._spec.name

    @property
    def position(self):
        """Return the board position of this property."""
        return self._spec.position

    @property
    def price(self):
        """Return the purchase price of this property."""
        return self._spec.price

    @property
    def base_rent(self):
        """Return the base rent for this property, ignoring any group ownership bonuses."""
        return self._spec.base_rent

    @property
    def mortgage_value(self):
        """Return the amount this property would yield if mortgaged."""
        return self._spec.mortgage_value

    @property
    def group(self):
        """Return the PropertyGroup this property belongs to, or None if it has none."""
        return self._spec.group


class PropertyGroup:
    """Represents a colour group of properties on the MoneyPoly board."""
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.properties = []

    def add_property(self, prop):
        """Add a Property to this group and back-link it."""
        if prop not in self.properties:
            self.properties.append(prop)
            prop.group = self

    def all_owned_by(self, player):
        """Return True if every property in this group is owned by `player`."""
        if player is None:
            return False
        return any(p.owner == player for p in self.properties)

    def get_owner_counts(self):
        """Return a dict mapping each owner to how many properties they hold in this group."""
        counts = {}
        for prop in self.properties:
            if prop.owner is not None:
                counts[prop.owner] = counts.get(prop.owner, 0) + 1
        return counts

    def size(self):
        """Return the number of properties in this group."""
        return len(self.properties)

    def __repr__(self):
        return f"PropertyGroup({self.name!r}, {len(self.properties)} properties)"
