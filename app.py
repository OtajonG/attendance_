from flask import Flask, render_template, jsonify, request
import sqlite3
import face_recognition
import cv2
import numpy as np
import os
from datetime import datetime
import asyncio
from bleak import BleakScanner
import uvicorn

app = Flask(__name__)

DATABASE = "attendance.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    conn = get_db()
    cur = conn.execute(query, args)
    conn.commit()
    cur.close()
    conn.close()


def record_attendance(student_id):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    execute_db(
        "INSERT INTO attendance (student_id, timestamp) VALUES (?, ?)",
        (student_id, timestamp),
    )


@app.route("/")
def attendance_page():
    students_data = query_db("SELECT id, name FROM students")  # Using 'name' here
    return render_template("index.html", students=students_data)


@app.route("/students_list")
def students_list():
    students_data = query_db("SELECT id, name FROM students")  # Using 'name' here
    return jsonify([dict(row) for row in students_data])


@app.route("/records")
def records():
    attendance_records = query_db(
        "SELECT s.name, a.timestamp FROM attendance a JOIN students s ON a.student_id = s.id"
    )  # Using 'name' here
    return jsonify([dict(row) for row in attendance_records])


@app.route("/verify_face", methods=["POST"])
def verify_face():
    if "webcamImage" not in request.files or "student_id" not in request.form:
        return jsonify({"success": False, "message": "Missing data."})

    webcam_image_file = request.files["webcamImage"]
    student_id = request.form["student_id"]

    webcam_img_bytes = webcam_image_file.read()
    webcam_img_array = np.frombuffer(webcam_img_bytes, np.uint8)
    webcam_img = cv2.imdecode(webcam_img_array, cv2.IMREAD_COLOR)
    webcam_face_locations = face_recognition.face_locations(webcam_img)

    if not webcam_face_locations:
        return jsonify(
            {"success": False, "message": "No face detected in the captured image."}
        )

    webcam_face_encoding = face_recognition.face_encodings(
        webcam_img, webcam_face_locations
    )[0]

    student_data = query_db(
        "SELECT face_encoding FROM students WHERE id = ?", (student_id,), one=True
    )

    if student_data and student_data["face_encoding"]:
        stored_face_encoding = np.frombuffer(
            student_data["face_encoding"], dtype=np.float64
        )
        results = face_recognition.compare_faces(
            [stored_face_encoding], webcam_face_encoding
        )
        if results[0]:
            record_attendance(student_id)
            return jsonify({"success": True, "message": "Attendance recorded."})
        else:
            return jsonify({"success": False, "message": "Face verification failed."})
    else:
        return jsonify({"success": False, "message": "Student face data not found."})


@app.route("/live_records")
def live_records():
    attendance_records = query_db(
        "SELECT s.name, a.timestamp FROM attendance a JOIN students s ON a.student_id = s.id ORDER BY a.timestamp DESC LIMIT 5"  # Adjust LIMIT as needed
    )
    return jsonify([dict(row) for row in attendance_records])


async def scan_for_teacher_beacon():
    while True:
        devices = await BleakScanner.discover()
        for device in devices:
            for ad in device.advertisement_data.manufacturer_data.values():
                if (
                    len(ad) >= 25 and ad[0] == 0x4C and ad[1] == 0x00
                ):  # Apple manufacturer ID (for iBeacon)
                    beacon_uuid_bytes = ad[2:18]
                    beacon_uuid = "-".join(
                        [beacon_uuid_bytes[i : i + 4].hex() for i in range(0, 16, 4)]
                    )
                    major = int.from_bytes(ad[18:20], "big")
                    minor = int.from_bytes(ad[20:22], "big")

                    if (
                        beacon_uuid.lower() == TEACHER_BEACON_UUID.lower()
                        and major == TEACHER_BEACON_MAJOR
                        and minor == TEACHER_BEACON_MINOR
                    ):
                        student_id_to_record = 1  # IMPORTANT: Replace with your logic to identify the current student
                        print(
                            f"Teacher beacon detected (UUID: {beacon_uuid}, Major: {major}, Minor: {minor})! Recording attendance for student ID: {student_id_to_record}"
                        )
                        record_attendance(student_id_to_record)
                        await asyncio.sleep(10)  # Wait a bit to avoid repeated triggers
                        break
        await asyncio.sleep(1)  # Scan every 1 second


# ... (your existing app.py code) ...


async def main():
    asyncio.create_task(scan_for_teacher_beacon())
    uvicorn.run(
        app, host="0.0.0.0", port=5000, reload=True
    )  # You can adjust host and port


if __name__ == "__main__":
    asyncio.run(main())
