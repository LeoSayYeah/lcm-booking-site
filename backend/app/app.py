from flask import Flask, request, jsonify
from datetime import datetime, date, time, timedelta
import sqlite3
import os

app = Flask(__name__)

LAUNCH_DATE = date(2025, 8, 18)
WORK_START = time(8, 15)
WORK_END = time(14, 0)
MINIMUM_BOOKING = 50
ADMIN_PASSWORD = "lcmadmin"

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

    {"id": 12, "category": "Sofa Cleaning", "name": "Arm chair", "price": 30, "duration": 60},
    {"id": 13, "category": "Sofa Cleaning", "name": "2 seater sofa", "price": 50, "duration": 60},
    {"id": 14, "category": "Sofa Cleaning", "name": "3 seater sofa", "price": 80, "duration": 90},
    {"id": 15, "category": "Sofa Cleaning", "name": "Corner sofa", "price": 100, "duration": 120},

    {"id": 16, "category": "White Goods", "name": "Washing machine", "price": 30, "duration": 30},
    {"id": 17, "category": "White Goods", "name": "Dishwasher", "price": 30, "duration": 30},
]

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
            duration INTEGER,
            price INTEGER,
            services TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/services")
def services():
    return jsonify(SERVICES)

@app.route("/bookings", methods=["POST"])
def bookings():
    data = request.json

    selected = [s for s in SERVICES if s["id"] in data.get("services", [])]

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
        (name, phone, address, postcode, date, start_time, end_time, duration, price, services)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["phone"],
        data["address"],
        data["postcode"],
        data["date"],
        data["time"],
        end.strftime("%H:%M"),
        duration,
        price,
        ", ".join(s["name"] for s in selected)
    ))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/")
def home():
    return "<h1>LCM Booking Running ✅</h1>"

@app.route("/admin")
def admin():
    password = request.args.get("password")

    if password != ADMIN_PASSWORD:
        return """
        <html>
        <body style="font-family:Arial;padding:20px">
            <h2>LCM Admin Login</h2>
            <input id="pw" type="password">
            <button onclick="location.href='/admin?password=' + document.getElementById('pw').value">
                Login
            </button>
        </body>
        </html>
        """

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("SELECT * FROM bookings ORDER BY date, start_time")
    rows = c.fetchall()
    conn.close()

    timeline = ""
    current_time = WORK_START

    for b in rows:
        start = datetime.strptime(b[6], "%H:%M").time()

        if start > current_time:
            timeline += f"<div>Free: {current_time} → {start}</div>"

        timeline += f"""
        <div style='background:white;padding:10px;margin:10px;border-left:5px solid gold'>
            <b>{b[6]} - {b[7]}</b><br>
            {b[1]}<br>
            {b[3]}<br>
            £{b[9]}
        </div>
        """

        current_time = datetime.strptime(b[7], "%H:%M").time()

    return f"""
    <html>
    <body>
        <h1>Admin Dashboard</h1>
        {timeline}
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
