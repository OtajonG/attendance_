import time
import random

current_student_id = None  # Declare current_student_id as a global variable


def broadcast_student_id():
    """Simulates a beacon broadcasting a student ID."""
    global current_student_id  # Use the global keyword to modify the global variable
    current_student_id = random.randint(1000, 9999)  # Simulate a student ID
    print(f"Beacon broadcasting student ID: {current_student_id}")
    return current_student_id


if __name__ == "__main__":
    while True:
        broadcast_student_id()  # Call the function to update the global variable
        time.sleep(5)  # Simulate broadcasting every 5 seconds
