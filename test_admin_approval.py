import requests
import sys
import json
import time
import subprocess

class AdminApprovalSystemTester:
    def __init__(self, base_url="https://berkai-companion.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_users = []  # Track created test users
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
            self.failed_tests.append({"test": name, "error": details})

    def run_api_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.admin_token:
            test_headers['Authorization'] = f'Bearer {self.admin_token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=30)

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

    def setup_admin_session(self):
        """Login as admin to get admin token"""
        print("\n🔐 Setting up admin session...")
        
        # Create admin session directly in MongoDB
        admin_token = f"admin_test_session_{int(time.time())}"
        
        mongo_script = f"""
        use('berkai_database');
        db.admin_sessions.insertOne({{
          session_token: '{admin_token}',
          email: 'admin@berkai.com',
          expires_at: new Date(Date.now() + 24*60*60*1000),
          created_at: new Date()
        }});
        print('Admin session created');
        """
        
        try:
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.admin_token = admin_token
                print(f"✅ Admin session created: {admin_token}")
                return True
            else:
                print(f"❌ Admin session setup failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Admin session error: {str(e)}")
            return False

    def create_test_user(self, user_type, email_suffix):
        """Create a test user directly in MongoDB"""
        user_id = f"test-{user_type}-{int(time.time())}-{email_suffix}"
        email = f"test.{user_type}.{email_suffix}@example.com"
        
        # Determine account status based on user type
        account_status = "pending" if user_type in ["doctor", "psychiatrist"] else "approved"
        
        mongo_script = f"""
        use('berkai_database');
        db.users.insertOne({{
          _id: '{user_id}',
          email: '{email}',
          name: 'Test {user_type.title()} {email_suffix}',
          picture: 'https://via.placeholder.com/150',
          user_type: '{user_type}',
          account_status: '{account_status}',
          status_updated_by: null,
          status_updated_at: null,
          rejection_reason: null,
          user_id_number: 'BRK{int(time.time())}{email_suffix}',
          license_number: 'LIC{int(time.time())}{email_suffix}',
          specialization: 'Test Specialization',
          assigned_patients: [],
          assigned_doctor_id: null,
          therapy_approach: 'general',
          created_at: new Date()
        }});
        print('Test user created: {user_id}');
        """
        
        try:
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.test_users.append(user_id)
                print(f"✅ Created test {user_type}: {email}")
                return user_id, email
            else:
                print(f"❌ Failed to create test {user_type}: {result.stderr}")
                return None, None
        except Exception as e:
            print(f"❌ Test user creation error: {str(e)}")
            return None, None

    def test_get_pending_users(self):
        """Test admin endpoint to get pending users"""
        print("\n📋 Testing Get Pending Users...")
        
        # Create multiple pending users
        doctor_id, _ = self.create_test_user("doctor", "pending1")
        psychiatrist_id, _ = self.create_test_user("psychiatrist", "pending1")
        patient_id, _ = self.create_test_user("patient", "approved1")  # Should not appear in pending list
        
        # Get pending users
        success, response = self.run_api_test(
            "Get pending users",
            "GET",
            "admin/pending-users",
            200
        )
        
        if success and isinstance(response, list):
            # Check if only doctors and psychiatrists with pending status are returned
            pending_user_ids = [user.get("id") for user in response]
            
            doctor_in_list = doctor_id in pending_user_ids
            psychiatrist_in_list = psychiatrist_id in pending_user_ids
            patient_in_list = patient_id in pending_user_ids
            
            if doctor_in_list and psychiatrist_in_list:
                self.log_test("Pending doctors/psychiatrists listed", True, "Both doctor and psychiatrist in pending list")
            else:
                self.log_test("Pending doctors/psychiatrists listed", False, f"Doctor: {doctor_in_list}, Psychiatrist: {psychiatrist_in_list}")
            
            if not patient_in_list:
                self.log_test("Patients excluded from pending list", True, "Patient not in pending list")
            else:
                self.log_test("Patients excluded from pending list", False, "Patient should not be in pending list")
        
        return doctor_id, psychiatrist_id

    def test_admin_approve_user(self):
        """Test admin approval of pending user"""
        print("\n✅ Testing Admin User Approval...")
        
        # Create pending doctor
        doctor_id, doctor_email = self.create_test_user("doctor", "approve1")
        if not doctor_id:
            return False
        
        # Approve the doctor
        success, response = self.run_api_test(
            "Admin approve doctor",
            "POST",
            f"admin/approve-user/{doctor_id}",
            200
        )
        
        if success:
            # Verify user status was updated in database
            mongo_script = f"""
            use('berkai_database');
            const user = db.users.findOne({{_id: '{doctor_id}'}});
            if (user) {{
                print('STATUS:' + user.account_status);
                print('UPDATED_BY:' + (user.status_updated_by || 'null'));
                print('UPDATED_AT:' + (user.status_updated_at ? 'set' : 'null'));
            }} else {{
                print('USER_NOT_FOUND');
            }}
            """
            
            try:
                result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                      capture_output=True, text=True, timeout=30)
                
                output = result.stdout
                if "STATUS:approved" in output:
                    self.log_test("User status updated to approved", True, "Account status changed to approved")
                else:
                    self.log_test("User status updated to approved", False, "Account status not updated")
                
                if "UPDATED_BY:" in output and "null" not in output.split("UPDATED_BY:")[1].split("\n")[0]:
                    self.log_test("Status updated by admin tracked", True, "Admin ID recorded")
                else:
                    self.log_test("Status updated by admin tracked", False, "Admin ID not recorded")
                
                if "UPDATED_AT:set" in output:
                    self.log_test("Status update timestamp recorded", True, "Timestamp recorded")
                else:
                    self.log_test("Status update timestamp recorded", False, "Timestamp not recorded")
                    
            except Exception as e:
                self.log_test("Database verification after approval", False, f"Verification failed: {str(e)}")
        
        return doctor_id

    def test_admin_reject_user(self):
        """Test admin rejection of pending user"""
        print("\n❌ Testing Admin User Rejection...")
        
        # Create pending psychiatrist
        psychiatrist_id, psychiatrist_email = self.create_test_user("psychiatrist", "reject1")
        if not psychiatrist_id:
            return False
        
        rejection_reason = "Yetersiz bilgi sağlandı"
        
        # Reject the psychiatrist
        success, response = self.run_api_test(
            "Admin reject psychiatrist",
            "POST",
            f"admin/reject-user/{psychiatrist_id}",
            200,
            data={"reason": rejection_reason}
        )
        
        if success:
            # Verify user status and rejection reason in database
            mongo_script = f"""
            use('berkai_database');
            const user = db.users.findOne({{_id: '{psychiatrist_id}'}});
            if (user) {{
                print('STATUS:' + user.account_status);
                print('REJECTION_REASON:' + (user.rejection_reason || 'null'));
                print('UPDATED_BY:' + (user.status_updated_by || 'null'));
            }} else {{
                print('USER_NOT_FOUND');
            }}
            """
            
            try:
                result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                      capture_output=True, text=True, timeout=30)
                
                output = result.stdout
                if "STATUS:rejected" in output:
                    self.log_test("User status updated to rejected", True, "Account status changed to rejected")
                else:
                    self.log_test("User status updated to rejected", False, "Account status not updated")
                
                if f"REJECTION_REASON:{rejection_reason}" in output:
                    self.log_test("Rejection reason saved", True, "Rejection reason recorded correctly")
                else:
                    self.log_test("Rejection reason saved", False, "Rejection reason not saved")
                    
            except Exception as e:
                self.log_test("Database verification after rejection", False, f"Verification failed: {str(e)}")
        
        return psychiatrist_id

    def cleanup_test_data(self):
        """Clean up all test data"""
        print("\n🧹 Cleaning up admin approval test data...")
        
        if self.test_users:
            user_ids = "', '".join(self.test_users)
            mongo_script = f"""
            use('berkai_database');
            db.users.deleteMany({{_id: {{$in: ['{user_ids}']}}}});
            db.user_sessions.deleteMany({{user_id: {{$in: ['{user_ids}']}}}});
            """
            
            if self.admin_token:
                mongo_script += f"""
                db.admin_sessions.deleteMany({{session_token: '{self.admin_token}'}});
                """
            
            mongo_script += "print('Admin approval test data cleaned up');"
            
            try:
                subprocess.run(['mongosh', '--eval', mongo_script], 
                             capture_output=True, text=True, timeout=30)
                print("✅ Admin approval test data cleaned up")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {str(e)}")

    def run_all_tests(self):
        """Run all admin approval system tests"""
        print("🚀 Starting Admin Approval System Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: Doctor/psychiatrist approval workflow, admin endpoints, status management")
        
        # Setup admin session
        if not self.setup_admin_session():
            print("❌ Cannot proceed without admin session")
            return False
        
        try:
            print("\n" + "="*60)
            print("👨‍⚕️ ADMIN APPROVAL SYSTEM TESTS")
            print("="*60)
            
            # Test 1: Get Pending Users
            self.test_get_pending_users()
            
            # Test 2: Admin Approve User
            self.test_admin_approve_user()
            
            # Test 3: Admin Reject User
            self.test_admin_reject_user()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print detailed summary
        print(f"\n" + "="*60)
        print(f"📊 ADMIN APPROVAL SYSTEM TEST SUMMARY")
        print(f"="*60)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {len(self.failed_tests)}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print(f"Test users created: {len(self.test_users)}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['error']}")
        else:
            print(f"\n✅ All tests passed! Admin approval system is working correctly.")
        
        return len(self.failed_tests) == 0

def main():
    tester = AdminApprovalSystemTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())