from __future__ import annotations

from typing import List

from .domain import ResultRecord, SystemState


class ReportingModule:
    """Provides read-only reporting views over the current system state."""

    def __init__(self, state: SystemState) -> None:
        self._state = state

    def generate_overview(self) -> str:
        total_races = len(self._state.races)
        completed_races = sum(1 for r in self._state.races.values() if r.result is not None)
        total_crew = len(self._state.crew)
        cash = self._state.inventory.cash_balance
        return (
            f"Races: {completed_races}/{total_races}, "
            f"Crew members: {total_crew}, "
            f"Cash balance: {cash}"
        )

    def list_crew_status(self) -> List[str]:
        lines: List[str] = []
        for member in self._state.crew.values():
            roles = ",".join(sorted(role.value for role in member.roles)) or "(no roles)"
            availability = "available" if member.available else "unavailable"
            lines.append(f"{member.member_id}: {member.name} [{roles}] - {availability}")
        return lines

    def list_results(self) -> List[ResultRecord]:
        return list(self._state.results)
