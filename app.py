

import os
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, jsonify, request

CREATE_ROOMS_TABLE =(
    "CREATE TABLE IF NOT EXISTS rooms (id SERIAL PRIMARY KEY, name TEXT);"    
)

CREATE_TEMP_TABLE =(
    """CREATE TABLE IF NOT EXISTS temperatues (room_id INTEGER, temp_no INTEGER,
    date TIMESTAMP, FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE);""" 
)

INSERT_ROOM_RETURN_ID = "INSERT INTO rooms(name) VALUES (%s) RETURNING id;"

INSERT_TEMP = "INSERT INTO temperatues (room_id, temp_no) VALUES (%s, %s);"

GLOBAL_NUMBER_OF_DAYS =(
    """ SELECT COUNT(DISTINCT DATE(date)) AS days FROM temperatues;"""
)

GLOBAL_AVG = """SELECT AVG(temp_no) AS average FROM temperatues;"""

SHOW_ROOM_TEMP = "SELECT * FROM temperatues;"

GET_DATA_ID = "SELECT id AS id FROM rooms"

GET_DATA_NAME = "SELECT name AS name FROM rooms"

load_dotenv()


app=Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")
PORT = os.getenv("PORT", "8080")
connection = psycopg2.connect(DATABASE_URL)



@app.get("/")
def Hello_World():
     return jsonify({
         "room" : "/room" ,
        "Temparature" :  "/temparature",
        "GetTemparature" : "/gettemp",
        "Average" : "/average",
        "Data" : "/datas", 
        "Room_Datas" : "/rooms-data",
        "Temparature_Datas" : "/temp-data"
    })

@app.post("/room")
def create_room():
    data = request.get_json()
    name = data["name"]
    with connection:
        with connection.cursor() as cursor:   
            cursor.execute(CREATE_ROOMS_TABLE)
            cursor.execute(INSERT_ROOM_RETURN_ID,(name,))
            room_id = cursor.fetchone()[0]
    return {"id": room_id, "message": f"{name} room created."}, 201
@app.post("/temperature")
def add_temp():
    data = request.get_json()
    temp_no = data["temp_no"]
    room_id = data["room_id"]
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TEMP_TABLE)
            cursor.execute(INSERT_TEMP,(room_id,temp_no))
    return {"message" : "Temperature added."}, 201
@app.get("/gettemp")
def get_temp():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SHOW_ROOM_TEMP)
            tempval = cursor.fetchall
    return {"data: [{tempval}]"}


@app.get("/average")
def get_global_avg():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(GLOBAL_AVG)
            average = cursor.fetchone()[0]
            cursor.execute(GLOBAL_NUMBER_OF_DAYS)
            days = cursor.fetchone()[0]
    return {"average" : round(average, 2), "days" : days}

@app.get("/datas")
def get_data():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(GET_DATA_ID)
            id = cursor.fetchone()[0]
            cursor.execute(GET_DATA_NAME)
            name = cursor.fetchone()[0]
    return {"id" : id, "name" : name}

@app.get("/rooms-data")
def rooms_data():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM rooms;")
            rows = cursor.fetchall()
    data = [{"id": row[0], "name": row[1]} for row in rows]
    return jsonify(data), 200


@app.get("/temp-data")
def temps_data():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT room_id, temp_no FROM temperatues;")
            rows = cursor.fetchall()
    data = [{"room_id": row[0], "temp_no": row[1]} for row in rows]
    return jsonify(data), 200


if __name__ == "__main__":
    app.run(debug=True, port=PORT)

