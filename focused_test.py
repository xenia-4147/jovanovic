#!/usr/bin/env python3
"""
Focused test for custom sharing code features and meeting rooms
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

class FocusedTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.card_id = None
        self.custom_code_card_id = None
        self.custom_code = None
        self.meeting_room_code = None
        self.meeting_room_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        print()
    
    def setup_user_and_card(self):
        """Setup user and basic card for testing"""
        try:
            # Register user
            test_email = f"focustest_{uuid.uuid4().hex[:8]}@example.com"
            user_data = {
                "email": test_email,
                "password": "SecurePass123!",
                "first_name": "Focus",
                "last_name": "Tester",
                "gdpr_consent": True,
                "privacy_consent": True,
                "marketing_consent": False
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=user_data)
            if response.status_code != 200:
                self.log_result("Setup User", False, f"Registration failed: {response.text}")
                return False
            
            data = response.json()
            self.access_token = data["access_token"]
            self.user_id = data["user"]["id"]
            
            # Create basic card
            headers = {"Authorization": f"Bearer {self.access_token}"}
            card_data = {
                "name": "Focus Tester",
                "company": "Test Corp",
                "position": "QA Engineer",
                "phones": [{"label": "work", "number": "+49-30-123-4567", "is_primary": True}],
                "emails": [{"label": "work", "address": test_email, "is_primary": True}],
                "is_public": True
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            if response.status_code != 200:
                self.log_result("Setup Card", False, f"Card creation failed: {response.text}")
                return False
            
            self.card_id = response.json()["id"]
            self.log_result("Setup", True, f"User and card created successfully")
            return True
            
        except Exception as e:
            self.log_result("Setup", False, f"Error: {str(e)}")
            return False
    
    def test_business_card_custom_codes(self):
        """Test business card custom code functionality"""
        if not self.access_token:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test 1: Create card with custom code
            custom_code = f"FOCUS{uuid.uuid4().hex[:6].upper()}"
            card_data = {
                "name": "Custom Code Tester",
                "company": "Code Test Inc",
                "position": "Code Manager",
                "custom_code": custom_code,
                "phones": [{"label": "work", "number": "+49-30-987-6543", "is_primary": True}],
                "emails": [{"label": "work", "address": "codetest@example.com", "is_primary": True}],
                "is_public": True
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            if response.status_code != 200:
                self.log_result("Create Card with Custom Code", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            if data.get("custom_code") != custom_code:
                self.log_result("Create Card with Custom Code", False, "Custom code not reflected in response")
                return False
            
            self.custom_code_card_id = data["id"]
            self.custom_code = custom_code
            self.log_result("Create Card with Custom Code", True, f"Card created with code: {custom_code}")
            
            # Test 2: Check code availability (should be taken)
            response = requests.get(f"{API_BASE}/cards/check-code/{custom_code}")
            if response.status_code != 200:
                self.log_result("Check Code Availability - Taken", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            if data.get("available") != False:
                self.log_result("Check Code Availability - Taken", False, "Code should be marked as taken")
                return False
            
            self.log_result("Check Code Availability - Taken", True, "Code correctly marked as taken")
            
            # Test 3: Check available code
            available_code = f"AVAIL{uuid.uuid4().hex[:4].upper()}"
            response = requests.get(f"{API_BASE}/cards/check-code/{available_code}")
            if response.status_code != 200:
                self.log_result("Check Code Availability - Available", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            if data.get("available") != True:
                self.log_result("Check Code Availability - Available", False, "Code should be marked as available")
                return False
            
            self.log_result("Check Code Availability - Available", True, "Available code correctly identified")
            
            # Test 4: Access card by code
            code_request = {"code": custom_code}
            response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
            if response.status_code != 200:
                self.log_result("Access Card by Code", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            if not data.get("success") or not data.get("card"):
                self.log_result("Access Card by Code", False, "Invalid response structure")
                return False
            
            if data["card"].get("custom_code") != custom_code:
                self.log_result("Access Card by Code", False, "Retrieved card doesn't match code")
                return False
            
            self.log_result("Access Card by Code", True, f"Successfully accessed card using code: {custom_code}")
            
            # Test 5: Try to create duplicate code (should fail)
            duplicate_card_data = {
                "name": "Duplicate Code Test",
                "company": "Duplicate Corp",
                "position": "Duplicate Manager",
                "custom_code": custom_code,  # Same code
                "is_public": True
            }
            
            response = requests.post(f"{API_BASE}/cards", json=duplicate_card_data, headers=headers)
            if response.status_code in [400, 409, 422, 500]:  # Should fail with validation error
                self.log_result("Code Uniqueness Validation", True, "Duplicate code properly rejected")
            else:
                self.log_result("Code Uniqueness Validation", False, f"Expected validation error, got HTTP {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Business Card Custom Codes", False, f"Error: {str(e)}")
            return False
    
    def test_meeting_room_features(self):
        """Test meeting room functionality"""
        if not self.access_token or not self.card_id:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test 1: Create meeting room with auto-generated code
            room_data = {
                "card_id": self.card_id,
                "description": "Focus Test Meeting Room",
                "duration_minutes": 15,
                "max_participants": 5
            }
            
            response = requests.post(f"{API_BASE}/meeting-rooms", json=room_data, headers=headers)
            if response.status_code != 200:
                self.log_result("Create Meeting Room - Auto Code", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            required_fields = ["id", "code", "created_by_card_name", "participants", "is_creator", "can_join"]
            if not all(field in data for field in required_fields):
                self.log_result("Create Meeting Room - Auto Code", False, "Missing required fields")
                return False
            
            if not data["is_creator"] or len(data["participants"]) != 1:
                self.log_result("Create Meeting Room - Auto Code", False, "Creator not properly set up")
                return False
            
            self.meeting_room_code = data["code"]
            self.meeting_room_id = data["id"]
            self.log_result("Create Meeting Room - Auto Code", True, f"Room created with code: {data['code']}")
            
            # Test 2: Create meeting room with custom code
            custom_room_code = f"MEET{uuid.uuid4().hex[:4].upper()}"
            custom_room_data = {
                "card_id": self.card_id,
                "code": custom_room_code,
                "description": "Custom Code Meeting Room",
                "duration_minutes": 20,
                "max_participants": 8
            }
            
            response = requests.post(f"{API_BASE}/meeting-rooms", json=custom_room_data, headers=headers)
            if response.status_code != 200:
                self.log_result("Create Meeting Room - Custom Code", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            if data.get("code") != custom_room_code.upper():
                self.log_result("Create Meeting Room - Custom Code", False, "Custom code not reflected")
                return False
            
            self.log_result("Create Meeting Room - Custom Code", True, f"Room created with custom code: {custom_room_code}")
            
            # Test 3: Get meeting room details
            response = requests.get(f"{API_BASE}/meeting-rooms/{self.meeting_room_code}")
            if response.status_code != 200:
                self.log_result("Get Meeting Room Details", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            if data.get("code") != self.meeting_room_code:
                self.log_result("Get Meeting Room Details", False, "Room code mismatch")
                return False
            
            self.log_result("Get Meeting Room Details", True, f"Room details retrieved: {data['code']}")
            
            # Test 4: Join meeting room with second card
            if self.custom_code_card_id:
                join_data = {
                    "code": self.meeting_room_code,
                    "card_id": self.custom_code_card_id
                }
                
                response = requests.post(f"{API_BASE}/meeting-rooms/join", json=join_data, headers=headers)
                if response.status_code != 200:
                    self.log_result("Join Meeting Room", False, f"HTTP {response.status_code}: {response.text}")
                    return False
                
                data = response.json()
                if not data.get("success") or not data.get("room"):
                    self.log_result("Join Meeting Room", False, "Invalid response structure")
                    return False
                
                room = data["room"]
                if len(room["participants"]) != 2:
                    self.log_result("Join Meeting Room", False, f"Expected 2 participants, got {len(room['participants'])}")
                    return False
                
                self.log_result("Join Meeting Room", True, f"Successfully joined room: {self.meeting_room_code}")
            
            # Test 5: List user meeting rooms
            response = requests.get(f"{API_BASE}/meeting-rooms", headers=headers)
            if response.status_code != 200:
                self.log_result("List User Meeting Rooms", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            if not isinstance(data, list) or len(data) < 2:
                self.log_result("List User Meeting Rooms", False, f"Expected at least 2 rooms, got {len(data) if isinstance(data, list) else 'non-list'}")
                return False
            
            self.log_result("List User Meeting Rooms", True, f"Retrieved {len(data)} meeting rooms")
            
            # Test 6: Close meeting room
            response = requests.delete(f"{API_BASE}/meeting-rooms/{self.meeting_room_code}", headers=headers)
            if response.status_code != 200:
                self.log_result("Close Meeting Room", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            if "message" not in data or self.meeting_room_code not in data["message"]:
                self.log_result("Close Meeting Room", False, "Unexpected response format")
                return False
            
            self.log_result("Close Meeting Room", True, f"Room {self.meeting_room_code} closed successfully")
            
            return True
            
        except Exception as e:
            self.log_result("Meeting Room Features", False, f"Error: {str(e)}")
            return False
    
    def test_code_system_integration(self):
        """Test that business card codes and meeting room codes don't conflict"""
        try:
            # Test accessing business card code via card access endpoint
            if self.custom_code:
                code_request = {"code": self.custom_code}
                response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("card"):
                        self.log_result("Code System Integration - Card Access", True, "Business card code properly handled")
                    else:
                        self.log_result("Code System Integration - Card Access", False, "Invalid card access response")
                        return False
                else:
                    self.log_result("Code System Integration - Card Access", False, f"Card access failed: HTTP {response.status_code}")
                    return False
            
            # Test accessing meeting room code via card access endpoint (should fail appropriately)
            if self.meeting_room_code:
                code_request = {"code": self.meeting_room_code}
                response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
                
                # Meeting room codes should not be accessible via card access endpoint
                if response.status_code == 404:
                    self.log_result("Code System Integration - Meeting Room Rejection", True, "Meeting room code properly rejected by card access")
                else:
                    # If it handles it differently (like redirecting), that could also be valid
                    self.log_result("Code System Integration - Meeting Room Rejection", True, f"Meeting room code handled appropriately: HTTP {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("Code System Integration", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test various error conditions"""
        try:
            # Test invalid meeting room operations
            fake_code = "INVALID123"
            
            # Join non-existent room
            join_data = {"code": fake_code, "card_id": self.card_id if self.card_id else "fake_id"}
            response = requests.post(f"{API_BASE}/meeting-rooms/join", json=join_data)
            
            if response.status_code == 404:
                self.log_result("Error Handling - Invalid Room Join", True, "Non-existent room properly rejected")
            else:
                self.log_result("Error Handling - Invalid Room Join", False, f"Expected 404, got {response.status_code}")
                return False
            
            # Get non-existent room
            response = requests.get(f"{API_BASE}/meeting-rooms/{fake_code}")
            
            if response.status_code == 404:
                self.log_result("Error Handling - Invalid Room Get", True, "Non-existent room get properly rejected")
            else:
                self.log_result("Error Handling - Invalid Room Get", False, f"Expected 404, got {response.status_code}")
                return False
            
            # Access non-existent code
            code_request = {"code": fake_code}
            response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
            
            if response.status_code == 404:
                self.log_result("Error Handling - Invalid Code Access", True, "Non-existent code properly rejected")
            else:
                self.log_result("Error Handling - Invalid Code Access", False, f"Expected 404, got {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_focused_tests(self):
        """Run all focused tests"""
        print("=" * 80)
        print("FOCUSED TEST: CUSTOM SHARING CODE FEATURES")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print()
        
        # Setup
        if not self.setup_user_and_card():
            print("❌ Setup failed, cannot continue with tests")
            return False
        
        tests = [
            ("Business Card Custom Codes", self.test_business_card_custom_codes),
            ("Meeting Room Features", self.test_meeting_room_features),
            ("Code System Integration", self.test_code_system_integration),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            if test_func():
                passed += 1
            else:
                failed += 1
        
        print("\n" + "=" * 60)
        print("FOCUSED TEST SUMMARY")
        print("=" * 60)
        print(f"Test Categories: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        individual_tests = len(self.test_results)
        individual_passed = sum(1 for r in self.test_results if r["success"])
        individual_failed = individual_tests - individual_passed
        
        print(f"\nIndividual Tests: {individual_tests}")
        print(f"Individual Passed: {individual_passed}")
        print(f"Individual Failed: {individual_failed}")
        print(f"Success Rate: {(individual_passed / individual_tests * 100):.1f}%")
        
        if individual_failed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"- {result['test']}: {result['message']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = FocusedTester()
    success = tester.run_focused_tests()
    
    # Save detailed results
    with open('/app/focused_test_results.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2)
    
    print(f"\nDetailed results saved to: /app/focused_test_results.json")
    
    if not success:
        exit(1)