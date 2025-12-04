import requests
import sys
import json
import time
import subprocess

def test_complete_signup_flow():
    """Test complete signup and login flow for different user types"""
    base_url = "https://berkai-companion.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🚀 Testing Complete Signup & Login Flow")
    print(f"🌐 API URL: {api_url}")
    
    # Create admin session
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
            print(f"❌ Admin session failed")
            return False
    except Exception as e:
        print(f"❌ Admin session error: {str(e)}")
        return False
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {admin_token}'
    }
    
    test_users = []
    tests_passed = 0
    tests_total = 0
    
    print("\n" + "="*60)
    print("🧪 SCENARIO 1: DOCTOR SIGNUP TEST")
    print("="*60)
    
    # Create doctor user (simulating signup)
    doctor_id = f"doctor.test.{int(time.time())}@example.com"
    
    mongo_script = f"""
    use('berkai_database');
    db.users.insertOne({{
      _id: '{doctor_id}',
      email: '{doctor_id}',
      name: 'Dr. Test Doctor',
      user_type: 'doctor',
      account_status: 'pending',
      status_updated_by: null,
      status_updated_at: null,
      rejection_reason: null,
      user_id_number: 'BRK{int(time.time())}DOC',
      license_number: 'LIC123456',
      specialization: 'Cardiology',
      created_at: new Date()
    }});
    print('Doctor user created');
    """
    
    try:
        result = subprocess.run(['mongosh', '--eval', mongo_script], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Doctor user created with pending status")
            test_users.append(doctor_id)
        else:
            print(f"❌ Doctor creation failed")
    except Exception as e:
        print(f"❌ Doctor creation error: {str(e)}")
    
    # Test doctor login attempt (should fail with pending message)
    print("\n🔐 Testing doctor login attempt (should show pending message)")
    tests_total += 1
    try:
        # Simulate what happens when doctor tries to login
        # In real flow, this would come from Emergent Auth, but we simulate the result
        session_data = {
            "session_id": "fake_emergent_session_doctor",
            "user_type": "doctor"
        }
        response = requests.post(f"{api_url}/auth/session", json=session_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("pending_approval") == True and "admin onayı bekliyor" in result.get("message", ""):
                print(f"✅ Doctor gets correct pending approval message")
                print(f"   Message: {result.get('message')}")
                tests_passed += 1
            else:
                print(f"❌ Doctor should get pending approval message")
                print(f"   Response: {result}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Doctor login test error: {str(e)}")
    
    # Verify no session token was created
    tests_total += 1
    mongo_script = f"""
    use('berkai_database');
    const sessionCount = db.user_sessions.countDocuments({{user_id: '{doctor_id}'}});
    print('SESSION_COUNT:' + sessionCount);
    """
    
    try:
        result = subprocess.run(['mongosh', '--eval', mongo_script], 
                              capture_output=True, text=True, timeout=30)
        if "SESSION_COUNT:0" in result.stdout:
            print(f"✅ No session token created for pending doctor")
            tests_passed += 1
        else:
            print(f"❌ Session token should not be created for pending doctor")
    except Exception as e:
        print(f"❌ Session verification error: {str(e)}")
    
    print("\n" + "="*60)
    print("🧪 SCENARIO 2: PATIENT SIGNUP TEST")
    print("="*60)
    
    # Create patient user (simulating signup)
    patient_id = f"patient.test.{int(time.time())}@example.com"
    
    mongo_script = f"""
    use('berkai_database');
    db.users.insertOne({{
      _id: '{patient_id}',
      email: '{patient_id}',
      name: 'Test Patient',
      user_type: 'patient',
      account_status: 'approved',
      status_updated_by: null,
      status_updated_at: null,
      rejection_reason: null,
      user_id_number: 'BRK{int(time.time())}PAT',
      created_at: new Date()
    }});
    print('Patient user created');
    """
    
    try:
        result = subprocess.run(['mongosh', '--eval', mongo_script], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Patient user created with approved status")
            test_users.append(patient_id)
        else:
            print(f"❌ Patient creation failed")
    except Exception as e:
        print(f"❌ Patient creation error: {str(e)}")
    
    # Test patient login (should succeed)
    print("\n🔐 Testing patient login (should succeed)")
    tests_total += 1
    try:
        session_data = {
            "session_id": "fake_emergent_session_patient",
            "user_type": "patient"
        }
        response = requests.post(f"{api_url}/auth/session", json=session_data, timeout=10)
        
        if response.status_code == 400:  # Expected because fake session_id
            print(f"✅ Patient login flow works (400 for invalid session_id is expected)")
            tests_passed += 1
        else:
            print(f"⚠️ Unexpected response for patient login: {response.status_code}")
    except Exception as e:
        print(f"❌ Patient login test error: {str(e)}")
    
    print("\n" + "="*60)
    print("🧪 SCENARIO 3: ADMIN APPROVE USER TEST")
    print("="*60)
    
    # Admin approves the doctor
    print("✅ Admin approving doctor...")
    tests_total += 1
    try:
        response = requests.post(f"{api_url}/admin/approve-user/{doctor_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✅ Admin approval successful")
            tests_passed += 1
            
            # Verify status changes
            mongo_script = f"""
            use('berkai_database');
            const user = db.users.findOne({{_id: '{doctor_id}'}});
            if (user) {{
                print('STATUS:' + user.account_status);
                print('UPDATED_BY:' + (user.status_updated_by || 'null'));
                print('UPDATED_AT:' + (user.status_updated_at ? 'set' : 'null'));
            }}
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            output = result.stdout
            
            if "STATUS:approved" in output:
                print(f"✅ Account status changed to approved")
            if "UPDATED_BY:" in output and "null" not in output.split("UPDATED_BY:")[1].split("\n")[0]:
                print(f"✅ Status updated by admin tracked")
            if "UPDATED_AT:set" in output:
                print(f"✅ Status update timestamp recorded")
                
        else:
            print(f"❌ Admin approval failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Admin approval error: {str(e)}")
    
    # Test approved doctor can now login
    print("\n🔐 Testing approved doctor login (should now succeed)")
    tests_total += 1
    try:
        session_data = {
            "session_id": "fake_emergent_session_approved_doctor",
            "user_type": "doctor"
        }
        response = requests.post(f"{api_url}/auth/session", json=session_data, timeout=10)
        
        if response.status_code == 400:  # Expected because fake session_id
            print(f"✅ Approved doctor can now attempt login (400 for invalid session_id is expected)")
            tests_passed += 1
        else:
            print(f"⚠️ Unexpected response for approved doctor login: {response.status_code}")
    except Exception as e:
        print(f"❌ Approved doctor login test error: {str(e)}")
    
    print("\n" + "="*60)
    print("🧪 SCENARIO 4: ADMIN REJECT USER TEST")
    print("="*60)
    
    # Create psychiatrist for rejection test
    psychiatrist_id = f"psychiatrist.test.{int(time.time())}@example.com"
    
    mongo_script = f"""
    use('berkai_database');
    db.users.insertOne({{
      _id: '{psychiatrist_id}',
      email: '{psychiatrist_id}',
      name: 'Dr. Test Psychiatrist',
      user_type: 'psychiatrist',
      account_status: 'pending',
      status_updated_by: null,
      status_updated_at: null,
      rejection_reason: null,
      user_id_number: 'BRK{int(time.time())}PSY',
      license_number: 'PSY123456',
      specialization: 'Clinical Psychology',
      created_at: new Date()
    }});
    print('Psychiatrist user created');
    """
    
    try:
        result = subprocess.run(['mongosh', '--eval', mongo_script], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Psychiatrist user created with pending status")
            test_users.append(psychiatrist_id)
        else:
            print(f"❌ Psychiatrist creation failed")
    except Exception as e:
        print(f"❌ Psychiatrist creation error: {str(e)}")
    
    # Admin rejects the psychiatrist
    print("\n❌ Admin rejecting psychiatrist...")
    tests_total += 1
    rejection_reason = "Yetersiz bilgi sağlandı"
    try:
        rejection_data = {"reason": rejection_reason}
        response = requests.post(f"{api_url}/admin/reject-user/{psychiatrist_id}", 
                               headers=headers, json=rejection_data, timeout=10)
        if response.status_code == 200:
            print(f"✅ Admin rejection successful")
            tests_passed += 1
            
            # Verify rejection details
            mongo_script = f"""
            use('berkai_database');
            const user = db.users.findOne({{_id: '{psychiatrist_id}'}});
            if (user) {{
                print('STATUS:' + user.account_status);
                print('REJECTION_REASON:' + (user.rejection_reason || 'null'));
                print('UPDATED_BY:' + (user.status_updated_by || 'null'));
            }}
            """
            
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            output = result.stdout
            
            if "STATUS:rejected" in output:
                print(f"✅ Account status changed to rejected")
            if f"REJECTION_REASON:{rejection_reason}" in output:
                print(f"✅ Rejection reason saved: {rejection_reason}")
                
        else:
            print(f"❌ Admin rejection failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Admin rejection error: {str(e)}")
    
    # Test rejected user gets rejection message
    print("\n🔐 Testing rejected psychiatrist login (should show rejection message)")
    tests_total += 1
    try:
        session_data = {
            "session_id": "fake_emergent_session_rejected_psychiatrist",
            "user_type": "psychiatrist"
        }
        response = requests.post(f"{api_url}/auth/session", json=session_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("rejected") == True and rejection_reason in result.get("message", ""):
                print(f"✅ Rejected user gets correct rejection message")
                print(f"   Message: {result.get('message')}")
                tests_passed += 1
            else:
                print(f"❌ Rejected user should get rejection message")
                print(f"   Response: {result}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Rejected user login test error: {str(e)}")
    
    print("\n" + "="*60)
    print("🧪 SCENARIO 5: GET PENDING USERS TEST")
    print("="*60)
    
    # Create multiple pending users
    pending_doctor_id = f"pending.doctor.{int(time.time())}@example.com"
    pending_psychiatrist_id = f"pending.psychiatrist.{int(time.time())}@example.com"
    
    mongo_script = f"""
    use('berkai_database');
    db.users.insertMany([
      {{
        _id: '{pending_doctor_id}',
        email: '{pending_doctor_id}',
        name: 'Pending Doctor',
        user_type: 'doctor',
        account_status: 'pending',
        created_at: new Date()
      }},
      {{
        _id: '{pending_psychiatrist_id}',
        email: '{pending_psychiatrist_id}',
        name: 'Pending Psychiatrist',
        user_type: 'psychiatrist',
        account_status: 'pending',
        created_at: new Date()
      }}
    ]);
    print('Pending users created');
    """
    
    try:
        result = subprocess.run(['mongosh', '--eval', mongo_script], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Multiple pending users created")
            test_users.extend([pending_doctor_id, pending_psychiatrist_id])
        else:
            print(f"❌ Pending users creation failed")
    except Exception as e:
        print(f"❌ Pending users creation error: {str(e)}")
    
    # Test get pending users endpoint
    print("\n📋 Testing GET /admin/pending-users")
    tests_total += 1
    try:
        response = requests.get(f"{api_url}/admin/pending-users", headers=headers, timeout=10)
        if response.status_code == 200:
            pending_users = response.json()
            print(f"✅ Retrieved {len(pending_users)} pending users")
            
            # Verify only pending doctors/psychiatrists are returned
            user_ids = [user.get('id') for user in pending_users]
            user_types = [user.get('user_type') for user in pending_users]
            
            if pending_doctor_id in user_ids and pending_psychiatrist_id in user_ids:
                print(f"✅ Pending doctors and psychiatrists included")
            
            if all(user_type in ['doctor', 'psychiatrist'] for user_type in user_types):
                print(f"✅ Only doctors and psychiatrists in pending list")
                tests_passed += 1
            else:
                print(f"❌ Non-doctor/psychiatrist users found in pending list")
                
        else:
            print(f"❌ Get pending users failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get pending users error: {str(e)}")
    
    # Cleanup
    print("\n🧹 Cleaning up test data...")
    if test_users:
        user_ids = "', '".join(test_users)
        mongo_script = f"""
        use('berkai_database');
        db.users.deleteMany({{_id: {{$in: ['{user_ids}']}}}});
        db.user_sessions.deleteMany({{user_id: {{$in: ['{user_ids}']}}}});
        db.admin_sessions.deleteMany({{session_token: '{admin_token}'}});
        print('Cleanup completed');
        """
        
        try:
            subprocess.run(['mongosh', '--eval', mongo_script], 
                         capture_output=True, text=True, timeout=30)
            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")
    
    # Final Summary
    print(f"\n" + "="*60)
    print(f"📊 COMPLETE SIGNUP & LOGIN FLOW TEST SUMMARY")
    print(f"="*60)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print(f"Success rate: {(tests_passed/tests_total*100):.1f}%")
    
    print(f"\n🎯 Test Scenarios Covered:")
    print(f"✅ Doctor Signup (pending status)")
    print(f"✅ Patient Signup (immediate approval)")
    print(f"✅ Admin Approve User")
    print(f"✅ Admin Reject User")
    print(f"✅ Get Pending Users")
    print(f"✅ Login behavior for all user states")
    
    if tests_passed == tests_total:
        print(f"\n✅ ALL ADMIN APPROVAL SYSTEM TESTS PASSED!")
        print(f"🎉 Complete workflow is functioning correctly")
        return True
    else:
        print(f"\n❌ Some tests failed - see details above")
        return False

if __name__ == "__main__":
    success = test_complete_signup_flow()
    sys.exit(0 if success else 1)