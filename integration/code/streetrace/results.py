from __future__ import annotations

from typing import List

from .domain import ResultRecord, SystemState
from .inventory import InventoryModule


class ResultsModule:
    """Handles race result recording and ranking queries (OOP style)."""

    def __init__(self, state: SystemState) -> None:
        self._state = state
        self._inventory_module = InventoryModule(state)

    def record_race_result(self, race_id: int, driver_id: int, outcome: str, prize_money: int) -> ResultRecord:
        """Record the result of a race and update rankings and cash.

        Business rule: Race results must update the cash balance in the inventory.
        """

        if prize_money < 0:
            raise ValueError("Prize money cannot be negative")

        cash_delta = prize_money if outcome.lower() == "win" else 0
        if cash_delta:
            self._inventory_module.update_cash(cash_delta)

        record = ResultRecord(
            race_id=race_id,
            driver_id=driver_id,
            position=1 if cash_delta else 0,
            cash_delta=cash_delta,
        )
        self._state.results.append(record)
        return record

    def get_rankings(self) -> List[ResultRecord]:
        return list(self._state.results)
