"""
app.py - Main Flask Application Controller
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta
import os
import database as db
import risk

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mountainwatch-super-secret-key-2026")
app.config['JSON_SORT_KEYS'] = False

# Ensure database is initialized before serving requests
with app.app_context():
    db.init_db()

# --- Helper Functions ---
def get_sensor_freshness(last_seen_str):
    if not last_seen_str:
        return False, "Never"
    try:
        last_seen = datetime.strptime(last_seen_str, '%Y-%m-%d %H:%M:%S')
        diff_minutes = (datetime.utcnow() - last_seen).total_seconds() / 60.0
        if diff_minutes < 15:
            return True, f"{int(diff_minutes)}m ago" if diff_minutes >= 1 else "Just now"
        elif diff_minutes < 1440:
            return False, f"{int(diff_minutes / 60)}h ago"
        else:
            return False, f"{int(diff_minutes / 1440)}d ago"
    except Exception:
        return False, "Unknown"

# --- WEB PAGE ROUTES ---
@app.route('/')
def home():
    conn = db.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM mountains;")
    mountain_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM sensors WHERE status = 'ONLINE';")
    online_sensors = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Active';")
    active_alerts = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Active' AND risk_level = 'CRITICAL';")
    critical_alerts = c.fetchone()[0]

    conn.close()
    return render_template('index.html',
                           mountain_count=mountain_count,
                           online_sensors=online_sensors,
                           active_alerts=active_alerts,
                           critical_alerts=critical_alerts)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/map')
def map_page():
    return render_template('map.html')

@app.route('/mountains')
def mountains():
    return render_template('mountains.html')

@app.route('/mountain/<mountain_id>')
def mountain_detail(mountain_id):
    return render_template('mountain.html', mountain_id=mountain_id)

@app.route('/sensors')
def sensors_page():
    return render_template('sensors.html')

@app.route('/alerts')
def alerts_page():
    return render_template('alerts.html')

@app.route('/emergency')
def emergency_page():
    conn = db.get_db_connection()
    config = dict(conn.execute("SELECT key, value FROM system_config").fetchall())
    conn.close()
    phone = config.get('emergency_phone', '+91-112')
    return render_template('emergency.html', emergency_phone=phone)

@app.route('/incidents')
def incidents_page():
    return render_template('incidents.html')

@app.route('/history')
def history_page():
    return render_template('history.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        conn = db.get_db_connection()
        cfg = conn.execute("SELECT value FROM system_config WHERE key='admin_password'").fetchone()
        conn.close()
        if cfg and password == cfg['value']:
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid administrative passphrase.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('admin.html')


# --- REST API ENDPOINTS ---

# 1. Ingest Data from ESP32 or Simulator
@app.route('/api/sensor-data', methods=['POST'])
def ingest_sensor_data():
    """
    ESP32 sends payload:
    {
      "sensor_id": "M001",
      "mountain_id": "MT001",
      "moisture": 78.4,
      "rainfall": 12.0
    }
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Malformed or missing JSON payload"}), 400

    sensor_id = data.get("sensor_id")
    mountain_id = data.get("mountain_id")
    moisture = data.get("moisture")
    rainfall = data.get("rainfall", 0.0)

    if not sensor_id or not mountain_id or moisture is None:
        return jsonify({"status": "error", "message": "Missing required fields"}), 422

    try:
        moisture = float(moisture)
        rainfall = float(rainfall)
    except ValueError:
        return jsonify({"status": "error", "message": "Moisture & rainfall must be numeric"}), 422

    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    conn = db.get_db_connection()
    c = conn.cursor()

    # Verify mountain exists
    c.execute("SELECT id FROM mountains WHERE id = ?", (mountain_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({"status": "error", "message": f"Mountain {mountain_id} not registered"}), 404

    # Ensure sensor exists & update heartbeat
    c.execute("""
    INSERT INTO sensors (id, mountain_id, status, last_seen)
    VALUES (?, ?, 'ONLINE', ?)
    ON CONFLICT(id) DO UPDATE SET
        mountain_id=excluded.mountain_id,
        status='ONLINE',
        last_seen=excluded.last_seen;
    """, (sensor_id, mountain_id, now_str))

    # Insert time-series record
    c.execute("""
    INSERT INTO sensor_data (sensor_id, mountain_id, moisture, rainfall, timestamp, is_demo)
    VALUES (?, ?, ?, ?, ?, 0);
    """, (sensor_id, mountain_id, moisture, rainfall, now_str))

    # Calculate trend and evaluate risk
    c.execute("""
    SELECT moisture, timestamp FROM sensor_data 
    WHERE mountain_id = ? 
    ORDER BY timestamp DESC LIMIT 2;
    """, (mountain_id,))
    recent_rows = [dict(r) for r in c.fetchall()]
    rate_per_hour, trend = risk.calculate_moisture_trend(recent_rows)
    hazard = risk.evaluate_hazard_risk(moisture, rate_per_hour, rainfall, is_online=True)

    # Spawn auto-alert if Warning or Critical
    if hazard['level'] in ['WARNING', 'CRITICAL']:
        # Check if an active alert already exists within 2 hours
        c.execute("""
        SELECT id FROM alerts 
        WHERE mountain_id = ? AND risk_level = ? AND status = 'Active' 
        AND timestamp >= datetime('now', '-2 hours');
        """, (mountain_id, hazard['level']))
        if not c.fetchone():
            c.execute("""
            INSERT INTO alerts (mountain_id, risk_level, moisture, rainfall, message, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Active');
            """, (mountain_id, hazard['level'], moisture, rainfall, hazard['message'], now_str))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Data ingested successfully",
        "timestamp": now_str,
        "evaluated_risk": hazard['level'],
        "trend": trend,
        "rate_per_hour": rate_per_hour
    }), 201

