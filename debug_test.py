#!/usr/bin/env python3
"""
Debug test to identify specific issues with the enhanced digital business cards API
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

def debug_card_access():
    """Debug card access issues"""
    print("=== DEBUGGING CARD ACCESS ISSUES ===\n")
    
    # Step 1: Register and get token
    test_email = f"debug_{uuid.uuid4().hex[:8]}@example.com"
    user_data = {
        "email": test_email,
        "password": "DebugTest123!",
        "first_name": "Debug",
        "last_name": "User",
        "gdpr_consent": True,
        "privacy_consent": True,
        "marketing_consent": False
    }
    
    print("1. Registering user...")
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"Registration failed: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    access_token = data["access_token"]
    user_id = data["user"]["id"]
    print(f"   User registered: {test_email}")
    print(f"   User ID: {user_id}")
    
    # Step 2: Create business card
    headers = {"Authorization": f"Bearer {access_token}"}
    card_data = {
        "name": "Debug Card",
        "company": "Debug Corp",
        "position": "Debugger",
        "phones": [{"label": "work", "number": "+1-555-DEBUG", "is_primary": True}],
        "emails": [{"label": "work", "address": "debug@example.com", "is_primary": True}],
        "is_public": True
    }
    
    print("\n2. Creating business card...")
    response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
    if response.status_code != 200:
        print(f"Card creation failed: {response.status_code} - {response.text}")
        return
    
    card_response = response.json()
    card_id = card_response["id"]
    print(f"   Card created: {card_response['name']}")
    print(f"   Card ID: {card_id}")
    
    # Step 3: Test getting user cards
    print("\n3. Getting user cards...")
    response = requests.get(f"{API_BASE}/cards", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        cards = response.json()
        print(f"   Found {len(cards)} cards")
        if cards:
            print(f"   First card ID: {cards[0]['id']}")
    else:
        print(f"   Error: {response.text}")
    
    # Step 4: Test accessing specific card (public, should work without auth)
    print(f"\n4. Accessing card {card_id} without authentication...")
    response = requests.get(f"{API_BASE}/cards/{card_id}")
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        print("   Success: Card accessed without auth")
    
    # Step 5: Test accessing specific card with authentication
    print(f"\n5. Accessing card {card_id} with authentication...")
    response = requests.get(f"{API_BASE}/cards/{card_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        card_data = response.json()
        print(f"   Success: Card accessed with auth, is_owner: {card_data.get('is_owner')}")
    
    # Step 6: Test QR code generation
    print(f"\n6. Testing QR code generation for card {card_id}...")
    response = requests.get(f"{API_BASE}/cards/{card_id}/qr")
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        print(f"   Success: QR code generated, size: {len(response.content)} bytes")
    
    # Step 7: Test vCard generation
    print(f"\n7. Testing vCard generation for card {card_id}...")
    response = requests.get(f"{API_BASE}/cards/{card_id}/vcard")
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        print("   Success: vCard generated")
    
    # Step 8: Test updating card
    print(f"\n8. Testing card update for card {card_id}...")
    update_data = {"description": "Updated debug description"}
    response = requests.put(f"{API_BASE}/cards/{card_id}", json=update_data, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        print("   Success: Card updated")
    
    # Step 9: Test privacy export
    print(f"\n9. Testing privacy data export...")
    response = requests.get(f"{API_BASE}/privacy/export", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        print("   Success: Data exported")
    
    # Step 10: Test non-existent card
    fake_card_id = str(uuid.uuid4())
    print(f"\n10. Testing non-existent card {fake_card_id}...")
    response = requests.get(f"{API_BASE}/cards/{fake_card_id}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print("   Success: Properly returned 404")
    else:
        print(f"   Issue: Expected 404, got {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_card_access()