# StreetRace Manager – CLI Call Graphs

This file now shows **only** the flows that are reachable via the
command-line interface in `cli.py`:

- `python3 -m integration.code.streetrace.cli` → interactive menu
- `python3 -m integration.code.streetrace.cli --demo` → fixed demo

Notation:
- Each indent (`->`) means a call into another method.
- Methods are written as `ClassName.method()` or `module.function()`.

---

## 1. Entry Points

```text
python -m integration.code.streetrace.cli
  -> cli.main(argv)
    -> run_interactive()

python -m integration.code.streetrace.cli --demo
  -> cli.main(argv)
    -> run_demo()
```

---

## 2. Interactive Menu Flows (`run_interactive`)

### 2.1 Register Crew Member (option 1)

```text
run_interactive()
  -> StreetRaceManager.__init__()
    -> SystemState.__init__()
    -> RegistrationModule.__init__(state)
    -> CrewManagementModule.__init__(state)
    -> InventoryModule.__init__(state)
    -> MaintenanceModule.__init__(state)
    -> RaceManagementModule.__init__(state)
    -> MissionPlanningModule.__init__(state)
    -> ResultsModule.__init__(state)
    -> ReportingModule.__init__(state)

  # option "1"
  -> RegistrationModule.register_member(name, initial_role)
    -> SystemState.generate_crew_id()
    -> CrewMember.__init__()
    -> state.crew[member_id] = CrewMember
  -> (optional) CrewManagementModule.set_skill(member_id, role, level)
    -> CrewManagementModule._get_member()
```

### 2.2 Add Car (option 2)

```text
run_interactive()
  # option "2"
  -> InventoryModule.add_car(model, speed_rating, durability)
    -> SystemState.generate_car_id()
    -> Car.__init__()
    -> state.inventory.cars[car_id] = Car
```

### 2.3 Create + Auto-run Race (option 3)

```text
run_interactive()
  # option "3"
  -> RaceManagementModule.create_race(name, prize_money, min_driver_skill, min_car_speed)
    -> SystemState.generate_race_id()
    -> Race.__init__(race_id, ...)
    -> state.races[race_id] = Race

  -> RaceManagementModule.select_driver_and_car(race_id)
    -> lookup race in state.races
    -> CrewManagementModule.get_available_drivers(min_skill = race.min_driver_skill)
       -> iterate state.crew.values()
       -> filter by Role.DRIVER, availability, and skill >= threshold
    -> InventoryModule.get_available_cars(min_speed = race.min_car_speed)
       -> iterate state.inventory.cars.values()
       -> filter by not damaged, available, speed_rating >= threshold
    -> pick best driver + best car

  -> RaceManagementModule.assign_driver_and_car(race_id, driver_id, car_id)
    -> validate driver in state.crew with Role.DRIVER and available
    -> validate car in state.inventory.cars (not damaged, available)
    -> set race.driver_id, race.car_id
    -> set race.status = SCHEDULED

  -> RaceManagementModule.run_race(race_id)
    -> validate race is runnable
    -> set race.status = RUNNING
    -> compute outcome = "win" or "loss" (random)
    -> set race.result, race.status = COMPLETED
    -> ResultsModule.record_race_result(race_id, driver_id, outcome, prize_money)
       -> if outcome == "win":
          InventoryModule.update_cash(+prize_money)
       -> ResultRecord.__init__()
       -> state.results.append(ResultRecord)
    -> maybe damage car (random vs race.damage_risk)
       -> MaintenanceModule.mark_car_damaged(car_id)
          -> lookup car in state.inventory.cars
          -> set car.damaged = True, car.available = False
```

### 2.4 Reporting / Listings (options 4–6, 11)

```text
run_interactive()
  # option "4" – Show overview
  -> ReportingModule.generate_overview()
    -> read state.races, state.crew, state.inventory.cash_balance

  # option "5" – List crew
  -> ReportingModule.list_crew_status()
    -> iterate state.crew.values()

  # option "6" – List race results
  -> ReportingModule.list_results()
    -> return list(state.results)

  # option "11" – List cars
  -> access state.inventory.cars
```

### 2.5 Mission Planning (options 7–10)

```text
run_interactive()
  # option "7" – Create mission
  -> MissionPlanningModule.create_mission(mission_type, required_roles)
    -> SystemState.generate_mission_id()
    -> Mission.__init__(mission_id, mission_type, required_roles)
    -> state.missions[mission_id] = Mission

  # option "8" – Assign crew to mission
  -> MissionPlanningModule.assign_crew(mission_id, crew_ids)
    -> lookup mission in state.missions
    -> validate each crew_id exists in state.crew
    -> mission.assigned_crew_ids = crew_ids

  # option "9" – Start mission
  -> MissionPlanningModule.start_mission(mission_id)
    -> lookup mission in state.missions
    -> check status == PLANNED and crew assigned
    -> compute assigned_roles from state.crew[crew_id].roles
    -> ensure all mission.required_roles are present
    -> ensure all assigned crew are available
    -> if Role.MECHANIC required and MaintenanceModule.get_damaged_car() is not None:
       -> if not MaintenanceModule.is_mechanic_available(): return False
    -> mission.status = IN_PROGRESS

  # option "10" – List missions
  -> iterate state.missions.values()
```

### 2.6 Maintenance & Inventory Extras (options 12–14)

```text
run_interactive()
  # option "12" – Repair damaged car
  -> MaintenanceModule.repair_car(car_id, cost)
    -> InventoryModule.update_cash(-cost)
    -> set car.damaged = False, car.available = True

  # option "13" – Add spare part
  -> InventoryModule.add_spare_part(name, quantity)
    -> update state.inventory.spare_parts[name]

  # option "14" – Add tool
  -> InventoryModule.add_tool(name, quantity)
    -> update state.inventory.tools[name]
```

---

## 3. Demo Scenario (`--demo`)

```text
main(["--demo"]) or python -m ... --demo
  -> run_demo()
    -> initialise_demo_manager()
      -> StreetRaceManager.__init__()  # as in 2.1
      -> seed crew + cars (same calls as option 1 + 2)
    -> RaceManagementModule.create_race(...)
    -> RaceManagementModule.select_driver_and_car(...)
    -> RaceManagementModule.assign_driver_and_car(...)
    -> RaceManagementModule.run_race(...)
    -> MissionPlanningModule.create_mission(...)
    -> MissionPlanningModule.assign_crew(...)
    -> MissionPlanningModule.start_mission(...)
    -> ReportingModule.generate_overview()
```

These call graphs now match exactly what a user can trigger from the
CLI, either through the interactive menu or via the `--demo` flag.
