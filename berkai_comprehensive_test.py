import requests
import sys
import json
import time
import subprocess
from datetime import datetime

class BerkAIComprehensiveTest:
    def __init__(self, base_url="https://berkaihealth.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Test users for different types
        self.patient_token = None
        self.patient_id = None
        self.patient_id_number = None
        
        self.doctor_token = None
        self.doctor_id = None
        
        self.psychiatrist_token = None
        self.psychiatrist_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
            self.failed_tests.append({"test": name, "error": details})

    def run_api_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Expected {expected_status}, got {response.status_code}"
            
            if not success:
                try:
                    error_detail = response.json()
                    details += f" - {error_detail}"
                except:
                    details += f" - {response.text[:200]}"
            
            self.log_test(name, success, details if not success else "")
            
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def setup_test_users(self):
        """Create test users for all user types"""
        print("\n🔧 Setting up test users (Patient, Doctor, Psychiatrist)...")
        
        timestamp = int(time.time())
        
        # Patient user
        patient_email = f"patient.{timestamp}@test.com"
        self.patient_id = f"patient-{timestamp}"
        self.patient_token = f"patient_session_{timestamp}"
        self.patient_id_number = f"BRK{timestamp}"
        
        # Doctor user  
        doctor_email = f"doctor.{timestamp}@test.com"
        self.doctor_id = f"doctor-{timestamp}"
        self.doctor_token = f"doctor_session_{timestamp}"
        
        # Psychiatrist user
        psychiatrist_email = f"psychiatrist.{timestamp}@test.com"
        self.psychiatrist_id = f"psychiatrist-{timestamp}"
        self.psychiatrist_token = f"psychiatrist_session_{timestamp}"
        
        mongo_script = f"""
        use('berkai_database');
        
        // Create Patient
        db.users.insertOne({{
          _id: '{self.patient_id}',
          email: '{patient_email}',
          name: 'Test Patient',
          picture: 'https://via.placeholder.com/150',
          user_type: 'patient',
          user_id_number: '{self.patient_id_number}',
          assigned_patients: [],
          therapy_approach: 'general',
          created_at: new Date()
        }});
        
        db.user_sessions.insertOne({{
          user_id: '{self.patient_id}',
          session_token: '{self.patient_token}',
          expires_at: new Date(Date.now() + 7*24*60*60*1000),
          created_at: new Date()
        }});
        
        // Create Doctor
        db.users.insertOne({{
          _id: '{self.doctor_id}',
          email: '{doctor_email}',
          name: 'Test Doctor',
          picture: 'https://via.placeholder.com/150',
          user_type: 'doctor',
          user_id_number: 'DOC{timestamp}',
          assigned_patients: [],
          license_number: 'LIC123456',
          specialization: 'Clinical Psychology',
          therapy_approach: 'CBT',
          created_at: new Date()
        }});
        
        db.user_sessions.insertOne({{
          user_id: '{self.doctor_id}',
          session_token: '{self.doctor_token}',
          expires_at: new Date(Date.now() + 7*24*60*60*1000),
          created_at: new Date()
        }});
        
        // Create Psychiatrist
        db.users.insertOne({{
          _id: '{self.psychiatrist_id}',
          email: '{psychiatrist_email}',
          name: 'Test Psychiatrist',
          picture: 'https://via.placeholder.com/150',
          user_type: 'psychiatrist',
          user_id_number: 'PSY{timestamp}',
          assigned_patients: [],
          license_number: 'PSY789012',
          specialization: 'Psychiatry',
          therapy_approach: 'DBT',
          created_at: new Date()
        }});
        
        db.user_sessions.insertOne({{
          user_id: '{self.psychiatrist_id}',
          session_token: '{self.psychiatrist_token}',
          expires_at: new Date(Date.now() + 7*24*60*60*1000),
          created_at: new Date()
        }});
        
        print('All test users created successfully');
        """
        
        try:
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ Patient created: {patient_email} (ID: {self.patient_id_number})")
                print(f"✅ Doctor created: {doctor_email}")
                print(f"✅ Psychiatrist created: {psychiatrist_email}")
                return True
            else:
                print(f"❌ MongoDB setup failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ MongoDB setup error: {str(e)}")
            return False

    def test_patient_features(self):
        """Test patient-specific features"""
        print("\n👤 Testing Patient Features...")
        
        # Test patient can access their own data
        success, user_data = self.run_api_test(
            "Patient - Get own profile",
            "GET",
            "auth/me",
            200,
            token=self.patient_token
        )
        
        if success:
            if user_data.get('user_type') == 'patient':
                print(f"✅ Patient user type confirmed: {user_data.get('user_type')}")
                print(f"✅ Patient ID number: {user_data.get('user_id_number')}")
            else:
                self.log_test("Patient user type verification", False, f"Expected 'patient', got '{user_data.get('user_type')}'")
        
        # Test patient can create sessions
        success, session_data = self.run_api_test(
            "Patient - Create therapy session",
            "POST",
            "sessions?session_name=Patient Test Session",
            200,
            token=self.patient_token
        )
        
        if success and 'id' in session_data:
            session_id = session_data['id']
            print(f"📝 Patient session created: {session_id}")
            
            # Test patient can send messages
            success, chat_response = self.run_api_test(
                "Patient - Send chat message",
                "POST",
                f"sessions/{session_id}/chat",
                200,
                data={"message": "Merhaba, bugün kendimi çok kötü hissediyorum."},
                token=self.patient_token
            )
            
            if success and 'risk_assessment' in chat_response:
                risk = chat_response['risk_assessment']
                print(f"🔍 Risk assessment: Level {risk.get('risk_level')}, Category: {risk.get('risk_category')}")
                
                # Test high-risk message
                success, high_risk_response = self.run_api_test(
                    "Patient - Send high-risk message",
                    "POST",
                    f"sessions/{session_id}/chat",
                    200,
                    data={"message": "Artık yaşamak istemiyorum, intihar etmeyi düşünüyorum."},
                    token=self.patient_token
                )
                
                if success and 'risk_assessment' in high_risk_response:
                    high_risk = high_risk_response['risk_assessment']
                    print(f"🚨 High-risk assessment: Level {high_risk.get('risk_level')}, Category: {high_risk.get('risk_category')}")
                    if high_risk.get('suicide_risk'):
                        print("✅ Suicide risk detected correctly")
                    else:
                        self.log_test("Suicide risk detection", False, "Suicide risk not detected for high-risk message")

    def test_doctor_features(self):
        """Test doctor-specific features"""
        print("\n👨‍⚕️ Testing Doctor Features...")
        
        # Test doctor can access their profile
        success, doctor_data = self.run_api_test(
            "Doctor - Get own profile",
            "GET",
            "auth/me",
            200,
            token=self.doctor_token
        )
        
        if success:
            if doctor_data.get('user_type') == 'doctor':
                print(f"✅ Doctor user type confirmed: {doctor_data.get('user_type')}")
            else:
                self.log_test("Doctor user type verification", False, f"Expected 'doctor', got '{doctor_data.get('user_type')}'")
        
        # Test doctor can view patients (should be empty initially)
        success, patients = self.run_api_test(
            "Doctor - Get assigned patients",
            "GET",
            "doctor/patients",
            200,
            token=self.doctor_token
        )
        
        if success:
            print(f"📋 Doctor has {len(patients)} assigned patients")
        
        # Test doctor can add patient by ID
        success, add_result = self.run_api_test(
            "Doctor - Add patient by ID",
            "POST",
            "doctor/add-patient",
            200,
            data={"patient_id_number": self.patient_id_number},
            token=self.doctor_token
        )
        
        if success:
            print(f"✅ Patient {self.patient_id_number} added to doctor")
            
            # Test doctor can now see the patient
            success, patients_after = self.run_api_test(
                "Doctor - Get patients after adding",
                "GET",
                "doctor/patients",
                200,
                token=self.doctor_token
            )
            
            if success and len(patients_after) > 0:
                print(f"✅ Doctor now has {len(patients_after)} assigned patients")
                patient = patients_after[0]
                print(f"📋 Patient details: {patient.get('name')} (ID: {patient.get('user_id_number')})")
                
                # Test doctor can view patient risk alerts
                success, risk_alerts = self.run_api_test(
                    "Doctor - Get patient risk alerts",
                    "GET",
                    f"doctor/patient/{self.patient_id}/risk-alerts",
                    200,
                    token=self.doctor_token
                )
                
                if success:
                    print(f"🚨 Found {len(risk_alerts)} risk alerts for patient")
                
                # Test doctor can add clinical notes
                success, note_result = self.run_api_test(
                    "Doctor - Add clinical note",
                    "POST",
                    f"doctor/patient/{self.patient_id}/note",
                    200,
                    data={
                        "content": "Patient shows signs of depression. Recommended CBT sessions.",
                        "note_type": "clinical_note",
                        "tags": ["depression", "CBT"]
                    },
                    token=self.doctor_token
                )
                
                if success:
                    print("✅ Clinical note added successfully")
                    
                    # Test doctor can retrieve notes
                    success, notes = self.run_api_test(
                        "Doctor - Get patient notes",
                        "GET",
                        f"doctor/patient/{self.patient_id}/notes",
                        200,
                        token=self.doctor_token
                    )
                    
                    if success:
                        print(f"📝 Retrieved {len(notes)} clinical notes")

    def test_psychiatrist_features(self):
        """Test psychiatrist-specific features (should be same as doctor)"""
        print("\n🧠 Testing Psychiatrist Features...")
        
        # Test psychiatrist can access their profile
        success, psychiatrist_data = self.run_api_test(
            "Psychiatrist - Get own profile",
            "GET",
            "auth/me",
            200,
            token=self.psychiatrist_token
        )
        
        if success:
            if psychiatrist_data.get('user_type') == 'psychiatrist':
                print(f"✅ Psychiatrist user type confirmed: {psychiatrist_data.get('user_type')}")
            else:
                self.log_test("Psychiatrist user type verification", False, f"Expected 'psychiatrist', got '{psychiatrist_data.get('user_type')}'")
        
        # Test psychiatrist can add patient (same as doctor)
        success, add_result = self.run_api_test(
            "Psychiatrist - Add patient by ID",
            "POST",
            "doctor/add-patient",
            200,
            data={"patient_id_number": self.patient_id_number},
            token=self.psychiatrist_token
        )
        
        if success:
            print(f"✅ Patient {self.patient_id_number} added to psychiatrist")
            
            # Test psychiatrist can add clinical notes
            success, note_result = self.run_api_test(
                "Psychiatrist - Add clinical note",
                "POST",
                f"doctor/patient/{self.patient_id}/note",
                200,
                data={
                    "content": "Patient requires medication evaluation. Considering antidepressants.",
                    "note_type": "clinical_note",
                    "tags": ["medication", "evaluation"]
                },
                token=self.psychiatrist_token
            )
            
            if success:
                print("✅ Psychiatrist clinical note added successfully")

    def test_access_control(self):
        """Test access control between user types"""
        print("\n🔒 Testing Access Control...")
        
        # Test patient cannot access doctor endpoints
        success, _ = self.run_api_test(
            "Patient - Cannot access doctor patients",
            "GET",
            "doctor/patients",
            403,
            token=self.patient_token
        )
        
        # Test patient cannot add other patients
        success, _ = self.run_api_test(
            "Patient - Cannot add patients",
            "POST",
            "doctor/add-patient",
            403,
            data={"patient_id_number": "BRK12345678"},
            token=self.patient_token
        )
        
        # Test doctor cannot access unassigned patient
        fake_patient_id = "fake-patient-id"
        success, _ = self.run_api_test(
            "Doctor - Cannot access unassigned patient",
            "GET",
            f"doctor/patient/{fake_patient_id}/risk-alerts",
            403,
            token=self.doctor_token
        )

    def cleanup_test_data(self):
        """Clean up all test data"""
        print("\n🧹 Cleaning up test data...")
        
        mongo_script = f"""
        use('berkai_database');
        
        // Clean up all test users and related data
        db.users.deleteMany({{_id: {{$in: ['{self.patient_id}', '{self.doctor_id}', '{self.psychiatrist_id}']}}}});
        db.user_sessions.deleteMany({{user_id: {{$in: ['{self.patient_id}', '{self.doctor_id}', '{self.psychiatrist_id}']}}}});
        db.therapy_sessions.deleteMany({{user_id: {{$in: ['{self.patient_id}', '{self.doctor_id}', '{self.psychiatrist_id}']}}}});
        db.messages.deleteMany({{user_id: {{$in: ['{self.patient_id}', '{self.doctor_id}', '{self.psychiatrist_id}']}}}});
        db.risk_assessments.deleteMany({{user_id: {{$in: ['{self.patient_id}', '{self.doctor_id}', '{self.psychiatrist_id}']}}}});
        db.doctor_notes.deleteMany({{patient_id: '{self.patient_id}'}});
        db.video_analyses.deleteMany({{user_id: {{$in: ['{self.patient_id}', '{self.doctor_id}', '{self.psychiatrist_id}']}}}});
        
        print('All test data cleaned up');
        """
        
        try:
            subprocess.run(['mongosh', '--eval', mongo_script], 
                         capture_output=True, text=True, timeout=30)
            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")

    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting BerkAI Comprehensive Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("📋 Testing Features: User Types, Patient Management, Risk Assessment, Clinical Notes")
        
        # Setup
        if not self.setup_test_users():
            print("❌ Cannot proceed without test user setup")
            return False
        
        try:
            # Run all test suites
            self.test_patient_features()
            self.test_doctor_features()
            self.test_psychiatrist_features()
            self.test_access_control()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print summary
        print(f"\n📊 Comprehensive Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {len(self.failed_tests)}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['error']}")
        
        return len(self.failed_tests) == 0

def main():
    tester = BerkAIComprehensiveTest()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())