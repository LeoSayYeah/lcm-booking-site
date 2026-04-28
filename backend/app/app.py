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
    conn.commit()
    conn.close()


init_db()


def get_day_bookings(selected_date):
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("SELECT id, start_time, end_time FROM bookings WHERE date=?", (selected_date,))
    rows = c.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "start": datetime.strptime(row[1], "%H:%M").time(),
            "end": datetime.strptime(row[2], "%H:%M").time(),
        }
        for row in rows
    ]


def get_admin_bookings(selected_date=None):
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()

    if selected_date:
        c.execute("""
            SELECT id, name, phone, address, postcode, date, start_time, end_time,
                   duration, price, services, notes
            FROM bookings
            WHERE date=?
            ORDER BY start_time
        """, (selected_date,))
    else:
        c.execute("""
            SELECT id, name, phone, address, postcode, date, start_time, end_time,
                   duration, price, services, notes
            FROM bookings
            ORDER BY date, start_time
        """)

    rows = c.fetchall()
    conn.close()
    return rows


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


def is_available(start_time_value, duration, bookings, ignore_booking_id=None):
    start_dt = datetime.combine(date.today(), start_time_value)
    end_dt = start_dt + timedelta(minutes=duration)

    for booking in bookings:
        if ignore_booking_id is not None and booking["id"] == ignore_booking_id:
            continue

        b_start = datetime.combine(date.today(), booking["start"])
        b_end = datetime.combine(date.today(), booking["end"])

        if start_dt < b_end and end_dt > b_start:
            return False

    return True


def clean_phone_for_whatsapp(phone):
    cleaned = "".join(ch for ch in str(phone) if ch.isdigit())
    if cleaned.startswith("0"):
        cleaned = "44" + cleaned[1:]
    return cleaned


@app.route("/availability")
def availability():
    date_str = request.args.get("date")
    duration = int(request.args.get("duration", 60))

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify([])

    if selected_date < LAUNCH_DATE or selected_date.weekday() > 4:
        return jsonify([])

    bookings = get_day_bookings(date_str)
    slots = generate_slots(duration, selected_date)

    available = []
    for slot in slots:
        slot_time = datetime.strptime(slot, "%H:%M").time()
        if is_available(slot_time, duration, bookings):
            available.append(slot)

    return jsonify(available)


@app.route("/services")
def services():
    return jsonify(SERVICES)


@app.route("/bookings", methods=["POST"])
def bookings():
    data = request.json or {}

    if not data.get("name") or not data.get("phone") or not data.get("address") or not data.get("postcode"):
        return jsonify({"error": "Please enter your name, phone number, address and postcode"}), 400

    if not data.get("date") or not data.get("time"):
        return jsonify({"error": "Please select a date and available time slot"}), 400

    selected = [s for s in SERVICES if s["id"] in data.get("services", [])]

    if not selected:
        return jsonify({"error": "Please select at least one service"}), 400

    try:
        selected_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        selected_time = datetime.strptime(data["time"], "%H:%M").time()
    except Exception:
        return jsonify({"error": "Invalid date or time"}), 400

    if selected_date < LAUNCH_DATE:
        return jsonify({"error": "Online bookings start from 18 August 2025"}), 400

    if selected_date.weekday() > 4:
        return jsonify({"error": "Bookings are Monday to Friday only"}), 400

    duration = sum(s["duration"] for s in selected)
    price = sum(s["price"] for s in selected)

    if price < MINIMUM_BOOKING:
        return jsonify({"error": "Minimum booking is £50"}), 400

    current_bookings = get_day_bookings(data["date"])

    if not is_available(selected_time, duration, current_bookings):
        return jsonify({"error": "That time slot has just been taken. Please choose another time."}), 400

    start_dt = datetime.combine(selected_date, selected_time)
    end_dt = start_dt + timedelta(minutes=duration)

    if end_dt.time() > WORK_END:
        return jsonify({"error": "This booking would finish after 2pm. Please choose an earlier time."}), 400

    services_text = ", ".join(s["name"] for s in selected)

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO bookings (
            name, phone, address, postcode, date, start_time, end_time,
            duration, price, services, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["phone"],
        data["address"],
        data["postcode"].upper().strip(),
        data["date"],
        data["time"],
        end_dt.strftime("%H:%M"),
        duration,
        price,
        services_text,
        data.get("notes", "")
    ))
    conn.commit()
    conn.close()

    message = (
        "Hi LCM Oven & Carpet Cleaning, I have just made a booking request.\n\n"
        f"Name: {data['name']}\n"
        f"Phone: {data['phone']}\n"
        f"Address: {data['address']}\n"
        f"Postcode: {data['postcode'].upper().strip()}\n"
        f"Date: {data['date']}\n"
        f"Time: {data['time']}\n"
        f"Services: {services_text}\n"
        f"Total: £{price}\n"
        f"Estimated finish time: {end_dt.strftime('%H:%M')}"
    )

    return jsonify({
        "ok": True,
        "booking": {
            "name": data["name"],
            "phone": data["phone"],
            "address": data["address"],
            "postcode": data["postcode"].upper().strip(),
            "date": data["date"],
            "start_time": data["time"],
            "end_time": end_dt.strftime("%H:%M"),
            "total_price": price,
            "total_duration": duration,
            "services": services_text,
        },
        "whatsapp_message": message
    })


