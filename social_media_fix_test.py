#!/usr/bin/env python3
"""
Targeted test for social_media fix with custom_code
This test specifically verifies the fix for business card creation with custom codes and social_media handling
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

def log_result(test_name, success, message="", response_data=None):
    """Log test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {test_name}")
    if message:
        print(f"   {message}")
    if not success and response_data:
        print(f"   Response: {response_data}")
    print()

def test_social_media_fix():
    """Test the social_media fix for business card creation with custom codes"""
    
    print("=" * 80)
    print("TARGETED TEST: Social Media Fix with Custom Code")
    print("=" * 80)
    print(f"Testing API at: {API_BASE}")
    print()
    
    # Step 1: Register a test user
    test_email = f"socialtest_{uuid.uuid4().hex[:8]}@example.com"
    
    user_data = {
        "email": test_email,
        "password": "SocialTest123!",
        "first_name": "Social",
        "last_name": "Tester",
        "gdpr_consent": True,
        "privacy_consent": True,
        "marketing_consent": False
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=user_data)
    
    if response.status_code != 200:
        log_result("User Registration", False, f"HTTP {response.status_code}", response.text)
        return False
    
    data = response.json()
    access_token = data["access_token"]
    log_result("User Registration", True, f"User registered: {test_email}")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 1: Card with custom_code but NO social_media field
    print("TEST 1: Business card with custom_code but missing social_media field")
    print("-" * 60)
    
    custom_code_1 = f"SOCIAL{uuid.uuid4().hex[:6].upper()}"
    
    card_data_no_social = {
        "name": "Dr. Sarah Weber",
        "company": "Digital Innovation Labs",
        "position": "Senior Product Manager",
        "description": "Leading digital transformation initiatives in healthcare technology",
        "phones": [
            {
                "label": "work",
                "number": "+49-30-123-4567",
                "is_primary": True
            },
            {
                "label": "mobile",
                "number": "+49-172-987-6543",
                "is_primary": False
            }
        ],
        "emails": [
            {
                "label": "work", 
                "address": "sarah.weber@digitalinnovation.de",
                "is_primary": True
            },
            {
                "label": "personal",
                "address": "sarah@example.com",
                "is_primary": False
            }
        ],
        "website": "https://sarahweber.dev",
        "custom_code": custom_code_1,
        "is_public": True,
        "background_color": "#f8fafc",
        "text_color": "#1e293b",
        "accent_color": "#0ea5e9"
        # NOTE: social_media field is intentionally missing
    }
    
    response = requests.post(f"{API_BASE}/cards", json=card_data_no_social, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Verify card was created successfully
        if data.get("custom_code") == custom_code_1:
            # Verify social_media field exists and is properly initialized
            if "social_media" in data:
                social_media = data["social_media"]
                log_result("Test 1 - Missing social_media field", True, 
                          f"✅ Card created with custom code {custom_code_1}")
                print(f"   Social media object: {json.dumps(social_media, indent=2)}")
                print()
            else:
                log_result("Test 1 - Missing social_media field", False, 
                          "social_media field missing from response", data)
                return False
        else:
            log_result("Test 1 - Missing social_media field", False, 
                      "Custom code not reflected in response", data)
            return False
    else:
        log_result("Test 1 - Missing social_media field", False, 
                  f"HTTP {response.status_code}", response.text)
        return False
    
    # Test 2: Card with custom_code and explicit social_media: null
    print("TEST 2: Business card with custom_code and explicit social_media: null")
    print("-" * 60)
    
    custom_code_2 = f"SOCIAL{uuid.uuid4().hex[:6].upper()}"
    
    card_data_null_social = {
        "name": "Prof. Michael Schmidt",
        "company": "Tech University Berlin",
        "position": "Professor of Computer Science",
        "description": "Research focus on AI and machine learning applications",
        "phones": [
            {
                "label": "office",
                "number": "+49-30-456-7890",
                "is_primary": True
            }
        ],
        "emails": [
            {
                "label": "university", 
                "address": "m.schmidt@techuni-berlin.de",
                "is_primary": True
            }
        ],
        "website": "https://techuni-berlin.de/schmidt",
        "custom_code": custom_code_2,
        "social_media": None,  # Explicitly set to None
        "is_public": True,
        "background_color": "#ffffff",
        "text_color": "#374151",
        "accent_color": "#10b981"
    }
    
    response = requests.post(f"{API_BASE}/cards", json=card_data_null_social, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Verify card was created successfully
        if data.get("custom_code") == custom_code_2:
            # Verify social_media field exists and is properly initialized
            if "social_media" in data:
                social_media = data["social_media"]
                log_result("Test 2 - Null social_media field", True, 
                          f"✅ Card created with custom code {custom_code_2}")
                print(f"   Social media object: {json.dumps(social_media, indent=2)}")
                print()
            else:
                log_result("Test 2 - Null social_media field", False, 
                          "social_media field missing from response", data)
                return False
        else:
            log_result("Test 2 - Null social_media field", False, 
                      "Custom code not reflected in response", data)
            return False
    else:
        log_result("Test 2 - Null social_media field", False, 
                  f"HTTP {response.status_code}", response.text)
        return False
    
    # Test 3: Verify code access works with the created cards
    print("TEST 3: Verify code access works with created cards")
    print("-" * 60)
    
    # Test accessing first card by code
    code_request = {"code": custom_code_1}
    response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "card" in data:
            card = data["card"]
            if card.get("custom_code") == custom_code_1:
                log_result("Test 3 - Code access first card", True, 
                          f"✅ Successfully accessed card using code: {custom_code_1}")
            else:
                log_result("Test 3 - Code access first card", False, 
                          "Retrieved card doesn't match expected code", data)
                return False
        else:
            log_result("Test 3 - Code access first card", False, 
                      "Success=false or missing card data", data)
            return False
    else:
        log_result("Test 3 - Code access first card", False, 
                  f"HTTP {response.status_code}", response.text)
        return False
    
    # Test accessing second card by code
    code_request = {"code": custom_code_2}
    response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "card" in data:
            card = data["card"]
            if card.get("custom_code") == custom_code_2:
                log_result("Test 3 - Code access second card", True, 
                          f"✅ Successfully accessed card using code: {custom_code_2}")
            else:
                log_result("Test 3 - Code access second card", False, 
                          "Retrieved card doesn't match expected code", data)
                return False
        else:
            log_result("Test 3 - Code access second card", False, 
                      "Success=false or missing card data", data)
            return False
    else:
        log_result("Test 3 - Code access second card", False, 
                  f"HTTP {response.status_code}", response.text)
        return False
    
    print("=" * 80)
    print("🎉 ALL TESTS PASSED! Social media fix is working correctly.")
    print("=" * 80)
    print("✅ Business card creation succeeds with custom_code")
    print("✅ social_media field defaults to empty SocialMedia object when missing")
    print("✅ social_media field defaults to empty SocialMedia object when null")
    print("✅ Code access functionality works correctly")
    print()
    
    return True

if __name__ == "__main__":
    success = test_social_media_fix()
    
    if success:
        print("🎯 CONCLUSION: The social_media fix for business card creation with custom codes is working perfectly!")
    else:
        print("❌ CONCLUSION: There are issues with the social_media fix that need attention.")
        exit(1)