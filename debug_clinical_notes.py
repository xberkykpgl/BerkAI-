import requests
import subprocess
import time

# Create a simple test
timestamp = int(time.time())
doctor_id = f"debug-doctor-{timestamp}"
patient_id = f"debug-patient-{timestamp}"
doctor_token = f"debug_doctor_session_{timestamp}"
patient_id_number = f"BRK{timestamp}"

print("Creating test users...")

mongo_script = f"""
use('berkai_database');

// Create Patient
db.users.insertOne({{
  _id: '{patient_id}',
  email: 'debug.patient.{timestamp}@test.com',
  name: 'Debug Patient',
  user_type: 'patient',
  user_id_number: '{patient_id_number}',
  assigned_patients: [],
  created_at: new Date()
}});

// Create Doctor
db.users.insertOne({{
  _id: '{doctor_id}',
  email: 'debug.doctor.{timestamp}@test.com',
  name: 'Debug Doctor',
  user_type: 'doctor',
  user_id_number: 'DOC{timestamp}',
  assigned_patients: ['{patient_id}'],
  created_at: new Date()
}});

db.user_sessions.insertOne({{
  user_id: '{doctor_id}',
  session_token: '{doctor_token}',
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
}});

print('Debug users created');
"""

result = subprocess.run(['mongosh', '--eval', mongo_script], 
                      capture_output=True, text=True, timeout=30)

if result.returncode == 0:
    print("✅ Debug users created")
    
    # Test the clinical note endpoint
    url = f"https://berkaihealth.preview.emergentagent.com/api/doctor/patient/{patient_id}/note"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {doctor_token}'
    }
    data = {
        "content": "Debug clinical note",
        "note_type": "clinical_note",
        "tags": ["debug"]
    }
    
    print(f"Testing clinical note endpoint: {url}")
    response = requests.post(url, json=data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Cleanup
    cleanup_script = f"""
    use('berkai_database');
    db.users.deleteMany({{_id: {{$in: ['{patient_id}', '{doctor_id}']}}}});
    db.user_sessions.deleteMany({{user_id: '{doctor_id}'}});
    db.doctor_notes.deleteMany({{patient_id: '{patient_id}'}});
    print('Cleanup done');
    """
    
    subprocess.run(['mongosh', '--eval', cleanup_script], 
                  capture_output=True, text=True, timeout=30)
    print("✅ Cleanup done")
    
else:
    print(f"❌ Failed to create debug users: {result.stderr}")