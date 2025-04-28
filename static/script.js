document.addEventListener('DOMContentLoaded', () => {
  console.log('JavaScript is Running!');
  const studentList = document.getElementById('studentList');
  const webcamVideo = document.getElementById('webcamVideo');
  const webcamCanvas = document.getElementById('webcamCanvas');
  const captureContext = webcamCanvas.getContext('2d');
  const beaconStatus = document.getElementById('beacon-status');
  const studentIdInput = document.getElementById('studentIdInput'); // Get the ID input field (assuming you've added this to your HTML)
  const scanFaceButton = document.querySelector('.scan-face-button'); // Get the scan button (using class in case of multiple buttons)
  const verificationStatus = document.getElementById('verificationStatus'); // Get the status display (assuming you've added this to your HTML)

  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      webcamVideo.srcObject = stream;
    })
    .catch(error => {
      console.error("Error accessing webcam:", error);
      alert("Unable to access webcam. Please ensure permissions are granted.");
    });

  fetch('/students_list') // New Flask endpoint to get student data
    .then(response => response.json())
    .then(students => {
      students.forEach(student => {
        const listItem = document.createElement('li');
        listItem.dataset.studentId = student.id;

        const nameSpan = document.createElement('span');
        nameSpan.textContent = student.name; // Assuming 'name' for now

        const scanButton = document.createElement('button');
        scanButton.className = 'scan-face-button';
        scanButton.dataset.studentId = student.id;
        scanButton.textContent = 'Scan Face';

        const statusSpan = document.createElement('span');
        statusSpan.className = 'attendance-status';
        statusSpan.id = `status-${student.id}`; // Corrected line: template literal

        listItem.appendChild(nameSpan);
        listItem.appendChild(scanButton);
        listItem.appendChild(statusSpan);

        studentList.appendChild(listItem);
      });
      attachScanFaceListeners();
    })
    .catch(error => {
      console.error("Error fetching student list:", error);
      alert("Could not load the list of students.");
    });

  function attachScanFaceListeners() {
    const scanFaceButtons = document.querySelectorAll('.scan-face-button');
    scanFaceButtons.forEach(button => {
      button.addEventListener('click', function() {
        const studentId = this.dataset.studentId;
        const currentStudentIdInput = studentIdInput ? studentIdInput.value : studentId; // Use input if available, else fallback
        beaconStatus.textContent = "Scanning for beacon...";
        verificationStatus.textContent = ""; // Clear previous status

        fetch('/verify_face', {
          method: 'POST',
          body: new FormData() // Initial beacon check doesn't need image or ID
        })
        .then(response => response.json())
        .then(data => {
          beaconStatus.textContent = data.message;
          if (data.success) {
            captureContext.drawImage(webcamVideo, 0, 0, webcamCanvas.width, webcamCanvas.height);
            webcamCanvas.toBlob(blob => {
              const formData = new FormData();
              formData.append('webcamImage', blob, 'face.jpg');
              formData.append('student_id', currentStudentIdInput); // Send the entered student ID

              fetch('/verify_face', {
                method: 'POST',
                body: formData
              })
              .then(response => response.json())
              .then(faceData => {
                const statusSpan = document.getElementById(`status-${studentId}`); // Corrected line: template literal
                if (faceData.success) {

statusSpan.textContent = '✅'; // Tick mark
                  verificationStatus.textContent = 'Attendance recorded.';
                  button.disabled = true; // Disable button after successful attendance
                  fetchAttendanceRecords(); // Update the attendance table
                } else {
                  alert('Face verification failed: ' + faceData.message);
                  verificationStatus.textContent = 'Verification failed: ' + faceData.message;
                }
              })
              .catch(error => {
                console.error('Error verifying face:', error);
                alert('Error verifying face.');
                verificationStatus.textContent = 'Verification error.';
              });
            }, 'image/jpeg');
          } else {
            console.error('Beacon not found:', data.message);
            verificationStatus.textContent = 'Beacon not found: ' + data.message;
          }
        })
        .catch(error => {
          beaconStatus.textContent = "Error checking beacon.";
          console.error('Error checking beacon:', error);
          verificationStatus.textContent = 'Beacon check error.';
        });
      });
    });
  }

  function updateLiveLogs() {
    fetch('/live_records')
      .then(response => response.json())
      .then(data => {
        const liveLogsDiv = document.getElementById('live-attendance-logs-content');
        liveLogsDiv.innerHTML = ''; // Clear previous logs

        if (data && data.length > 0) {
          const ul = document.createElement('ul');
          data.forEach(record => {
            const li = document.createElement('li');
            li.textContent = `${record.name} - ${record.timestamp}`; // Corrected line: template literal
            ul.appendChild(li);
          });
          liveLogsDiv.appendChild(ul);
        } else {
          liveLogsDiv.textContent = 'No recent attendance.';
        }
      })
      .catch(error => {
        console.error("Error fetching live attendance logs:", error);
      });
  }

  // Call it initially
  updateLiveLogs();

  // Update every 3 seconds (adjust as needed)
  setInterval(updateLiveLogs, 3000);

  function fetchAttendanceRecords() {
    const attendanceTable = document.getElementById("attendanceTable");
    fetch("/records")
      .then(response => response.json())
      .then(data => {
        if (attendanceTable) {
          const tbody = attendanceTable.querySelector('tbody');
          tbody.innerHTML = ''; // Clear existing rows
          data.forEach(record => {
            const row = tbody.insertRow();
            const nameCell = row.insertCell();
            const timestampCell = row.insertCell();
            nameCell.textContent = record.name; // Assuming 'name' in records now
            timestampCell.textContent = record.timestamp;
          });
        } else {
          console.error("attendanceTable element not found.");
        }
      })
      .catch(error => console.error("Error fetching attendance records:", error));
  }

  // Fetch initial attendance records
  fetchAttendanceRecords();
});