# 2. Get All Mountains with Summarized Live Status
@app.route('/api/mountains', methods=['GET'])
def get_mountains():
    conn = db.get_db_connection()
    c = conn.cursor()

    c.execute("""
    SELECT m.*, s.id as sensor_id, s.status as sensor_status, s.last_seen
    FROM mountains m
    LEFT JOIN sensors s ON m.id = s.mountain_id
    """)
    mountains_list = []
    for row in c.fetchall():
        m = dict(row)
        is_fresh, freshness_label = get_sensor_freshness(m['last_seen'])
        
        # Override sensor status if inactive over 20 minutes
        effective_online = (m['sensor_status'] == 'ONLINE' and is_fresh)
        m['sensor_status'] = 'ONLINE' if effective_online else 'OFFLINE'
        m['last_seen_label'] = freshness_label

        # Get latest sensor reading
        c.execute("""
        SELECT moisture, rainfall, timestamp FROM sensor_data
        WHERE mountain_id = ? ORDER BY timestamp DESC LIMIT 2;
        """, (m['id'],))
        readings = [dict(r) for r in c.fetchall()]

        if readings:
            curr_moisture = readings[0]['moisture']
            curr_rainfall = readings[0]['rainfall']
            rate, trend = risk.calculate_moisture_trend(readings)
            hazard = risk.evaluate_hazard_risk(curr_moisture, rate, curr_rainfall, effective_online)
            m['current_moisture'] = curr_moisture
            m['current_rainfall'] = curr_rainfall
            m['moisture_rate'] = rate
            m['moisture_trend'] = trend
            m['risk'] = hazard
        else:
            m['current_moisture'] = None
            m['current_rainfall'] = None
            m['moisture_rate'] = 0.0
            m['moisture_trend'] = "No Data"
            m['risk'] = risk.evaluate_hazard_risk(0, 0, 0, False)

        mountains_list.append(m)

    conn.close()
    return jsonify({"mountains": mountains_list})

