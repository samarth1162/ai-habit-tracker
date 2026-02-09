from flask import Flask, render_template, redirect, request
from datetime import date, timedelta
import json
from urllib.parse import quote, unquote

app = Flask(__name__)

# ---------------- LOAD DATA ----------------
with open("habits.json", "r") as f:
    habits = json.load(f)

# ---------------- MESSAGE TEMPLATES ----------------
TASK_MESSAGES = {
    "gym": {
        1: "Good start. Showing up matters more than intensity.",
        7: "Seven days in. Your body is adapting to consistency."
    },
    "read": {
        1: "One reading session done. Knowledge compounds quietly.",
        7: "Seven days of reading. Focus is becoming a habit."
    },
    "walk": {
        1: "You moved today. That is always a win.",
        7: "Seven days of movement. This supports everything else you do."
    },
    "default": {
        1: "Day one complete. You started.",
        7: "Seven days in. This habit is forming."
    }
}

def get_weekly_summary(habits):
    today = date.today()
    start = today - timedelta(days=6)

    completed_days = 0
    total_effort = 0
    effort_entries = 0

    for habit in habits:
        for entry in habit["effort_log"]:
            entry_date = date.fromisoformat(entry["date"])
            if start <= entry_date <= today:
                completed_days += 1
                total_effort += entry["effort"]
                effort_entries += 1

    if completed_days == 0:
        return None

    avg_effort = round(total_effort / effort_entries, 1)

    return (
        f"This week: you completed {completed_days} habit check-ins. "
        f"Average effort was {avg_effort}/10."
    )


# ---------------- HOME ----------------
@app.route("/")
def home():
    today = date.today().isoformat()
    message = app.config.pop("STREAK_MESSAGE", None)
    weekly_summary = get_weekly_summary(habits)

    return render_template(
        "index.html",
        habits=habits,
        today=today,
        message=message,
        weekly_summary=weekly_summary
    )

# ---------------- ADD HABIT ----------------
@app.route("/add", methods=["POST"])
def add_habit():
    name = request.form.get("habit_name", "").strip()

    if name:
        habits.append({
            "name": name,
            "streak": 0,
            "longest_streak": 0,
            "last_done": None,
            "effort_log": [],
            "last_milestone": 0
        })
        save_data()

    return redirect("/")

# ---------------- MARK DONE ----------------
@app.route("/done/<path:habit_name>", methods=["POST"])
def mark_done(habit_name):
    habit_name = unquote(habit_name)

    today = date.today()
    effort = int(request.form.get("effort", 5))

    for habit in habits:
        if habit["name"].lower() == habit_name.lower():

            # Streak logic
            if habit["last_done"]:
                last_done = date.fromisoformat(habit["last_done"])

                if last_done == today:
                    return redirect("/")

                if last_done == today - timedelta(days=1):
                    habit["streak"] += 1
                else:
                    habit["streak"] = 1
            else:
                habit["streak"] = 1

            habit["last_done"] = today.isoformat()

            if habit["streak"] > habit["longest_streak"]:
                habit["longest_streak"] = habit["streak"]

            # Effort logging
            habit["effort_log"].append({
                "date": today.isoformat(),
                "effort": effort
            })

            # Streak messages (1-day and 7-day)
            streak = habit["streak"]
            last_milestone = habit.get("last_milestone", 0)

            task_key = habit["name"].lower()
            messages = TASK_MESSAGES.get(task_key, TASK_MESSAGES["default"])

            if streak in (1, 7) and last_milestone < streak:
                app.config["STREAK_MESSAGE"] = messages.get(
                    streak,
                    TASK_MESSAGES["default"][streak]
                )
                habit["last_milestone"] = streak

            save_data()
            return redirect("/")

    return redirect("/")

# ---------------- DELETE HABIT ----------------
@app.route("/delete/<path:habit_name>", methods=["POST"])
def delete_habit(habit_name):
    habit_name = unquote(habit_name)

    global habits
    habits = [h for h in habits if h["name"].lower() != habit_name.lower()]
    save_data()
    return redirect("/")

# ---------------- SAVE ----------------
def save_data():
    with open("habits.json", "w") as f:
        json.dump(habits, f, indent=2)

# ---------------- RUN ----------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

