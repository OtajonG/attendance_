import random
import datetime
import database
import beacon_simulator


def simulate_face_recognition(student_id):
    """Simulates facial recognition for a student."""

    # Simulate a successful face match (e.g., 90% chance of success)
    if random.random() < 0.9:
        print(f"Face recognized for student ID: {student_id}")
        return True  # Face match
    else:
        print(f"Face not recognized for student ID: {student_id}")
        return False  # No face match


def check_in():
    """Simulates a student checking in via facial recognition."""
    student_id = beacon_simulator.current_student_id  # Access the global variable

    if simulate_face_recognition(student_id):
        if database.student_exists(student_id):
            timestamp = datetime.datetime.now()
            database.record_attendance(student_id, timestamp)
            print(f"Check-in recorded for student ID: {student_id} at {timestamp}")
        else:
            print(f"Student ID {student_id} not found.")
    else:
        print("Check-in failed: Facial recognition failed.")


if __name__ == "__main__":
    check_in()
