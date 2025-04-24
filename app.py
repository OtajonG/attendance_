from flask import Flask, render_template, jsonify, request
import sqlite3
import face_recognition
import cv2
import numpy as np
import os
from datetime import datetime
import asyncio
from check_attendance import find_teacher_beacon, check_attendance

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
def index():
    return render_template("index.html")


@app.route("/check_attendance_page")
def attendance_page():
    students_data = query_db("SELECT id, name FROM students")  # Using 'name' here
    return render_template("attendance.html", students=students_data)


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


async def process_attendance():
    beacon_found = await find_teacher_beacon()
    if beacon_found:
        attendance_message = check_attendance("attendance_check.jpg")
        return {"success": True, "message": attendance_message}
    else:
        return {
            "success": False,
            "message": "Teacher beacon not found. Attendance check skipped.",
        }


@app.route("/verify_face", methods=["POST"])
async def verify_face():
    beacon_result = await process_attendance()
    if not beacon_result["success"]:
        return jsonify(beacon_result)

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


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
