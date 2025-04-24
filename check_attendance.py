import face_recognition
import sqlite3
import datetime
import asyncio
from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData
import struct

# iBeacon parameters to look for
TEACHER_BEACON_UUID = "019637fa-978a-7a1c-8447-f914acdc999c"
TEACHER_BEACON_MAJOR = 1
TEACHER_BEACON_MINOR = 10


async def find_teacher_beacon():
    scanner = BleakScanner()
    devices = await scanner.discover(timeout=5.0)  # Scan for 5 seconds

    for device in devices:
        advertisement_data = device.metadata.get("manufacturer_data", {})
        for manufacturer_id, data in advertisement_data.items():
            if (
                manufacturer_id == 0x004C and len(data) >= 23
            ):  # Apple manufacturer ID and minimum iBeacon length
                # Parse iBeacon data
                ibeacon_prefix = data[0:2]
                if ibeacon_prefix == b"\x02\x15":
                    proximity_uuid_bytes = data[2:18]
                    major_bytes = data[18:20]
                    minor_bytes = data[20:22]

                    proximity_uuid = proximity_uuid_bytes.hex()
                    major = int.from_bytes(major_bytes, byteorder="big")
                    minor = int.from_bytes(minor_bytes, byteorder="big")

                    # Check if it's our teacher beacon
                    if (
                        proximity_uuid == TEACHER_BEACON_UUID.replace("-", "")
                        and major == TEACHER_BEACON_MAJOR
                        and minor == TEACHER_BEACON_MINOR
                    ):
                        print("Teacher beacon found!")
                        return True
    print("Teacher beacon not found.")
    return False


def check_attendance(image_path):
    try:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) > 0:
            face_encoding = face_encodings[0]

            conn = sqlite3.connect("attendance.db")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, face_encoding FROM students"
            )  # Select id instead of name
            rows = cursor.fetchall()

            for row in rows:
                student_id = row[0]  # Get student id
                known_face_encoding = row[1]
                known_face_encoding_array = face_recognition.load_image_file(
                    f"Student {student_id}.jpg"  # load student photo to compare
                )
                known_face_encoding_array = face_recognition.face_encodings(
                    known_face_encoding_array
                )
                if len(known_face_encoding_array) > 0:
                    known_face_encoding_array = known_face_encoding_array[0]
                    results = face_recognition.compare_faces(
                        [known_face_encoding_array], face_encoding
                    )

                    if results[0]:
                        now = datetime.datetime.now()
                        date_time = now.strftime("%Y-%m-%d %H:%M:%S")

                        # Record attendance
                        cursor.execute(
                            "INSERT INTO attendance (student_id, timestamp) VALUES (?, ?)",  # change name to student_id and date_time to timestamp
                            (student_id, date_time),
                        )
                        conn.commit()
                        conn.close()
                        return f"Attendance recorded for Student {student_id} at {date_time}."
            conn.close()
            return "Unknown face."
        else:
            return "No face found in image."
    except Exception as e:
        return f"Error checking attendance: {e}"


async def main():
    beacon_found = await find_teacher_beacon()
    if beacon_found:
        result = check_attendance("attendance_check.jpg")
        print(result)
    else:
        print("Teacher beacon not found. Attendance check skipped.")


if __name__ == "__main__":
    asyncio.run(main())
