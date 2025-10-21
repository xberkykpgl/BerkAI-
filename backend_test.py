import requests
import sys
import json
import base64
from datetime import datetime
import time

class BerkAIAPITester:
    def __init__(self, base_url="https://berkaihealth.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.test_session_id = None
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
        
        if self.session_token:
            test_headers['Authorization'] = f'Bearer {self.session_token}'
        
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

    def setup_test_user(self):
        """Create test user and session using MongoDB directly"""
        print("\n🔧 Setting up test user...")
        
        # Create test user data
        test_user_id = f"test-user-{int(time.time())}"
        test_email = f"test.user.{int(time.time())}@example.com"
        self.session_token = f"test_session_{int(time.time())}"
        
        # Use mongosh to create test data
        mongo_script = f"""
        use('berkai_database');
        db.users.insertOne({{
          _id: '{test_user_id}',
          email: '{test_email}',
          name: 'Test User',
          picture: 'https://via.placeholder.com/150',
          created_at: new Date()
        }});
        db.user_sessions.insertOne({{
          user_id: '{test_user_id}',
          session_token: '{self.session_token}',
          expires_at: new Date(Date.now() + 7*24*60*60*1000),
          created_at: new Date()
        }});
        print('Test user created successfully');
        """
        
        import subprocess
        try:
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.user_id = test_user_id
                print(f"✅ Test user created: {test_email}")
                print(f"✅ Session token: {self.session_token}")
                return True
            else:
                print(f"❌ MongoDB setup failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ MongoDB setup error: {str(e)}")
            return False

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication...")
        
        # Test /auth/me with valid token
        self.run_api_test(
            "Get current user",
            "GET",
            "auth/me",
            200
        )
        
        # Test /auth/me without token
        temp_token = self.session_token
        self.session_token = None
        self.run_api_test(
            "Get current user (no auth)",
            "GET", 
            "auth/me",
            401
        )
        self.session_token = temp_token

    def test_session_endpoints(self):
        """Test therapy session endpoints"""
        print("\n🏥 Testing Session Management...")
        
        # Get user sessions
        success, sessions = self.run_api_test(
            "Get user sessions",
            "GET",
            "sessions",
            200
        )
        
        # Create new session
        success, session_data = self.run_api_test(
            "Create therapy session",
            "POST",
            "sessions?session_name=Test Session",
            200
        )
        
        if success and 'id' in session_data:
            self.test_session_id = session_data['id']
            print(f"📝 Created test session: {self.test_session_id}")
            
            # Get specific session
            self.run_api_test(
                "Get specific session",
                "GET",
                f"sessions/{self.test_session_id}",
                200
            )
            
            # Complete session
            self.run_api_test(
                "Complete session",
                "PATCH",
                f"sessions/{self.test_session_id}/complete",
                200,
                data={"analysis_summary": {"test": "completed"}}
            )

    def test_message_endpoints(self):
        """Test messaging and chat endpoints"""
        print("\n💬 Testing Chat & Messaging...")
        
        if not self.test_session_id:
            print("⚠️ Skipping message tests - no session ID")
            return
        
        # Get session messages (should be empty initially)
        self.run_api_test(
            "Get session messages",
            "GET",
            f"sessions/{self.test_session_id}/messages",
            200
        )
        
        # Send chat message (this will test GPT-5 integration)
        print("🤖 Testing GPT-5 integration...")
        success, response = self.run_api_test(
            "Send chat message",
            "POST",
            f"sessions/{self.test_session_id}/chat",
            200,
            data={
                "message": "Merhaba, nasılsın? Bu bir test mesajıdır.",
                "video_frame": None
            }
        )
        
        if success:
            if 'message' in response and response['message']:
                print(f"✅ GPT-5 Response received: {response['message'][:100]}...")
            else:
                self.log_test("GPT-5 response content", False, "No message in response")

    def test_video_analysis(self):
        """Test video analysis with Gemini"""
        print("\n📹 Testing Video Analysis...")
        
        if not self.test_session_id:
            print("⚠️ Skipping video analysis - no session ID")
            return
        
        # Create a simple test image (1x1 pixel base64)
        test_image_b64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A"
        
        print("🔍 Testing Gemini Pro video analysis...")
        success, response = self.run_api_test(
            "Send message with video frame",
            "POST",
            f"sessions/{self.test_session_id}/chat",
            200,
            data={
                "message": "Bu görüntüyü analiz edebilir misin?",
                "video_frame": test_image_b64
            }
        )
        
        if success:
            if 'video_analysis' in response and response['video_analysis']:
                print(f"✅ Gemini analysis received: {json.dumps(response['video_analysis'], indent=2)}")
            else:
                self.log_test("Gemini video analysis", False, "No video_analysis in response")

    def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        print("\n📊 Testing Analytics...")
        
        if not self.test_session_id:
            print("⚠️ Skipping analytics - no session ID")
            return
        
        # Get session analytics
        success, analytics = self.run_api_test(
            "Get session analytics",
            "GET",
            f"sessions/{self.test_session_id}/analytics",
            200
        )
        
        if success:
            print(f"📈 Analytics data: {json.dumps(analytics, indent=2)}")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        if self.user_id:
            mongo_script = f"""
            use('berkai_database');
            db.users.deleteOne({{_id: '{self.user_id}'}});
            db.user_sessions.deleteMany({{user_id: '{self.user_id}'}});
            db.therapy_sessions.deleteMany({{user_id: '{self.user_id}'}});
            db.messages.deleteMany({{user_id: '{self.user_id}'}});
            db.video_analyses.deleteMany({{user_id: '{self.user_id}'}});
            print('Test data cleaned up');
            """
            
            import subprocess
            try:
                subprocess.run(['mongosh', '--eval', mongo_script], 
                             capture_output=True, text=True, timeout=30)
                print("✅ Test data cleaned up")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting BerkAI Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        
        # Setup
        if not self.setup_test_user():
            print("❌ Cannot proceed without test user setup")
            return False
        
        try:
            # Run all test suites
            self.test_auth_endpoints()
            self.test_session_endpoints()
            self.test_message_endpoints()
            self.test_video_analysis()
            self.test_analytics_endpoints()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print summary
        print(f"\n📊 Test Summary:")
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
    tester = BerkAIAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())