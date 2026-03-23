from __future__ import annotations

"""Inventory module with an object-oriented interface."""

from typing import Dict, List

from .domain import Car, Inventory, SystemState


class InventoryModule:
    """Tracks cars, spare parts, tools, and cash balance."""

    def __init__(self, state: SystemState) -> None:
        self._state = state

    @property
    def inventory(self) -> Inventory:
        return self._state.inventory

    def add_car(self, model: str, speed_rating: int, durability: int) -> Car:
        if speed_rating <= 0 or durability <= 0:
            raise ValueError("Speed and durability must be positive")

        car_id = self._state.generate_car_id()
        car = Car(car_id=car_id, model=model, speed_rating=speed_rating, durability=durability)
        self._state.inventory.cars[car_id] = car
        return car

    def add_spare_part(self, part_name: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        parts: Dict[str, int] = self._state.inventory.spare_parts
        parts[part_name] = parts.get(part_name, 0) + quantity

    def add_tool(self, tool_name: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        tools: Dict[str, int] = self._state.inventory.tools
        tools[tool_name] = tools.get(tool_name, 0) + quantity

    def update_cash(self, delta: int) -> None:
        new_balance = self._state.inventory.cash_balance + delta
        if new_balance < 0:
            raise ValueError("Cash balance cannot go negative")
        self._state.inventory.cash_balance = new_balance

    def get_available_cars(self, min_speed: int = 0) -> List[Car]:
        cars: List[Car] = []
        for car in self._state.inventory.cars.values():
            if not car.available or car.damaged:
                continue
            if car.speed_rating < min_speed:
                continue
            cars.append(car)
        cars.sort(key=lambda c: c.speed_rating, reverse=True)
        return cars

