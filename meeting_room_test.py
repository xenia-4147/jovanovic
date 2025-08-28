#!/usr/bin/env python3
"""
Focused Meeting Room Test Suite
"""

import requests
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def test_meeting_room_workflow():
    """Test complete meeting room workflow"""
    print("=" * 60)
    print("MEETING ROOM WORKFLOW TEST")
    print("=" * 60)
    
    # Step 1: Register user and create card
    test_email = f"meetingtest_{uuid.uuid4().hex[:8]}@example.com"
    
    user_data = {
        "email": test_email,
        "password": "SecurePass123!",
        "first_name": "Meeting",
        "last_name": "Tester",
        "gdpr_consent": True,
        "privacy_consent": True,
        "marketing_consent": False
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code}")
        return False
    
    data = response.json()
    access_token = data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"✅ User registered: {test_email}")
    
    # Step 2: Create business card
    card_data = {
        "name": "Meeting Room Creator",
        "company": "Test Company",
        "position": "Event Organizer",
        "description": "Testing meeting room functionality",
        "phones": [{"label": "work", "number": "+49-30-123-4567", "is_primary": True}],
        "emails": [{"label": "work", "address": test_email, "is_primary": True}],
        "is_public": True,
        "custom_code": f"MEET{uuid.uuid4().hex[:6].upper()}"
    }
    
    response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Card creation failed: {response.status_code}")
        return False
    
    card = response.json()
    card_id = card["id"]
    print(f"✅ Business card created: {card['name']}")
    
    # Step 3: Create meeting room
    room_data = {
        "card_id": card_id,
        "description": "Test Meeting Room for API Testing",
        "duration_minutes": 15,
        "max_participants": 10
    }
    
    response = requests.post(f"{API_BASE}/meeting-rooms", json=room_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Meeting room creation failed: {response.status_code} - {response.text}")
        return False
    
    room = response.json()
    room_code = room["code"]
    print(f"✅ Meeting room created: {room_code}")
    print(f"   Participants: {len(room['participants'])}")
    print(f"   Can join: {room['can_join']}")
    print(f"   Is creator: {room['is_creator']}")
    
    # Step 4: Get meeting room details
    response = requests.get(f"{API_BASE}/meeting-rooms/{room_code}")
    if response.status_code != 200:
        print(f"❌ Get meeting room failed: {response.status_code}")
        return False
    
    room_details = response.json()
    print(f"✅ Meeting room retrieved: {room_details['code']}")
    print(f"   Time remaining: {room_details['time_remaining_minutes']} minutes")
    
    # Step 5: Create second card for joining
    card_data_2 = {
        "name": "Meeting Participant",
        "company": "Participant Corp",
        "position": "Attendee",
        "description": "Joining the meeting room",
        "phones": [{"label": "mobile", "number": "+49-30-987-6543", "is_primary": True}],
        "emails": [{"label": "personal", "address": f"participant_{uuid.uuid4().hex[:6]}@example.com", "is_primary": True}],
        "is_public": True,
        "custom_code": f"PART{uuid.uuid4().hex[:6].upper()}"
    }
    
    response = requests.post(f"{API_BASE}/cards", json=card_data_2, headers=headers)
    if response.status_code != 200:
        print(f"❌ Second card creation failed: {response.status_code}")
        return False
    
    card_2 = response.json()
    card_2_id = card_2["id"]
    print(f"✅ Second business card created: {card_2['name']}")
    
    # Step 6: Join meeting room with second card
    join_data = {
        "code": room_code,
        "card_id": card_2_id
    }
    
    response = requests.post(f"{API_BASE}/meeting-rooms/join", json=join_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Join meeting room failed: {response.status_code} - {response.text}")
        return False
    
    join_result = response.json()
    print(f"✅ Joined meeting room: {join_result['message']}")
    print(f"   Participants now: {len(join_result['room']['participants'])}")
    print(f"   Cards received: {len(join_result['cards_received'])}")
    
    # Step 7: List user meeting rooms
    response = requests.get(f"{API_BASE}/meeting-rooms", headers=headers)
    if response.status_code != 200:
        print(f"❌ List meeting rooms failed: {response.status_code}")
        return False
    
    rooms_list = response.json()
    print(f"✅ Listed meeting rooms: {len(rooms_list)} rooms found")
    
    # Step 8: Test code access with meeting room code (should fail)
    code_request = {"code": room_code}
    response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
    if response.status_code == 404:
        print(f"✅ Meeting room code properly rejected by card access endpoint")
    else:
        print(f"⚠️  Meeting room code handling: {response.status_code}")
    
    # Step 9: Close meeting room
    response = requests.delete(f"{API_BASE}/meeting-rooms/{room_code}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Close meeting room failed: {response.status_code} - {response.text}")
        return False
    
    close_result = response.json()
    print(f"✅ Meeting room closed: {close_result['message']}")
    
    # Step 10: Verify room is closed (should return 404)
    response = requests.get(f"{API_BASE}/meeting-rooms/{room_code}")
    if response.status_code == 404:
        print(f"✅ Closed meeting room properly returns 404")
    else:
        print(f"⚠️  Closed meeting room still accessible: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("✅ MEETING ROOM WORKFLOW TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_meeting_room_workflow()
    if not success:
        exit(1)