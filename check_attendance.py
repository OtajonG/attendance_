import asyncio
from bleak import BleakScanner
import struct
import face_recognition
import sqlite3
import numpy as np
import os

DATABASE = "attendance.db"
TEACHER_BEACON_UUID = "019637fa-978a-7a1c-8447-f914acdc999c"
TEACHER_BEACON_MAJOR = 1
TEACHER_BEACON_MINOR = 10
FACE_MATCH_THRESHOLD = 0.6  # Adjust as needed


async def find_teacher_beacon():
    scanner = BleakScanner()
    devices = await scanner.discover(timeout=5.0)  # Scan for 5 seconds

    for device in devices:
        advertisement_data = device.metadata.get("manufacturer_data", {})
        for manufacturer_id, data in advertisement_data.items():
            if manufacturer_id == 0x004C and len(data) >= 21:
                # Look for the iBeacon prefix within the first few bytes
                for i in range(min(5, len(data) - 1)):
                    if data[i : i + 2] == b"\x02\x15":
                        # Prefix found, now parse the rest based on the offset
                        if len(data) >= i + 21:
                            proximity_uuid_bytes = data[i + 2 : i + 18]
                            major_bytes = data[i + 18 : i + 20]
                            minor_bytes = data[i + 20 : i + 22]

                            proximity_uuid = proximity_uuid_bytes.hex()
                            major = int.from_bytes(major_bytes, byteorder="big")
                            minor = int.from_bytes(minor_bytes, byteorder="big")

                            target_uuid = TEACHER_BEACON_UUID.replace("-", "")

                            print(
                                f"Found potential iBeacon - UUID: {proximity_uuid}, Major: {major}, Minor: {minor}"
                            )

                            if proximity_uuid == target_uuid:
                                print(
                                    f"Potential Beacon Found with Correct UUID - Major: {major}, Minor: {minor}"
                                )
                                print("Teacher beacon found!")
                                return True
                            break  # Break after finding a potential prefix

    print("Teacher beacon not found.")
    return False


def verify_face(image_path):  # Assuming you are passing the path to the scanned image
    try:
        # Load the scanned image
        scan_image = face_recognition.load_image_file(image_path)
        scan_face_encodings = face_recognition.face_encodings(scan_image)

        if not scan_face_encodings:
            print("No face found in the scanned image.")
            return None

        scan_face_encoding = scan_face_encodings[0]  # Assuming only one face per scan

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("SELECT student_id, name, face_encoding FROM students")
        enrolled_students = cursor.fetchall()

        for student_id, name, encoded_data in enrolled_students:
            if encoded_data:
                known_face_encoding = np.frombuffer(encoded_data, dtype=np.float64)
                face_distances = face_recognition.face_distance(
                    [known_face_encoding], scan_face_encoding
                )
                if face_distances[0] < FACE_MATCH_THRESHOLD:
                    conn.close()
                    print(f"Face recognized as student: {name} (ID: {student_id})")
                    return student_id

        conn.close()
        print("Face not recognized.")
        return None

    except Exception as e:
        print(f"Error during face verification: {e}")
        return None


async def main():
    beacon_found = await find_teacher_beacon()
    if beacon_found:
        # For testing, let's assume the captured image is saved as 'current_scan.jpg'
        # In a real application, you would get the path to the captured image
        face_recognized_student_id = verify_face("current_scan.jpg")
        if face_recognized_student_id:

            # Record attendance using the recognized student_id
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO attendance (student_id, timestamp) VALUES (?, DATETIME('now'))",
                (face_recognized_student_id,),
            )
            conn.commit()
            conn.close()
            print(f"Attendance recorded for student ID: {face_recognized_student_id}")
            return f"Attendance recorded for Student {face_recognized_student_id}"  # Return a message for the web page
        else:
            return "No face found or recognized."  # Return a message for the web page
    else:
        return "Teacher beacon not found. Attendance check skipped."  # Return a message for the web page


if __name__ == "__main__":
    asyncio.run(main())
