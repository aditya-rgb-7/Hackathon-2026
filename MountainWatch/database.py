"""
database.py - SQLite Database Setup, Seed Data, and CRUD Operations
"""
import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_FILE = "mountainwatch.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Mountains table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mountains (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        state TEXT NOT NULL,
        location TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        elevation INTEGER NOT NULL,
        nearby_river TEXT,
        description TEXT
    );
    """)

    # 2. Sensors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensors (
        id TEXT PRIMARY KEY,
        mountain_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'OFFLINE',
        last_seen DATETIME,
        FOREIGN KEY(mountain_id) REFERENCES mountains(id) ON DELETE CASCADE
    );
    """)

    # 3. Sensor Data table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sensor_id TEXT NOT NULL,
        mountain_id TEXT NOT NULL,
        moisture REAL NOT NULL,
        rainfall REAL NOT NULL,
        timestamp DATETIME NOT NULL,
        is_demo INTEGER DEFAULT 0,
        FOREIGN KEY(sensor_id) REFERENCES sensors(id),
        FOREIGN KEY(mountain_id) REFERENCES mountains(id)
    );
    """)

    # 4. Alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mountain_id TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        moisture REAL NOT NULL,
        rainfall REAL NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        status TEXT DEFAULT 'Active',
        FOREIGN KEY(mountain_id) REFERENCES mountains(id)
    );
    """)

    # 5. Historical Disasters table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mountain_id TEXT NOT NULL,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        description TEXT NOT NULL,
        sensor_observation TEXT,
        alert_generated TEXT,
        response TEXT NOT NULL,
        outcome TEXT NOT NULL,
        is_simulated INTEGER DEFAULT 1,
        source_ref TEXT,
        FOREIGN KEY(mountain_id) REFERENCES mountains(id)
    );
    """)

    # 6. Nearby Villages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nearby_villages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mountain_id TEXT NOT NULL,
        name TEXT NOT NULL,
        distance_km REAL NOT NULL,
        population INTEGER,
        FOREIGN KEY(mountain_id) REFERENCES mountains(id)
    );
    """)

    # 7. Safe Locations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS safe_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mountain_id TEXT NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        contact TEXT,
        FOREIGN KEY(mountain_id) REFERENCES mountains(id)
    );
    """)

    # 8. Emergency Reports table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emergency_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mountain_id TEXT NOT NULL,
        emergency_type TEXT NOT NULL,
        location TEXT NOT NULL,
        people_affected INTEGER NOT NULL,
        description TEXT NOT NULL,
        contact_phone TEXT,
        timestamp DATETIME NOT NULL,
        status TEXT DEFAULT 'PENDING',
        FOREIGN KEY(mountain_id) REFERENCES mountains(id)
    );
    """)

    # 9. System Config table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)

    conn.commit()

    # Check if database is empty; if so, populate demo content
    cursor.execute("SELECT COUNT(*) FROM mountains;")
    if cursor.fetchone()[0] == 0:
        seed_demo_data(cursor)
        conn.commit()

    conn.close()

