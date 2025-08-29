#!/usr/bin/env python3
"""
Focused Business Card Scanner Testing - Review Request
Tests the FIXED Business Card Scanner workflow after custom_code null handling fixes
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

class ScannerWorkflowTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message="", response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response"] = response_data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
    
    def setup_authentication(self):
        """Setup authentication for testing"""
        try:
            # Generate unique test data
            test_email = f"scanner_test_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "SecurePass123!",
                "first_name": "Scanner",
                "last_name": "Tester",
                "gdpr_consent": True,
                "privacy_consent": True,
                "marketing_consent": False
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.log_result("Authentication Setup", True, f"User registered: {test_email}")
                return True
            else:
                self.log_result("Authentication Setup", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Error: {str(e)}")
            return False
    
    def test_scanner_conversion_with_custom_code_fix(self):
        """Test POST /api/scanner/scan/{scan_id}/convert with custom_code null handling fix"""
        if not self.access_token:
            self.log_result("Scanner Conversion Fix", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Step 1: Upload test image
            test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            scan_request = {
                "image_data": test_image_base64,
                "scan_method": "camera",
                "device_info": {
                    "platform": "web",
                    "user_agent": "test_client"
                }
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Scanner Conversion Fix", False, f"Upload failed: HTTP {response.status_code}", response.text)
                return False
            
            scan_data = response.json()
            scan_id = scan_data["scan_id"]
            
            # Step 2: Convert to business card (this is where the custom_code null fix should work)
            convert_request = {
                "scan_id": scan_id,
                "card_name": "Test Scanned Card with Null Custom Code",
                "auto_map_fields": True,
                "field_mapping": {
                    "name": "Dr. Maria Schmidt",
                    "company": "Tech Solutions GmbH",
                    "position": "Senior Developer",
                    "phone": "+49 30 12345678",
                    "email": "maria.schmidt@techsolutions.de"
                }
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan/{scan_id}/convert", json=convert_request, headers=headers)
            
            if response.status_code == 200:
                card_data = response.json()
                card_id = card_data["id"]
                
                # Step 3: Verify the card was created successfully and appears in user's cards
                response = requests.get(f"{API_BASE}/cards", headers=headers)
                
                if response.status_code == 200:
                    cards = response.json()
                    converted_card_found = any(card.get("id") == card_id for card in cards)
                    
                    if converted_card_found:
                        self.log_result("Scanner Conversion Fix", True, f"✅ FIXED: Scanner conversion with null custom_code works! Card {card_id} appears in contact list")
                        return True
                    else:
                        self.log_result("Scanner Conversion Fix", False, f"❌ ISSUE: Card {card_id} created but not in contact list")
                        return False
                else:
                    self.log_result("Scanner Conversion Fix", False, f"Failed to get cards: HTTP {response.status_code}")
                    return False
            else:
                self.log_result("Scanner Conversion Fix", False, f"Conversion failed: HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Scanner Conversion Fix", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_scanned_cards_null_custom_code(self):
        """Test creating multiple scanned cards to ensure sparse index allows multiple null custom_code values"""
        if not self.access_token:
            self.log_result("Multiple Scanned Cards", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            created_cards = []
            
            # Create 3 scanned cards to test multiple null custom_code values
            for i in range(3):
                # Upload image
                scan_request = {
                    "image_data": test_image_base64,
                    "scan_method": "camera",
                    "device_info": {"platform": "web", "user_agent": "test_client"}
                }
                
                response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
                if response.status_code != 200:
                    continue
                    
                scan_id = response.json()["scan_id"]
                
                # Convert to card
                convert_request = {
                    "scan_id": scan_id,
                    "card_name": f"Scanned Card #{i+1}",
                    "auto_map_fields": True,
                    "field_mapping": {
                        "name": f"Test Person {i+1}",
                        "company": f"Company {i+1}",
                        "position": "Manager"
                    }
                }
                
                response = requests.post(f"{API_BASE}/scanner/scan/{scan_id}/convert", json=convert_request, headers=headers)
                if response.status_code == 200:
                    card_data = response.json()
                    created_cards.append(card_data["id"])
            
            if len(created_cards) >= 2:
                # Verify all cards appear in user's list
                response = requests.get(f"{API_BASE}/cards", headers=headers)
                if response.status_code == 200:
                    cards = response.json()
                    found_cards = [card["id"] for card in cards if card["id"] in created_cards]
                    
                    if len(found_cards) == len(created_cards):
                        self.log_result("Multiple Scanned Cards", True, f"✅ FIXED: Created {len(created_cards)} scanned cards with null custom_code - all appear in contact list")
                        return True
                    else:
                        self.log_result("Multiple Scanned Cards", False, f"❌ ISSUE: Created {len(created_cards)} cards but only {len(found_cards)} appear in list")
                        return False
                else:
                    self.log_result("Multiple Scanned Cards", False, f"Failed to get cards: HTTP {response.status_code}")
                    return False
            else:
                self.log_result("Multiple Scanned Cards", False, f"Only created {len(created_cards)} cards, need at least 2 for test")
                return False
                
        except Exception as e:
            self.log_result("Multiple Scanned Cards", False, f"Error: {str(e)}")
            return False
    
    def test_complete_scanner_workflow(self):
        """Test complete end-to-end scanner workflow: Upload → Poll → Convert → Verify in contact list"""
        if not self.access_token:
            self.log_result("Complete Scanner Workflow", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Step 1: Upload test image
            test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            scan_request = {
                "image_data": test_image_base64,
                "scan_method": "camera"
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Complete Scanner Workflow", False, f"Upload failed: HTTP {response.status_code}")
                return False
            
            scan_data = response.json()
            scan_id = scan_data["scan_id"]
            
            # Step 2: Poll for results
            response = requests.get(f"{API_BASE}/scanner/scan/{scan_id}", headers=headers)
            
            if response.status_code != 200:
                self.log_result("Complete Scanner Workflow", False, f"Poll failed: HTTP {response.status_code}")
                return False
            
            poll_data = response.json()
            
            # Step 3: Convert to business card
            convert_request = {
                "scan_id": scan_id,
                "card_name": "Complete Workflow Test Card",
                "auto_map_fields": True,
                "field_mapping": {
                    "name": "Dr. Anna Weber",
                    "company": "Digital Solutions AG",
                    "position": "CTO",
                    "phone": "+49 89 98765432",
                    "email": "anna.weber@digitalsolutions.de"
                }
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan/{scan_id}/convert", json=convert_request, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Complete Scanner Workflow", False, f"Convert failed: HTTP {response.status_code}", response.text)
                return False
            
            card_data = response.json()
            card_id = card_data["id"]
            
            # Step 4: Verify card appears in contact list
            response = requests.get(f"{API_BASE}/cards", headers=headers)
            
            if response.status_code == 200:
                cards = response.json()
                converted_card_found = any(card.get("id") == card_id for card in cards)
                
                if converted_card_found:
                    self.log_result("Complete Scanner Workflow", True, f"✅ COMPLETE SUCCESS: Full workflow works! Upload → Poll → Convert → Card {card_id} in contact list")
                    return True
                else:
                    self.log_result("Complete Scanner Workflow", False, f"❌ FINAL STEP FAILED: Card {card_id} not in contact list")
                    return False
            else:
                self.log_result("Complete Scanner Workflow", False, f"Failed to get contact list: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Complete Scanner Workflow", False, f"Error: {str(e)}")
            return False
    
    def run_focused_tests(self):
        """Run focused scanner tests for the review request"""
        print("=" * 80)
        print("🔍 FOCUSED BUSINESS CARD SCANNER TESTING - CUSTOM_CODE NULL HANDLING FIXES")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print("🎯 FOCUS: Testing FIXED scanner workflow after custom_code null handling fixes")
        print()
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ CRITICAL: Authentication setup failed - cannot proceed with tests")
            return
        
        tests = [
            ("Scanner Conversion with Custom Code Fix", self.test_scanner_conversion_with_custom_code_fix),
            ("Multiple Scanned Cards with Null Custom Code", self.test_multiple_scanned_cards_null_custom_code),
            ("Complete Scanner Workflow End-to-End", self.test_complete_scanner_workflow),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"🧪 Running: {test_name}")
            if test_func():
                passed += 1
            else:
                failed += 1
            print("-" * 60)
        
        print("=" * 60)
        print(f"📊 FOCUSED TEST RESULTS:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "0%")
        print("=" * 60)
        
        if failed == 0:
            print("🎉 ALL SCANNER TESTS PASSED! The custom_code null handling fixes are working correctly.")
        else:
            print("⚠️  Some scanner tests failed. The 'nothing happens after photographing business card' issue may still exist.")

if __name__ == "__main__":
    tester = ScannerWorkflowTester()
    tester.run_focused_tests()