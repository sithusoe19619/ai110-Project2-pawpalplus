import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pawpal_system import Task, Pet, Owner, Scheduler, Priority


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def basic_task():
    return Task("Walk", 30, Priority.HIGH, "exercise", "Around the block")

@pytest.fixture
def basic_pet():
    return Pet("Rex", "dog", 3)

@pytest.fixture
def pet_with_tasks():
    pet = Pet("Rex", "dog", 3)
    pet.add_task(Task("Walk",  30, Priority.HIGH,   "exercise", ""))
    pet.add_task(Task("Bath",  20, Priority.MEDIUM, "grooming", ""))
    pet.add_task(Task("Treat",  5, Priority.LOW,    "food",     ""))
    return pet

@pytest.fixture
def owner_with_pets():
    owner = Owner("Alex", available_minutes=90)
    dog = Pet("Rex", "dog", 3)
    cat = Pet("Luna", "cat", 5)
    dog.add_task(Task("Walk",     30, Priority.HIGH,   "exercise",  ""))
    dog.add_task(Task("Brush",    10, Priority.MEDIUM, "grooming",  ""))
    cat.add_task(Task("Feeding",  10, Priority.HIGH,   "nutrition", ""))
    cat.add_task(Task("Playtime", 20, Priority.LOW,    "enrichment",""))
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


# ── Task ──────────────────────────────────────────────────────────────────────

class TestTask:
    def test_default_status_is_pending(self, basic_task):
        assert basic_task.status == "pending"

    def test_default_frequency_is_daily(self, basic_task):
        assert basic_task.frequency == "daily"

    def test_is_high_priority_true(self, basic_task):
        assert basic_task.is_high_priority() is True

    def test_is_high_priority_false_for_medium(self):
        task = Task("Bath", 20, Priority.MEDIUM, "grooming", "")
        assert task.is_high_priority() is False

    def test_mark_complete_changes_status(self, basic_task):
        basic_task.mark_complete()
        assert basic_task.status == "completed"


# ── Pet ───────────────────────────────────────────────────────────────────────

class TestPet:
    def test_has_special_needs_false_by_default(self, basic_pet):
        assert basic_pet.has_special_needs() is False

    def test_has_special_needs_true_when_set(self):
        pet = Pet("Luna", "cat", 5, special_needs="kidney diet")
        assert pet.has_special_needs() is True

    def test_add_task_appends_to_list(self, basic_pet, basic_task):
        basic_pet.add_task(basic_task)
        assert basic_task in basic_pet.tasks

    def test_add_task_increases_task_count(self, basic_pet, basic_task):
        before = len(basic_pet.tasks)
        basic_pet.add_task(basic_task)
        assert len(basic_pet.tasks) == before + 1

    def test_add_task_sets_pet_reference(self, basic_pet, basic_task):
        basic_pet.add_task(basic_task)
        assert basic_task.pet is basic_pet

    def test_remove_task_removes_from_list(self, basic_pet, basic_task):
        basic_pet.add_task(basic_task)
        basic_pet.remove_task(basic_task)
        assert basic_task not in basic_pet.tasks

    def test_remove_task_clears_pet_reference(self, basic_pet, basic_task):
        basic_pet.add_task(basic_task)
        basic_pet.remove_task(basic_task)
        assert basic_task.pet is None

    def test_get_tasks_returns_all_tasks(self, pet_with_tasks):
        assert len(pet_with_tasks.get_tasks()) == 3


# ── Owner ─────────────────────────────────────────────────────────────────────

class TestOwner:
    def test_starts_with_no_pets(self):
        owner = Owner("Alex", 60)
        assert owner.pets == []

    def test_add_pet(self, basic_pet):
        owner = Owner("Alex", 60)
        owner.add_pet(basic_pet)
        assert basic_pet in owner.pets

    def test_remove_pet(self, basic_pet):
        owner = Owner("Alex", 60)
        owner.add_pet(basic_pet)
        owner.remove_pet(basic_pet)
        assert basic_pet not in owner.pets

    def test_get_all_tasks_returns_flat_list(self, owner_with_pets):
        tasks = owner_with_pets.get_all_tasks()
        assert len(tasks) == 4

    def test_get_all_tasks_empty_when_no_pets(self):
        owner = Owner("Alex", 60)
        assert owner.get_all_tasks() == []


# ── Scheduler ─────────────────────────────────────────────────────────────────

class TestScheduler:
    def test_fits_in_budget_true(self, owner_with_pets):
        scheduler = Scheduler(owner_with_pets)
        task = Task("Quick", 10, Priority.LOW, "misc", "")
        assert scheduler.fits_in_budget(task, 30) is True

    def test_fits_in_budget_false(self, owner_with_pets):
        scheduler = Scheduler(owner_with_pets)
        task = Task("Long", 60, Priority.LOW, "misc", "")
        assert scheduler.fits_in_budget(task, 30) is False

    def test_fits_in_budget_exact_match(self, owner_with_pets):
        scheduler = Scheduler(owner_with_pets)
        task = Task("Exact", 30, Priority.MEDIUM, "misc", "")
        assert scheduler.fits_in_budget(task, 30) is True

    def test_generate_plan_returns_correct_keys(self, owner_with_pets):
        plan = Scheduler(owner_with_pets).generate_plan()
        assert "scheduled" in plan
        assert "skipped" in plan
        assert "reasoning" in plan

    def test_high_priority_scheduled_before_low(self, owner_with_pets):
        plan = Scheduler(owner_with_pets).generate_plan()
        priorities = [t.priority for t in plan["scheduled"]]
        high_indices = [i for i, p in enumerate(priorities) if p == Priority.HIGH]
        low_indices  = [i for i, p in enumerate(priorities) if p == Priority.LOW]
        if high_indices and low_indices:
            assert max(high_indices) < min(low_indices)

    def test_tasks_exceeding_budget_are_skipped(self):
        owner = Owner("Alex", available_minutes=10)
        pet = Pet("Rex", "dog", 2)
        pet.add_task(Task("Long Walk", 60, Priority.HIGH, "exercise", ""))
        owner.add_pet(pet)
        plan = Scheduler(owner).generate_plan()
        assert len(plan["skipped"]) == 1
        assert len(plan["scheduled"]) == 0

    def test_get_skipped_tasks_matches_plan(self, owner_with_pets):
        scheduler = Scheduler(owner_with_pets)
        plan = scheduler.generate_plan()
        assert scheduler.get_skipped_tasks() == plan["skipped"]
