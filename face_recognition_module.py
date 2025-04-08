import face_recognition
import cv2
import sqlite3
import numpy as np
import io

def recognize_face(image):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, face_encoding FROM students")
    students = cursor.fetchall()
    conn.close()

    unknown_image = face_recognition.load_image_file(image)
    unknown_encodings = face_recognition.face_encodings(unknown_image)

    if len(unknown_encodings) == 0:
        return None

    unknown_encoding = unknown_encodings[0]

    for student_id, student_name, student_encoding_blob in students:
        student_encoding = np.frombuffer(student_encoding_blob, dtype=np.float64)
        results = face_recognition.compare_faces([student_encoding], unknown_encoding)
        if results[0]:
            return student_id

    return None