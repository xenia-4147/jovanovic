#!/usr/bin/env python3
"""
Debug Scanner Issue - Investigate why converted cards don't appear in contact list
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

def debug_scanner_issue():
    """Debug why scanner converted cards don't appear in contact list"""
    
    # Setup authentication
    test_email = f"debug_test_{uuid.uuid4().hex[:8]}@example.com"
    
    user_data = {
        "email": test_email,
        "password": "SecurePass123!",
        "first_name": "Debug",
        "last_name": "Tester",
        "gdpr_consent": True,
        "privacy_consent": True,
        "marketing_consent": False
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ Auth failed: {response.status_code}")
        return
    
    auth_data = response.json()
    access_token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"✅ Authenticated as user: {user_id}")
    
    # Step 1: Check initial cards list
    response = requests.get(f"{API_BASE}/cards", headers=headers)
    if response.status_code == 200:
        initial_cards = response.json()
        print(f"📋 Initial cards count: {len(initial_cards)}")
    else:
        print(f"❌ Failed to get initial cards: {response.status_code}")
        return
    
    # Step 2: Create a regular business card for comparison
    regular_card_data = {
        "name": "Regular Test Card",
        "company": "Test Company",
        "position": "Tester",
        "phones": [{"label": "Business", "number": "+49 30 12345678", "is_primary": True}],
        "emails": [{"label": "Business", "address": "test@example.com", "is_primary": True}],
        "is_public": True,
        "accent_color": "#3B82F6"
    }
    
    response = requests.post(f"{API_BASE}/cards", json=regular_card_data, headers=headers)
    if response.status_code == 200:
        regular_card = response.json()
        regular_card_id = regular_card["id"]
        print(f"✅ Created regular card: {regular_card_id}")
    else:
        print(f"❌ Failed to create regular card: {response.status_code} - {response.text}")
        return
    
    # Step 3: Check cards list after regular card creation
    response = requests.get(f"{API_BASE}/cards", headers=headers)
    if response.status_code == 200:
        cards_after_regular = response.json()
        print(f"📋 Cards after regular creation: {len(cards_after_regular)}")
        regular_found = any(card["id"] == regular_card_id for card in cards_after_regular)
        print(f"🔍 Regular card found in list: {regular_found}")
    else:
        print(f"❌ Failed to get cards after regular creation: {response.status_code}")
    
    # Step 4: Create scanner card
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    scan_request = {
        "image_data": test_image_base64,
        "scan_method": "camera"
    }
    
    response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
    if response.status_code != 200:
        print(f"❌ Scanner upload failed: {response.status_code} - {response.text}")
        return
    
    scan_data = response.json()
    scan_id = scan_data["scan_id"]
    print(f"✅ Scanner upload successful: {scan_id}")
    
    # Step 5: Convert scanner to card
    convert_request = {
        "scan_id": scan_id,
        "card_name": "Debug Scanner Card",
        "auto_map_fields": True,
        "field_mapping": {
            "name": "Scanner Test Person",
            "company": "Scanner Test Corp",
            "position": "Scanner Tester"
        }
    }
    
    response = requests.post(f"{API_BASE}/scanner/scan/{scan_id}/convert", json=convert_request, headers=headers)
    if response.status_code == 200:
        scanner_card = response.json()
        scanner_card_id = scanner_card["id"]
        print(f"✅ Scanner conversion successful: {scanner_card_id}")
        print(f"📄 Scanner card data: {json.dumps(scanner_card, indent=2)}")
    else:
        print(f"❌ Scanner conversion failed: {response.status_code} - {response.text}")
        return
    
    # Step 6: Check cards list after scanner conversion
    response = requests.get(f"{API_BASE}/cards", headers=headers)
    if response.status_code == 200:
        final_cards = response.json()
        print(f"📋 Final cards count: {len(final_cards)}")
        
        scanner_found = any(card["id"] == scanner_card_id for card in final_cards)
        regular_still_found = any(card["id"] == regular_card_id for card in final_cards)
        
        print(f"🔍 Scanner card found in list: {scanner_found}")
        print(f"🔍 Regular card still found: {regular_still_found}")
        
        if not scanner_found:
            print("❌ ISSUE CONFIRMED: Scanner converted card is NOT appearing in GET /api/cards")
            print("📋 Cards in list:")
            for card in final_cards:
                print(f"   - {card['id']}: {card['name']} (owner: {card.get('is_owner', 'unknown')})")
        else:
            print("✅ Scanner card appears correctly in contact list")
    else:
        print(f"❌ Failed to get final cards: {response.status_code}")
    
    # Step 7: Try to get the scanner card directly
    response = requests.get(f"{API_BASE}/cards/{scanner_card_id}", headers=headers)
    if response.status_code == 200:
        direct_card = response.json()
        print(f"✅ Scanner card accessible directly: {direct_card['name']}")
        print(f"📄 Direct card data: {json.dumps(direct_card, indent=2)}")
    else:
        print(f"❌ Scanner card not accessible directly: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_scanner_issue()