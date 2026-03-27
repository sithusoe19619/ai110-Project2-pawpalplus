from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: Priority
    category: str
    notes: str
    frequency: str = "daily"      # e.g. "daily", "weekly", "as needed"
    status: str = "pending"
    pet: Optional["Pet"] = None

    def is_high_priority(self) -> bool:
        """Return True if this task has HIGH priority."""
        return self.priority == Priority.HIGH

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.status = "completed"

    def __repr__(self) -> str:
        return (
            f"Task(name={self.name!r}, duration={self.duration_minutes}min, "
            f"priority={self.priority.value}, frequency={self.frequency!r}, status={self.status!r})"
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""
    tasks: List["Task"] = field(default_factory=list)

    def has_special_needs(self) -> bool:
        """Return True if this pet has a non-empty special needs description."""
        return bool(self.special_needs.strip())

    def add_task(self, task: "Task") -> None:
        """Add a task to this pet and set the task's pet reference."""
        task.pet = self
        self.tasks.append(task)

    def remove_task(self, task: "Task") -> None:
        """Remove a task from this pet and clear the task's pet reference."""
        self.tasks.remove(task)
        task.pet = None

    def get_tasks(self) -> List["Task"]:
        """Return the list of tasks assigned to this pet."""
        return self.tasks


class Owner:
    def __init__(self, name: str, available_minutes: int):
        self.name = name
        self.available_minutes = available_minutes
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's pet list."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return a flat list of every task across all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.scheduled_tasks: List[Task] = []
        self.skipped_tasks: List[Task] = []

    def generate_plan(self) -> dict:
        """
        Returns: {"scheduled": List[Task], "skipped": List[Task], "reasoning": List[str]}
        Schedules high-priority tasks first, fitting within the owner's available minutes.
        """
        self.scheduled_tasks = []
        self.skipped_tasks = []
        reasoning = []

        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        all_tasks = sorted(
            self.owner.get_all_tasks(),
            key=lambda t: priority_order[t.priority]
        )

        time_remaining = self.owner.available_minutes

        for task in all_tasks:
            if self.fits_in_budget(task, time_remaining):
                self.scheduled_tasks.append(task)
                time_remaining -= task.duration_minutes
                reasoning.append(
                    f"Scheduled '{task.name}' for {task.pet.name} "
                    f"({task.duration_minutes} min, {task.priority.value} priority)"
                )
            else:
                self.skipped_tasks.append(task)
                reasoning.append(
                    f"Skipped '{task.name}' for {task.pet.name} "
                    f"({task.duration_minutes} min) — only {time_remaining} min remaining"
                )

        return {
            "scheduled": self.scheduled_tasks,
            "skipped": self.skipped_tasks,
            "reasoning": reasoning,
        }

    def fits_in_budget(self, task: Task, time_remaining: int) -> bool:
        """Return True if the task's duration fits within the remaining time."""
        return task.duration_minutes <= time_remaining

    def get_skipped_tasks(self) -> List[Task]:
        """Return the list of tasks that were skipped due to time constraints."""
        return self.skipped_tasks
