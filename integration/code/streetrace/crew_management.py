from __future__ import annotations

"""Crew Management module with an object-oriented interface."""

from typing import List

from .domain import CrewMember, Role, SystemState


class CrewManagementModule:
    """Manages crew roles and skills.

    Business rules enforced here:
    - A crew member must already be registered before roles/skills are set.
    - Only available members are considered for role-based queries.
    """

    def __init__(self, state: SystemState) -> None:
        self._state = state

    def _get_member(self, member_id: int) -> CrewMember:
        try:
            return self._state.crew[member_id]
        except KeyError as exc:
            raise ValueError(f"Unknown crew member id {member_id}") from exc

    def assign_role(self, member_id: int, role: Role) -> None:
        """Assign a new role to an existing crew member."""

        member = self._get_member(member_id)
        member.roles.add(role)

    def set_skill(self, member_id: int, role: Role, level: int) -> None:
        """Set the skill level for a member in a given role."""

        if level < 0:
            raise ValueError("Skill level cannot be negative")
        member = self._get_member(member_id)
        member.skills[role] = level

    def get_members_by_role(self, role: Role) -> List[CrewMember]:
        return [member for member in self._state.crew.values() if role in member.roles]

    def get_available_drivers(self, min_skill: int = 0) -> List[CrewMember]:
        """Return available drivers who meet at least the given skill threshold."""

        drivers: List[CrewMember] = []
        for member in self._state.crew.values():
            if not member.available:
                continue
            if Role.DRIVER not in member.roles:
                continue
            if member.skills.get(Role.DRIVER, 0) < min_skill:
                continue
            drivers.append(member)
        # Sort best first
        drivers.sort(key=lambda m: m.skills.get(Role.DRIVER, 0), reverse=True)
        return drivers