def seed_demo_data(cursor):
    mountains_data = [
        ("MT001", "Kedarnath Slope Zone", "Uttarakhand", "Rudraprayag District", 30.7346, 79.0669, 3583, "Mandakini River", "Steep glaciated catchment with unstable glacial till and moraines."),
        ("MT002", "Rohtang Ridge Sector 4", "Himachal Pradesh", "Manali Basin", 32.3716, 77.2466, 3978, "Beas River", "High precipitation mountain corridor vulnerable to monsoon slope destabilization."),
        ("MT003", "Nathula Pass Escarpment", "Sikkim", "East Sikkim Corridor", 27.3866, 88.8309, 4310, "Tista Tributary", "High seismic vulnerability zone with fractured rock beds and water percolation risks."),
        ("MT004", "Tawang West Slope", "Arunachal Pradesh", "Tawang Valley", 27.5861, 91.8653, 3048, "Tawang Chu", "Sub-tropical highland forest with heavy rainstorms and erosion channels.")
    ]
    cursor.executemany("""
    INSERT INTO mountains (id, name, state, location, latitude, longitude, elevation, nearby_river, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, mountains_data)

    sensors_data = [
        ("M001", "MT001", "ONLINE", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')),
        ("M002", "MT002", "ONLINE", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')),
        ("M003", "MT003", "ONLINE", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')),
        ("M004", "MT004", "OFFLINE", (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'))
    ]
    cursor.executemany("""
    INSERT INTO sensors (id, mountain_id, status, last_seen) VALUES (?, ?, ?, ?);
    """, sensors_data)

    accidents_data = [
        ("MT001", "2023-08-14", "Debris Flow / Landslide", 
         "Intense cloudburst over upper catchment saturated sub-soil over 48 hours.",
         "Moisture spiked from 52% to 89% in 3 hours. Rapid spike warning triggered.",
         "System generated Level 4 Critical Alert.", 
         "SDRF deployed roadblock 12km downstream. Village head alerted via dispatch.", 
         "Traffic halted early; 140 pilgrims sheltered in designated concrete structures. Zero casualties.", 
         1, "NDRF Post-Incident Audit 2023 (Simulated Case Study)"),
        ("MT002", "2022-07-29", "Rockfall & Mudflow", 
         "Continuous moderate precipitation caused hydraulic cleft pressure buildup.",
         "Moisture rose at +3.8%/hr, reaching 78% moisture status.",
         "System generated Level 3 Warning Alert.",
         "Highway safety patrol restricted traffic to single lane.",
         "Moderate road damage; cleared in 8 hours without vehicle entrapment.",
         1, "State Highway Division Incident Archive")
    ]
    cursor.executemany("""
    INSERT INTO accidents (mountain_id, date, type, description, sensor_observation, alert_generated, response, outcome, is_simulated, source_ref)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, accidents_data)

    villages = [
        ("MT001", "Rambara Hamlet", 3.2, 450),
        ("MT001", "Gaurikund Base", 6.5, 1200),
        ("MT002", "Marhi Outpost", 4.1, 280),
        ("MT003", "Sherathang", 5.0, 600),
        ("MT004", "Lhou Settlement", 2.8, 850)
    ]
    cursor.executemany("INSERT INTO nearby_villages (mountain_id, name, distance_km, population) VALUES (?, ?, ?, ?);", villages)

    safe_locations = [
        ("MT001", "Kedarnath Concrete Transit Shelter", "Emergency Shelter", "+91-0135-274000"),
        ("MT001", "Gaurikund Medical Outpost", "Hospital", "+91-0135-274001"),
        ("MT002", "Kothi Police & Disaster Sub-Station", "Police Station", "+91-01902-252100"),
        ("MT003", "Sherathang Military Border Camp", "Army Base / Shelter", "+91-03592-202000"),
        ("MT004", "Tawang District Hospital", "Hospital", "+91-03794-222200")
    ]
    cursor.executemany("INSERT INTO safe_locations (mountain_id, name, type, contact) VALUES (?, ?, ?, ?);", safe_locations)

    cursor.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('emergency_phone', '+91-112-892-DISASTER');")
    cursor.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('admin_password', 'admin123');")

    now = datetime.utcnow()
    # Fixed order: (sensor_id, mountain_id, ...)
    for s_id, m_id, status, _ in sensors_data:
        base_moisture = 42.0 if m_id != "MT001" else 72.0
        for day in range(15, -1, -1):
            day_time = now - timedelta(days=day)
            for hour in [0, 6, 12, 18]:
                reading_time = day_time.replace(hour=hour, minute=0, second=0)
                if reading_time > now:
                    continue
                fluctuation = (random.random() - 0.48) * 3.5
                if m_id == "MT001" and day < 2:
                    base_moisture += 2.0
                base_moisture = max(20.0, min(95.0, base_moisture + fluctuation))
                rainfall = round(max(0.0, (base_moisture - 45.0) * 0.7 + random.uniform(0, 5)), 1)

                cursor.execute("""
                INSERT INTO sensor_data (sensor_id, mountain_id, moisture, rainfall, timestamp, is_demo)
                VALUES (?, ?, ?, ?, ?, 1);
                """, (s_id, m_id, round(base_moisture, 1), rainfall, reading_time.strftime('%Y-%m-%d %H:%M:%S')))

    cursor.execute("""
    INSERT INTO alerts (mountain_id, risk_level, moisture, rainfall, message, timestamp, status)
    VALUES ('MT001', 'CRITICAL', 86.4, 28.5, 'Sustained ground saturation in upper moraine corridor.', ?, 'Active');
    """, (now.strftime('%Y-%m-%d %H:%M:%S'),))