@app.route("/admin/update", methods=["POST"])
def admin_update():
    data = request.json or {}
    password = data.get("password")

    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    booking_id = data.get("id")
    new_time = data.get("start_time")

    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("SELECT date, duration FROM bookings WHERE id=?", (booking_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Booking not found"}), 404

    booking_date, duration = row
    selected_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
    selected_time = datetime.strptime(new_time, "%H:%M").time()

    if selected_time < WORK_START:
        conn.close()
        return jsonify({"error": "Too early"}), 400

    start_dt = datetime.combine(selected_date, selected_time)
    end_dt = start_dt + timedelta(minutes=duration)

    if end_dt.time() > WORK_END:
        conn.close()
        return jsonify({"error": "This move would finish after 2pm"}), 400

    bookings_today = get_day_bookings(booking_date)
    if not is_available(selected_time, duration, bookings_today, ignore_booking_id=int(booking_id)):
        conn.close()
        return jsonify({"error": "That time clashes with another booking"}), 400

    c.execute(
        "UPDATE bookings SET start_time=?, end_time=? WHERE id=?",
        (new_time, end_dt.strftime("%H:%M"), booking_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "end_time": end_dt.strftime("%H:%M")})
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>LCM Oven & Carpet Cleaning</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <style>
    :root{
      --blue:#0e3a67;
      --blue2:#15538f;
      --gold:#d4af37;
      --bg:#f4f8fc;
      --text:#102a43;
      --muted:#64748b;
      --card:#ffffff;
    }

    body{
      margin:0;
      font-family:Arial;
      background:var(--bg);
      color:var(--text);
    }

    header{
      background:linear-gradient(135deg,var(--blue),var(--blue2));
      color:white;
      padding:30px;
      text-align:center;
    }

    h1{margin:0}

    .tag{color:var(--gold);font-weight:bold}

    main{
      max-width:1000px;
      margin:auto;
      padding:20px;
    }

    .card{
      background:white;
      padding:20px;
      border-radius:16px;
      box-shadow:0 8px 20px #0001;
    }

    input,select,textarea,button{
      width:100%;
      padding:12px;
      margin:6px 0;
      border-radius:10px;
      border:1px solid #ccc;
    }

    button{
      background:var(--gold);
      font-weight:bold;
      border:0;
      cursor:pointer;
    }

    .service{
      background:#f8fafc;
      padding:10px;
      margin:6px 0;
      border-radius:10px;
    }

    .note{font-size:13px;color:var(--muted)}

    .success{color:green;font-weight:bold}
    .error{color:red;font-weight:bold}

  </style>
</head>

<body>

<header>
  <h1>LCM Oven & Carpet Cleaning</h1>
  <p class="tag">Let Me Do The Dirty Work</p>
  <p>Bookings Mon–Fri · 8:15am–2:00pm</p>
</header>

<main>
<div class="card">

<h2>Book a Clean</h2>
<p class="note"><strong>Minimum booking: £50</strong></p>

<input id="name" placeholder="Full name">
<input id="phone" placeholder="Phone number">
<input id="address" placeholder="Address">
<input id="postcode" placeholder="Postcode">
<textarea id="notes" placeholder="Notes"></textarea>

<h3>Services</h3>
<div id="services"></div>

<h3>Date & Time</h3>
<input id="date" type="date" onchange="loadTimes()">
<select id="time"><option>Select services first</option></select>

<p id="summary">Select services to see total.</p>

<button onclick="book()">Book Now</button>

<p id="result"></p>

</div>
</main>

<script>
let SERVICES = []
let selectedServices = []

async function loadServices(){
  const res = await fetch('/services')
  SERVICES = await res.json()

  let html = ""

  const grouped = {}
  SERVICES.forEach(s=>{
    if(!grouped[s.category]) grouped[s.category]=[]
    grouped[s.category].push(s)
  })

  Object.keys(grouped).forEach(cat=>{
    html += `<h4>${cat}</h4>`

    if(cat === "Carpet Cleaning" || cat === "Sofa Cleaning"){
      html += `<p class="note">Prices may vary depending on size</p>`
    }

    grouped[cat].forEach(s=>{
      html += `
      <label class="service">
        <input type="checkbox" value="${s.id}" onchange="updateServices()">
        ${s.name} - £${s.price}
      </label>`
    })
  })

  document.getElementById("services").innerHTML = html
}

function updateServices(){
  selectedServices = [...document.querySelectorAll('input[type=checkbox]:checked')]
    .map(x=>Number(x.value))

  const chosen = SERVICES.filter(s=>selectedServices.includes(s.id))
  const price = chosen.reduce((a,b)=>a+b.price,0)
  const duration = chosen.reduce((a,b)=>a+b.duration,0)

  document.getElementById("summary").innerText =
    chosen.length ? `Total: £${price} · ${duration} mins` : "Select services to see total."

  loadTimes()
}

async function loadTimes(){
  const date = document.getElementById("date").value
  const chosen = SERVICES.filter(s=>selectedServices.includes(s.id))
  const duration = chosen.reduce((a,b)=>a+b.duration,0)

  if(!date || !duration){
    document.getElementById("time").innerHTML = "<option>Select services first</option>"
    return
  }

  const res = await fetch(`/availability?date=${date}&duration=${duration}`)
  const times = await res.json()

  document.getElementById("time").innerHTML =
    times.length ? times.map(t=>`<option value="${t}">${t}</option>`).join("")
    : "<option>No slots</option>"
}

async function book(){
  const data = {
    name:name.value,
    phone:phone.value,
    address:address.value,
    postcode:postcode.value,
    notes:notes.value,
    date:date.value,
    time:time.value,
    services:selectedServices
  }

  const res = await fetch('/bookings',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(data)
  })

  const out = await res.json()

  if(res.ok){
    result.className = "success"
    result.innerText = "Booking saved. Opening WhatsApp..."

    setTimeout(()=>{
      const url = "https://wa.me/447565873770?text=" + encodeURIComponent(out.whatsapp_message)
      window.open(url,"_blank")
    },800)

  } else {
    result.className = "error"
    result.innerText = out.error
  }
}

loadServices()
</script>

</body>
</html>
"""
    @app.route("/admin")
    def admin():
    password = request.args.get("password")

    if password != ADMIN_PASSWORD:
        return """
        <html>
        <body style="font-family:Arial;padding:20px">
          <h2>LCM Admin Login</h2>
          <input id="pw" type="password" placeholder="Password">
          <button onclick="location.href='/admin?password=' + document.getElementById('pw').value">
            Login
          </button>
        </body>
        </html>
        """

    selected_date = request.args.get("date", date.today().isoformat())
    rows = get_admin_bookings(selected_date)

    postcodes = [r[4] for r in rows]
    maps_link = "https://www.google.com/maps/dir/" + "/".join(postcodes) if postcodes else "#"

    cards = ""
    for r in rows:
        phone_clean = clean_phone_for_whatsapp(r[2])
        cards += f"""
        <div class="booking" draggable="true">
          <h3>{r[6]} - {r[7]} | {r[1]}</h3>
          <p><strong>Phone:</strong> {r[2]}</p>
          <p><strong>Address:</strong> {r[3]}</p>
          <p><strong>Postcode:</strong> {r[4]}</p>
          <p><strong>Services:</strong> {r[10]}</p>
          <p><strong>Total:</strong> £{r[9]}</p>
          <p><strong>Duration:</strong> {r[8]} mins</p>
          <p><strong>Notes:</strong> {r[11] or ""}</p>

          <label>Move time:</label>
          <select onchange="moveBooking({r[0]}, this.value)">
            <option value="">Select new time</option>
            <option>08:15</option>
            <option>08:30</option>
            <option>08:45</option>
            <option>09:00</option>
            <option>09:15</option>
            <option>09:30</option>
            <option>09:45</option>
            <option>10:00</option>
            <option>10:15</option>
            <option>10:30</option>
            <option>10:45</option>
            <option>11:00</option>
            <option>11:15</option>
            <option>11:30</option>
            <option>11:45</option>
            <option>12:00</option>
          </select>

          <br><br>
          <a class="whatsapp" href="https://wa.me/{phone_clean}" target="_blank">Message Customer</a>
        </div>
        """

    return f"""
    <html>
    <head>
      <title>LCM Admin Dashboard</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body{{font-family:Arial;margin:0;background:#f4f8fc;color:#102a43}}
        header{{background:#0e3a67;color:white;text-align:center;padding:22px}}
        main{{max-width:1000px;margin:auto;padding:20px}}
        .toolbar{{background:white;padding:15px;border-radius:12px;margin-bottom:15px;box-shadow:0 4px 12px #0001}}
        .booking{{background:white;padding:15px;margin:12px 0;border-radius:12px;box-shadow:0 4px 14px #0001;border-left:6px solid #d4af37}}
        .booking h3{{color:#0e3a67;margin-top:0}}
        input,button,select{{padding:10px;border-radius:8px;border:1px solid #ccc;margin:5px 0}}
        button{{background:#d4af37;font-weight:bold;border:0;cursor:pointer}}
        .route{{display:inline-block;background:#d4af37;color:#111;padding:10px 12px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:8px}}
        .whatsapp{{display:inline-block;background:#25D366;color:white;padding:10px 12px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:8px}}
      </style>
    </head>

    <body>
      <header>
        <h1>LCM Admin Day View</h1>
        <p>{selected_date}</p>
      </header>

      <main>
        <div class="toolbar">
          <form method="get">
            <input type="hidden" name="password" value="{ADMIN_PASSWORD}">
            <label>Choose date:</label><br>
            <input type="date" name="date" value="{selected_date}">
            <button type="submit">View Day</button>
            <button type="button" onclick="window.print()">Print Day</button>
          </form>

          <a class="route" href="{maps_link}" target="_blank">Plan Route in Google Maps</a>
          <p><strong>Total bookings:</strong> {len(rows)}</p>
        </div>

        {cards if cards else "<p>No bookings for this date.</p>"}
      </main>

      <script>
        async function moveBooking(id, time){{
          if(!time) return;

          const res = await fetch('/admin/update', {{
            method:'POST',
            headers:{{'Content-Type':'application/json'}},
            body:JSON.stringify({{
              id:id,
              start_time:time,
              password:'{ADMIN_PASSWORD}'
            }})
          }});

          const out = await res.json();

          if(res.ok){{
            alert('Booking moved to ' + time);
            location.reload();
          }} else {{
            alert(out.error || 'Could not move booking');
          }}
        }}
      </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
