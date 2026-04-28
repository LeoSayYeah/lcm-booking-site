from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, date, time, timedelta

app = Flask(__name__)
@app.route("/")
def home():
    return "Backend working!"
CORS(app)

LAUNCH_DATE = date(2025, 8, 18)
WORK_END = time(14, 0)

SERVICES = [
    {"id": 1, "name": "Single oven clean", "price": 50, "duration": 90},
    {"id": 2, "name": "Oven and grill", "price": 75, "duration": 120},
    {"id": 3, "name": "Range oven", "price": 125, "duration": 150},
]

BOOKINGS = []

@app.get("/services")
def services():
    return jsonify(SERVICES)

@app.post("/bookings")
def create_booking():
    data = request.get_json() or {}
    return jsonify({"ok": True, "data": data})
