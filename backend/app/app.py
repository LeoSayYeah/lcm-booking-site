from flask import Flask, request, jsonify, render_template
from datetime import datetime, date, time, timedelta
import sqlite3
import os

app = Flask(__name__, template_folder="templates", static_folder="static")

# SETTINGS
WORK_START = time(8, 15)
WORK_END = time(14, 0)
MINIMUM_BOOKING = 50


SERVICES = [
    {"id": 1, "category": "Oven Cleaning", "name": "Single oven", "price": 50, "duration": 90},
    {"id": 2, "category": "Oven Cleaning", "name": "Double oven", "price": 75, "duration": 120},
    {"id": 3, "category": "Oven Cleaning", "name": "Ceramic hob range", "price": 125, "duration": 150},
    {"id": 4, "category": "Oven Cleaning", "name": "Gas hob range", "price": 150, "duration": 150},
    {"id": 5, "category": "Oven Cleaning", "name": "4 ring hob", "price": 20, "duration": 30},
    {"id": 6, "category": "Oven Cleaning", "name": "Extractor", "price": 20, "duration": 30},

    {"id": 7, "category": "Carpet Cleaning", "name": "1 room carpet", "price": 50, "duration": 60},
    {"id": 8, "category": "Carpet Cleaning", "name": "2 rooms carpet", "price": 75, "duration": 90},
    {"id": 9, "category": "Carpet Cleaning", "name": "3 rooms carpet", "price": 95, "duration": 90},
    {"id": 10, "category": "Carpet Cleaning", "name": "Stairs & landing", "price": 50, "duration": 60},
    {"id": 11, "category": "Carpet Cleaning", "name": "Stairs & landing with another room", "price": 30, "duration": 60},

    {"id": 12, "category": "Sofa Cleaning", "name": "Arm chair", "price": 30, "duration": 60},
    {"id": 13, "category": "Sofa Cleaning", "name": "2 seater sofa", "price": 50, "duration": 60},
    {"id": 14, "category": "Sofa Cleaning", "name": "3 seater sofa", "price": 80, "duration": 90},
    {"id": 15, "category": "Sofa Cleaning", "name": "Corner sofa", "price": 100, "duration": 120},

    {"id": 16, "category": "White Goods", "name": "Washing machine", "price": 30, "duration": 30},
    {"id": 17, "category": "White Goods", "name": "Dishwasher", "price": 30, "duration": 30},
    {"id": 18, "category": "White Goods", "name": "Washing machine + dishwasher", "price": 50, "duration": 60},
]
# DATABASE
def init_db():
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            address TEXT,
            postcode TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            price INTEGER,
            services TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ROUTES
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/admin")
def admin():
    selected_date = request.args.get("date", date.today().isoformat())

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, name, phone, address, postcode, date, start_time, end_time, price, services
        FROM bookings
        WHERE date=?
        ORDER BY start_time
    """, (selected_date,))
    rows = c

@app.route("/services")
def services():
    return jsonify(SERVICES)

@app.route("/availability")
def availability():
    date_str = request.args.get("date")
    duration = int(request.args.get("duration", 60))

    selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("SELECT start_time, end_time FROM bookings WHERE date=?", (date_str,))
    existing = c.fetchall()
    conn.close()

    slots = []
    current = datetime.combine(selected_date, WORK_START)

    while True:
        end = current + timedelta(minutes=duration)
        if end.time() > WORK_END:
            break

        available = True
        for b in existing:
            b_start = datetime.strptime(b[0], "%H:%M")
            b_end = datetime.strptime(b[1], "%H:%M")

            if current < b_end and end > b_start:
                available = False

        if available:
            slots.append(current.strftime("%H:%M"))

        current += timedelta(minutes=15)

    return jsonify(slots)

@app.route("/book", methods=["POST"])
def book():
    data = request.json
    selected = [s for s in SERVICES if s["id"] in data["services"]]

    price = sum(s["price"] for s in selected)
    duration = sum(s["duration"] for s in selected)

    if price < MINIMUM_BOOKING:
        return jsonify({"error": "Minimum booking is £50"}), 400

    start = datetime.strptime(data["time"], "%H:%M")
    end = start + timedelta(minutes=duration)

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO bookings
        (name, phone, address, postcode, date, start_time, end_time, price, services)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["phone"],
        data["address"],
        data["postcode"],
        data["date"],
        data["time"],
        end.strftime("%H:%M"),
        price,
        ", ".join(s["name"] for s in selected)
    ))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

# RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
