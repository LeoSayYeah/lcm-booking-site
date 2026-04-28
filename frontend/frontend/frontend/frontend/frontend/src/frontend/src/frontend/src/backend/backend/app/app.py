from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, date, time, timedelta

app = Flask(__name__)
CORS(app)

LAUNCH_DATE = date(2025, 8, 18)
WORK_END = time(14, 0)

SERVICES = [
    {"id": 1, "name": "Single oven clean", "price": 50, "duration": 90},
    {"id": 2, "name": "Oven and grill", "price": 75, "duration": 120},
    {"id": 3, "name": "Range oven", "price": 125, "duration": 150},
    {"id": 4, "name": "1 carpet", "price": 50, "duration": 60},
    {"id": 5, "name": "2 carpets", "price": 70, "duration": 90},
    {"id": 6, "name": "Corner sofa", "price": 100, "duration": 120},
]

BOOKINGS = []

@app.get("/")
def home():
    return jsonify({"ok": True, "message": "LCM booking backend running"})

@app.get("/services")
def services():
    return jsonify(SERVICES)

@app.post("/bookings")
def create_booking():
    data = request.get_json() or {}

    try:
        booking_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        start_hour, start_minute = map(int, data["time"].split(":"))
        start_time = time(start_hour, start_minute)
    except Exception:
        return jsonify({"error": "Invalid date or time"}), 400

    if booking_date < LAUNCH_DATE:
        return jsonify({"error": "Bookings start from 18 August 2025"}), 400

    if booking_date.weekday() > 4:
        return jsonify({"error": "Bookings are Monday to Friday only"}), 400

    selected_ids = data.get("services", [])
    selected = [s for s in SERVICES if s["id"] in selected_ids]

    if not selected:
        return jsonify({"error": "Please select at least one service"}), 400

    total_duration = sum(s["duration"] for s in selected)
    total_price = sum(s["price"] for s in selected)

    start_dt = datetime.combine(booking_date, start_time)
    end_dt = start_dt + timedelta(minutes=total_duration)

    if end_dt.time() > WORK_END:
        return jsonify
