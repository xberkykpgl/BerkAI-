# Auth-Gated App Testing Playbook

## Step 1: Create Test User & Session
```bash
mongosh --eval "
use('berkai_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  _id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend API
```bash
# Test auth endpoint
curl -X GET "https://berkai-companion.preview.emergentagent.com/api/auth/me" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Test sessions
curl -X GET "https://berkai-companion.preview.emergentagent.com/api/sessions" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Create session
curl -X POST "https://berkai-companion.preview.emergentagent.com/api/sessions?session_name=Test%20Session" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

## Step 3: Browser Testing
Set cookie and navigate to dashboard

## Critical Fix: ID Schema
MongoDB + Pydantic ID Mapping using alias="_id"

## Quick Debug
Check data format and clean test data as needed
