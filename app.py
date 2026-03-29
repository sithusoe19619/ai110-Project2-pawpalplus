import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, Priority

DATA_FILE = "data.json"

PRIORITY_EMOJI = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Load saved data on first run ─────────────────────────────────────────────
if "owner" not in st.session_state:
    saved = Owner.load_from_json(DATA_FILE)
    if saved:
        st.session_state["owner"] = saved
        st.session_state["pet"] = saved.pets[0] if saved.pets else None

# ── Step 1: Owner & Pet Setup ──────────────────────────────────────────────
st.subheader("Step 1: Set Up Your Profile")

owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
available_minutes = st.number_input("Available time today (minutes)", min_value=10, max_value=480, value=90)

if st.button("Create Profile"):
    pet = Pet(pet_name, species, age=0)
    owner = Owner(owner_name, available_minutes=int(available_minutes))
    owner.add_pet(pet)
    st.session_state["owner"] = owner
    st.session_state["pet"] = pet
    owner.save_to_json(DATA_FILE)
    st.success(f"Profile created for {owner_name} and {pet_name}!")

# ── Step 2: Add Tasks ──────────────────────────────────────────────────────
if "owner" in st.session_state:
    st.divider()
    st.subheader("Step 2: Add Tasks")

    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        scheduled_time = st.text_input("Time (HH:MM)", value="08:00")

    if st.button("Add task"):
        pet = st.session_state["pet"]
        priority_map = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}
        task = Task(task_title, int(duration), priority_map[priority], "general", "",
                    scheduled_time=scheduled_time)
        pet.add_task(task)
        st.session_state["owner"].save_to_json(DATA_FILE)
        st.success(f"Added '{task_title}' to {pet.name}'s tasks.")

    pet = st.session_state["pet"]
    if pet.tasks:
        scheduler = Scheduler(st.session_state["owner"])
        sorted_tasks = scheduler.sort_by_time(pet.tasks)
        st.write(f"**{pet.name}'s current tasks (sorted by time):**")
        st.table([
            {"Time": t.scheduled_time, "Task": t.name,
             "Duration (min)": t.duration_minutes,
             "Priority": PRIORITY_EMOJI[t.priority.value]}
            for t in sorted_tasks
        ])
    else:
        st.info("No tasks yet. Add one above.")

    # ── Step 3: Generate Schedule ──────────────────────────────────────────
    st.divider()
    st.subheader("Step 3: Generate Schedule")

    if st.button("Generate schedule"):
        owner = st.session_state["owner"]
        if not owner.get_all_tasks():
            st.warning("Add at least one task before generating a schedule.")
        else:
            scheduler = Scheduler(owner)
            plan = scheduler.generate_plan()

            st.success(f"Schedule generated for {owner.name}!")

            sorted_scheduled = scheduler.sort_by_time(plan["scheduled"])

            conflicts = scheduler.detect_conflicts(sorted_scheduled)
            if conflicts:
                with st.container(border=True):
                    st.markdown(f"**Conflicts Found: {len(conflicts)}**")
                    for c in conflicts:
                        a, b = c["task_a"], c["task_b"]
                        end_a = scheduler._to_minutes(a.scheduled_time) + a.duration_minutes
                        suggested = f"{end_a // 60:02d}:{end_a % 60:02d}"
                        if c["type"] == "same_pet":
                            st.error(f"**Same-pet overlap for {a.pet.name}**")
                            col1, col2 = st.columns(2)
                            col1.markdown(f"**{a.name}**  \n{a.scheduled_time} — {a.duration_minutes} min")
                            col2.markdown(f"**{b.name}**  \n{b.scheduled_time} — {b.duration_minutes} min")
                            st.info(f"Suggestion: Move **{b.name}** to **{suggested}**")
                        else:
                            st.warning(f"**Cross-pet overlap**")
                            col1, col2 = st.columns(2)
                            col1.markdown(f"**{a.name}** ({a.pet.name})  \n{a.scheduled_time} — {a.duration_minutes} min")
                            col2.markdown(f"**{b.name}** ({b.pet.name})  \n{b.scheduled_time} — {b.duration_minutes} min")
                            st.info(f"Suggestion: Move **{b.name}** to **{suggested}** — you can only attend one pet at a time")
            else:
                st.success("No scheduling conflicts detected.")

            if sorted_scheduled:
                st.markdown("**Scheduled Tasks (by time)**")
                st.table([
                    {"Time": t.scheduled_time, "Task": t.name, "Pet": t.pet.name,
                     "Duration (min)": t.duration_minutes,
                     "Priority": PRIORITY_EMOJI[t.priority.value]}
                    for t in sorted_scheduled
                ])

            if plan["skipped"]:
                st.markdown("**Skipped Tasks**")
                st.table([
                    {"Task": t.name, "Pet": t.pet.name,
                     "Duration (min)": t.duration_minutes,
                     "Priority": PRIORITY_EMOJI[t.priority.value]}
                    for t in plan["skipped"]
                ])

            time_used = sum(t.duration_minutes for t in plan["scheduled"])
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("Scheduled", f"{len(plan['scheduled'])} tasks")
            col2.metric("Time Used", f"{time_used} / {owner.available_minutes} min")
            col3.metric("Remaining", f"{owner.available_minutes - time_used} min")
