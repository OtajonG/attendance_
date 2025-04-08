import face_recognition
import sqlite3
import datetime

def check_attendance(image_path):
    try:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) > 0:
            face_encoding = face_encodings[0]

            conn = sqlite3.connect("attendance.db")
            cursor = conn.cursor()

            cursor.execute("SELECT id, face_encoding FROM students")  # Select id instead of name
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
                            "INSERT INTO attendance (student_id, timestamp) VALUES (?, ?)", #change name to student_id and date_time to timestamp
                            (student_id, date_time),
                        )
                        conn.commit()
                        print(f"Attendance recorded for Student {student_id} at {date_time}.")
                        conn.close()
                        return

            print("Unknown face.")
            conn.close()
        else:
            print("No face found in image.")
    except Exception as e:
        print(f"Error checking attendance: {e}")

if __name__ == "__main__":
    check_attendance("attendance_check.jpg")