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
        
        success, response = self.run_api_test(
            "Admin login",
            "POST",
            "admin/login",
            200,
            data={
                "email": "admin@berkai.com",
                "password": "BerkAI2025!"
            }
        )
        
        if success:
            # Extract admin token from cookies or response
            # For testing, we'll create admin session directly in MongoDB
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

    def test_doctor_signup_flow(self):
        """Test doctor signup with pending status"""
        print("\n👨‍⚕️ Testing Doctor Signup Flow...")
        
        # Create doctor user
        doctor_id, doctor_email = self.create_test_user("doctor", "1")
        if not doctor_id:
            return False
        
        # Simulate session creation attempt (should fail for pending users)
        success, response = self.run_api_test(
            "Doctor session creation (should fail)",
            "POST",
            "auth/session",
            200,  # API returns 200 but with pending_approval flag
            data={
                "session_id": "fake_session_id_doctor",
                "user_type": "doctor"
            }
        )
        
        if success:
            # Check if response indicates pending approval
            if response.get("pending_approval") == True:
                self.log_test("Doctor pending approval response", True, "Correct pending approval message")
            else:
                self.log_test("Doctor pending approval response", False, "Should return pending_approval=true")
            
            # Verify no session token was created
            if "user" not in response:
                self.log_test("Doctor session token prevention", True, "No session token created for pending user")
            else:
                self.log_test("Doctor session token prevention", False, "Session token created for pending user")
        
        return doctor_id

    def test_patient_signup_flow(self):
        """Test patient signup with immediate approval"""
        print("\n🧑‍🦱 Testing Patient Signup Flow...")
        
        # Create patient user
        patient_id, patient_email = self.create_test_user("patient", "1")
        if not patient_id:
            return False
        
        # Simulate session creation (should succeed for patients)
        success, response = self.run_api_test(
            "Patient session creation (should succeed)",
            "POST",
            "auth/session",
            200,
            data={
                "session_id": "fake_session_id_patient",
                "user_type": "patient"
            }
        )
        
        if success:
            # Check if response indicates successful login
            if response.get("success") == True:
                self.log_test("Patient immediate approval", True, "Patient can login immediately")
            else:
                self.log_test("Patient immediate approval", False, "Patient should be able to login immediately")
        
        return patient_id

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
        
        # Test that approved doctor can now login
        success, response = self.run_api_test(
            "Approved doctor login test",
            "POST",
            "auth/session",
            200,
            data={
                "session_id": "fake_session_approved_doctor",
                "user_type": "doctor"
            }
        )
        
        if success and response.get("success") == True:
            self.log_test("Approved doctor can login", True, "Doctor can login after approval")
        else:
            self.log_test("Approved doctor can login", False, "Doctor cannot login after approval")
        
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
        
        # Test that rejected user gets rejection message on login attempt
        success, response = self.run_api_test(
            "Rejected user login attempt",
            "POST",
            "auth/session",
            200,
            data={
                "session_id": "fake_session_rejected_psychiatrist",
                "user_type": "psychiatrist"
            }
        )
        
        if success:
            if response.get("rejected") == True and rejection_reason in response.get("message", ""):
                self.log_test("Rejected user gets rejection message", True, "Correct rejection message shown")
            else:
                self.log_test("Rejected user gets rejection message", False, "Rejection message not shown correctly")
        
        return psychiatrist_id

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        print("\n🔍 Testing Edge Cases...")
        
        # Test approving non-existent user
        fake_user_id = "non_existent_user_id"
        success, response = self.run_api_test(
            "Approve non-existent user",
            "POST",
            f"admin/approve-user/{fake_user_id}",
            404
        )
        
        # Test rejecting non-existent user
        success, response = self.run_api_test(
            "Reject non-existent user",
            "POST",
            f"admin/reject-user/{fake_user_id}",
            404,
            data={"reason": "Test rejection"}
        )
        
        # Test admin endpoints without admin token
        temp_token = self.admin_token
        self.admin_token = None
        
        self.run_api_test(
            "Get pending users without admin auth",
            "GET",
            "admin/pending-users",
            401
        )
        
        self.run_api_test(
            "Approve user without admin auth",
            "POST",
            f"admin/approve-user/{fake_user_id}",
            401
        )
        
        self.admin_token = temp_token

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
            
            # Test 1: Doctor Signup Flow
            self.test_doctor_signup_flow()
            
            # Test 2: Patient Signup Flow  
            self.test_patient_signup_flow()
            
            # Test 3: Get Pending Users
            self.test_get_pending_users()
            
            # Test 4: Admin Approve User
            self.test_admin_approve_user()
            
            # Test 5: Admin Reject User
            self.test_admin_reject_user()
            
            # Test 6: Edge Cases
            self.test_edge_cases()
            
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
    print("🔧 BerkAI Backend Testing Suite")
    print("=" * 50)
    
    # Run MongoDB + RAG Memory Tests
    print("\n1️⃣ Running MongoDB + RAG Memory System Tests...")
    rag_tester = BerkAIRAGMemoryTester()
    rag_success = rag_tester.run_all_tests()
    
    print("\n" + "="*50)
    
    # Run Admin Approval System Tests
    print("\n2️⃣ Running Admin Approval System Tests...")
    admin_tester = AdminApprovalSystemTester()
    admin_success = admin_tester.run_all_tests()
    
    # Overall summary
    print("\n" + "="*60)
    print("🏁 OVERALL TEST SUMMARY")
    print("="*60)
    print(f"MongoDB + RAG Memory Tests: {'✅ PASSED' if rag_success else '❌ FAILED'}")
    print(f"Admin Approval System Tests: {'✅ PASSED' if admin_success else '❌ FAILED'}")
    
    overall_success = rag_success and admin_success
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())