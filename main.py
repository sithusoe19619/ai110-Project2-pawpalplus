from pawpal_system import Owner, Pet, Task, Priority, Scheduler


# --- Setup ---
owner = Owner("Alex", available_minutes=90)

dog = Pet("Rex", "dog", 3)
cat = Pet("Luna", "cat", 5, special_needs="kidney diet")

dog.add_task(Task("Morning Walk",    30, Priority.HIGH,   "exercise",  "Go around the block twice"))
dog.add_task(Task("Flea Treatment",  15, Priority.MEDIUM, "health",    "Apply monthly drops"))
dog.add_task(Task("Brush Teeth",      5, Priority.LOW,    "grooming",  "Use dog toothpaste"))
cat.add_task(Task("Special Feeding", 10, Priority.HIGH,   "nutrition", "Kidney diet wet food only"))
cat.add_task(Task("Playtime",        20, Priority.LOW,    "enrichment","Feather wand session"))
cat.add_task(Task("Grooming",        25, Priority.MEDIUM, "grooming",  "Brush coat and check ears"))

owner.add_pet(dog)
owner.add_pet(cat)

# --- Run Scheduler ---
scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# --- Print Today's Schedule ---
print("=" * 40)
print("         PAWPAL+ DAILY SCHEDULE")
print("=" * 40)
print(f"Owner  : {owner.name}")
print(f"Budget : {owner.available_minutes} min")

# Group scheduled tasks by pet
for pet in owner.pets:
    pet_tasks = [t for t in plan["scheduled"] if t.pet == pet]
    if not pet_tasks:
        continue
    print(f"\n--- {pet.name} ({pet.species}) ---")
    for task in pet_tasks:
        print(f"  [{task.priority.value.upper():<6}] {task.name:<20} {task.duration_minutes} min")

# Skipped tasks (if any)
if plan["skipped"]:
    print("\n--- Skipped ---")
    for task in plan["skipped"]:
        print(f"  [{task.priority.value.upper():<6}] {task.name:<20} {task.duration_minutes} min  ({task.pet.name})")

# Summary footer
time_used = sum(t.duration_minutes for t in plan["scheduled"])
print("\n" + "." * 40)
print(f"  {'Scheduled':<10}: {len(plan['scheduled'])} tasks")
print(f"  {'Time Used':<10}: {time_used} / {owner.available_minutes} min")
print(f"  {'Remaining':<10}: {owner.available_minutes - time_used} min")
print("=" * 40)
