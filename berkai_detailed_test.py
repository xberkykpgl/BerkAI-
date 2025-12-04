import requests
import sys
import json
import time
import re
from datetime import datetime

class BerkAIDetailedTester:
    def __init__(self, base_url="https://berkai-companion.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.test_session_id = None
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
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)

    def count_questions(self, text):
        """Count questions in text"""
        return text.count('?')

    def setup_test_user(self):
        """Create test user and session using MongoDB directly"""
        print("\n🔧 Setting up detailed test user...")
        
        test_user_id = f"detailed-test-user-{int(time.time())}"
        test_email = f"detailed.test.user.{int(time.time())}@example.com"
        self.session_token = f"detailed_test_session_{int(time.time())}"
        
        mongo_script = f"""
        use('berkai_database');
        db.users.insertOne({{
          _id: '{test_user_id}',
          email: '{test_email}',
          name: 'Elif Demir',
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
        print('Detailed test user created successfully');
        """
        
        import subprocess
        try:
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.user_id = test_user_id
                print(f"✅ Test user created: {test_email}")
                return True
            else:
                print(f"❌ MongoDB setup failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ MongoDB setup error: {str(e)}")
            return False

    def create_therapy_session(self, session_name="Detailed Test Session"):
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
                print(f"❌ Failed to create session: {response.status_code}")
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

    def test_question_storm_prevention(self):
        """Test that AI doesn't ask too many questions in regular conversation"""
        print("\n🌪️ Test: Question Storm Prevention")
        
        self.test_session_id = self.create_therapy_session("Question Storm Test")
        if not self.test_session_id:
            self.log_test("Create session for question storm test", False, "Could not create session")
            return
        
        # Test multiple regular conversation messages
        test_messages = [
            "Merhaba, bugün çok stresli bir gün geçirdim",
            "Ailemle sorunlar yaşıyorum, annemle tartıştık",
            "Üniversite sınavları yaklaşıyor, çok kaygılıyım",
            "Arkadaşlarımla ilişkilerimde problemler var"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Message {i} ---")
            ai_response = self.send_chat_message(self.test_session_id, message)
            
            if ai_response:
                sentence_count = self.count_sentences(ai_response)
                question_count = self.count_questions(ai_response)
                
                print(f"👤 User: {message}")
                print(f"🤖 BerkAI: {ai_response}")
                print(f"📊 Analysis: {sentence_count} sentences, {question_count} questions")
                
                # Check sentence limit
                if sentence_count <= 4:
                    self.log_test(f"Message {i} sentence limit (≤4)", True)
                else:
                    self.log_test(f"Message {i} sentence limit (≤4)", False, f"Got {sentence_count} sentences")
                
                # Check question limit (should be reasonable, not overwhelming)
                if question_count <= 3:
                    self.log_test(f"Message {i} question limit (≤3)", True)
                else:
                    self.log_test(f"Message {i} question limit (≤3)", False, f"Got {question_count} questions")

    def test_advice_vs_conversation_mode(self):
        """Test difference between advice mode and conversation mode"""
        print("\n🎯 Test: Advice vs Conversation Mode")
        
        if not self.test_session_id:
            self.log_test("Advice vs conversation test", False, "No active session")
            return
        
        # First, regular conversation (should be short)
        print("\n--- Regular Conversation Mode ---")
        regular_message = "Bugün işte çok yoruldum, eve geldiğimde hiçbir şey yapmak istemiyorum"
        ai_response = self.send_chat_message(self.test_session_id, regular_message)
        
        if ai_response:
            sentence_count = self.count_sentences(ai_response)
            print(f"👤 User: {regular_message}")
            print(f"🤖 BerkAI: {ai_response}")
            print(f"📊 Regular mode: {sentence_count} sentences")
            
            if sentence_count <= 4:
                self.log_test("Regular conversation mode (≤4 sentences)", True)
            else:
                self.log_test("Regular conversation mode (≤4 sentences)", False, f"Got {sentence_count} sentences")
        
        # Then, explicit advice request (should be detailed)
        print("\n--- Advice Mode ---")
        advice_message = "Bu durumla nasıl başa çıkabilirim? Bana detaylı öneriler verebilir misin?"
        ai_response = self.send_chat_message(self.test_session_id, advice_message)
        
        if ai_response:
            sentence_count = self.count_sentences(ai_response)
            word_count = len(ai_response.split())
            print(f"👤 User: {advice_message}")
            print(f"🤖 BerkAI: {ai_response}")
            print(f"📊 Advice mode: {sentence_count} sentences, {word_count} words")
            
            if sentence_count >= 5:
                self.log_test("Advice mode detailed response (≥5 sentences)", True)
            else:
                self.log_test("Advice mode detailed response (≥5 sentences)", False, f"Got {sentence_count} sentences")
            
            if word_count >= 100:
                self.log_test("Advice mode comprehensive (≥100 words)", True)
            else:
                self.log_test("Advice mode comprehensive (≥100 words)", False, f"Got {word_count} words")

    def test_empathy_and_professionalism(self):
        """Test that responses maintain empathy and professionalism"""
        print("\n❤️ Test: Empathy and Professionalism")
        
        if not self.test_session_id:
            self.log_test("Empathy test", False, "No active session")
            return
        
        # Test emotional message
        emotional_message = "Kendimi çok yalnız hissediyorum, kimse beni anlamıyor"
        ai_response = self.send_chat_message(self.test_session_id, emotional_message)
        
        if ai_response:
            print(f"👤 User: {emotional_message}")
            print(f"🤖 BerkAI: {ai_response}")
            
            # Check for empathetic language
            empathy_keywords = ['anlıyorum', 'hissediyorsun', 'zor', 'üzgün', 'destek', 'yanında', 'dinliyorum', 'buradayım']
            has_empathy = any(keyword in ai_response.lower() for keyword in empathy_keywords)
            self.log_test("Empathetic language", has_empathy, "No empathetic keywords found" if not has_empathy else "")
            
            # Check for professional boundaries
            professional_indicators = ['berkai', 'profesyonel', 'destek', 'yardım']
            maintains_boundaries = any(indicator in ai_response.lower() for indicator in professional_indicators)
            self.log_test("Professional boundaries", maintains_boundaries, "No professional indicators found" if not maintains_boundaries else "")
            
            # Check response is still concise (not advice)
            sentence_count = self.count_sentences(ai_response)
            if sentence_count <= 4:
                self.log_test("Empathetic response conciseness (≤4 sentences)", True)
            else:
                self.log_test("Empathetic response conciseness (≤4 sentences)", False, f"Got {sentence_count} sentences")

    def test_turkish_language_quality(self):
        """Test Turkish language quality and naturalness"""
        print("\n🇹🇷 Test: Turkish Language Quality")
        
        if not self.test_session_id:
            self.log_test("Turkish language test", False, "No active session")
            return
        
        # Test with Turkish-specific context
        turkish_message = "Bayramda ailemle görüştüm ama çok gergin geçti, herkesle tartıştım"
        ai_response = self.send_chat_message(self.test_session_id, turkish_message)
        
        if ai_response:
            print(f"👤 User: {turkish_message}")
            print(f"🤖 BerkAI: {ai_response}")
            
            # Check for Turkish cultural context
            cultural_keywords = ['aile', 'bayram', 'gergin', 'tartışma']
            understands_culture = any(keyword in ai_response.lower() for keyword in cultural_keywords)
            self.log_test("Turkish cultural context", understands_culture, "No cultural context found" if not understands_culture else "")
            
            # Check for natural Turkish expressions
            natural_expressions = ['anlıyorum', 'nasıl hissediyorsun', 'ne oldu', 'anlatabilir misin']
            sounds_natural = any(expr in ai_response.lower() for expr in natural_expressions)
            self.log_test("Natural Turkish expressions", sounds_natural, "No natural expressions found" if not sounds_natural else "")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up detailed test data...")
        
        if self.user_id:
            mongo_script = f"""
            use('berkai_database');
            db.users.deleteOne({{_id: '{self.user_id}'}});
            db.user_sessions.deleteMany({{user_id: '{self.user_id}'}});
            db.therapy_sessions.deleteMany({{user_id: '{self.user_id}'}});
            db.messages.deleteMany({{user_id: '{self.user_id}'}});
            db.video_analyses.deleteMany({{user_id: '{self.user_id}'}});
            db.risk_assessments.deleteMany({{user_id: '{self.user_id}'}});
            print('Detailed test data cleaned up');
            """
            
            import subprocess
            try:
                subprocess.run(['mongosh', '--eval', mongo_script], 
                             capture_output=True, text=True, timeout=30)
                print("✅ Test data cleaned up")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {str(e)}")

    def run_detailed_tests(self):
        """Run detailed conversation tests"""
        print("🚀 Starting BerkAI Detailed Conversation Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: Question storms, mode switching, empathy, Turkish quality")
        
        # Setup
        if not self.setup_test_user():
            print("❌ Cannot proceed without test user setup")
            return False
        
        try:
            # Run detailed tests
            self.test_question_storm_prevention()
            self.test_advice_vs_conversation_mode()
            self.test_empathy_and_professionalism()
            self.test_turkish_language_quality()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print summary
        print(f"\n📊 Detailed Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {len(self.failed_tests)}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['error']}")
        else:
            print(f"\n✅ All detailed tests passed!")
        
        return len(self.failed_tests) == 0

def main():
    tester = BerkAIDetailedTester()
    success = tester.run_detailed_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())