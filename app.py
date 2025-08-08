# add the history of the crop product



#      IMPORT MODULES      

import os
import psycopg2
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from dotenv import load_dotenv
from datetime import timedelta


#     LOAD ENVIRONMENT     

# Loads database connection details from a .env file (like DATABASE_URL)
load_dotenv()


#     INITIALIZE FLASK     

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
jwt = JWTManager(app)

#    DATABASE CONNECTION   

# Connects to the PostgreSQL database using credentials from .env
DATABASE_URL = os.getenv("DATABASE_URL")
connection = psycopg2.connect(DATABASE_URL)


# CREATE SENSOR DATA TABLE 

# Table to store sensor data with automatic timestamp
CREATE_SENSOR_TABLE = """
CREATE TABLE IF NOT EXISTS demo (
    id SERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,
    temperature REAL,
    humidity REAL,
    soil_moisture REAL,
    ph REAL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

# SQL query to insert data into the 'demo' table (auto adds timestamp)
INSERT_SENSOR_DATA_RETURN_ID = """
INSERT INTO demo (device_id, temperature, humidity, soil_moisture, ph)
VALUES (%s, %s, %s, %s, %s)
RETURNING id;
"""

# CREATE TABLE FOR CROP HISTORY
CREATE_CROP_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS crop_history (
    id SERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,
    crop TEXT NOT NULL,
    year INT NOT NULL,
    region TEXT NOT NULL,
    yield_per_hectare REAL,
    area_hectare INT
);
"""

# CREATE ALERTS TABLE
CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""


