from flask import Flask, request, jsonify
from datetime import datetime, date, time, timedelta
import sqlite3

app = Flask(__name__)

LAUNCH_DATE = date(2025, 8, 18)
WORK_START = time(8, 15)
WORK_END = time(14, 0)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            address TEXT,
            postcode TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            duration INTEGER,
            price INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- SERVICES ----------
SERVICES = [
    {"id": 1, "name": "Single oven", "price": 50, "duration": 90},
    {"id": 2, "name": "Double oven", "price": 75, "duration": 120},
    {"id": 3, "name": "Ceramic hob range", "price": 125, "duration": 150},
    {"id": 4, "name": "Gas hob range", "price": 150, "duration": 150},
    {"id": 5, "name": "4 ring hob", "price": 20, "duration": 30},
    {"id": 6, "name": "Extractor", "price": 20, "duration": 30},

    {"id": 7, "name": "1 room carpet", "price": 50, "duration": 60},
    {"id": 8, "name": "2 rooms carpet", "price": 75, "duration": 90},
    {"id": 9, "name": "3 rooms carpet", "price": 95, "duration": 90},
    {"id": 10, "name": "Stairs & landing", "price": 50, "duration": 60},
    {"id": 11, "name": "Stairs & landing with another room", "price": 30, "duration": 60},

    {"id": 12, "name": "Arm chair", "price": 30, "duration": 60},
    {"id": 13, "name": "2 seater sofa", "price": 50, "duration": 60},
    {"id": 14, "name": "3 seater sofa", "price": 80, "duration": 90},
    {"id": 15, "name": "Corner sofa", "price": 100, "duration": 120},

    {"id": 16, "name": "Washing machine", "price": 30, "duration": 30},
    {"id": 17, "name": "Dishwasher", "price": 30, "duration": 30},
    {"id": 18, "name": "Washing machine + dishwasher", "price": 50, "duration": 60},
]

# ---------- HELPERS ----------
def get_day_bookings(selected_date):
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("SELECT start_time, end_time FROM bookings WHERE date=?", (selected_date,))
    rows = c.fetchall()
    conn.close()

    bookings = []
    for r in rows:
        bookings.append({
            "start": datetime.strptime(r[0], "%H:%M").time(),
            "end": datetime.strptime(r[1], "%H:%M").time()
        })
    return bookings


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


def is_available(start_time, duration, bookings):
    start_dt = datetime.combine(date.today(), start_time)
    end_dt = start_dt + timedelta(minutes=duration)

    for b in bookings:
        b_start = datetime.combine(date.today(), b["start"])
        b_end = datetime.combine(date.today(), b["end"])

        if start_dt < b_end and end_dt > b_start:
            return False

    return True


# ---------- ROUTES ----------

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


@app.route("/")
def home():
    return """
    <html>
    <head>
      <title>LCM Booking</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body style="font-family:Arial;padding:20px">

    <h2>Book a Clean</h2>

    <input id="name" placeholder="Name"><br><br>
    <input id="address" placeholder="Address"><br><br>
    <input id="postcode" placeholder="Postcode"><br><br>

    <input id="date" type="date" onchange="loadTimes()"><br><br>

    <select id="time">
      <option>Select a date first</option>
    </select><br><br>

    <div id="services"></div><br>

    <button onclick="book()">Book</button>

    <p id="result"></p>

    <script>
    let selectedServices = []

    async function loadServices(){
        const res = await fetch('/services')
        const data = await res.json()

        document.getElementById('services').innerHTML =
            data.map(s =>
              `<label><input type="checkbox" value="${s.id}" onchange="updateServices()"> ${s.name} £${s.price}</label>`
            ).join('')
    }

    function updateServices(){
        selectedServices = [...document.querySelectorAll('input[type=checkbox]:checked')]
            .map(x => Number(x.value))
    }

    async function loadTimes(){
        if(selectedServices.length === 0){
            alert("Select services first")
            return
        }

        const duration = selectedServices.reduce((sum,id)=>{
            const s = SERVICES.find(x=>x.id===id)
            return sum + s.duration
        },0)

        const date = document.getElementById('date').value
        const res = await fetch(`/availability?date=${date}&duration=${duration}`)
        const times = await res.json()

        document.getElementById('time').innerHTML =
            times.map(t => `<option>${t}</option>`).join('')
    }

    async function book(){
        const res = await fetch('/bookings', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
                name: name.value,
                address: address.value,
                postcode: postcode.value,
                date: date.value,
                time: time.value,
                services: selectedServices
            })
        })

        const out = await res.json()
        result.innerText = out.ok ? "Booked!" : out.error
    }

    loadServices()
    </script>

    </body>
    </html>
    """


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
        INSERT INTO bookings (name,address,postcode,date,start_time,end_time,duration,price)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        data["name"], data["address"], data["postcode"],
        data["date"], data["time"], end.strftime("%H:%M"),
        duration, price
    ))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})