# 3. Get Single Mountain Detail with 15-Day Metrics
@app.route('/api/mountains/<mountain_id>', methods=['GET'])
def get_single_mountain(mountain_id):
    conn = db.get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM mountains WHERE id = ?", (mountain_id,))
    mountain_row = c.fetchone()
    if not mountain_row:
        conn.close()
        return jsonify({"error": "Mountain not found"}), 404

    m = dict(mountain_row)

    # Sensor
    c.execute("SELECT * FROM sensors WHERE mountain_id = ?", (mountain_id,))
    s_row = c.fetchone()
    sensor = dict(s_row) if s_row else {"id": "N/A", "status": "OFFLINE", "last_seen": None}
    is_fresh, freshness_label = get_sensor_freshness(sensor.get('last_seen'))
    effective_online = (sensor['status'] == 'ONLINE' and is_fresh)
    sensor['status'] = 'ONLINE' if effective_online else 'OFFLINE'
    sensor['last_seen_label'] = freshness_label
    m['sensor'] = sensor

    # 15-Day time series data
    c.execute("""
    SELECT moisture, rainfall, timestamp, is_demo 
    FROM sensor_data 
    WHERE mountain_id = ? AND timestamp >= datetime('now', '-15 days')
    ORDER BY timestamp ASC;
    """, (mountain_id,))
    series = [dict(r) for r in c.fetchall()]

    # 15-Day Stats
    if series:
        moistures = [pt['moisture'] for pt in series]
        max_m = max(moistures)
        min_m = min(moistures)
        avg_m = round(sum(moistures) / len(moistures), 1)

        # Timestamps for max/min
        max_rec = next(item for item in series if item["moisture"] == max_m)
        min_rec = next(item for item in series if item["moisture"] == min_m)
        max_time = max_rec['timestamp']
        min_time = min_rec['timestamp']
    else:
        max_m = min_m = avg_m = 0.0
        max_time = min_time = "N/A"

    # All-time Historical Max
    c.execute("SELECT MAX(moisture), timestamp FROM sensor_data WHERE mountain_id = ?", (mountain_id,))
    h_max = c.fetchone()
    historical_max = h_max[0] if (h_max and h_max[0] is not None) else max_m

    # Latest 2 readings for trend
    c.execute("""
    SELECT moisture, rainfall, timestamp FROM sensor_data 
    WHERE mountain_id = ? ORDER BY timestamp DESC LIMIT 2;
    """, (mountain_id,))
    latest = [dict(r) for r in c.fetchall()]

    if latest:
        cur_m = latest[0]['moisture']
        cur_rain = latest[0]['rainfall']
        rate, trend = risk.calculate_moisture_trend(latest)
        hazard = risk.evaluate_hazard_risk(cur_m, rate, cur_rain, effective_online)
    else:
        cur_m = cur_rain = 0.0
        rate = 0.0
        trend = "Stable"
        hazard = risk.evaluate_hazard_risk(0, 0, 0, False)

    # Nearby Villages & Safe Locations
    c.execute("SELECT * FROM nearby_villages WHERE mountain_id = ?", (mountain_id,))
    villages = [dict(r) for r in c.fetchall()]

    c.execute("SELECT * FROM safe_locations WHERE mountain_id = ?", (mountain_id,))
    safe_locs = [dict(r) for r in c.fetchall()]

    # Historical Incidents
    c.execute("SELECT * FROM accidents WHERE mountain_id = ? ORDER BY date DESC", (mountain_id,))
    incidents = [dict(r) for r in c.fetchall()]

    conn.close()

    return jsonify({
        "mountain": m,
        "current": {
            "moisture": cur_m,
            "rainfall": cur_rain,
            "rate_per_hour": rate,
            "trend": trend,
            "risk": hazard
        },
        "stats_15_days": {
            "max": max_m,
            "max_timestamp": max_time,
            "min": min_m,
            "min_timestamp": min_time,
            "average": avg_m,
            "historical_max": historical_max
        },
        "history_graph": series,
        "nearby_villages": villages,
        "safe_locations": safe_locs,
        "incidents": incidents
    })

