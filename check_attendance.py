import asyncio
from bleak import BleakScanner
import struct
import face_recognition
import sqlite3
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE = "attendance.db"
TEACHER_BEACON_UUID = os.getenv("TEACHER_BEACON_UUID")
TEACHER_BEACON_MAJOR = os.getenv("TEACHER_BEACON_MAJOR")
TEACHER_BEACON_MINOR = os.getenv("TEACHER_BEACON_MINOR")
FACE_MATCH_THRESHOLD = 0.6  # Adjust as needed


async def find_teacher_beacon():
    if not TEACHER_BEACON_UUID:
        print("Teacher Beacon UUID not configured (check .env file).")
        return False

    scanner = BleakScanner()
    devices = await scanner.discover(timeout=5.0)  # Scan for 5 seconds

    for device in devices:
        advertisement_data = device.metadata.get("manufacturer_data", {})
        for manufacturer_id, data in advertisement_data.items():
            if manufacturer_id == 0x004C and len(data) >= 21:
                for i in range(min(5, len(data) - 1)):
                    if data[i : i + 2] == b"\x02\x15":
                        if len(data) >= i + 21:
                            proximity_uuid_bytes = data[i + 2 : i + 18]
                            major_bytes = data[i + 18 : i + 20]
                            minor_bytes = data[i + 20 : i + 22]

                            proximity_uuid = proximity_uuid_bytes.hex()
                            major = int.from_bytes(major_bytes, byteorder="big")
                            minor = int.from_bytes(minor_bytes, byteorder="big")

                            target_uuid = TEACHER_BEACON_UUID.replace("-", "")

                            match_uuid = proximity_uuid == target_uuid
                            match_major = (TEACHER_BEACON_MAJOR is None) or (
                                str(major) == TEACHER_BEACON_MAJOR
                            )
                            match_minor = (TEACHER_BEACON_MINOR is None) or (
                                str(minor) == TEACHER_BEACON_MINOR
                            )

                            if match_uuid and match_major and match_minor:
                                print("Teacher beacon found!")
                                return True
                            break

    print("Teacher beacon not found.")
    return False


# This function is not being used in the current app.py
def check_attendance(image_path):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, face_encoding FROM students")
    students_data = cursor.fetchall()

    known_face_encodings = []
    known_face_names = []

    for id, name, encoding_bytes in students_data:
        if encoding_bytes:
            encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
            known_face_encodings.append(encoding)
            known_face_names.append(name)

    if not known_face_encodings:
        conn.close()
        return "No student face data available."

    try:
        unknown_image = face_recognition.load_image_file(image_path)
        unknown_face_locations = face_recognition.face_locations(unknown_image)
        unknown_face_encodings = face_recognition.face_encodings(
            unknown_image, unknown_face_locations
        )

        if not unknown_face_encodings:
            conn.close()
            return "No faces detected in the scanned image."

        face_distances = face_recognition.face_distance(
            known_face_encodings, unknown_face_encodings[0]
        )
        best_match_index = np.argmin(face_distances)

        if face_distances[best_match_index] < FACE_MATCH_THRESHOLD:
            name = known_face_names[best_match_index]
            cursor.execute("SELECT id FROM students WHERE name = ?", (name,))
            student_id = cursor.fetchone()[0]
            conn.close()
            return f"Attendance marked for {name} (ID: {student_id})."
        else:
            conn.close()
            return "Face not recognized."

    except FileNotFoundError:
        conn.close()
        return f"Error: Image file not found at {image_path}"
    except Exception as e:
        conn.close()
        return f"An error occurred during face recognition: {e}"


if __name__ == "__main__":

    async def main():
        beacon_found = await find_teacher_beacon()
        print(f"Beacon found in main: {beacon_found}")

    asyncio.run(main())
