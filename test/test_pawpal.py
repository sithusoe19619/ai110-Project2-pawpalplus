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


# ── Phase 5: Sorting ────────────────────────────────────────────────────────

class TestSortByTime:
    def test_sorts_tasks_in_chronological_order(self):
        owner = Owner("Alex", 120)
        pet = Pet("Rex", "dog", 3)
        t1 = Task("Evening Walk", 30, Priority.HIGH, "exercise", "", scheduled_time="18:00")
        t2 = Task("Morning Walk", 30, Priority.HIGH, "exercise", "", scheduled_time="07:00")
        t3 = Task("Lunch Feed",  10, Priority.MEDIUM, "nutrition", "", scheduled_time="12:00")
        pet.add_task(t1)
        pet.add_task(t2)
        pet.add_task(t3)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        result = scheduler.sort_by_time([t1, t2, t3])
        assert result == [t2, t3, t1]

    def test_same_time_returns_both_without_error(self):
        owner = Owner("Alex", 120)
        pet = Pet("Rex", "dog", 3)
        t1 = Task("Walk",  30, Priority.HIGH, "exercise", "", scheduled_time="08:00")
        t2 = Task("Train", 20, Priority.MEDIUM, "training", "", scheduled_time="08:00")
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        result = scheduler.sort_by_time([t1, t2])
        assert len(result) == 2
        assert all(t in result for t in [t1, t2])

    def test_empty_list_returns_empty(self):
        owner = Owner("Alex", 120)
        scheduler = Scheduler(owner)

        result = scheduler.sort_by_time([])
        assert result == []


# ── Phase 5: Recurring Tasks ────────────────────────────────────────────────

class TestMarkComplete:
    def test_daily_task_creates_next_day(self):
        task = Task("Walk", 30, Priority.HIGH, "exercise", "",
                    scheduled_date="2026-03-28", frequency="daily")
        next_task = task.mark_complete()

        assert task.status == "completed"
        assert next_task is not None
        assert next_task.scheduled_date == "2026-03-29"
        assert next_task.status == "pending"

    def test_weekly_task_creates_next_week(self):
        task = Task("Bath", 45, Priority.MEDIUM, "grooming", "",
                    scheduled_date="2026-03-28", frequency="weekly")
        next_task = task.mark_complete()

        assert next_task is not None
        assert next_task.scheduled_date == "2026-04-04"
        assert next_task.status == "pending"

    def test_as_needed_returns_none(self):
        task = Task("Vet Visit", 60, Priority.HIGH, "health", "",
                    frequency="as needed")
        next_task = task.mark_complete()

        assert task.status == "completed"
        assert next_task is None

    def test_next_task_added_to_same_pet(self):
        pet = Pet("Rex", "dog", 3)
        task = Task("Walk", 30, Priority.HIGH, "exercise", "",
                    scheduled_date="2026-03-28", frequency="daily")
        pet.add_task(task)
        before_count = len(pet.tasks)

        next_task = task.mark_complete()

        assert next_task in pet.tasks
        assert len(pet.tasks) == before_count + 1
        assert next_task.pet is pet


# ── Phase 5: Conflict Detection ─────────────────────────────────────────────

class TestDetectConflicts:
    def test_same_pet_overlap(self):
        owner = Owner("Alex", 120)
        pet = Pet("Rex", "dog", 3)
        t1 = Task("Walk",  30, Priority.HIGH, "exercise", "",
                  scheduled_time="08:00", scheduled_date="2026-03-28")
        t2 = Task("Train", 30, Priority.MEDIUM, "training", "",
                  scheduled_time="08:15", scheduled_date="2026-03-28")
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        conflicts = scheduler.detect_conflicts([t1, t2])
        assert len(conflicts) == 1
        assert conflicts[0]["type"] == "same_pet"

    def test_cross_pet_overlap(self):
        owner = Owner("Alex", 120)
        dog = Pet("Rex", "dog", 3)
        cat = Pet("Luna", "cat", 5)
        t1 = Task("Walk Rex",  30, Priority.HIGH, "exercise", "",
                  scheduled_time="08:00", scheduled_date="2026-03-28")
        t2 = Task("Feed Luna", 20, Priority.HIGH, "nutrition", "",
                  scheduled_time="08:10", scheduled_date="2026-03-28")
        dog.add_task(t1)
        cat.add_task(t2)
        owner.add_pet(dog)
        owner.add_pet(cat)
        scheduler = Scheduler(owner)

        conflicts = scheduler.detect_conflicts([t1, t2])
        assert len(conflicts) == 1
        assert conflicts[0]["type"] == "cross_pet"

    def test_different_dates_no_conflict(self):
        owner = Owner("Alex", 120)
        pet = Pet("Rex", "dog", 3)
        t1 = Task("Walk", 30, Priority.HIGH, "exercise", "",
                  scheduled_time="08:00", scheduled_date="2026-03-28")
        t2 = Task("Walk", 30, Priority.HIGH, "exercise", "",
                  scheduled_time="08:00", scheduled_date="2026-03-29")
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        conflicts = scheduler.detect_conflicts([t1, t2])
        assert conflicts == []

    def test_adjacent_times_no_conflict(self):
        owner = Owner("Alex", 120)
        pet = Pet("Rex", "dog", 3)
        t1 = Task("Walk",  30, Priority.HIGH, "exercise", "",
                  scheduled_time="08:00", scheduled_date="2026-03-28")
        t2 = Task("Train", 30, Priority.MEDIUM, "training", "",
                  scheduled_time="08:30", scheduled_date="2026-03-28")
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        conflicts = scheduler.detect_conflicts([t1, t2])
        assert conflicts == []


