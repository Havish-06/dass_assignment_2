from __future__ import annotations

import random
from typing import Tuple

from .domain import Race, RaceStatus, Role, SystemState
from .crew_management import CrewManagementModule
from .inventory import InventoryModule
from .maintenance import MaintenanceModule
from .results import ResultsModule


class RaceManagementModule:
    """Coordinates race creation, participant selection, and execution (OOP style)."""

    def __init__(self, state: SystemState) -> None:
        self._state = state
        self._crew = CrewManagementModule(state)
        self._inventory = InventoryModule(state)
        self._maintenance = MaintenanceModule(state)
        self._results = ResultsModule(state)

    def create_race(
        self,
        name: str,
        prize_money: int,
        min_driver_skill: int = 0,
        min_car_speed: int = 0,
        location: str | None = None,
        damage_risk: float = 0.2,
    ) -> Race:
        if prize_money < 0:
            raise ValueError("Prize money cannot be negative")
        if not 0.0 <= damage_risk <= 1.0:
            raise ValueError("Damage risk must be between 0 and 1")

        race_id = self._state.generate_race_id()
        race = Race(
            race_id=race_id,
            name=name,
            location=location,
            min_driver_skill=min_driver_skill,
            min_car_speed=min_car_speed,
            prize_money=prize_money,
            damage_risk=damage_risk,
            status=RaceStatus.PLANNED,
        )
        self._state.races[race_id] = race
        return race

    def select_driver_and_car(self, race_id: int) -> Tuple[int, int]:
        """Select an appropriate driver and car for the race.

        Selection strategy (for UML and implementation):
        - Ask Crew module for available drivers meeting min_driver_skill, sorted by skill.
        - Ask Inventory module for available cars meeting min_car_speed, sorted by speed.
        - Pick the best driver and best car (first from each list).
        Business rules:
        - Only crew with the DRIVER role may be entered in a race.
        - Only non-damaged, available cars may be used.
        """

        race = self._state.races.get(race_id)
        if race is None:
            raise ValueError(f"Unknown race id {race_id}")

        drivers = self._crew.get_available_drivers(race.min_driver_skill)
        cars = self._inventory.get_available_cars(race.min_car_speed)

        if not drivers:
            raise ValueError("No available drivers meet the requirements")
        if not cars:
            raise ValueError("No available cars meet the requirements")

        driver = drivers[0]
        car = cars[0]
        return driver.member_id, car.car_id

    def assign_driver_and_car(self, race_id: int, driver_id: int, car_id: int) -> None:
        race = self._state.races.get(race_id)
        if race is None:
            raise ValueError(f"Unknown race id {race_id}")

        # Validate driver
        driver = self._state.crew.get(driver_id)
        if driver is None:
            raise ValueError(f"Unknown driver id {driver_id}")

        if Role.DRIVER not in driver.roles:
            raise ValueError("Crew member is not a driver")
        if not driver.available:
            raise ValueError("Driver is not available")

        # Validate car
        car = self._state.inventory.cars.get(car_id)
        if car is None:
            raise ValueError(f"Unknown car id {car_id}")
        if car.damaged or not car.available:
            raise ValueError("Car is not available for racing")

        race.driver_id = driver_id
        race.car_id = car_id
        race.status = RaceStatus.SCHEDULED

    def run_race(self, race_id: int) -> Race:
        """Run a scheduled race.

        Business rules:
        - Only drivers with DRIVER role and available cars participate (enforced by assignment).
        - Race results must update the cash balance in Inventory via Results module.
        - Car may be damaged after the race; if so, Maintenance marks it damaged,
          which later affects Mission planning.
        """

        race = self._state.races.get(race_id)
        if race is None:
            raise ValueError(f"Unknown race id {race_id}")
        if race.status not in {RaceStatus.SCHEDULED, RaceStatus.PLANNED}:
            raise ValueError("Race is not in a runnable state")
        if race.driver_id is None or race.car_id is None:
            raise ValueError("Race has no assigned driver and car")

        race.status = RaceStatus.RUNNING

        # Simple random outcome: 60% chance to win, otherwise lose.
        outcome = "win" if random.random() < 0.6 else "loss"
        race.result = outcome
        race.status = RaceStatus.COMPLETED

        # Record result and update cash.
        self._results.record_race_result(
            race_id=race.race_id,
            driver_id=race.driver_id,
            outcome=outcome,
            prize_money=race.prize_money,
        )

        # Chance to damage the car.
        if random.random() < race.damage_risk:
            self._maintenance.mark_car_damaged(race.car_id)

        return race
