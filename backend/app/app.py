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
    conn.commit()
    conn.close()


init_db()


def get_day_bookings(selected_date):
    conn = sqlite3.connect("bookings.db")
    c = conn.cursor()
    c.execute("SELECT start_time, end_time FROM bookings WHERE date=?", (selected_date,))
    rows = c.fetchall()
    conn.close()

    return [
        {
            "start": datetime.strptime(row[0], "%H:%M").time(),
            "end": datetime.strptime(row[1], "%H:%M").time(),
        }
        for row in rows
    ]


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

    for booking in bookings:
        b_start = datetime.combine(date.today(), booking["start"])
        b_end = datetime.combine(date.today(), booking["end"])

        if start_dt < b_end and end_dt > b_start:
            return False

    return True


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
    if price < 50:
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
        }
    })


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

    *{box-sizing:border-box}

    body{
      margin:0;
      font-family:Arial, sans-serif;
      background:var(--bg);
      color:var(--text);
    }

    header{
      background:linear-gradient(135deg,var(--blue),var(--blue2));
      color:white;
      padding:34px 18px;
      text-align:center;
    }

    header h1{
      margin:0;
      font-size:30px;
      line-height:1.15;
    }

    .tagline{
      color:var(--gold);
      font-weight:bold;
      margin:8px 0;
    }

    .header-actions{
      display:flex;
      justify-content:center;
      gap:10px;
      flex-wrap:wrap;
      margin-top:18px;
    }

    .btn, button{
      display:inline-block;
      width:100%;
      padding:13px 15px;
      border-radius:12px;
      border:0;
      font-size:16px;
      font-weight:bold;
      cursor:pointer;
      text-align:center;
      text-decoration:none;
    }

    .btn-gold, button{
      background:var(--gold);
      color:#111827;
    }

    .btn-light{
      background:white;
      color:var(--blue);
    }

    .btn-whatsapp{
      background:#25D366;
      color:white;
      margin-top:10px;
      width:100%;
    }

    main{
      max-width:1050px;
      margin:auto;
      padding:18px;
    }

    .grid{
      display:grid;
      grid-template-columns:1fr;
      gap:18px;
    }

    .card{
      background:var(--card);
      border-radius:18px;
      padding:18px;
      box-shadow:0 8px 24px rgba(15, 23, 42, 0.08);
    }

    h2{
      margin-top:0;
      color:var(--blue);
    }

    h3{
      color:var(--blue);
      margin-top:22px;
      border-bottom:2px solid var(--gold);
      padding-bottom:6px;
    }

    .note{
      color:var(--muted);
      font-size:13px;
      margin:4px 0 10px;
    }

    input, textarea, select{
      width:100%;
      padding:13px;
      border-radius:12px;
      border:1px solid #cbd5e1;
      margin:6px 0;
      font-size:15px;
      background:white;
    }

    textarea{
      min-height:85px;
    }

    .service{
      display:flex;
      gap:10px;
      align-items:flex-start;
      padding:11px;
      background:#f8fafc;
      border:1px solid #e2e8f0;
      border-radius:12px;
      margin:8px 0;
    }

    .service input{
      width:auto;
      margin-top:3px;
    }

    .service-title{
      font-weight:bold;
    }

    .service-meta{
      color:var(--muted);
      font-size:13px;
      margin-top:3px;
    }

    .summary{
      background:#f8fafc;
      border:1px solid #e2e8f0;
      border-radius:14px;
      padding:14px;
      margin-top:14px;
    }

    #result{
      font-weight:bold;
      margin-top:12px;
      color:var(--blue);
      line-height:1.4;
    }

    .success{color:#166534!important}
    .error{color:#b91c1c!important}

    footer{
      text-align:center;
      padding:28px 18px;
      color:var(--muted);
      font-size:14px;
    }

    @media(min-width:850px){
      header h1{font-size:42px}
      .grid{grid-template-columns:1.15fr .85fr}
      .btn, button{width:auto}
      .wide-button{width:100%}
    }
  </style>
</head>

<body>

<header>
  <h1>LCM Oven & Carpet Cleaning</h1>
  <p class="tagline">Let Me Do The Dirty Work</p>
  <p>Professional oven, carpet, sofa and white goods cleaning</p>

  <div class="header-actions">
    <a class="btn btn-gold" href="#booking">Book Online</a>
    <a class="btn btn-light" href="https://wa.me/447565873770" target="_blank">WhatsApp Us</a>
  </div>
</header>

<main>
  <div class="grid">
    <section class="card" id="booking">
      <h2>Book a Clean</h2>
      <p class="note">
Bookings are Monday to Friday, 8:15am to 2:00pm.<br>
<strong>Minimum booking: £50</strong>
</p>

      <input id="name" placeholder="Full name">
      <input id="phone" placeholder="Phone number">
      <input id="address" placeholder="Address">
      <input id="postcode" placeholder="Postcode">
      <textarea id="notes" placeholder="Notes / tailored booking details"></textarea>

      <h3>Choose Services</h3>

      <h4>Oven Cleaning</h4>
      <div id="ovens"></div>

      <h4>Carpet Cleaning</h4>
      <p class="note">Carpet prices may vary depending on size.</p>
      <div id="carpets"></div>

      <h4>Sofa Cleaning</h4>
      <p class="note">Sofa prices may vary depending on size.</p>
      <div id="sofas"></div>

      <h4>White Goods</h4>
      <div id="whitegoods"></div>

      <h3>Choose Date & Time</h3>
      <input id="date" type="date" onchange="loadTimes()">

      <select id="time">
        <option value="">Select services and date first</option>
      </select>

      <div class="summary">
        <strong>Booking Summary</strong>
        <p id="summaryText">Select services to see total.</p>
      </div>

      <button class="wide-button" type="button" onclick="book()">Book Now</button>

      <a href="https://wa.me/447565873770" target="_blank" style="text-decoration:none;">
        <button class="wide-button" type="button">Message on WhatsApp</button>
      </a>

      <button class="wide-button" type="button" onclick="window.print()">Print Booking</button>

      <p id="result"></p>
    </section>

    <aside class="card">
      <h2>Why choose LCM?</h2>
      <p><strong>DBS checked</strong></p>
      <p><strong>Fully insured</strong></p>
      <p><strong>11 years experience</strong></p>
      <p><strong>Eco friendly oven cleaning</strong></p>

      <h3>Contact</h3>
      <p><strong>Phone / WhatsApp</strong><br>07565 873770</p>
      <p><strong>Email</strong><br>lcmovencleaning@hotmail.com</p>

      <h3>Socials</h3>
      <p>
        <a href="https://www.facebook.com/share/17FSCs5xqU/" target="_blank">Facebook</a><br>
        <a href="https://www.instagram.com/lcmovencleaning?igsh=MW44NmlpOGRiNW9rMQ==" target="_blank">Instagram</a>
      </p>
    </aside>
  </div>
</main>

<footer>
  © LCM Oven & Carpet Cleaning
</footer>

<script>
let allServices = [];
let selectedServices = [];

async function loadServices(){
  const res = await fetch('/services');
  allServices = await res.json();

  const groups = {
    ovens: allServices.filter(s => s.category === "Oven Cleaning"),
    carpets: allServices.filter(s => s.category === "Carpet Cleaning"),
    sofas: allServices.filter(s => s.category === "Sofa Cleaning"),
    whitegoods: allServices.filter(s => s.category === "White Goods"),
  };

  Object.keys(groups).forEach(id => {
    document.getElementById(id).innerHTML = groups[id].map(s => `
      <label class="service">
        <input type="checkbox" value="${s.id}" onchange="updateServices()">
        <span>
          <span class="service-title">${s.name}</span><br>
          <span class="service-meta">£${s.price} · approx ${s.duration} mins</span>
        </span>
      </label>
    `).join('');
  });
}

function updateServices(){
  selectedServices = [...document.querySelectorAll('input[type=checkbox]:checked')]
    .map(x => Number(x.value));

  const chosen = allServices.filter(s => selectedServices.includes(s.id));
  const totalPrice = chosen.reduce((sum, s) => sum + s.price, 0);
  const totalDuration = chosen.reduce((sum, s) => sum + s.duration, 0);

  document.getElementById('summaryText').innerText =
    chosen.length === 0
      ? "Select services to see total."
      : `${chosen.length} service(s) selected · £${totalPrice} · approx ${totalDuration} mins`;

  loadTimes();
}

async function loadTimes(){
  const dateValue = document.getElementById('date').value;
  const timeSelect = document.getElementById('time');

  if(selectedServices.length === 0 || !dateValue){
    timeSelect.innerHTML = '<option value="">Select services and date first</option>';
    return;
  }

  const chosen = allServices.filter(s => selectedServices.includes(s.id));
  const duration = chosen.reduce((sum, s) => sum + s.duration, 0);

  const res = await fetch(`/availability?date=${dateValue}&duration=${duration}`);
  const times = await res.json();

  if(times.length === 0){
    timeSelect.innerHTML = '<option value="">No available slots</option>';
  } else {
    timeSelect.innerHTML = times.map(t => `<option value="${t}">${t}</option>`).join('');
  }
}

async function book(){
  const result = document.getElementById('result');
  result.className = "";
  result.innerText = "Sending booking...";

  const data = {
    name: document.getElementById('name').value,
    phone: document.getElementById('phone').value,
    address: document.getElementById('address').value,
    postcode: document.getElementById('postcode').value,
    notes: document.getElementById('notes').value,
    date: document.getElementById('date').value,
    time: document.getElementById('time').value,
    services: selectedServices
  };

  const res = await fetch('/bookings', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(data)
  });

  const out = await res.json();

  if(res.ok){
    result.className = "success";

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

    const whatsappUrl = `https://wa.me/447565873770?text=${encodeURIComponent(message)}`;

    result.innerHTML =
      `Booking received. ${out.booking.services}. Total £${out.booking.total_price}. ` +
      `Estimated finish time: ${out.booking.end_time}.<br><br>` +
      `<a href="${whatsappUrl}" target="_blank" class="btn btn-whatsapp">Confirm booking on WhatsApp</a>`;

    loadTimes();
  } else {
    result.className = "error";
    result.innerText = out.error;
  }
}

loadServices();
</script>

</body>
</html>
    """


if __name__ == "__main__":
    app.run()
