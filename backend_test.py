import requests
import sys
import json
import base64
from datetime import datetime
import time
import subprocess

class BerkAIRAGMemoryTester:
    def __init__(self, base_url="https://berkai-companion.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.test_sessions = []  # Track multiple sessions
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.session_summaries = []  # Track generated summaries

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

    def test_session_summary_generation(self):
        """Test Session Summary Generation with AI"""
        print("\n🧠 Testing Session Summary Generation...")
        
        # Create new session for work stress conversation
        success, session_data = self.run_api_test(
            "Create work stress session",
            "POST",
            "sessions?session_name=Work Stress Session",
            200
        )
        
        if not success or 'id' not in session_data:
            self.log_test("Session creation for summary test", False, "Failed to create session")
            return
        
        session_id = session_data['id']
        self.test_sessions.append(session_id)
        print(f"📝 Created work stress session: {session_id}")
        
        # Have a conversation about work stress (5-6 messages)
        work_messages = [
            "Merhaba, işte çok stresli bir dönem geçiriyorum.",
            "Patronum sürekli fazla mesai istiyor ve bu beni çok yoruyor.",
            "Evde de bu stresi yaşıyorum, ailemle vakit geçiremiyorum.",
            "Bazen işi bırakmayı düşünüyorum ama maddi durumum elvermez.",
            "Bu durumla nasıl başa çıkabilirim? Çok bunaldım.",
            "Uyku düzenim de bozuldu, sürekli endişeliyim."
        ]
        
        print("💬 Simulating work stress conversation...")
        for i, message in enumerate(work_messages):
            success, response = self.run_api_test(
                f"Work stress message {i+1}",
                "POST",
                f"sessions/{session_id}/chat",
                200,
                data={"message": message}
            )
            
            if success and 'message' in response:
                print(f"  User: {message[:50]}...")
                print(f"  AI: {response['message'][:80]}...")
            
            time.sleep(1)  # Brief pause between messages
        
        # Complete the session to trigger AI summary generation
        print("🔄 Completing session to generate AI summary...")
        success, complete_response = self.run_api_test(
            "Complete work stress session",
            "PATCH",
            f"sessions/{session_id}/complete",
            200,
            data={"analysis_summary": {"topic": "work_stress"}}
        )
        
        if success:
            summary_generated = complete_response.get('summary_generated', False)
            if summary_generated:
                print("✅ AI summary generation confirmed")
                
                # Verify summary was saved to user_profiles collection
                self.verify_user_profile_summary(session_id, "work stress")
            else:
                self.log_test("AI summary generation", False, "No summary generated flag")
        
        return session_id

    def test_multi_session_memory(self):
        """Test Multi-Session Memory System"""
        print("\n🔗 Testing Multi-Session Memory...")
        
        # First session already created in previous test (work stress)
        # Create second session for relationship issues
        success, session_data = self.run_api_test(
            "Create relationship session",
            "POST",
            "sessions?session_name=Relationship Issues Session",
            200
        )
        
        if not success or 'id' not in session_data:
            self.log_test("Second session creation", False, "Failed to create relationship session")
            return
        
        relationship_session_id = session_data['id']
        self.test_sessions.append(relationship_session_id)
        print(f"💕 Created relationship session: {relationship_session_id}")
        
        # Have conversation about relationship issues
        relationship_messages = [
            "Şimdi de ilişki problemlerimden bahsetmek istiyorum.",
            "Partnerimle iletişim kurmakta zorlanıyorum.",
            "O beni anlamıyor, ben de onu anlayamıyorum.",
            "Sürekli tartışıyoruz ve bu beni çok üzüyor.",
            "Bu durumu nasıl çözebiliriz?"
        ]
        
        print("💬 Simulating relationship conversation...")
        for i, message in enumerate(relationship_messages):
            success, response = self.run_api_test(
                f"Relationship message {i+1}",
                "POST",
                f"sessions/{relationship_session_id}/chat",
                200,
                data={"message": message}
            )
            
            if success and 'message' in response:
                print(f"  User: {message[:50]}...")
                print(f"  AI: {response['message'][:80]}...")
            
            time.sleep(1)
        
        # Complete relationship session
        print("🔄 Completing relationship session...")
        success, complete_response = self.run_api_test(
            "Complete relationship session",
            "PATCH",
            f"sessions/{relationship_session_id}/complete",
            200,
            data={"analysis_summary": {"topic": "relationship_issues"}}
        )
        
        if success and complete_response.get('summary_generated'):
            self.verify_user_profile_summary(relationship_session_id, "relationship")
        
        # Create third session to test memory recall
        success, session_data = self.run_api_test(
            "Create memory test session",
            "POST",
            "sessions?session_name=Memory Test Session",
            200
        )
        
        if not success or 'id' not in session_data:
            self.log_test("Memory test session creation", False, "Failed to create memory test session")
            return
        
        memory_test_session_id = session_data['id']
        self.test_sessions.append(memory_test_session_id)
        print(f"🧠 Created memory test session: {memory_test_session_id}")
        
        # Ask about previous conversations
        print("🔍 Testing memory recall...")
        success, response = self.run_api_test(
            "Memory recall test",
            "POST",
            f"sessions/{memory_test_session_id}/chat",
            200,
            data={"message": "Daha önce neler konuştuk? Geçmiş seanslarımızda hangi konuları ele aldık?"}
        )
        
        if success and 'message' in response:
            ai_response = response['message'].lower()
            print(f"🤖 AI Memory Response: {response['message'][:200]}...")
            
            # Check if AI remembers both work and relationship topics
            work_keywords = ['iş', 'stres', 'patron', 'mesai', 'çalış']
            relationship_keywords = ['ilişki', 'partner', 'tartış', 'iletişim']
            
            work_mentioned = any(keyword in ai_response for keyword in work_keywords)
            relationship_mentioned = any(keyword in ai_response for keyword in relationship_keywords)
            
            if work_mentioned and relationship_mentioned:
                self.log_test("Multi-session memory recall", True, "AI remembered both work and relationship topics")
            elif work_mentioned or relationship_mentioned:
                self.log_test("Multi-session memory recall", False, f"AI only remembered {'work' if work_mentioned else 'relationship'} topics")
            else:
                self.log_test("Multi-session memory recall", False, "AI did not recall previous session topics")
        
        return memory_test_session_id

    def test_profile_context_loading(self):
        """Test Profile Context Loading"""
        print("\n📋 Testing Profile Context Loading...")
        
        # Create a new session for user with existing profile
        success, session_data = self.run_api_test(
            "Create profile context test session",
            "POST",
            "sessions?session_name=Profile Context Test",
            200
        )
        
        if not success or 'id' not in session_data:
            self.log_test("Profile context session creation", False, "Failed to create session")
            return
        
        context_session_id = session_data['id']
        self.test_sessions.append(context_session_id)
        print(f"📝 Created profile context session: {context_session_id}")
        
        # Send first message to trigger profile loading
        success, response = self.run_api_test(
            "Profile context loading test",
            "POST",
            f"sessions/{context_session_id}/chat",
            200,
            data={"message": "Merhaba, bugün nasılsın?"}
        )
        
        if success and 'message' in response:
            ai_response = response['message'].lower()
            print(f"🤖 AI Response with Profile Context: {response['message'][:150]}...")
            
            # Check if response shows awareness of previous sessions
            context_indicators = ['önceki', 'geçen', 'daha önce', 'seanslar', 'konuştuk', 'bahset']
            has_context = any(indicator in ai_response for indicator in context_indicators)
            
            if has_context:
                self.log_test("Profile context awareness", True, "AI shows awareness of previous sessions")
            else:
                # This might be normal for a greeting, so we'll test with a more specific question
                success2, response2 = self.run_api_test(
                    "Specific context test",
                    "POST",
                    f"sessions/{context_session_id}/chat",
                    200,
                    data={"message": "Geçen seanslarımızda neler konuşmuştuk?"}
                )
                
                if success2 and 'message' in response2:
                    ai_response2 = response2['message'].lower()
                    has_specific_context = any(indicator in ai_response2 for indicator in ['iş', 'stres', 'ilişki', 'partner'])
                    
                    if has_specific_context:
                        self.log_test("Specific profile context recall", True, "AI recalled specific previous topics")
                    else:
                        self.log_test("Specific profile context recall", False, "AI did not recall specific previous topics")
        
        return context_session_id

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