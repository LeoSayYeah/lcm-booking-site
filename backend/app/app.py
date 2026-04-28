from flask import Flask, request, jsonify
from datetime import datetime, date, time, timedelta

app = Flask(__name__)

LAUNCH_DATE = date(2025, 8, 18)
WORK_END = time(14, 0)

SERVICES = [
    {"id": 1, "name": "Single oven", "price": 50, "duration": 90},
    {"id": 2, "name": "Double oven", "price": 75, "duration": 120},
    {"id": 3, "name": "Ceramic hob range", "price": 125, "duration": 150},
    {"id": 4, "name": "Gas hob range", "price": 150, "duration": 150},
    {"id": 5, "name": "4 ring hob", "price": 25, "duration": 30},
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

BOOKINGS = []

@app.route("/")
def home():
    return """
    <html>
    <head>
      <title>LCM Oven & Carpet Cleaning</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body{font-family:Arial;margin:0;background:#f5f8fb;color:#102a43}
        header{background:#0e3a67;color:white;padding:30px 20px;text-align:center}
        h1{margin:0;font-size:30px}
        .gold{color:#d4af37;font-weight:bold}
        main{padding:20px;max-width:900px;margin:auto}
        .card{background:white;padding:20px;border-radius:14px;margin:15px 0;box-shadow:0 2px 8px #0001}
        input,textarea,button{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:1px solid #ccc;font-size:15px}
        button{background:#d4af37;font-weight:bold;border:0;cursor:pointer}
        label{display:block;margin:7px 0;padding:8px;background:#f7fafc;border-radius:8px}
        h3{margin-top:24px;color:#0e3a67;border-bottom:2px solid #d4af37;padding-bottom:5px}
        .note{font-size:13px;color:#666;margin-bottom:10px}
        #result{font-weight:bold;margin-top:12px;color:#0e3a67}
      </style>
    </head>

    <body>
      <header>
        <h1>LCM Oven & Carpet Cleaning</h1>
        <p class="gold">Let Me Do The Dirty Work</p>
        <p>Call / WhatsApp: 07565 873770</p>
      </header>

      <main>
        <div class="card">
          <h2>Book a Clean</h2>

          <input id="name" placeholder="Full name">
          <input id="address" placeholder="Address">
          <input id="postcode" placeholder="Postcode">
          <input id="date" type="date">
          <input id="time" type="time">
          <textarea id="notes" placeholder="Notes / tailored booking"></textarea>

          <h3>Oven Cleaning</h3>
          <div id="ovens"></div>

          <h3>Carpet Cleaning</h3>
          <p class="note">Carpet prices may vary depending on size</p>
          <div id="carpets"></div>

          <h3>Sofa Cleaning</h3>
          <p class="note">Sofa prices may vary depending on size</p>
          <div id="sofas"></div>

          <h3>White Goods</h3>
          <div id="whitegoods"></div>

          <button onclick="book()">Book Now</button>

          <a href="https://wa.me/447565873770" target="_blank" style="text-decoration:none;">
            <button type="button">Message on WhatsApp</button>
          </a>

          <button onclick="window.print()">Print Booking</button>

          <p id="result"></p>
        </div>
      </main>

      <script>
        async function loadServices(){
          const res = await fetch('/services');
          const services = await res.json();

          const ovens = services.filter(s => s.id <= 6);
          const carpets = services.filter(s => s.id >= 7 && s.id <= 11);
          const sofas = services.filter(s => s.id >= 12 && s.id <= 15);
          const white = services.filter(s => s.id >= 16);

          function render(list, el){
            document.getElementById(el).innerHTML = list.map(s =>
              `<label><input type="checkbox" value="${s.id}"> ${s.name} - £${s.price}</label>`
            ).join('');
          }

          render(ovens, "ovens");
          render(carpets, "carpets");
          render(sofas, "sofas");
          render(white, "whitegoods");
        }

        async function book(){
          const checked = [...document.querySelectorAll('input[type=checkbox]:checked')].map(x => Number(x.value));

          const data = {
            name: document.getElementById('name').value,
            address: document.getElementById('address').value,
            postcode: document.getElementById('postcode').value,
            date: document.getElementById('date').value,
            time: document.getElementById('time').value,
            notes: document.getElementById('notes').value,
            services: checked
          };

          const res = await fetch('/bookings', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(data)
          });

          const out = await res.json();

          document.getElementById('result').innerText = res.ok
            ? 'Booking received. Total £' + out.booking.total_price
            : out.error;
        }

        loadServices();
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
    selected = [s for s in SERVICES if s["id"] in data.get("services", [])]

    if not selected:
        return jsonify({"error": "Please select at least one service"}), 400

    booking = {
        "id": len(BOOKINGS) + 1,
        **data,
        "services_selected": selected,
        "total_price": sum(s["price"] for s in selected),
        "total_duration": sum(s["duration"] for s in selected),
    }

    BOOKINGS.append(booking)

    return jsonify({"ok": True, "booking": booking})
