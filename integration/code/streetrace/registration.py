from __future__ import annotations

"""Registration module implemented with an OOP interface.

The main entry point is the :class:`RegistrationModule`, which wraps access
to the shared :class:`~streetrace.domain.SystemState` object.
"""

from typing import Optional

from .domain import CrewMember, Role, SystemState


class RegistrationModule:
    """Handles registering new crew members.

    In UML terms this is the *Registration* subsystem. Other modules use
    it via methods on :class:`StreetRaceManager` rather than touching
    ``SystemState`` directly.
    """

    def __init__(self, state: SystemState) -> None:
        self._state = state

    def register_member(self, name: str, initial_role: Optional[Role] = None) -> CrewMember:
        """Register a new crew member with an optional initial role.

        Business rule: a member must be registered before any roles or
        skills can be managed by other modules.
        """

        if not name.strip():
            raise ValueError("Name cannot be empty")

        member_id = self._state.generate_crew_id()
        member = CrewMember(member_id=member_id, name=name.strip())

        if initial_role is not None:
            member.roles.add(initial_role)

        self._state.crew[member_id] = member
        return member

