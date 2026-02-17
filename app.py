from flask import Flask, render_template, redirect, request, flash
from datetime import date, timedelta
import json
import os

app = Flask(__name__)
app.secret_key = "dev-secret-key"

DATA_FILE = "habits.json"

TASK_MESSAGES = {
    "gym": {
        1: "You started Gym. Showing up matters more than intensity.",
        7: "Seven days of Gym. Your body is adapting to consistency."
    },
    "read": {
        1: "You started Reading. Knowledge compounds quietly.",
        7: "Seven days of Reading. Focus is becoming a habit."
    },
    "walk": {
        1: "You started Walking. Movement always counts.",
        7: "Seven days of Walking. This supports everything else you do."
    },
    "default": {
        1: "Day one complete. You started.",
        7: "Seven days in. This habit is forming."
    }
}

def make_id(name):
    return name.lower().strip().replace(" ", "_").replace("/", "_")

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(habits):
    with open(DATA_FILE, "w") as f:
        json.dump(habits, f, indent=2)

@app.route("/")
def home():
    habits = load_data()
    today = date.today().isoformat()
    return render_template("index.html", habits=habits, today=today)

@app.route("/add", methods=["POST"])
def add_habit():
    habits = load_data()
    name = request.form.get("habit_name", "").strip()

    if name:
        habits.append({
            "id": make_id(name),
            "name": name,
            "streak": 0,
            "longest_streak": 0,
            "last_done": None
        })
        save_data(habits)

    return redirect("/")

@app.route("/done/<habit_id>", methods=["POST"])
def mark_done(habit_id):
    habits = load_data()
    today = date.today()

    for habit in habits:
        if habit["id"] == habit_id:

            if habit["last_done"]:
                last = date.fromisoformat(habit["last_done"])
                if last == today:
                    return redirect("/")
                if last == today - timedelta(days=1):
                    habit["streak"] += 1
                else:
                    habit["streak"] = 1
            else:
                habit["streak"] = 1

            habit["last_done"] = today.isoformat()
            habit["longest_streak"] = max(habit["longest_streak"], habit["streak"])

            messages = TASK_MESSAGES.get(
                habit["name"].lower(),
                TASK_MESSAGES["default"]
            )

            if habit["streak"] in messages:
                flash(messages[habit["streak"]], "streak")


            save_data(habits)
            break

    return redirect("/")

@app.route("/delete/<habit_id>", methods=["POST"])
def delete_habit(habit_id):
    habits = load_data()
    habits = [h for h in habits if h["id"] != habit_id]
    save_data(habits)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, port=8000)
