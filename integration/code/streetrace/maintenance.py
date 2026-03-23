from __future__ import annotations

"""Maintenance module for car damage and repairs (OOP style)."""

from typing import Optional

from .domain import Car, Role, SystemState


class MaintenanceModule:
    """Handles car damage, repairs, and mechanic availability checks."""

    def __init__(self, state: SystemState) -> None:
        self._state = state

    def mark_car_damaged(self, car_id: int) -> None:
        car = self._state.inventory.cars.get(car_id)
        if car is None:
            raise ValueError(f"Unknown car id {car_id}")
        car.damaged = True
        car.available = False

    def repair_car(self, car_id: int, cost: int) -> None:
        from .inventory import InventoryModule  # imported lazily to avoid cycles

        if cost < 0:
            raise ValueError("Repair cost cannot be negative")
        car = self._state.inventory.cars.get(car_id)
        if car is None:
            raise ValueError(f"Unknown car id {car_id}")
        if not car.damaged:
            return
        InventoryModule(self._state).update_cash(-cost)
        car.damaged = False
        car.available = True

    def is_mechanic_available(self) -> bool:
        from .crew_management import CrewManagementModule  # lazy import

        crew_module = CrewManagementModule(self._state)
        mechanics = crew_module.get_members_by_role(Role.MECHANIC)
        return any(member.available for member in mechanics)

    def get_damaged_car(self) -> Optional[Car]:
        for car in self._state.inventory.cars.values():
            if car.damaged:
                return car
        return None

