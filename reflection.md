# PawPal+ Project Reflection

## 1. System Design
The three core actions a user should be able to perform in PawPal+ are:

1. **Enter owner and pet info** — The user provides basic context about themselves and their pet, including the owner's name, the pet's name and type, and how much time is available in the day. This information gives the scheduler the constraints it needs to build a realistic plan.

2. **Add and manage care tasks** — The user creates tasks representing pet care responsibilities (such as walks, feeding, medications, grooming, or enrichment). Each task includes at minimum a name, an estimated duration, and a priority level. Users can also edit or remove tasks as their pet's needs change.

3. **Generate and view a daily plan** — The user triggers the scheduler to produce a prioritized, constraint-aware daily schedule. The app displays the resulting plan clearly and explains the reasoning behind it — for example, why certain tasks were included, deferred, or ordered the way they were.

**a. Initial design**
The system is built around four core classes:

- **`Pet`** — A dataclass that holds information about the pet, including name, species, age, and any special needs (such as required medication). It is responsible for representing the pet's profile and exposing a `has_special_needs()` method that the scheduler can use to prioritize certain tasks.

- **`Task`** — A dataclass that represents a single pet care responsibility. It stores the task name, estimated duration in minutes, priority level (low/medium/high), category (e.g. walk, feeding, grooming), notes, and a status field to track whether it was scheduled or skipped. It provides `is_high_priority()` as a convenience method for scheduling logic.

- **`Owner`** — Holds the owner's name, their daily time budget (`available_minutes`), a reference to their `Pet`, and a list of `Task` objects. It is responsible for managing the task list through `add_task()` and `remove_task()`, making it the single source of truth for all scheduling inputs.

- **`Scheduler`** — Takes an `Owner` as its only input and accesses the pet and tasks through it. Responsible for generating a daily care plan via `generate_plan()`, checking whether a task fits within the remaining time budget via `fits_in_budget()`, and returning any tasks that couldn't be scheduled via `get_skipped_tasks()`.

**b. Design changes**
Yes, the design changed several times during the skeleton review phase. The most significant changes were:

- **Removed `Pet` from `Scheduler`** — The initial UML had `Scheduler` holding both `owner` and `pet` as separate attributes. Since `pet` is already accessible via `owner.pet`, this was redundant. Removing it made `Owner` the single entry point into the model, which is cleaner and avoids the two getting out of sync.

- **Added `Priority` enum** — The original design used a plain `str` for `Task.priority`. This was replaced with a `Priority` enum (`LOW`, `MEDIUM`, `HIGH`) to prevent invalid values like `"HIGH"` or `"urgent"` from silently breaking scheduling logic.

- **Added `Task.pet` reference** — Tasks initially had no link back to the `Pet` they belonged to. A `pet: Optional[Pet]` field was added so the scheduler can inspect pet-specific constraints (like `special_needs`) directly from a task. `Owner.add_task()` automatically sets this link when a task is added.

- **Added `status` default and `Scheduler` state** — `Task.status` originally had no default, requiring callers to always pass it. It now defaults to `"pending"`. Similarly, `Scheduler` was given `scheduled_tasks` and `skipped_tasks` lists so that `get_skipped_tasks()` has persistent state to return after `generate_plan()` runs.

- **Gave `generate_plan()` a defined return structure** — The method originally returned `None`. It now returns a `dict` with keys `"scheduled"`, `"skipped"`, and `"reasoning"` so the UI layer knows exactly what to expect.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**
The scheduler considers two primary constraints:

1. **Time budget** — The owner's `available_minutes` sets a hard cap on how much can be scheduled. `fits_in_budget()` checks each task's `duration_minutes` against the remaining time before including it.

2. **Priority** — Tasks are sorted by a `Priority` enum (HIGH=0, MEDIUM=1, LOW=2) so high-priority tasks are always considered first. This ensures critical care like medication or feeding is never bumped by a low-priority task like enrichment.

Priority was chosen as the primary sort key because a pet owner's most urgent concern is "did the essential care happen?" Time budget is the secondary gate — it determines how far down the priority list the scheduler can reach. Other constraints like `scheduled_time` and `frequency` influence how the plan is displayed and how tasks recur, but they don't affect which tasks make the cut.

**b. Tradeoffs**
The scheduler uses a greedy algorithm — it sorts all tasks by priority (HIGH → MEDIUM → LOW) and schedules them one by one until the time budget runs out. Once a task is skipped because it doesn't fit, the algorithm moves on and never revisits that decision. This means it can leave time on the table: if a 25-minute MEDIUM task is skipped with 20 minutes remaining, a 10-minute LOW task that comes later in the list is also skipped, even though it would have fit.