# SQL Queries
CREATE_SUBADMINS_TABLE = """
CREATE TABLE IF NOT EXISTS subadmin (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'subadmin',
    phone TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

INSERT_SUBADMIN = """
INSERT INTO subadmin (name, email, role, phone)
VALUES (%s, %s, %s, %s)
RETURNING id;
"""

GET_ALL_SUBADMINS = "SELECT id, name, email, role, phone, created_at FROM subadmin;"

GET_SUBADMIN_BY_ID = "SELECT id, name, email, role, phone, created_at FROM subadmin WHERE id = %s;"

UPDATE_SUBADMIN = """
UPDATE subadmin
SET name = %s, email = %s, role = %s, phone = %s
WHERE id = %s;
"""
DELETE_SUBADMIN = "DELETE FROM subadmin WHERE id = %s;"

# SQL Queries
CREATE_VENDOR_CLIENTS_TABLE = """
CREATE TABLE IF NOT EXISTS vendor_clients (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

INSERT_VENDOR_CLIENT_RETURN_ID = """
INSERT INTO vendor_clients (name, email, phone, address)
VALUES (%s, %s, %s, %s)
RETURNING id;
"""

GET_ALL_VENDOR_CLIENTS = "SELECT id, name, email, phone, address, created_at FROM vendor_clients;"

GET_VENDOR_CLIENT_BY_ID = "SELECT id, name, email, phone, address, created_at FROM vendor_clients WHERE id = %s;"

DELETE_VENDOR_CLIENT = "DELETE FROM vendor_clients WHERE id = %s;"

UPDATE_VENDOR_CLIENT = """
UPDATE vendor_clients
SET name = %s, email = %s, phone = %s, address = %s
WHERE id = %s;
"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""


# HOME ROUTE        

@app.route("/")
def home():
        return jsonify({
        "UPLOAD SENSOR DATA API": {"url": "/api/demo/upload", "method": "POST"},
        "GET ALL SENSOR TABLE DATA": {"url": "/all-data", "method": "GET"},
        "GET LATEST SENSOR DATA FOR DEVICE": {"url": "/api/demo/latest/<device_id>", "method": "GET"},
        "IRRIGATION TRIGGER LOGIC": {"url": "/api/irrigation/trigger", "method": "POST"},
        "MARKET PRICE API": {"url": "/api/market/prices", "method": "GET"},
        "HISTORICAL CROP DATA API": {"url": "/api/crop/history", "method": "GET"},
        "GET CROP HISTORY BY ID": {"url": "/api/crop/history/<int:id>", "method": "GET"},
        "GET CROP HISTORY BY DEVICE_ID": {"url": "/api/crop/history/device/<device_id>", "method": "GET"},
        "ALERT SUMMARY": {"url": "/api/alerts/summary", "method": "GET"},
        "SUBADMIN LIST & CREATE": {"url": "/api/admin/subadmins", "method": "GET, POST"},
        "SUBADMIN GET/UPDATE/DELETE": {"url": "/api/admin/subadmins/<int:id>", "method": "GET, PUT, DELETE"},
        "VENDOR CLIENTS LIST & CREATE": {"url": "/api/vendor/clients", "method": "GET, POST"},
        "VENDOR CLIENT GET/UPDATE/DELETE": {"url": "/api/vendor/clients/<int:id>", "method": "GET, PUT, DELETE"},
        "USER REGISTER": {"url": "/api/auth/register", "method": "POST"},
        "USER LOGIN": {"url": "/api/auth/login", "method": "POST"},
        "USER LOGOUT": {"url": "/api/auth/logout", "method": "POST"},
        "GET PROFILE": {"url": "/api/profile", "method": "GET"},
        "ADMIN DASHBOARD": {"url": "/api/admin/dashboard", "method": "GET"}
    })


#     UPLOAD SENSOR DATA API    

@app.post("/api/demo/upload")
def upload_sensor_data():
    # Expect JSON input with sensor values
    data = request.get_json()
    required_fields = ['device_id', 'temperature', 'humidity', 'soil_moisture', 'ph']

    # Check all required fields are present
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400

    # Extract data from request
    device_id = data["device_id"]
    temperature = data["temperature"]
    humidity = data["humidity"]
    soil_moisture = data["soil_moisture"]
    ph = data["ph"]

    # Insert into database
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_SENSOR_TABLE)  # Ensure table exists
            cursor.execute(
                INSERT_SENSOR_DATA_RETURN_ID,
                (device_id, temperature, humidity, soil_moisture, ph)
            )
            sensor_id = cursor.fetchone()[0]

    return jsonify({"id": sensor_id, "message": "Sensor data uploaded successfully"}), 201


#   GET ALL SENSOR DATA (with timestamp) 

@app.get("/all-data")
def sensors_data():
    # Fetch all data from 'demo' table
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT device_id, temperature, humidity, soil_moisture, ph, timestamp FROM demo;")
            rows = cursor.fetchall()

    # Format data as list of dictionaries
    data = [{
        "device_id": row[0],
        "temperature": row[1],
        "humidity": row[2],
        "soil_moisture": row[3],
        "ph": row[4],
        "timestamp": row[5].isoformat()
    } for row in rows]

    return jsonify(data), 200


# GET LATEST SENSOR DATA FOR A DEVICE (latest only)

@app.get("/api/demo/latest/<device_id>")
def get_latest_sensor_data(device_id):
    SELECT_LATEST_SENSOR_DATA = """
    SELECT id, device_id, temperature, humidity, soil_moisture, ph, timestamp
    FROM demo
    WHERE device_id = %s
    ORDER BY timestamp DESC
    LIMIT 1;
    """

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_LATEST_SENSOR_DATA, (device_id,))
            result = cursor.fetchone()

            if result is None:
                return {"message": f"No sensor data found for device: {device_id}"}, 404

            sensor_data = {
                "id": result[0],
                "device_id": result[1],
                "temperature": result[2],
                "humidity": result[3],
                "soil_moisture": result[4],
                "ph": result[5],
                "timestamp": result[6].isoformat()
            }

    return {"latest_data": sensor_data}, 200


#  IRRIGATION TRIGGER LOGIC BASED ON DATA  

@app.post("/api/irrigation/trigger")
def trigger_irrigation():
    # Expect JSON input
    data = request.get_json()
    required_fields = ['device_id', 'temperature', 'soil_moisture']

    # Validate inputs
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400

    device_id = data["device_id"]
    temperature = data["temperature"]
    soil_moisture = data["soil_moisture"]

    # Logic: Irrigation turns on if moisture is low or temp is high
    if soil_moisture < 40 or temperature > 35:
        irrigation_status = "on"
    else:
        irrigation_status = "off"

    return {
        "device_id": device_id,
        "irrigation_status": irrigation_status,
        "logic": {
            "soil_moisture": soil_moisture,
            "temperature": temperature,
            "thresholds": {
                "min_soil_moisture": 40,
                "max_temperature": 35
            }
        }
    }, 200


#     MARKET PRICE API (MOCKED)     

@app.get("/api/market/prices")
def get_market_prices():
    crop = request.args.get("crop", "").lower()
    region = request.args.get("region", "").lower()

    # Example market data (mocked for now)
    market_data = [
        {"crop": "rice", "region": "tamil nadu", "price_per_quintal": 3100},
        {"crop": "rice", "region": "punjab", "price_per_quintal": 2950},
        {"crop": "wheat", "region": "uttar pradesh", "price_per_quintal": 2700},
        {"crop": "cotton", "region": "maharashtra", "price_per_quintal": 6100},
        {"crop": "maize", "region": "karnataka", "price_per_quintal": 2200},
        {"crop": "atta", "region": "delhi", "price_per_quintal": 3500},
        {"crop": "sugercane", "region": "tamil nadu", "price_per_quintal": 3450}
    ]

    # Filter data based on crop or region
    filtered_data = [
        entry for entry in market_data
        if (not crop or crop in entry["crop"]) and
           (not region or region in entry["region"])
    ]

    if not filtered_data:
        return {"message": "No price data found for the specified crop or region."}, 404

    return {"prices": filtered_data}, 200


#   HISTORICAL CROP DATA API (STATIC)     

@app.get("/api/crop/history")
def get_crop_history():
    crop = request.args.get("crop", "").lower()

    if not crop:
        return {"error": "Crop name is required as a query parameter (e.g. ?crop=rice)."}, 400

    # Historical data (static example)
    historical_data = {
        "rice": [
            {"year": 2020, "region": "Tamil Nadu", "yield_per_hectare": 3600, "area_hectare": 1200000},
            {"year": 2021, "region": "Tamil Nadu", "yield_per_hectare": 3750, "area_hectare": 1225000},
            {"year": 2022, "region": "Tamil Nadu", "yield_per_hectare": 3900, "area_hectare": 1250000}
        ],
        "wheat": [
            {"year": 2020, "region": "Punjab", "yield_per_hectare": 4200, "area_hectare": 1500000},
            {"year": 2021, "region": "Punjab", "yield_per_hectare": 4350, "area_hectare": 1480000},
            {"year": 2022, "region": "Punjab", "yield_per_hectare": 4400, "area_hectare": 1495000}
        ]
    }

    crop_data = historical_data.get(crop)

    if not crop_data:
        return {"message": f"No historical data found for crop: {crop}"}, 404

    return {
        "crop": crop,
        "history": crop_data
    }, 200



# GET CROP HISTORY BY ID
@app.get("/api/crop/history/<int:id>")
def get_crop_history_by_id(id):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_CROP_HISTORY_TABLE)  # Ensure table exists
            cursor.execute("SELECT * FROM crop_history WHERE id = %s;", (id,))
            row = cursor.fetchone()

    if row:
        data = {
            "id": row[0],
            "device_id": row[1],
            "crop": row[2],
            "year": row[3],
            "region": row[4],
            "yield_per_hectare": row[5],
            "area_hectare": row[6]
        }
        return jsonify(data), 200
    else:
        return {"message": f"No crop history found with id: {id}"}, 404


# GET CROP HISTORY BY DEVICE_ID
@app.get("/api/crop/history/device/<device_id>")
def get_crop_history_by_device(device_id):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_CROP_HISTORY_TABLE)  # Ensure table exists
            cursor.execute("SELECT * FROM crop_history WHERE device_id = %s;", (device_id,))
            rows = cursor.fetchall()

    if not rows:
        return {"message": f"No crop history found for device: {device_id}"}, 404

    data = []
    for row in rows:
        data.append({
            "id": row[0],
            "device_id": row[1],
            "crop": row[2],
            "year": row[3],
            "region": row[4],
            "yield_per_hectare": row[5],
            "area_hectare": row[6]
        })

    return jsonify(data), 200


@app.get("/api/alerts/summary")
def alert_summary():
    with connection:
        with connection.cursor() as cursor:
            # Ensure the alerts table exists
            cursor.execute(CREATE_ALERTS_TABLE)

            # Group and count alerts by type
            cursor.execute("""
                SELECT alert_type, COUNT(*) q1
                FROM alerts 
                GROUP BY alert_type;
            """)
            rows = cursor.fetchall()

    summary = [{"alert_type": row[0], "count": row[1]} for row in rows]

    return jsonify({"summary": summary}), 200


# Flask route for /api/admin/subadmins
@app.route("/api/admin/subadmins", methods=["GET", "POST"])
def handle_subadmins():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_SUBADMINS_TABLE)

            if request.method == "POST":
                data = request.get_json()
                name = data.get("name")
                email = data.get("email")
                role = data.get("role", "subadmin")
                phone = data.get("phone")

                if not name or not email or not role or not phone:
                    return {"error": "All fields (name, email, role, phone) are required."}, 400

                try:
                    cursor.execute(INSERT_SUBADMIN, (name, email, role, phone))
                    subadmin_id = cursor.fetchone()[0]
                    return {
                        "id": subadmin_id,
                        "message": f"Subadmin '{email}' created successfully."
                    }, 201
                except psycopg2.errors.UniqueViolation:
                    return {"error": "Email already exists."}, 409

            # GET all subadmins
            cursor.execute(GET_ALL_SUBADMINS)
            rows = cursor.fetchall()
            subadmins = [{
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "role": row[3],
                "phone": row[4],
                "created_at": row[5].isoformat()
            } for row in rows]

            return jsonify({"subadmins": subadmins}), 200


# Flask route for /api/admin/subadmins/<id>
@app.route("/api/admin/subadmins/<int:id>", methods=["GET", "PUT", "DELETE"])
def handle_subadmin_by_id(id):
    with connection:
        with connection.cursor() as cursor:
            if request.method == "GET":
                cursor.execute(GET_SUBADMIN_BY_ID, (id,))
                row = cursor.fetchone()
                if not row:
                    return {"error": "Subadmin not found."}, 404

                subadmin = {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "role": row[3],
                    "phone": row[4],
                    "created_at": row[5].isoformat()
                }
                return jsonify(subadmin), 200

            elif request.method == "PUT":
                data = request.get_json()
                name = data.get("name")
                email = data.get("email")
                role = data.get("role")
                phone = data.get("phone")

                if not name or not email or not role:
                    return {"error": "All fields (name, email, role, phone) are required."}, 400

                cursor.execute(UPDATE_SUBADMIN, (name, email, role, phone, id))
                return {"message": f"Subadmin ID {id} updated successfully."}, 200

            elif request.method == "DELETE":
                cursor.execute(DELETE_SUBADMIN, (id,))
                return {"message": f"Subadmin ID {id} deleted successfully."}, 200



# Endpoint: /api/vendor/clients
@app.route("/api/vendor/clients", methods=["GET", "POST"])
def manage_vendor_clients():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_VENDOR_CLIENTS_TABLE)

            if request.method == "POST":
                data = request.get_json()
                name = data.get("name")
                email = data.get("email")
                phone = data.get("phone")
                address = data.get("address")

                if not name or not email:
                    return {"error": "Name and email are required"}, 400

                try:
                    cursor.execute(INSERT_VENDOR_CLIENT_RETURN_ID, (name, email, phone, address))
                    client_id = cursor.fetchone()[0]
                    return {
                        "id": client_id,
                        "message": f"Vendor client {name} created successfully"
                    }, 201
                except psycopg2.errors.UniqueViolation:
                    return {"error": "Email already exists"}, 409

            # GET all clients
            cursor.execute(GET_ALL_VENDOR_CLIENTS)
            rows = cursor.fetchall()
            clients = [{
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "address": row[4],
                "created_at": row[5].isoformat()
            } for row in rows]

            return jsonify({"clients": clients}), 200


# Endpoint: /api/vendor/clients/<id>
@app.route("/api/vendor/clients/<int:id>", methods=["GET", "PUT", "DELETE"])
def handle_vendor_client(id):
    with connection:
        with connection.cursor() as cursor:
            # GET client by ID
            if request.method == "GET":
                cursor.execute(GET_VENDOR_CLIENT_BY_ID, (id,))
                row = cursor.fetchone()
                if row is None:
                    return {"error": "Vendor client not found"}, 404

                client = {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "phone": row[3],
                    "address": row[4],
                    "created_at": row[5].isoformat()
                }
                return jsonify(client), 200

            # PUT: Update client
            elif request.method == "PUT":
                data = request.get_json()
                name = data.get("name")
                email = data.get("email")
                phone = data.get("phone")
                address = data.get("address")

                if not name or not email:
                    return {"error": "Name and email are required"}, 400

                cursor.execute(UPDATE_VENDOR_CLIENT, (name, email, phone, address, id))
                return {"message": f"Vendor client {id} updated successfully"}, 200

            # DELETE: Remove client
            elif request.method == "DELETE":
                cursor.execute(DELETE_VENDOR_CLIENT, (id,))
                return {"message": f"Vendor client {id} deleted successfully"}, 200

@app.post("/api/auth/register")
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")  # Default role: user

    if not username or not email or not password:
        return {"error": "All fields are required"}, 400

    hashed_password = generate_password_hash(password)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_USERS_TABLE)
            try:
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s) RETURNING id;",
                    (username, email, hashed_password, role)
                )
                user_id = cursor.fetchone()[0]
            except psycopg2.errors.UniqueViolation:
                return {"error": "Username or Email already exists"}, 409

    return {"id": user_id, "message": "User registered successfully"}, 201

#  Login

@app.post("/api/auth/login")
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Email and password are required"}, 400

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, password_hash, role FROM users WHERE email = %s;", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                # ✅ Store only user ID as string in JWT
                access_token = create_access_token(identity=str(user[0]))
                return {
                    "message": "Login successful",
                    "access_token": access_token
                }, 200
            else:
                return {"error": "Invalid email or password"}, 401

#  Logout (Mock)

@app.post("/api/auth/logout")
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    return {"message": f"User ID {user_id} logged out successfully (mock)"}, 200

#  Get Profile

@app.get("/api/profile")
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()  # string user ID from token

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, email, role FROM users WHERE id = %s;", (user_id,))
            user = cursor.fetchone()

            if not user:
                return {"error": "User not found"}, 404

            return jsonify({
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "role": user[3]
            }), 200

#  Admin Dashboard

@app.get("/api/admin/dashboard")
@jwt_required()
def admin_dashboard():
    user_id = get_jwt_identity()

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT username, role FROM users WHERE id = %s;", (user_id,))
            user = cursor.fetchone()

            if not user:
                return {"error": "User not found"}, 404

            username, role = user
            if role != "admin":
                return {"error": "Access denied: Admins only"}, 403

            return {"message": f"Welcome Admin {username}"}, 200



# RUN THE SERVER       

if __name__ == "__main__":
    app.run(port=8080, debug=True)

