import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
CODE_ROOT = os.path.join(PROJECT_ROOT, "code")
if CODE_ROOT not in sys.path:
    sys.path.insert(0, CODE_ROOT)

from streetrace.domain import Role, MissionStatus, RaceStatus  # type: ignore
from streetrace.manager import StreetRaceManager  # type: ignore
import streetrace.race_management as race_management_module  # type: ignore


class RegistrationAndListingIntegrationTests(unittest.TestCase):
    """Integration tests for crew registration and listing flows (CLI options 1, 5)."""

    def setUp(self) -> None:
        self.manager = StreetRaceManager()

    def test_register_crew_and_list_status(self) -> None:
        """Register crew members and verify reporting lists them with roles and availability."""

        alice = self.manager.registration.register_member("Alice", initial_role=Role.DRIVER)
        bob = self.manager.registration.register_member("Bob", initial_role=Role.MECHANIC)

        self.manager.crew.set_skill(alice.member_id, Role.DRIVER, 4)
        self.manager.crew.set_skill(bob.member_id, Role.MECHANIC, 3)

        lines = self.manager.reporting.list_crew_status()

        # Expect both crew members to be present with their roles.
        summary = "\n".join(lines)
        self.assertIn("Alice", summary)
        self.assertIn("driver", summary)
        self.assertIn("Bob", summary)
        self.assertIn("mechanic", summary)


class InventoryAndCarsIntegrationTests(unittest.TestCase):
    """Integration tests for adding cars and viewing inventory (CLI options 2, 11, 13, 14)."""

    def setUp(self) -> None:
        self.manager = StreetRaceManager()

    def test_add_car_and_list_cars(self) -> None:
        """Adding cars via the inventory module should be reflected in the shared state."""

        car1 = self.manager.inventory.add_car("NightRider", speed_rating=8, durability=7)
        car2 = self.manager.inventory.add_car("StreetFox", speed_rating=6, durability=5)

        cars = self.manager.state.inventory.cars
        self.assertIn(car1.car_id, cars)
        self.assertIn(car2.car_id, cars)

    def test_add_spare_parts_and_tools(self) -> None:
        """Spare parts and tools should accumulate quantities in the inventory."""

        self.manager.inventory.add_spare_part("tyre", 2)
        self.manager.inventory.add_spare_part("tyre", 3)
        self.manager.inventory.add_tool("wrench", 1)
        self.manager.inventory.add_tool("wrench", 4)

        inventory = self.manager.state.inventory
        self.assertEqual(inventory.spare_parts.get("tyre"), 5)
        self.assertEqual(inventory.tools.get("wrench"), 5)


class RaceFlowIntegrationTests(unittest.TestCase):
    """Integration tests for the create/select/assign/run race flow (CLI option 3)."""

    def setUp(self) -> None:
        self.manager = StreetRaceManager()

        # Seed one capable driver and one suitable car.
        driver = self.manager.registration.register_member("Alice", initial_role=Role.DRIVER)
        self.manager.crew.set_skill(driver.member_id, Role.DRIVER, 5)

        # Start with zero cash so we can observe prize changes clearly.
        self.manager.inventory.update_cash(0)
        car = self.manager.inventory.add_car("NightRider", speed_rating=9, durability=7)
        self.car_id = car.car_id
        self.driver_id = driver.member_id

    def test_race_win_updates_cash_and_can_damage_car(self) -> None:
        """A winning race should update cash and may mark the car damaged."""

        # Create a race with thresholds satisfied by our seeded driver and car.
        race = self.manager.races.create_race(
            name="Downtown Dash",
            prize_money=5_000,
            min_driver_skill=3,
            min_car_speed=5,
        )

        # Deterministically force a win and car damage by patching random.random
        # used inside RaceManagementModule.
        original_random = race_management_module.random.random
        sequence = [0.0, 0.0]  # first call: win, second call: damage

        def fake_random() -> float:
            return sequence.pop(0)

        try:
            race_management_module.random.random = fake_random

            driver_id, car_id = self.manager.races.select_driver_and_car(race.race_id)
            self.manager.races.assign_driver_and_car(race.race_id, driver_id, car_id)
            race = self.manager.races.run_race(race.race_id)
        finally:
            race_management_module.random.random = original_random

        self.assertEqual(race.status, RaceStatus.COMPLETED)
        self.assertEqual(race.result, "win")

        # Cash balance should have increased by the prize money.
        self.assertEqual(self.manager.state.inventory.cash_balance, 5_000)

        # A single result record should have been recorded.
        self.assertEqual(len(self.manager.state.results), 1)
        record = self.manager.state.results[0]
        self.assertEqual(record.race_id, race.race_id)
        self.assertEqual(record.driver_id, driver_id)
        self.assertEqual(record.cash_delta, 5_000)

        # The used car should now be marked damaged and unavailable.
        car = self.manager.state.inventory.cars[car_id]
        self.assertTrue(car.damaged)
        self.assertFalse(car.available)

    def test_select_driver_and_car_fails_when_no_eligible_driver(self) -> None:
        """Race selection should fail if no driver meets the minimum skill requirement."""

        # Our seeded driver has skill 5; require more than that so the list is empty.
        race = self.manager.races.create_race(
            name="Too Hard Race",
            prize_money=1_000,
            min_driver_skill=10,
            min_car_speed=0,
        )

        with self.assertRaises(ValueError):
            self.manager.races.select_driver_and_car(race.race_id)

    def test_select_driver_and_car_fails_when_no_eligible_car(self) -> None:
        """Race selection should fail if no car meets the minimum speed requirement."""

        # Our seeded car has speed 9; require more than that so there are no candidates.
        race = self.manager.races.create_race(
            name="No Fast Cars",
            prize_money=1_000,
            min_driver_skill=0,
            min_car_speed=10,
        )

        with self.assertRaises(ValueError):
            self.manager.races.select_driver_and_car(race.race_id)


