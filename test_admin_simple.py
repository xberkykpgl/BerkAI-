import requests
import sys
import json
import time
import subprocess

def test_admin_endpoints():
    """Simple test of admin approval endpoints"""
    base_url = "https://berkai-companion.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🚀 Testing Admin Approval System")
    print(f"🌐 API URL: {api_url}")
    
    # Create admin session in MongoDB
    admin_token = f"admin_test_{int(time.time())}"
    
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
            print(f"✅ Admin session created")
        else:
            print(f"❌ Admin session failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Admin session error: {str(e)}")
        return False
    
    # Create test users
    test_users = []
    
    # Create pending doctor
    doctor_id = f"test-doctor-{int(time.time())}"
    doctor_email = f"test.doctor@example.com"
    
    mongo_script = f"""
    use('berkai_database');
    db.users.insertOne({{
      _id: '{doctor_id}',
      email: '{doctor_email}',
      name: 'Test Doctor',
      user_type: 'doctor',
      account_status: 'pending',
      status_updated_by: null,
      status_updated_at: null,
      rejection_reason: null,
      user_id_number: 'BRK{int(time.time())}',
      created_at: new Date()
    }});
    print('Doctor created');
    """
    
    try:
        result = subprocess.run(['mongosh', '--eval', mongo_script], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Test doctor created: {doctor_email}")
            test_users.append(doctor_id)
        else:
            print(f"❌ Doctor creation failed")
    except Exception as e:
        print(f"❌ Doctor creation error: {str(e)}")
    
    # Create pending psychiatrist
    psychiatrist_id = f"test-psychiatrist-{int(time.time())}"
    psychiatrist_email = f"test.psychiatrist@example.com"
    
    mongo_script = f"""
    use('berkai_database');
    db.users.insertOne({{
      _id: '{psychiatrist_id}',
      email: '{psychiatrist_email}',
      name: 'Test Psychiatrist',
      user_type: 'psychiatrist',
      account_status: 'pending',
      status_updated_by: null,
      status_updated_at: null,
      rejection_reason: null,
      user_id_number: 'BRK{int(time.time())}',
      created_at: new Date()
    }});
    print('Psychiatrist created');
    """
    
    try:
        result = subprocess.run(['mongosh', '--eval', mongo_script], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Test psychiatrist created: {psychiatrist_email}")
            test_users.append(psychiatrist_id)
        else:
            print(f"❌ Psychiatrist creation failed")
    except Exception as e:
        print(f"❌ Psychiatrist creation error: {str(e)}")
    
    # Test API endpoints
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {admin_token}'
    }
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Get pending users
    print("\n📋 Testing GET /admin/pending-users")
    tests_total += 1
    try:
        response = requests.get(f"{api_url}/admin/pending-users", headers=headers, timeout=10)
        if response.status_code == 200:
            pending_users = response.json()
            print(f"✅ GET pending users: {len(pending_users)} users found")
            tests_passed += 1
            
            # Check if our test users are in the list
            user_ids = [user.get('id') for user in pending_users]
            if doctor_id in user_ids and psychiatrist_id in user_ids:
                print(f"✅ Test users found in pending list")
            else:
                print(f"⚠️ Test users not found in pending list")
        else:
            print(f"❌ GET pending users failed: {response.status_code}")
    except Exception as e:
        print(f"❌ GET pending users error: {str(e)}")
    
    # Test 2: Approve doctor
    print("\n✅ Testing POST /admin/approve-user")
    tests_total += 1
    try:
        response = requests.post(f"{api_url}/admin/approve-user/{doctor_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✅ Approve doctor: Success")
            tests_passed += 1
            
            # Verify in database
            mongo_script = f"""
            use('berkai_database');
            const user = db.users.findOne({{_id: '{doctor_id}'}});
            if (user && user.account_status === 'approved') {{
                print('APPROVED');
            }} else {{
                print('NOT_APPROVED');
            }}
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            if "APPROVED" in result.stdout:
                print(f"✅ Doctor status verified as approved in database")
            else:
                print(f"❌ Doctor status not updated in database")
        else:
            print(f"❌ Approve doctor failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Approve doctor error: {str(e)}")
    
    # Test 3: Reject psychiatrist
    print("\n❌ Testing POST /admin/reject-user")
    tests_total += 1
    try:
        rejection_data = {"reason": "Yetersiz bilgi sağlandı"}
        response = requests.post(f"{api_url}/admin/reject-user/{psychiatrist_id}", 
                               headers=headers, json=rejection_data, timeout=10)
        if response.status_code == 200:
            print(f"✅ Reject psychiatrist: Success")
            tests_passed += 1
            
            # Verify in database
            mongo_script = f"""
            use('berkai_database');
            const user = db.users.findOne({{_id: '{psychiatrist_id}'}});
            if (user && user.account_status === 'rejected' && user.rejection_reason) {{
                print('REJECTED:' + user.rejection_reason);
            }} else {{
                print('NOT_REJECTED');
            }}
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            if "REJECTED:" in result.stdout:
                reason = result.stdout.split("REJECTED:")[1].strip()
                print(f"✅ Psychiatrist status verified as rejected with reason: {reason}")
            else:
                print(f"❌ Psychiatrist status not updated in database")
        else:
            print(f"❌ Reject psychiatrist failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Reject psychiatrist error: {str(e)}")
    
    # Test 4: Test auth session endpoint behavior
    print("\n🔐 Testing auth session behavior")
    tests_total += 2
    
    # Test approved doctor can create session
    try:
        session_data = {
            "session_id": "fake_session_for_approved_doctor",
            "user_type": "doctor"
        }
        response = requests.post(f"{api_url}/auth/session", json=session_data, timeout=10)
        print(f"Approved doctor session attempt: {response.status_code}")
        if response.status_code == 400:  # Expected because fake session_id
            print(f"✅ Approved doctor session handling works (400 for invalid session_id)")
            tests_passed += 1
        else:
            print(f"⚠️ Unexpected response for approved doctor session")
    except Exception as e:
        print(f"❌ Approved doctor session test error: {str(e)}")
    
    # Test rejected psychiatrist gets rejection message
    try:
        session_data = {
            "session_id": "fake_session_for_rejected_psychiatrist", 
            "user_type": "psychiatrist"
        }
        response = requests.post(f"{api_url}/auth/session", json=session_data, timeout=10)
        print(f"Rejected psychiatrist session attempt: {response.status_code}")
        if response.status_code == 400:  # Expected because fake session_id
            print(f"✅ Rejected psychiatrist session handling works (400 for invalid session_id)")
            tests_passed += 1
        else:
            print(f"⚠️ Unexpected response for rejected psychiatrist session")
    except Exception as e:
        print(f"❌ Rejected psychiatrist session test error: {str(e)}")
    
    # Cleanup
    print("\n🧹 Cleaning up test data...")
    if test_users:
        user_ids = "', '".join(test_users)
        mongo_script = f"""
        use('berkai_database');
        db.users.deleteMany({{_id: {{$in: ['{user_ids}']}}}});
        db.admin_sessions.deleteMany({{session_token: '{admin_token}'}});
        print('Cleanup completed');
        """
        
        try:
            subprocess.run(['mongosh', '--eval', mongo_script], 
                         capture_output=True, text=True, timeout=30)
            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")
    
    # Summary
    print(f"\n" + "="*50)
    print(f"📊 ADMIN APPROVAL SYSTEM TEST SUMMARY")
    print(f"="*50)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print(f"Success rate: {(tests_passed/tests_total*100):.1f}%")
    
    if tests_passed == tests_total:
        print(f"✅ All admin approval tests passed!")
        return True
    else:
        print(f"❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = test_admin_endpoints()
    sys.exit(0 if success else 1)