# 4. Get Sensors List
@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    conn = db.get_db_connection()
    c = conn.cursor()
    c.execute("""
    SELECT s.*, m.name as mountain_name, 
           (SELECT moisture FROM sensor_data WHERE sensor_id = s.id ORDER BY timestamp DESC LIMIT 1) as current_moisture,
           (SELECT rainfall FROM sensor_data WHERE sensor_id = s.id ORDER BY timestamp DESC LIMIT 1) as current_rainfall
    FROM sensors s
    JOIN mountains m ON s.mountain_id = m.id;
    """)
    sensors = []
    for r in c.fetchall():
        item = dict(r)
        is_fresh, label = get_sensor_freshness(item['last_seen'])
        item['is_online'] = (item['status'] == 'ONLINE' and is_fresh)
        item['status'] = 'ONLINE' if item['is_online'] else 'OFFLINE'
        item['last_seen_label'] = label
        sensors.append(item)
    conn.close()
    return jsonify({"sensors": sensors})

# 5. Alerts API (GET, POST resolve)
@app.route('/api/alerts', methods=['GET', 'POST'])
def handle_alerts():
    conn = db.get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        alert_id = request.json.get('alert_id')
        status = request.json.get('status', 'Resolved')
        c.execute("UPDATE alerts SET status = ? WHERE id = ?", (status, alert_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "updated"})

    c.execute("""
    SELECT a.*, m.name as mountain_name, m.state
    FROM alerts a
    JOIN mountains m ON a.mountain_id = m.id
    ORDER BY a.timestamp DESC;
    """)
    alerts = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({"alerts": alerts})

# 6. Incidents API
@app.route('/api/accidents', methods=['GET'])
def get_accidents():
    conn = db.get_db_connection()
    c = conn.cursor()
    c.execute("""
    SELECT a.*, m.name as mountain_name, m.state
    FROM accidents a
    JOIN mountains m ON a.mountain_id = m.id
    ORDER BY a.date DESC;
    """)
    accidents = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify({"incidents": accidents})

# 7. Emergency Report Submission
@app.route('/api/emergency', methods=['POST'])
def submit_emergency():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    m_id = data.get('mountain_id')
    e_type = data.get('emergency_type')
    location = data.get('location')
    affected = data.get('people_affected', 1)
    desc = data.get('description', '')
    phone = data.get('contact_phone', '')

    if not m_id or not e_type or not location:
        return jsonify({"error": "All primary fields are required."}), 422

    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    conn = db.get_db_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO emergency_reports (mountain_id, emergency_type, location, people_affected, description, contact_phone, timestamp, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING');
    """, (m_id, e_type, location, affected, desc, phone, now_str))
    conn.commit()
    report_id = c.lastrowid
    conn.close()

    return jsonify({
        "status": "success",
        "report_id": report_id,
        "message": "Emergency dispatch alert successfully routed to control center."
    }), 201

# 8. Admin Control Endpoint
@app.route('/api/admin/mountain', methods=['POST'])
def admin_add_mountain():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    try:
        conn = db.get_db_connection()
        conn.execute("""
        INSERT INTO mountains (id, name, state, location, latitude, longitude, elevation, nearby_river, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (data['id'], data['name'], data['state'], data['location'], float(data['latitude']),
              float(data['longitude']), int(data['elevation']), data.get('nearby_river', ''), data.get('description', '')))
        
        # Also create placeholder sensor
        conn.execute("""
        INSERT INTO sensors (id, mountain_id, status, last_seen)
        VALUES (?, ?, 'OFFLINE', NULL);
        """, (f"S-{data['id']}", data['id']))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    # Local development server
    app.run(host='0.0.0.0', port=5000, debug=True)