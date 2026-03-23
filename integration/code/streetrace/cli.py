from __future__ import annotations

"""Command-line interface for the StreetRace Manager system.

Two main entry points:
- an interactive text menu ("real" CLI for manual use)
"""

import sys

from .domain import Role, SystemState
from .manager import StreetRaceManager


def _prompt(text: str) -> str:
    return input(text).strip()


def run_interactive() -> None:
    """Run a small interactive CLI around StreetRaceManager.

    This gives you a *functioning system* you can drive from the
    terminal.
    """

    manager = StreetRaceManager()

    while True:
        print("\n=== StreetRace Manager ===")
        print("1) Register crew member")
        print("2) Add car")
        print("3) Create + auto-run race")
        print("4) Show overview")
        print("5) List crew")
        print("6) List race results")
        print("7) Create mission")
        print("8) Assign crew to mission")
        print("9) Start mission")
        print("10) List missions")
        print("11) List cars")
        print("12) Repair damaged car")
        print("13) Add spare part")
        print("14) Add tool")
        print("0) Exit")

        choice = _prompt("Select option: ")

        if choice == "0":
            print("Exiting StreetRace Manager.")
            break

        if choice == "1":
            name = _prompt("Crew member name: ")
            role_str = _prompt("Initial role (driver/mechanic/strategist/leader or blank): ")
            role = None
            if role_str:
                mapping = {
                    "driver": Role.DRIVER,
                    "mechanic": Role.MECHANIC,
                    "strategist": Role.STRATEGIST,
                    "leader": Role.LEADER,
                }
                role = mapping.get(role_str.lower())
                if role is None:
                    print("Unknown role; member will be created with no roles.")
            member = manager.registration.register_member(name, initial_role=role)
            if role is not None:
                skill_str = _prompt(f"Skill level for {role.value} (int, default 0): ")
                if skill_str:
                    try:
                        level = int(skill_str)
                        manager.crew.set_skill(member.member_id, role, level)
                    except ValueError:
                        print("Invalid skill; leaving at default.")
            print(f"Registered crew member with id {member.member_id}.")

        elif choice == "2":
            model = _prompt("Car model: ")
            try:
                speed = int(_prompt("Speed rating (int): "))
                durability = int(_prompt("Durability (int): "))
            except ValueError:
                print("Invalid numbers for speed/durability.")
                continue
            try:
                car = manager.inventory.add_car(model=model, speed_rating=speed, durability=durability)
                print(f"Added car with id {car.car_id}.")
            except ValueError as exc:
                print(f"Error: {exc}")

        elif choice == "3":
            name = _prompt("Race name: ")
            try:
                prize = int(_prompt("Prize money: "))
                min_skill = int(_prompt("Min driver skill (int, default 0): ") or "0")
                min_speed = int(_prompt("Min car speed (int, default 0): ") or "0")
            except ValueError:
                print("Invalid numbers.")
                continue
            try:
                race = manager.races.create_race(
                    name=name,
                    prize_money=prize,
                    min_driver_skill=min_skill,
                    min_car_speed=min_speed,
                )
                driver_id, car_id = manager.races.select_driver_and_car(race.race_id)
                manager.races.assign_driver_and_car(race.race_id, driver_id, car_id)
                race = manager.races.run_race(race.race_id)
                print(f"Race '{race.name}' completed with result: {race.result}.")
            except ValueError as exc:
                print(f"Cannot run race: {exc}")

        elif choice == "4":
            print(manager.reporting.generate_overview())

        elif choice == "5":
            for line in manager.reporting.list_crew_status():
                print(line)

        elif choice == "6":
            for rec in manager.reporting.list_results():
                print(f"Race {rec.race_id}, driver {rec.driver_id}, position {rec.position}, cash {rec.cash_delta}")

        elif choice == "7":
            mission_type = _prompt("Mission type/description: ")
            roles_str = _prompt(
                "Required roles (comma-separated from driver,mechanic,strategist,leader): "
            )
            role_map = {
                "driver": Role.DRIVER,
                "mechanic": Role.MECHANIC,
                "strategist": Role.STRATEGIST,
                "leader": Role.LEADER,
            }
            required_roles = []
            if roles_str:
                for part in roles_str.split(","):
                    key = part.strip().lower()
                    if key in role_map:
                        required_roles.append(role_map[key])
                    elif key:
                        print(f"Ignoring unknown role '{key}'.")
            mission = manager.missions.create_mission(mission_type, required_roles)
            print(f"Created mission with id {mission.mission_id}.")

        elif choice == "8":
            try:
                mission_id = int(_prompt("Mission id: "))
            except ValueError:
                print("Invalid mission id.")
                continue
            print("Current crew:")
            for line in manager.reporting.list_crew_status():
                print("  ", line)
            crew_str = _prompt("Assign crew ids (comma-separated): ")
            try:
                crew_ids = [int(x.strip()) for x in crew_str.split(",") if x.strip()]
            except ValueError:
                print("Invalid crew id list.")
                continue
            try:
                manager.missions.assign_crew(mission_id, crew_ids)
                print("Crew assigned to mission.")
            except ValueError as exc:
                print(f"Error: {exc}")

        elif choice == "9":
            try:
                mission_id = int(_prompt("Mission id to start: "))
            except ValueError:
                print("Invalid mission id.")
                continue
            try:
                started = manager.missions.start_mission(mission_id)
                if started:
                    print("Mission started and is now IN_PROGRESS.")
                else:
                    print("Mission could not be started (requirements not met).")
            except ValueError as exc:
                print(f"Error: {exc}")

        elif choice == "10":
            if not manager.state.missions:
                print("No missions defined.")
            for mission in manager.state.missions.values():
                roles = ",".join(r.value for r in mission.required_roles) or "(none)"
                crew_ids = ",".join(str(cid) for cid in mission.assigned_crew_ids) or "(none)"
                print(
                    f"Mission {mission.mission_id}: {mission.mission_type} "
                    f"[roles={roles}] [crew={crew_ids}] status={mission.status.value}"
                )

        elif choice == "11":
            cars = manager.state.inventory.cars
            if not cars:
                print("No cars in inventory.")
            for car in cars.values():
                status = []
                status.append("available" if car.available else "unavailable")
                if car.damaged:
                    status.append("DAMAGED")
                print(
                    f"Car {car.car_id}: {car.model} "
                    f"speed={car.speed_rating} durability={car.durability} "
                    f"status={'/'.join(status)}"
                )

        elif choice == "12":
            try:
                car_id = int(_prompt("Car id to repair: "))
                cost = int(_prompt("Repair cost: "))
            except ValueError:
                print("Invalid car id or cost.")
                continue
            try:
                manager.maintenance.repair_car(car_id, cost)
                print("Repair attempted; check car list and cash balance.")
            except ValueError as exc:
                print(f"Error: {exc}")

        elif choice == "13":
            name = _prompt("Spare part name: ")
            try:
                qty = int(_prompt("Quantity: "))
            except ValueError:
                print("Invalid quantity.")
                continue
            try:
                manager.inventory.add_spare_part(name, qty)
                print("Spare part added.")
            except ValueError as exc:
                print(f"Error: {exc}")

        elif choice == "14":
            name = _prompt("Tool name: ")
            try:
                qty = int(_prompt("Quantity: "))
            except ValueError:
                print("Invalid quantity.")
                continue
            try:
                manager.inventory.add_tool(name, qty)
                print("Tool added.")
            except ValueError as exc:
                print(f"Error: {exc}")

        else:
            print("Unknown choice. Please try again.")


def main(argv: list[str] | None = None) -> None:
    run_interactive()


if __name__ == "__main__":  # pragma: no cover
    main()
