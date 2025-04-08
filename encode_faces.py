import face_recognition
import numpy as np
import sqlite3
import os


def encode_and_store_faces(image_folder, database_file):
    """Encodes faces from images and stores them in the database."""

    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    for filename in os.listdir(image_folder):
        if filename.lower().endswith(
            (".png", ".jpg", ".jpeg")
        ):  # Check if it's an image
            image_path = os.path.join(image_folder, filename)

            try:
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image)

                if face_encodings:
                    face_encoding = face_encodings[
                        0
                    ]  # Take the first face if multiple are detected
                    face_encoding_bytes = face_encoding.tobytes()

                    # Extract student ID from the filename (e.g., student1.jpg -> id = 1)
                    student_id = int(filename.split("")[1].split(".")[0])

                    cursor.execute(
                        "INSERT OR REPLACE INTO students (id, name, face_encoding) VALUES (?, ?, ?)",
                        (student_id, filename, face_encoding_bytes),
                    )  # update if exist
                    print(f"Encoded and stored: {filename}")
                else:
                    print(f"No face found in {filename}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    image_folder = "student_images"  # Replace with your image folder
    database_file = "attendance.db"  # Replace with your database file

    encode_and_store_faces(image_folder, database_file)