class MissionAndMaintenanceIntegrationTests(unittest.TestCase):
    """Integration tests for mission planning and maintenance rules (CLI options 7–10, 12)."""

    def setUp(self) -> None:
        self.manager = StreetRaceManager()

        # Seed one driver and one mechanic.
        self.driver = self.manager.registration.register_member("Driver", initial_role=Role.DRIVER)
        self.mechanic = self.manager.registration.register_member("Mechanic", initial_role=Role.MECHANIC)
        self.manager.crew.set_skill(self.driver.member_id, Role.DRIVER, 4)
        self.manager.crew.set_skill(self.mechanic.member_id, Role.MECHANIC, 4)

        car = self.manager.inventory.add_car("NightRider", speed_rating=8, durability=6)
        self.car_id = car.car_id

        # Mark the car as damaged to activate the special mechanic rule.
        self.manager.maintenance.mark_car_damaged(self.car_id)

    def test_mission_requires_mechanic_when_car_damaged(self) -> None:
        """Missions needing a mechanic cannot start without an available mechanic when a car is damaged."""

        # Mission 1: missing mechanic role among assigned crew.
        mission1 = self.manager.missions.create_mission("repairs", [Role.MECHANIC])
        self.manager.missions.assign_crew(mission1.mission_id, [self.driver.member_id])
        started = self.manager.missions.start_mission(mission1.mission_id)
        self.assertFalse(started)
        self.assertEqual(mission1.status, MissionStatus.PLANNED)

        # Mission 2: mechanic assigned but marked unavailable.
        self.manager.state.crew[self.mechanic.member_id].available = False
        mission2 = self.manager.missions.create_mission("repairs", [Role.MECHANIC])
        self.manager.missions.assign_crew(mission2.mission_id, [self.driver.member_id, self.mechanic.member_id])
        started = self.manager.missions.start_mission(mission2.mission_id)
        self.assertFalse(started)
        self.assertEqual(mission2.status, MissionStatus.PLANNED)

        # Mission 3: mechanic assigned and available, mission should start.
        self.manager.state.crew[self.mechanic.member_id].available = True
        mission3 = self.manager.missions.create_mission("repairs", [Role.MECHANIC])
        self.manager.missions.assign_crew(mission3.mission_id, [self.driver.member_id, self.mechanic.member_id])
        started = self.manager.missions.start_mission(mission3.mission_id)
        self.assertTrue(started)
        self.assertEqual(mission3.status, MissionStatus.IN_PROGRESS)

    def test_mission_cannot_start_without_any_assigned_crew(self) -> None:
        """Missions must have at least one crew member assigned before starting."""

        mission = self.manager.missions.create_mission("unassigned", [Role.DRIVER])
        started = self.manager.missions.start_mission(mission.mission_id)
        self.assertFalse(started)
        self.assertEqual(mission.status, MissionStatus.PLANNED)

    def test_repair_car_restores_availability_and_reduces_cash(self) -> None:
        """Repairing a damaged car should restore availability and deduct cash via inventory."""

        # Give the crew some cash and record the starting balance.
        self.manager.inventory.update_cash(1_000)
        start_cash = self.manager.state.inventory.cash_balance
        cost = 300

        self.manager.maintenance.repair_car(self.car_id, cost)

        car = self.manager.state.inventory.cars[self.car_id]
        self.assertFalse(car.damaged)
        self.assertTrue(car.available)
        self.assertEqual(self.manager.state.inventory.cash_balance, start_cash - cost)

    def test_repair_car_with_insufficient_cash_raises_and_keeps_state(self) -> None:
        """Repairs that would overdraw cash should raise and not change car state."""

        # Ensure cash is lower than the repair cost.
        start_cash = self.manager.state.inventory.cash_balance
        cost = start_cash + 100 or 100

        with self.assertRaises(ValueError):
            self.manager.maintenance.repair_car(self.car_id, cost)

        car = self.manager.state.inventory.cars[self.car_id]
        self.assertTrue(car.damaged)
        self.assertFalse(car.available)
        self.assertEqual(self.manager.state.inventory.cash_balance, start_cash)


class ReportingOverviewIntegrationTests(unittest.TestCase):
    """Integration test for the high-level overview report (CLI option 4)."""

    def test_generate_overview_reflects_state(self) -> None:
        manager = StreetRaceManager()

        # Seed minimal state: one crew, one car, one completed race result.
        crew = manager.registration.register_member("Alice", initial_role=Role.DRIVER)
        manager.crew.set_skill(crew.member_id, Role.DRIVER, 5)
        car = manager.inventory.add_car("NightRider", speed_rating=8, durability=7)

        race = manager.races.create_race(
            name="Test Race",
            prize_money=1_000,
            min_driver_skill=0,
            min_car_speed=0,
        )

        # Force deterministic win without damaging the car.
        original_random = race_management_module.random.random
        sequence = [0.0, 1.0]  # win, then no damage

        def fake_random() -> float:
            return sequence.pop(0)

        try:
            race_management_module.random.random = fake_random
            driver_id, car_id = manager.races.select_driver_and_car(race.race_id)
            manager.races.assign_driver_and_car(race.race_id, driver_id, car_id)
            manager.races.run_race(race.race_id)
        finally:
            race_management_module.random.random = original_random

        overview = manager.reporting.generate_overview()

        # Overview string should mention races, crew count, and cash balance.
        self.assertIn("Races:", overview)
        self.assertIn("Crew members:", overview)
        self.assertIn("Cash balance:", overview)


if __name__ == "__main__":
    unittest.main()