# ── Phase 5: Filtering ──────────────────────────────────────────────────────

class TestFilterTasks:
    def test_filter_by_status(self):
        owner = Owner("Alex", 120)
        pet = Pet("Rex", "dog", 3)
        t1 = Task("Walk",  30, Priority.HIGH, "exercise", "", status="pending")
        t2 = Task("Bath",  20, Priority.MEDIUM, "grooming", "", status="completed")
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        result = scheduler.filter_tasks([t1, t2], status="pending")
        assert result == [t1]

    def test_filter_by_pet_name_case_insensitive(self):
        owner = Owner("Alex", 120)
        dog = Pet("Rex", "dog", 3)
        cat = Pet("Luna", "cat", 5)
        t1 = Task("Walk", 30, Priority.HIGH, "exercise", "")
        t2 = Task("Feed", 10, Priority.HIGH, "nutrition", "")
        dog.add_task(t1)
        cat.add_task(t2)
        owner.add_pet(dog)
        owner.add_pet(cat)
        scheduler = Scheduler(owner)

        result = scheduler.filter_tasks([t1, t2], pet_name="rex")
        assert result == [t1]

    def test_combined_filters_use_and_logic(self):
        owner = Owner("Alex", 120)
        pet = Pet("Rex", "dog", 3)
        t1 = Task("Walk",  30, Priority.HIGH, "exercise", "", status="pending")
        t2 = Task("Bath",  20, Priority.MEDIUM, "grooming", "", status="completed")
        t3 = Task("Train", 15, Priority.LOW, "training", "", status="pending")
        pet.add_task(t1)
        pet.add_task(t2)
        pet.add_task(t3)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        result = scheduler.filter_tasks([t1, t2, t3], status="pending", pet_name="Rex")
        assert result == [t1, t3]

    def test_no_filters_returns_full_list(self):
        owner = Owner("Alex", 120)
        pet = Pet("Rex", "dog", 3)
        t1 = Task("Walk", 30, Priority.HIGH, "exercise", "")
        t2 = Task("Bath", 20, Priority.MEDIUM, "grooming", "")
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        result = scheduler.filter_tasks([t1, t2])
        assert result == [t1, t2]


# ── Phase 5: Scheduling ─────────────────────────────────────────────────────

class TestGeneratePlan:
    def test_all_tasks_fit_within_budget(self):
        owner = Owner("Alex", 120)
        pet = Pet("Rex", "dog", 3)
        pet.add_task(Task("Walk",  30, Priority.HIGH, "exercise", ""))
        pet.add_task(Task("Bath",  20, Priority.MEDIUM, "grooming", ""))
        pet.add_task(Task("Treat",  5, Priority.LOW, "food", ""))
        owner.add_pet(pet)

        plan = Scheduler(owner).generate_plan()
        assert len(plan["scheduled"]) == 3
        assert len(plan["skipped"]) == 0

    def test_high_priority_scheduled_low_skipped_when_budget_tight(self):
        owner = Owner("Alex", 35)
        pet = Pet("Rex", "dog", 3)
        high = Task("Walk",  30, Priority.HIGH, "exercise", "")
        low  = Task("Treat", 10, Priority.LOW, "food", "")
        pet.add_task(high)
        pet.add_task(low)
        owner.add_pet(pet)

        plan = Scheduler(owner).generate_plan()
        assert high in plan["scheduled"]
        assert low in plan["skipped"]

    def test_pet_with_no_tasks(self):
        owner = Owner("Alex", 60)
        pet = Pet("Rex", "dog", 3)
        owner.add_pet(pet)

        plan = Scheduler(owner).generate_plan()
        assert plan["scheduled"] == []
        assert plan["skipped"] == []
        assert plan["reasoning"] == []
