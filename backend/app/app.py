from flask import Flask, request, jsonify

app = Flask(__name__)

SERVICES = [
    {"id": 1, "name": "Single oven", "price": 50, "duration": 90},
    {"id": 2, "name": "Double oven", "price": 75, "duration": 120},
    {"id": 3, "name": "Ceramic hob range", "price": 125, "duration": 150},
    {"id": 4, "name": "Gas hob range", "price": 125, "duration": 150},
    {"id": 5, "name": "4 ring hob", "price": 25, "duration": 30},
    {"id": 6, "name": "Extractor", "price": 20, "duration": 30},

    {"id": 7, "name": "1 room carpet", "price": 50, "duration": 60},
    {"id": 8, "name": "2 rooms carpet", "price": 75, "duration": 90},
    {"id": 9, "name": "3 rooms carpet", "price": 95, "duration": 90},
    {"id": 10, "name": "Stairs & landing", "price": 50, "duration": 60},
    {"id": 11, "name": "Stairs & landing (with another room)", "price": 30, "duration": 60},

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
        header{background:#0e3a67;color:white;padding:30px 20px}
        h1{margin:0;font-size:30px}
        .gold{color:#d4af37}
        main{padding:20px;max-width:800px;margin:auto}
        .card{background:white;padding:18px;border-radius:14px;margin:15px 0;box-shadow:0 2px 8px #0001}
        input,textarea,button{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:1px solid #ccc}
        button{background:#d4af37;font-weight:bold;border:0}
        label{display:block;margin:6px 0}
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

          <h3>Services</h3>
          <div id="services"></div>

          <button onclick="book()">Book Now</button>
          <button onclick="window.print()">Print Booking</button>

          <p id="result"></p>
        </div>
      </main>

      <script>
        async function loadServices(){
          const res = await fetch('/services');
          const services = await res.json();
          document.getElementById('services').innerHTML = services.map(s =>
            `<label><input type="checkbox" value="${s.id}"> ${s.name} - £${s.price}</label>`
          ).join('');
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
