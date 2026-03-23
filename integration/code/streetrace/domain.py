from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set


class Role(str, Enum):
    DRIVER = "driver"
    MECHANIC = "mechanic"
    STRATEGIST = "strategist"
    LEADER = "leader"


class MissionStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RaceStatus(str, Enum):
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CrewMember:
    """Represents a member of the racing crew in a traditional OOP style."""

    def __init__(
        self,
        member_id: int,
        name: str,
        roles: Optional[Set[Role]] = None,
        skills: Optional[Dict[Role, int]] = None,
        available: bool = True,
    ) -> None:
        self.member_id = member_id
        self.name = name
        self.roles: Set[Role] = set(roles) if roles is not None else set()
        self.skills: Dict[Role, int] = dict(skills) if skills is not None else {}
        self.available = available


class Car:
    """Represents a car that can be used in races."""

    def __init__(
        self,
        car_id: int,
        model: str,
        speed_rating: int,
        durability: int,
        damaged: bool = False,
        available: bool = True,
    ) -> None:
        self.car_id = car_id
        self.model = model
        self.speed_rating = speed_rating
        self.durability = durability
        self.damaged = damaged
        self.available = available


class Inventory:
    """Holds all cars, parts, tools, and the crew's cash balance."""

    def __init__(
        self,
        cars: Optional[Dict[int, Car]] = None,
        spare_parts: Optional[Dict[str, int]] = None,
        tools: Optional[Dict[str, int]] = None,
        cash_balance: int = 0,
    ) -> None:
        self.cars: Dict[int, Car] = dict(cars) if cars is not None else {}
        self.spare_parts: Dict[str, int] = dict(spare_parts) if spare_parts is not None else {}
        self.tools: Dict[str, int] = dict(tools) if tools is not None else {}
        self.cash_balance = cash_balance


class Race:
    """Describes a race event with constraints and result."""

    def __init__(
        self,
        race_id: int,
        name: str,
        location: Optional[str] = None,
        min_driver_skill: int = 0,
        min_car_speed: int = 0,
        prize_money: int = 0,
        damage_risk: float = 0.2,
        status: RaceStatus = RaceStatus.PLANNED,
        driver_id: Optional[int] = None,
        car_id: Optional[int] = None,
        result: Optional[str] = None,
    ) -> None:
        self.race_id = race_id
        self.name = name
        self.location = location
        self.min_driver_skill = min_driver_skill
        self.min_car_speed = min_car_speed
        self.prize_money = prize_money
        self.damage_risk = damage_risk
        self.status = status
        self.driver_id = driver_id
        self.car_id = car_id
        self.result = result


class Mission:
    """Represents a mission involving one or more crew members."""

    def __init__(
        self,
        mission_id: int,
        mission_type: str,
        required_roles: List[Role],
        assigned_crew_ids: Optional[List[int]] = None,
        status: MissionStatus = MissionStatus.PLANNED,
    ) -> None:
        self.mission_id = mission_id
        self.mission_type = mission_type
        self.required_roles: List[Role] = list(required_roles)
        self.assigned_crew_ids: List[int] = list(assigned_crew_ids) if assigned_crew_ids is not None else []
        self.status = status


class ResultRecord:
    """Stores a single race result entry for rankings and cash flow."""

    def __init__(self, race_id: int, driver_id: int, position: int, cash_delta: int) -> None:
        self.race_id = race_id
        self.driver_id = driver_id
        self.position = position
        self.cash_delta = cash_delta


class SystemState:
    """Central in-memory storage for all domain objects and ID counters."""

    def __init__(
        self,
        crew: Optional[Dict[int, CrewMember]] = None,
        inventory: Optional[Inventory] = None,
        races: Optional[Dict[int, Race]] = None,
        missions: Optional[Dict[int, Mission]] = None,
        results: Optional[List[ResultRecord]] = None,
        next_crew_id: int = 1,
        next_car_id: int = 1,
        next_race_id: int = 1,
        next_mission_id: int = 1,
    ) -> None:
        self.crew: Dict[int, CrewMember] = dict(crew) if crew is not None else {}
        self.inventory: Inventory = inventory if inventory is not None else Inventory()
        self.races: Dict[int, Race] = dict(races) if races is not None else {}
        self.missions: Dict[int, Mission] = dict(missions) if missions is not None else {}
        self.results: List[ResultRecord] = list(results) if results is not None else []
        self.next_crew_id = next_crew_id
        self.next_car_id = next_car_id
        self.next_race_id = next_race_id
        self.next_mission_id = next_mission_id

    def generate_crew_id(self) -> int:
        member_id = self.next_crew_id
        self.next_crew_id += 1
        return member_id

    def generate_car_id(self) -> int:
        car_id = self.next_car_id
        self.next_car_id += 1
        return car_id

    def generate_race_id(self) -> int:
        race_id = self.next_race_id
        self.next_race_id += 1
        return race_id

    def generate_mission_id(self) -> int:
        mission_id = self.next_mission_id
        self.next_mission_id += 1
        return mission_id
