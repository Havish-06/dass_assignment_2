from __future__ import annotations

from typing import List

from .domain import Mission, MissionStatus, Role, SystemState
from .maintenance import MaintenanceModule


class MissionPlanningModule:
    """Plans missions and assigns crew using an OOP interface."""

    def __init__(self, state: SystemState) -> None:
        self._state = state
        self._maintenance = MaintenanceModule(state)

    def create_mission(self, mission_type: str, required_roles: List[Role]) -> Mission:
        mission_id = self._state.generate_mission_id()
        mission = Mission(mission_id=mission_id, mission_type=mission_type, required_roles=list(required_roles))
        self._state.missions[mission_id] = mission
        return mission

    def assign_crew(self, mission_id: int, crew_ids: List[int]) -> None:
        mission = self._state.missions.get(mission_id)
        if mission is None:
            raise ValueError(f"Unknown mission id {mission_id}")
        for crew_id in crew_ids:
            if crew_id not in self._state.crew:
                raise ValueError(f"Unknown crew member id {crew_id}")
        mission.assigned_crew_ids = list(crew_ids)

    def _assigned_roles(self, mission: Mission) -> List[Role]:
        roles: List[Role] = []
        for crew_id in mission.assigned_crew_ids:
            member = self._state.crew[crew_id]
            roles.extend(member.roles)
        return roles

    def start_mission(self, mission_id: int) -> bool:
        """Attempt to start a mission.

        Business rules:
        - Missions cannot start if required roles are unavailable.
        - If a car is damaged during a race, and the mission requires a mechanic,
          then a mechanic must be available before the mission can proceed.
        """

        mission = self._state.missions.get(mission_id)
        if mission is None:
            raise ValueError(f"Unknown mission id {mission_id}")

        if mission.status is not MissionStatus.PLANNED:
            return False

        # Check that assigned crew cover required roles and are available.
        if not mission.assigned_crew_ids:
            return False

        assigned_roles = self._assigned_roles(mission)
        for required in mission.required_roles:
            if required not in assigned_roles:
                return False

        # Check crew availability
        for crew_id in mission.assigned_crew_ids:
            if not self._state.crew[crew_id].available:
                return False

        # Special rule: if mission needs a mechanic and there is a damaged car,
        # ensure a mechanic is available.
        if Role.MECHANIC in mission.required_roles and self._maintenance.get_damaged_car() is not None:
            if not self._maintenance.is_mechanic_available():
                return False

        mission.status = MissionStatus.IN_PROGRESS
        return True
