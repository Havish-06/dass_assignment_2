from __future__ import annotations

"""Central façade object for the StreetRace system.

This class wires together all module classes around a shared
``SystemState`` instance, giving you a very direct mapping to UML:
- one domain state object
- one object per logical module (registration, crew, inventory, races, ...)
"""

from .domain import SystemState
from .registration import RegistrationModule
from .crew_management import CrewManagementModule
from .inventory import InventoryModule
from .maintenance import MaintenanceModule
from .race_management import RaceManagementModule
from .mission_planning import MissionPlanningModule
from .results import ResultsModule
from .reporting import ReportingModule


class StreetRaceManager:
    """High-level entry point that composes all subsystem modules."""

    def __init__(self, state: SystemState | None = None) -> None:
        self.state: SystemState = state or SystemState()

        # Subsystem modules operating on the shared state.
        self.registration = RegistrationModule(self.state)
        self.crew = CrewManagementModule(self.state)
        self.inventory = InventoryModule(self.state)
        self.maintenance = MaintenanceModule(self.state)
        self.races = RaceManagementModule(self.state)
        self.missions = MissionPlanningModule(self.state)
        self.results = ResultsModule(self.state)
        self.reporting = ReportingModule(self.state)