The tradeoff is **simplicity and predictability over optimal time usage**. A more sophisticated approach (like a knapsack algorithm) could pack the schedule tighter, but it would be harder to explain to the user *why* a lower-priority task was chosen over a higher-priority one. For a pet owner glancing at their daily plan, "high-priority tasks go first" is an intuitive rule that builds trust in the output — even if it occasionally wastes a few minutes of available time.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude (Anthropic's AI assistant) throughout the entire project, and it became my primary collaborator for design, implementation, and testing. Here's how:

**Which Claude features were most effective for building the scheduler:**

- **Iterative skeleton review** — The single most effective pattern was asking Claude to review my class stubs repeatedly with "do you notice any more missing relationships or potential logic bottlenecks?" Each round caught something new: the first pass found that `Task.status` had no default value, the second caught that `priority` was an unconstrained string (leading to the `Priority` enum), and a third found that `generate_plan()` returned `None` with no defined structure. By the time I started writing actual logic, the skeleton was rock-solid.
- **Mermaid.js UML generation** — I described my classes in plain English and Claude produced a working Mermaid diagram that I could render immediately. When the design changed, I asked Claude to regenerate it, so the diagram always stayed in sync with the code.
- **Codebase-aware documentation** — When it came time to write the README and reflection, Claude read `pawpal_system.py` and `app.py` directly and drafted feature descriptions that accurately referenced real method names, parameters, and algorithms — not generic placeholders.

**b. Judgment and verification**

**One example of an AI suggestion I rejected or modified:**

When I asked Claude to brainstorm the main classes, it proposed five: Owner, Pet, Task, Scheduler, and DailyPlan. It then tried to narrow that down to four by folding DailyPlan into the Scheduler's return value. I pushed back and said the count could be six — I wanted Relationship included as an explicit design concern. Claude initially resisted, calling Relationship "more of a design concept than a class," but I kept it in scope because I wanted to force myself to think carefully about how the classes connected to each other before writing any code. That decision paid off — it's the reason we caught that `Owner` should own tasks through `Pet` rather than directly, and that `Scheduler` didn't need to hold `Pet` separately since it could access it through `Owner`.

I also rejected Claude's instinct to write all class stubs at once. When Claude filled in `pawpal_system.py` with a full skeleton on the first attempt, I cleared the file and told it "do not add anything yet." I wanted to control the pace — start with an empty file, add classes one phase at a time, and review between each step. That incremental approach is what made the iterative review cycles possible.

**How separate chat sessions for different phases helped me stay organized:**

I deliberately used separate Claude conversations for different project phases. The design phase (brainstorming classes, drawing the UML, reviewing the skeleton) happened in one session. Implementation of the core scheduling logic, sorting, filtering, recurrence, and conflict detection happened in later sessions. Testing and documentation each got their own sessions too.

This separation kept each conversation focused on one concern. The design session didn't get cluttered with debugging output, and the testing session didn't need to re-explain the class structure from scratch — Claude's memory system carried the key decisions forward (like the phase roadmap and the fact that Phase 1 features were complete). It also meant that if a session went in a wrong direction, I could start fresh without losing the work from previous phases that was already committed to git.

---

## 4. Testing and Verification

**a. What you tested**

The test suite (`test/test_pawpal.py`) includes 43 tests organized by class and feature:

- **Task** — default status is `"pending"`, default frequency is `"daily"`, `is_high_priority()` returns correct results, `mark_complete()` changes status
- **Pet** — `has_special_needs()` returns False by default and True when set, `add_task()` appends and sets the pet reference, `remove_task()` clears both list and reference, `get_tasks()` returns all tasks
- **Owner** — starts with no pets, `add_pet()`/`remove_pet()` work correctly, `get_all_tasks()` returns a flat list across all pets
- **Scheduler** — `fits_in_budget()` handles true/false/exact-match cases, `generate_plan()` returns correct keys, high-priority tasks are scheduled before low, tasks exceeding budget are skipped, `get_skipped_tasks()` matches plan output
- **Sorting** — tasks sort chronologically by `scheduled_time`, same-time tasks both appear, empty list returns empty
- **Recurrence** — daily tasks create next-day occurrence, weekly tasks create next-week occurrence, "as needed" tasks return None, next task auto-adds to same pet
- **Conflict detection** — same-pet overlap detected, cross-pet overlap detected, different dates produce no conflict, adjacent (non-overlapping) times produce no conflict
- **Filtering** — filter by status, filter by pet name (case-insensitive), combined AND logic, no filters returns full list
- **Scheduling integration** — all tasks fit within budget, high-priority scheduled while low skipped when budget is tight, pet with no tasks produces empty plan

These tests were important because they verify that the scheduler's core algorithm works correctly (priority ordering, budget enforcement), that the data model relationships hold (pet references, task lists), and that edge cases like empty lists, exact budget matches, and adjacent times don't break the system.

**b. Confidence**

Confidence level: 4/5 stars. All 43 tests pass across happy paths and edge cases for every core feature. The one star held back is because the UI layer (`app.py`) is not yet covered by automated tests.

Edge cases to test next if there was more time:
- Tasks with `duration_minutes = 0`
- Owner with `available_minutes = 0`
- `scheduled_time` in invalid format (e.g., `"25:00"`, `"abc"`)
- Very large task lists (performance testing)
- Multiple pets with identical task names
- Removing a pet that still has tasks assigned

---

## 5. Reflection

**a. What went well**

The iterative design process worked especially well. Starting with a basic four-class UML diagram and then running multiple rounds of "review the skeleton — find bottlenecks — fix them" caught real issues (missing defaults, undefined return types, unconstrained strings) before any logic was written. By the time implementation started, the class structure was solid and the methods had clear contracts. The result was that features like sorting, filtering, recurrence, and conflict detection slotted in cleanly without requiring major refactors.

**b. What you would improve**

If I had another iteration, I would:
- **Replace the greedy scheduler with a smarter algorithm** — the current approach can waste time budget by skipping tasks that don't individually fit, even when smaller tasks later in the list would. A knapsack-style approach or a second pass for remaining time would improve utilization.
- **Move task management to the UI** — currently there's no way to edit or delete tasks once added in the Streamlit app. Adding inline edit/delete buttons would make the app more usable.
- **Add validation to `scheduled_time`** — the `"HH:MM"` format is not validated, so invalid strings like `"99:99"` would silently break `_to_minutes()`.

**c. Key takeaway**

The most important lesson was that **design review before implementation saves more time than debugging after implementation**. The multiple rounds of "review the skeleton" caught issues like missing relationships, undefined return types, and unconstrained strings — all of which would have been much harder to fix after building logic on top of them. Working with AI as a design reviewer (not just a code generator) was the most productive pattern in the project.
