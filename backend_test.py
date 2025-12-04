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

    def test_message_limit_and_content(self):
        """Test Message Limit and Content Preservation"""
        print("\n📝 Testing Message Limit and Content...")
        
        # Create session for message limit testing
        success, session_data = self.run_api_test(
            "Create message limit test session",
            "POST",
            "sessions?session_name=Message Limit Test",
            200
        )
        
        if not success or 'id' not in session_data:
            self.log_test("Message limit session creation", False, "Failed to create session")
            return
        
        limit_session_id = session_data['id']
        self.test_sessions.append(limit_session_id)
        print(f"📝 Created message limit session: {limit_session_id}")
        
        # Send multiple long messages to test limits
        long_messages = []
        for i in range(25):  # Send more than 20 to test limit
            long_message = f"Bu {i+1}. mesajım ve çok uzun bir mesaj. " * 10  # ~400 characters
            long_messages.append(long_message)
            
            success, response = self.run_api_test(
                f"Long message {i+1}",
                "POST",
                f"sessions/{limit_session_id}/chat",
                200,
                data={"message": long_message}
            )
            
            if i == 0:  # Check first message for content preservation
                if success and 'message' in response:
                    # Verify no truncation occurred
                    if len(response['message']) > 50:  # AI should give substantial response
                        self.log_test("Message content preservation", True, "Full message content processed")
                    else:
                        self.log_test("Message content preservation", False, "Response too short, possible truncation")
        
        # Get all messages to verify 20-message limit
        success, messages = self.run_api_test(
            "Get session messages for limit test",
            "GET",
            f"sessions/{limit_session_id}/messages",
            200
        )
        
        if success and isinstance(messages, list):
            total_messages = len(messages)
            print(f"📊 Total messages stored: {total_messages}")
            
            # Check if messages are properly stored (should be all messages, limit applies to context loading)
            if total_messages >= 50:  # 25 user + 25 AI messages
                self.log_test("Message storage", True, f"All {total_messages} messages stored")
            else:
                self.log_test("Message storage", False, f"Only {total_messages} messages stored")
            
            # Verify no 100-character truncation
            long_messages_found = [msg for msg in messages if len(msg.get('content', '')) > 100]
            if long_messages_found:
                self.log_test("No message truncation", True, f"Found {len(long_messages_found)} messages > 100 chars")
            else:
                self.log_test("No message truncation", False, "No messages longer than 100 characters found")
        
        return limit_session_id

    def verify_user_profile_summary(self, session_id, expected_topic):
        """Verify AI summary was saved to user_profiles collection"""
        print(f"🔍 Verifying user profile summary for session {session_id}...")
        
        mongo_script = f"""
        use('berkai_database');
        const profile = db.user_profiles.findOne({{"user_id": "{self.user_id}"}});
        if (profile && profile.session_summaries) {{
            const sessionSummary = profile.session_summaries.find(s => s.session_id === "{session_id}");
            if (sessionSummary) {{
                print("SUMMARY_FOUND:" + JSON.stringify(sessionSummary));
            }} else {{
                print("SUMMARY_NOT_FOUND");
            }}
        }} else {{
            print("PROFILE_NOT_FOUND");
        }}
        """
        
        try:
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            
            if "SUMMARY_FOUND:" in result.stdout:
                summary_data = result.stdout.split("SUMMARY_FOUND:")[1].strip()
                try:
                    summary_obj = json.loads(summary_data)
                    summary_text = summary_obj.get('summary', '').lower()
                    
                    if expected_topic in summary_text or any(word in summary_text for word in expected_topic.split()):
                        self.log_test(f"AI summary generation for {expected_topic}", True, "Summary contains expected topic")
                        self.session_summaries.append(summary_obj)
                    else:
                        self.log_test(f"AI summary generation for {expected_topic}", False, f"Summary doesn't contain '{expected_topic}'")
                except json.JSONDecodeError:
                    self.log_test(f"AI summary parsing for {expected_topic}", False, "Could not parse summary JSON")
            elif "SUMMARY_NOT_FOUND" in result.stdout:
                self.log_test(f"AI summary storage for {expected_topic}", False, "Summary not found in user_profiles")
            else:
                self.log_test(f"User profile creation for {expected_topic}", False, "User profile not found")
                
        except Exception as e:
            self.log_test(f"MongoDB verification for {expected_topic}", False, f"MongoDB query failed: {str(e)}")

    def verify_mongodb_collections(self):
        """Verify MongoDB collections contain expected data"""
        print("\n🗄️ Verifying MongoDB Collections...")
        
        mongo_script = f"""
        use('berkai_database');
        
        // Check user_profiles collection
        const profileCount = db.user_profiles.countDocuments({{"user_id": "{self.user_id}"}});
        print("USER_PROFILES_COUNT:" + profileCount);
        
        // Check therapy_sessions collection
        const sessionCount = db.therapy_sessions.countDocuments({{"user_id": "{self.user_id}"}});
        print("THERAPY_SESSIONS_COUNT:" + sessionCount);
        
        // Check messages collection
        const messageCount = db.messages.countDocuments({{"user_id": "{self.user_id}"}});
        print("MESSAGES_COUNT:" + messageCount);
        
        // Get profile details
        const profile = db.user_profiles.findOne({{"user_id": "{self.user_id}"}});
        if (profile) {{
            print("SESSION_SUMMARIES_COUNT:" + (profile.session_summaries ? profile.session_summaries.length : 0));
        }}
        """
        
        try:
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            
            output = result.stdout
            
            # Parse counts
            profile_count = int(output.split("USER_PROFILES_COUNT:")[1].split("\n")[0]) if "USER_PROFILES_COUNT:" in output else 0
            session_count = int(output.split("THERAPY_SESSIONS_COUNT:")[1].split("\n")[0]) if "THERAPY_SESSIONS_COUNT:" in output else 0
            message_count = int(output.split("MESSAGES_COUNT:")[1].split("\n")[0]) if "MESSAGES_COUNT:" in output else 0
            summary_count = int(output.split("SESSION_SUMMARIES_COUNT:")[1].split("\n")[0]) if "SESSION_SUMMARIES_COUNT:" in output else 0
            
            print(f"📊 MongoDB Data Summary:")
            print(f"  User Profiles: {profile_count}")
            print(f"  Therapy Sessions: {session_count}")
            print(f"  Messages: {message_count}")
            print(f"  Session Summaries: {summary_count}")
            
            # Verify expected data
            if profile_count >= 1:
                self.log_test("User profile creation", True, f"Found {profile_count} user profile(s)")
            else:
                self.log_test("User profile creation", False, "No user profiles found")
            
            if session_count >= len(self.test_sessions):
                self.log_test("Session storage", True, f"Found {session_count} sessions")
            else:
                self.log_test("Session storage", False, f"Expected {len(self.test_sessions)} sessions, found {session_count}")
            
            if summary_count >= 2:  # Expect at least 2 summaries from work and relationship sessions
                self.log_test("Session summaries storage", True, f"Found {summary_count} session summaries")
            else:
                self.log_test("Session summaries storage", False, f"Expected at least 2 summaries, found {summary_count}")
                
        except Exception as e:
            self.log_test("MongoDB collections verification", False, f"Verification failed: {str(e)}")

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
            db.user_profiles.deleteMany({{user_id: '{self.user_id}'}});
            db.risk_assessments.deleteMany({{user_id: '{self.user_id}'}});
            print('Test data cleaned up');
            """
            
            try:
                subprocess.run(['mongosh', '--eval', mongo_script], 
                             capture_output=True, text=True, timeout=30)
                print("✅ Test data cleaned up")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {str(e)}")

    def run_all_tests(self):
        """Run all MongoDB + RAG memory system tests"""
        print("🚀 Starting BerkAI MongoDB + RAG Memory System Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: Session summaries, multi-session memory, profile context loading, message limits")
        
        # Setup
        if not self.setup_test_user():
            print("❌ Cannot proceed without test user setup")
            return False
        
        try:
            # Run authentication test first
            self.test_auth_endpoints()
            
            # Run RAG memory system tests in sequence
            print("\n" + "="*60)
            print("🧠 MONGODB + RAG MEMORY SYSTEM TESTS")
            print("="*60)
            
            # Test 1: Session Summary Generation
            self.test_session_summary_generation()
            
            # Test 2: Multi-Session Memory
            self.test_multi_session_memory()
            
            # Test 3: Profile Context Loading
            self.test_profile_context_loading()
            
            # Test 4: Message Limit and Content
            self.test_message_limit_and_content()
            
            # Verify MongoDB collections
            self.verify_mongodb_collections()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print detailed summary
        print(f"\n" + "="*60)
        print(f"📊 MONGODB + RAG MEMORY SYSTEM TEST SUMMARY")
        print(f"="*60)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {len(self.failed_tests)}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print(f"Sessions created: {len(self.test_sessions)}")
        print(f"Summaries generated: {len(self.session_summaries)}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['error']}")
        else:
            print(f"\n✅ All tests passed! MongoDB + RAG memory system is working correctly.")
        
        return len(self.failed_tests) == 0

def main():
    tester = BerkAIAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())