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
    return """
<!DOCTYPE html>
<html>
<head>
  <title>LCM Oven & Carpet Cleaning</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body{font-family:Arial;margin:0;background:#f4f8fc;color:#102a43}
    header{background:#0e3a67;color:white;text-align:center;padding:28px 15px}
    .container{max-width:900px;margin:auto;padding:20px}
    .card{background:white;border-radius:18px;padding:20px;margin:18px 0;box-shadow:0 6px 18px #0001}
    input,select,textarea,button{width:100%;padding:13px;margin:7px 0;border-radius:12px;border:1px solid #ccc;font-size:15px}
    button{background:#d4af37;border:0;font-weight:bold}
    .service{display:block;background:#f8fafc;border:1px solid #e2e8f0;padding:10px;margin:8px 0;border-radius:10px}
    .note{font-size:13px;color:#64748b}
    #result{font-weight:bold;margin-top:12px}
  </style>
</head>
<body>

<header>
  <h1>LCM Oven & Carpet Cleaning</h1>
  <p>Let Me Do The Dirty Work</p>
</header>

<div class="container">
  <div class="card">
    <input id="name" placeholder="Full name">
    <input id="phone" placeholder="Phone number">
    <input id="address" placeholder="Address">
    <input id="postcode" placeholder="Postcode">
  </div>

  <div class="card">
    <h2>Services</h2>
    <p class="note"><strong>Minimum booking: £50</strong></p>
    <div id="services"></div>
  </div>

  <div class="card">
    <h2>Date & Time</h2>
    <input id="dateInput" type="date" onchange="loadTimes()">
    <select id="timeInput">
      <option value="">Select services and date first</option>
    </select>
  </div>

  <div class="card">
    <p id="summary">Select services to see total.</p>
    <button onclick="book()">Book Now</button>
    <p id="result"></p>
  </div>
</div>

<script>
let services = [];
let selected = [];

async function loadServices(){
  const res = await fetch('/services');
  services = await res.json();

  document.getElementById('services').innerHTML = services.map(s => `
    <label class="service">
      <input type="checkbox" value="${s.id}" onchange="updateServices()">
      ${s.name} - £${s.price}
    </label>
  `).join('');
}

function updateServices(){
  selected = Array.from(document.querySelectorAll('input[type=checkbox]:checked'))
    .map(x => Number(x.value));

  const chosen = services.filter(s => selected.includes(s.id));
  const total = chosen.reduce((sum, s) => sum + s.price, 0);
  const duration = chosen.reduce((sum, s) => sum + s.duration, 0);

  document.getElementById('summary').innerText =
    chosen.length ? `Total: £${total} · Approx ${duration} mins` : 'Select services to see total.';

  loadTimes();
}

async function loadTimes(){
  const dateValue = document.getElementById('dateInput').value;
  const chosen = services.filter(s => selected.includes(s.id));
  const duration = chosen.reduce((sum, s) => sum + s.duration, 0);

  if(!dateValue || duration === 0){
    document.getElementById('timeInput').innerHTML =
      '<option value="">Select services and date first</option>';
    return;
  }

  const res = await fetch(`/availability?date=${dateValue}&duration=${duration}`);
  const times = await res.json();

  document.getElementById('timeInput').innerHTML =
    times.length
      ? times.map(t => `<option value="${t}">${t}</option>`).join('')
      : '<option value="">No available slots</option>';
}

async function book(){
  const data = {
    name: document.getElementById('name').value,
    phone: document.getElementById('phone').value,
    address: document.getElementById('address').value,
    postcode: document.getElementById('postcode').value,
    date: document.getElementById('dateInput').value,
    time: document.getElementById('timeInput').value,
    services: selected
  };

  const res = await fetch('/bookings', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(data)
  });

  const out = await res.json();

  if(res.ok){
    const msg =
      `Hi LCM Oven & Carpet Cleaning, I have just made a booking request.\\n\\n` +
      `Name: ${data.name}\\nPhone: ${data.phone}\\nAddress: ${data.address}\\n` +
      `Postcode: ${data.postcode}\\nDate: ${data.date}\\nTime: ${data.time}`;

    document.getElementById('result').innerText = 'Booking received. Opening WhatsApp...';
    setTimeout(() => {
      window.open(`https://wa.me/447565873770?text=${encodeURIComponent(msg)}`, '_blank');
    }, 800);
  } else {
    document.getElementById('result').innerText = out.error || 'Booking failed';
  }
}

loadServices();
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
