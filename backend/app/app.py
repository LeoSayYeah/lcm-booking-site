from flask import Flask, request, jsonify
from datetime import datetime, date, time, timedelta
import sqlite3

app = Flask(__name__)

LAUNCH_DATE = date(2025, 8, 18)
WORK_START = time(8, 15)
WORK_END = time(14, 0)

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
    try:
        c.execute("ALTER TABLE bookings ADD COLUMN phone TEXT")
    except:
        pass
    conn.commit()
    conn.close()

init_db()

def get_day_bookings(selected_date):
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("SELECT start_time, end_time FROM bookings WHERE date=?", (selected_date,))
    rows = c.fetchall()
    conn.close()

    return [{"start": datetime.strptime(r[0], "%H:%M").time(),
             "end": datetime.strptime(r[1], "%H:%M").time()} for r in rows]

def generate_slots(duration, selected_date):
    slots = []
    current = datetime.combine(selected_date, WORK_START)

    while True:
        end = current + timedelta(minutes=duration)
        if end.time() > WORK_END:
            break
        slots.append(current.time().strftime("%H:%M"))
        current += timedelta(minutes=15)

    return slots

def is_available(start_time_value, duration, bookings):
    start_dt = datetime.combine(date.today(), start_time_value)
    end_dt = start_dt + timedelta(minutes=duration)

    for b in bookings:
        b_start = datetime.combine(date.today(), b["start"])
        b_end = datetime.combine(date.today(), b["end"])
        if start_dt < b_end and end_dt > b_start:
            return False

    return True

@app.route("/availability")
def availability():
    date_str = request.args.get("date")
    duration = int(request.args.get("duration", 60))

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return jsonify([])

    if selected_date < LAUNCH_DATE or selected_date.weekday() > 4:
        return jsonify([])

    bookings = get_day_bookings(date_str)
    slots = generate_slots(duration, selected_date)

    available = []
    for s in slots:
        t = datetime.strptime(s, "%H:%M").time()
        if is_available(t, duration, bookings):
            available.append(s)

    return jsonify(available)

@app.route("/services")
def services():
    return jsonify(SERVICES)

@app.route("/bookings", methods=["POST"])
def bookings():
    data = request.json

    selected = [s for s in SERVICES if s["id"] in data["services"]]
    duration = sum(s["duration"] for s in selected)
    price = sum(s["price"] for s in selected)

    start = datetime.strptime(data["time"], "%H:%M")
    end = start + timedelta(minutes=duration)

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO bookings (name, phone, address, postcode, date, start_time, end_time, duration, price, services, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ", ".join(s["name"] for s in selected),
        data.get("notes", "")
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "booking": {
            "services": ", ".join(s["name"] for s in selected),
            "total_price": price,
            "end_time": end.strftime("%H:%M")
        }
    })

@app.route("/")
def home():
    return """
<html>
<body style="font-family:Arial;padding:20px">

<h2>Book a Clean</h2>

<input id="name" placeholder="Name"><br><br>
<input id="phone" placeholder="Phone"><br><br>
<input id="address" placeholder="Address"><br><br>
<input id="postcode" placeholder="Postcode"><br><br>

<input id="date" type="date"><br><br>
<input id="time" placeholder="Time (e.g 09:00)"><br><br>

<div id="services"></div><br>

<button onclick="book()">Book</button>

<p id="result"></p>

<script>
let selectedServices = []
let SERVICES = []

async function loadServices(){
    const res = await fetch('/services')
    SERVICES = await res.json()

    document.getElementById('services').innerHTML =
        SERVICES.map(s =>
          `<label><input type="checkbox" value="${s.id}" onchange="update()"> ${s.name} £${s.price}</label>`
        ).join('')
}

function update(){
    selectedServices = [...document.querySelectorAll('input[type=checkbox]:checked')]
        .map(x => Number(x.value))
}

async function book(){
    const data = {
        name: name.value,
        phone: phone.value,
        address: address.value,
        postcode: postcode.value,
        date: date.value,
        time: time.value,
        services: selectedServices
    }

    const res = await fetch('/bookings', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(data)
    })

    const out = await res.json()

    if(res.ok){

        const message =
          `Hi LCM Oven & Carpet Cleaning, I have just made a booking request.\\n\\n` +
          `Name: ${data.name}\\n` +
          `Phone: ${data.phone}\\n` +
          `Address: ${data.address}\\n` +
          `Postcode: ${data.postcode}\\n` +
          `Date: ${data.date}\\n` +
          `Time: ${data.time}\\n` +
          `Services: ${out.booking.services}\\n` +
          `Total: £${out.booking.total_price}\\n` +
          `Estimated finish time: ${out.booking.end_time}`;

        const url = "https://wa.me/447565873770?text=" + encodeURIComponent(message)

        result.innerHTML =
          "Booking saved!<br><br>" +
          `<a href="${url}" target="_blank">Confirm on WhatsApp</a>`

    } else {
        result.innerText = "Error"
    }
}

loadServices()
</script>

</body>
</html>
"""

if __name__ == "__main__":
    app.run()
