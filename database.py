import sqlite3
import face_recognition
import numpy as np
import os
import sys

print(sys.path)


def create_tables():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            face_encoding BLOB
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY,
            student_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """
    )

    conn.commit()
    conn.close()


def add_student(name, image_path):
    try:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        if len(face_encodings) > 0:
            face_encoding = face_encodings[0]
            face_encoding_bytes = face_encoding.tobytes()

            conn = sqlite3.connect("attendance.db")
            cursor = conn.cursor()

            # Check if student already exists
            cursor.execute("SELECT * FROM students WHERE name = ?", (name,))
            if cursor.fetchone() is None:  # Student doesn't exist
                cursor.execute(
                    "INSERT INTO students (name, face_encoding) VALUES (?, ?)",
                    (name, face_encoding_bytes),
                )
                conn.commit()
                print(f"Student '{name}' added successfully.")
            else:
                print(f"Student '{name}' already exists.")

            conn.close()

        else:
            print(f"No face found in image '{image_path}'.")
    except Exception as e:
        print(f"Error adding student '{name}': {e}")


def student_exists(student_id):
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM students WHERE id = ?", (student_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False


def record_attendance(student_id, timestamp):
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO attendance (student_id, timestamp) VALUES (?, ?)",
            (student_id, timestamp),
        )
        conn.commit()
        conn.close()
        print("Attendance recorded.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    create_tables()
    add_student("Student 1", "Student 1.jpg")  # change student name here.
    add_student("Student 2", "Student 2.jpg")  # change student name here.
    add_student("Student 3", "Student 3.jpg")  # change student name here.
    add_student("Student 4", "Student 4.jpg")  # change student name here.
