import requests
import sys
import json
import time
import re
from datetime import datetime

class BerkAIConversationTester:
    def __init__(self, base_url="https://berkai-companion.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.test_session_id = None
        self.second_session_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.conversation_log = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
            self.failed_tests.append({"test": name, "error": details})

    def count_sentences(self, text):
        """Count sentences in text"""
        # Split by sentence endings and filter out empty strings
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)

    def count_questions(self, text):
        """Count questions in text"""
        return text.count('?')

    def setup_test_user(self):
        """Create test user and session using MongoDB directly"""
        print("\n🔧 Setting up test user for conversation testing...")
        
        # Create test user data
        test_user_id = f"conv-test-user-{int(time.time())}"
        test_email = f"conv.test.user.{int(time.time())}@example.com"
        self.session_token = f"conv_test_session_{int(time.time())}"
        
        # Use mongosh to create test data
        mongo_script = f"""
        use('berkai_database');
        db.users.insertOne({{
          _id: '{test_user_id}',
          email: '{test_email}',
          name: 'Ahmet Yılmaz',
          picture: 'https://via.placeholder.com/150',
          user_type: 'patient',
          user_id_number: 'BRK{int(time.time())}',
          therapy_approach: 'general',
          created_at: new Date()
        }});
        db.user_sessions.insertOne({{
          user_id: '{test_user_id}',
          session_token: '{self.session_token}',
          expires_at: new Date(Date.now() + 7*24*60*60*1000),
          created_at: new Date()
        }});
        print('Conversation test user created successfully');
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

    def create_therapy_session(self, session_name="Test Session"):
        """Create a new therapy session"""
        url = f"{self.api_url}/sessions?session_name={session_name}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        try:
            response = requests.post(url, headers=headers, timeout=30)
            if response.status_code == 200:
                session_data = response.json()
                return session_data.get('id')
            else:
                print(f"❌ Failed to create session: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Session creation error: {str(e)}")
            return None

    def send_chat_message(self, session_id, message):
        """Send a chat message and return the AI response"""
        url = f"{self.api_url}/sessions/{session_id}/chat"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.session_token}'
        }
        
        data = {
            "message": message,
            "video_frame": None,
            "analyze_video": False
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=60)
            if response.status_code == 200:
                response_data = response.json()
                ai_message = response_data.get('message', '')
                
                # Log conversation
                self.conversation_log.append({
                    "user": message,
                    "ai": ai_message,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id
                })
                
                return ai_message
            else:
                print(f"❌ Chat failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Chat error: {str(e)}")
            return None

    def test_initial_conversation(self):
        """Test 1: Initial conversation - should be short with limited questions"""
        print("\n💬 Test 1: Initial Conversation (Short Response)")
        
        # Create first session
        self.test_session_id = self.create_therapy_session("İlk Seans")
        if not self.test_session_id:
            self.log_test("Create first session", False, "Could not create session")
            return
        
        # Send initial message
        user_message = "Merhaba, bugün kendimi çok kötü hissediyorum"
        ai_response = self.send_chat_message(self.test_session_id, user_message)
        
        if not ai_response:
            self.log_test("Initial conversation response", False, "No AI response received")
            return
        
        print(f"👤 User: {user_message}")
        print(f"🤖 BerkAI: {ai_response}")
        print()
        
        # Check response length (should be 3-4 sentences max)
        sentence_count = self.count_sentences(ai_response)
        question_count = self.count_questions(ai_response)
        
        print(f"📊 Analysis: {sentence_count} sentences, {question_count} questions")
        
        # Test sentence count (should be 3-4 max)
        if sentence_count <= 4:
            self.log_test("Response length (≤4 sentences)", True)
        else:
            self.log_test("Response length (≤4 sentences)", False, f"Got {sentence_count} sentences, expected ≤4")
        
        # Test question count (should be limited, not overwhelming)
        if question_count <= 3:
            self.log_test("Question count (≤3 questions)", True)
        else:
            self.log_test("Question count (≤3 questions)", False, f"Got {question_count} questions, expected ≤3")
        
        # Test empathetic tone
        empathy_keywords = ['anlıyorum', 'hissediyorsun', 'zor', 'üzgün', 'destek', 'yanında', 'dinliyorum']
        has_empathy = any(keyword in ai_response.lower() for keyword in empathy_keywords)
        self.log_test("Empathetic tone", has_empathy, "No empathetic keywords found" if not has_empathy else "")

    def test_followup_conversation(self):
        """Test 2: Follow-up conversation - should remain short"""
        print("\n💬 Test 2: Follow-up Conversation (Continued Short Responses)")
        
        if not self.test_session_id:
            self.log_test("Follow-up conversation", False, "No active session")
            return
        
        # Send follow-up message
        user_message = "İşimde sorunlar yaşıyorum, patronum bana baskı yapıyor"
        ai_response = self.send_chat_message(self.test_session_id, user_message)
        
        if not ai_response:
            self.log_test("Follow-up conversation response", False, "No AI response received")
            return
        
        print(f"👤 User: {user_message}")
        print(f"🤖 BerkAI: {ai_response}")
        print()
        
        # Check response length again
        sentence_count = self.count_sentences(ai_response)
        question_count = self.count_questions(ai_response)
        
        print(f"📊 Analysis: {sentence_count} sentences, {question_count} questions")
        
        # Test sentence count (should still be 3-4 max)
        if sentence_count <= 4:
            self.log_test("Follow-up response length (≤4 sentences)", True)
        else:
            self.log_test("Follow-up response length (≤4 sentences)", False, f"Got {sentence_count} sentences, expected ≤4")
        
        # Test focused questions (1-2 questions max)
        if question_count <= 2:
            self.log_test("Focused questions (≤2 questions)", True)
        else:
            self.log_test("Focused questions (≤2 questions)", False, f"Got {question_count} questions, expected ≤2")
        
        # Test professional therapeutic tone
        professional_keywords = ['iş', 'patron', 'baskı', 'stres', 'çözüm', 'başa çıkma']
        has_professional_context = any(keyword in ai_response.lower() for keyword in professional_keywords)
        self.log_test("Professional context understanding", has_professional_context, "No work-related context found" if not has_professional_context else "")

    def test_advice_request(self):
        """Test 3: Advice request - should be detailed and comprehensive"""
        print("\n💬 Test 3: Advice Request (Detailed Response Expected)")
        
        if not self.test_session_id:
            self.log_test("Advice request", False, "No active session")
            return
        
        # Request advice
        user_message = "Ne yapmam gerektiğini düşünüyorsun? Bana tavsiye verebilir misin?"
        ai_response = self.send_chat_message(self.test_session_id, user_message)
        
        if not ai_response:
            self.log_test("Advice request response", False, "No AI response received")
            return
        
        print(f"👤 User: {user_message}")
        print(f"🤖 BerkAI: {ai_response}")
        print()
        
        # Check response length (should be longer for advice)
        sentence_count = self.count_sentences(ai_response)
        word_count = len(ai_response.split())
        
        print(f"📊 Analysis: {sentence_count} sentences, {word_count} words")
        
        # Test that advice response is more detailed (more than 4 sentences is OK)
        if sentence_count >= 4:
            self.log_test("Detailed advice response (≥4 sentences)", True)
        else:
            self.log_test("Detailed advice response (≥4 sentences)", False, f"Got {sentence_count} sentences, expected ≥4 for advice")
        
        # Test word count (advice should be comprehensive)
        if word_count >= 50:
            self.log_test("Comprehensive advice (≥50 words)", True)
        else:
            self.log_test("Comprehensive advice (≥50 words)", False, f"Got {word_count} words, expected ≥50 for advice")
        
        # Test advice keywords
        advice_keywords = ['öneri', 'tavsiye', 'yapabilir', 'deneyebilir', 'çözüm', 'yöntem', 'strateji', 'adım']
        has_advice_content = any(keyword in ai_response.lower() for keyword in advice_keywords)
        self.log_test("Contains advice content", has_advice_content, "No advice keywords found" if not has_advice_content else "")

    def test_session_memory(self):
        """Test 4: Session memory - should remember previous conversations"""
        print("\n💬 Test 4: Session Memory (Context Retention)")
        
        # Create second session
        self.second_session_id = self.create_therapy_session("İkinci Seans")
        if not self.second_session_id:
            self.log_test("Create second session", False, "Could not create second session")
            return
        
        # Send message referencing previous session
        user_message = "Merhaba, tekrar benimle konuşur musun?"
        ai_response = self.send_chat_message(self.second_session_id, user_message)
        
        if not ai_response:
            self.log_test("Session memory response", False, "No AI response received")
            return
        
        print(f"👤 User: {user_message}")
        print(f"🤖 BerkAI: {ai_response}")
        print()
        
        # Test memory indicators
        memory_keywords = ['önceki', 'geçen', 'daha önce', 'hatırlıyorum', 'konuştuk', 'bahsetmiş', 'iş', 'patron']
        has_memory = any(keyword in ai_response.lower() for keyword in memory_keywords)
        self.log_test("Session memory retention", has_memory, "No memory indicators found" if not has_memory else "")
        
        # Test response is still concise (not advice)
        sentence_count = self.count_sentences(ai_response)
        if sentence_count <= 4:
            self.log_test("Memory response length (≤4 sentences)", True)
        else:
            self.log_test("Memory response length (≤4 sentences)", False, f"Got {sentence_count} sentences, expected ≤4")

    def get_session_messages(self, session_id):
        """Get all messages from a session"""
        url = f"{self.api_url}/sessions/{session_id}/messages"
        headers = {
            'Authorization': f'Bearer {self.session_token}'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get messages: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Get messages error: {str(e)}")
            return []

    def test_message_persistence(self):
        """Test 5: Message persistence in database"""
        print("\n💬 Test 5: Message Persistence")
        
        if not self.test_session_id:
            self.log_test("Message persistence", False, "No active session")
            return
        
        # Get messages from first session
        messages = self.get_session_messages(self.test_session_id)
        
        if messages:
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            ai_messages = [msg for msg in messages if msg.get('role') == 'assistant']
            
            print(f"📊 Found {len(user_messages)} user messages, {len(ai_messages)} AI messages")
            
            # Should have at least 3 exchanges (initial + follow-up + advice)
            if len(user_messages) >= 3:
                self.log_test("User messages stored", True)
            else:
                self.log_test("User messages stored", False, f"Expected ≥3 user messages, got {len(user_messages)}")
            
            if len(ai_messages) >= 3:
                self.log_test("AI messages stored", True)
            else:
                self.log_test("AI messages stored", False, f"Expected ≥3 AI messages, got {len(ai_messages)}")
        else:
            self.log_test("Message persistence", False, "No messages found in database")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up conversation test data...")
        
        if self.user_id:
            mongo_script = f"""
            use('berkai_database');
            db.users.deleteOne({{_id: '{self.user_id}'}});
            db.user_sessions.deleteMany({{user_id: '{self.user_id}'}});
            db.therapy_sessions.deleteMany({{user_id: '{self.user_id}'}});
            db.messages.deleteMany({{user_id: '{self.user_id}'}});
            db.video_analyses.deleteMany({{user_id: '{self.user_id}'}});
            db.risk_assessments.deleteMany({{user_id: '{self.user_id}'}});
            print('Conversation test data cleaned up');
            """
            
            import subprocess
            try:
                subprocess.run(['mongosh', '--eval', mongo_script], 
                             capture_output=True, text=True, timeout=30)
                print("✅ Test data cleaned up")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {str(e)}")

    def print_conversation_summary(self):
        """Print summary of all conversations"""
        print("\n📝 Conversation Summary:")
        for i, conv in enumerate(self.conversation_log, 1):
            print(f"\n--- Exchange {i} (Session: {conv['session_id'][-8:]}) ---")
            print(f"👤 User: {conv['user']}")
            print(f"🤖 BerkAI: {conv['ai']}")
            print(f"📊 Stats: {self.count_sentences(conv['ai'])} sentences, {self.count_questions(conv['ai'])} questions")

    def run_conversation_tests(self):
        """Run all conversation flow tests"""
        print("🚀 Starting BerkAI Conversation Flow Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: Response length, question density, and advice quality")
        
        # Setup
        if not self.setup_test_user():
            print("❌ Cannot proceed without test user setup")
            return False
        
        try:
            # Run conversation tests in sequence
            self.test_initial_conversation()
            self.test_followup_conversation()
            self.test_advice_request()
            self.test_session_memory()
            self.test_message_persistence()
            
            # Print conversation summary
            self.print_conversation_summary()
            
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
        else:
            print(f"\n✅ All conversation flow tests passed!")
        
        return len(self.failed_tests) == 0

def main():
    tester = BerkAIConversationTester()
    success = tester.run_conversation_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())