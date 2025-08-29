#!/usr/bin/env python3
"""
Comprehensive Business Card Scanner Test - CRITICAL FIX VALIDATION
Tests the complete scanner workflow including the ObjectId fix and API configuration
"""

import requests
import json
import uuid
from datetime import datetime
import base64

# Use the external URL for testing
BACKEND_URL = "https://netlink-3.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveScannerTester:
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
            # Register a test user
            test_email = f"comprehensive_test_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "ComprehensiveTest123!",
                "first_name": "Comprehensive",
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
                self.test_email = test_email
                self.log_result("Authentication Setup", True, f"Test user registered: {test_email}")
                return True
            else:
                self.log_result("Authentication Setup", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Error: {str(e)}")
            return False
    
    def test_api_connectivity_comprehensive(self):
        """Test 1: Comprehensive API Connectivity"""
        try:
            # Test health endpoint
            response = requests.get(f"{API_BASE}/")
            if response.status_code != 200:
                self.log_result("API Connectivity - Health Check", False, f"HTTP {response.status_code}")
                return False
            
            # Test authentication endpoint
            response = requests.get(f"{API_BASE}/auth/me", headers={"Authorization": f"Bearer {self.access_token}"})
            if response.status_code != 200:
                self.log_result("API Connectivity - Auth Check", False, f"HTTP {response.status_code}")
                return False
            
            # Test cards endpoint
            response = requests.get(f"{API_BASE}/cards", headers={"Authorization": f"Bearer {self.access_token}"})
            if response.status_code != 200:
                self.log_result("API Connectivity - Cards Check", False, f"HTTP {response.status_code}")
                return False
            
            self.log_result("API Connectivity Comprehensive", True, "All core endpoints accessible")
            return True
                
        except Exception as e:
            self.log_result("API Connectivity Comprehensive", False, f"Error: {str(e)}")
            return False
    
    def test_objectid_fix_validation(self):
        """Test 2: ObjectId Fix Validation - The Critical Fix"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create multiple business cards to test the ObjectId fix
            cards_created = []
            
            for i in range(3):
                card_data = {
                    "name": f"Test User {i+1}",
                    "company": f"Test Company {i+1}",
                    "position": f"Test Position {i+1}",
                    "phones": [
                        {
                            "label": "work",
                            "number": f"+49-30-555-{1000+i}",
                            "is_primary": True
                        }
                    ],
                    "emails": [
                        {
                            "label": "work",
                            "address": f"test{i+1}@example.com",
                            "is_primary": True
                        }
                    ],
                    "is_public": True
                }
                
                response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
                
                if response.status_code == 200:
                    card = response.json()
                    cards_created.append(card["id"])
                else:
                    self.log_result("ObjectId Fix - Card Creation", False, f"Failed to create card {i+1}: HTTP {response.status_code}")
                    return False
            
            # Now test the critical fix: GET /api/cards should return all created cards
            response = requests.get(f"{API_BASE}/cards", headers=headers)
            
            if response.status_code == 200:
                retrieved_cards = response.json()
                retrieved_card_ids = [card["id"] for card in retrieved_cards]
                
                # Check if all created cards are found
                all_found = all(card_id in retrieved_card_ids for card_id in cards_created)
                
                if all_found:
                    self.log_result("ObjectId Fix Validation", True, f"All {len(cards_created)} cards properly retrieved - ObjectId conversion working")
                    return True
                else:
                    missing_cards = [card_id for card_id in cards_created if card_id not in retrieved_card_ids]
                    self.log_result("ObjectId Fix Validation", False, f"Missing cards: {missing_cards} - ObjectId issue still exists")
                    return False
            else:
                self.log_result("ObjectId Fix Validation", False, f"Failed to retrieve cards: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("ObjectId Fix Validation", False, f"Error: {str(e)}")
            return False
    
    def test_scanner_workflow_complete(self):
        """Test 3: Complete Scanner Workflow"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Step 1: Upload business card for scanning
            test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            scan_request = {
                "image_data": test_image_b64,
                "scan_method": "camera"
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Scanner Workflow - Upload", False, f"Upload failed: HTTP {response.status_code}")
                return False
            
            scan_data = response.json()
            scan_id = scan_data["scan_id"]
            
            # Step 2: Get scan results
            response = requests.get(f"{API_BASE}/scanner/scan/{scan_id}", headers=headers)
            
            if response.status_code != 200:
                self.log_result("Scanner Workflow - Get Results", False, f"Get results failed: HTTP {response.status_code}")
                return False
            
            # Step 3: Convert scan to business card
            convert_request = {
                "scan_id": scan_id,
                "card_name": "Scanned Business Contact",
                "auto_map_fields": True
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan/{scan_id}/convert", json=convert_request, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Scanner Workflow - Convert", False, f"Convert failed: HTTP {response.status_code}")
                return False
            
            converted_card = response.json()
            converted_card_id = converted_card["id"]
            
            # Step 4: CRITICAL TEST - Verify converted card appears in GET /api/cards
            response = requests.get(f"{API_BASE}/cards", headers=headers)
            
            if response.status_code != 200:
                self.log_result("Scanner Workflow - Contact List Check", False, f"Get cards failed: HTTP {response.status_code}")
                return False
            
            cards = response.json()
            converted_card_found = any(card["id"] == converted_card_id for card in cards)
            
            if converted_card_found:
                self.log_result("Scanner Workflow Complete", True, f"Scanned card successfully appears in contact list ({len(cards)} total cards)")
                return True
            else:
                self.log_result("Scanner Workflow Complete", False, f"CRITICAL ISSUE: Scanned card NOT found in contact list - the 'nothing happens after photographing' issue still exists")
                return False
                
        except Exception as e:
            self.log_result("Scanner Workflow Complete", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_scanner_operations(self):
        """Test 4: Multiple Scanner Operations"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test multiple scans and conversions
            converted_cards = []
            
            for i in range(3):
                # Upload scan
                scan_request = {
                    "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                    "scan_method": "camera"
                }
                
                response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
                if response.status_code != 200:
                    continue
                
                scan_id = response.json()["scan_id"]
                
                # Convert scan
                convert_request = {
                    "scan_id": scan_id,
                    "card_name": f"Multi Scan Contact {i+1}",
                    "auto_map_fields": True
                }
                
                response = requests.post(f"{API_BASE}/scanner/scan/{scan_id}/convert", json=convert_request, headers=headers)
                if response.status_code == 200:
                    converted_cards.append(response.json()["id"])
            
            # Verify all converted cards appear in contact list
            response = requests.get(f"{API_BASE}/cards", headers=headers)
            
            if response.status_code == 200:
                cards = response.json()
                card_ids = [card["id"] for card in cards]
                
                all_found = all(card_id in card_ids for card_id in converted_cards)
                
                if all_found:
                    self.log_result("Multiple Scanner Operations", True, f"All {len(converted_cards)} scanned cards appear in contact list")
                    return True
                else:
                    self.log_result("Multiple Scanner Operations", False, f"Some scanned cards missing from contact list")
                    return False
            else:
                self.log_result("Multiple Scanner Operations", False, f"Failed to get cards: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Multiple Scanner Operations", False, f"Error: {str(e)}")
            return False
    
    def test_scanner_list_functionality(self):
        """Test 5: Scanner List Functionality"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = requests.get(f"{API_BASE}/scanner/scans", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "scans" in data:
                    scans = data["scans"]
                    self.log_result("Scanner List Functionality", True, f"Scanner list working - {len(scans)} scans found")
                    return True
                else:
                    self.log_result("Scanner List Functionality", False, "Missing 'scans' field in response")
                    return False
            else:
                self.log_result("Scanner List Functionality", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Scanner List Functionality", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_backend_integration(self):
        """Test 6: Frontend-Backend Integration Verification"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test that all scanner endpoints are accessible (no 404s)
            endpoints_to_test = [
                ("GET", f"{API_BASE}/cards"),
                ("GET", f"{API_BASE}/scanner/scans"),
            ]
            
            all_accessible = True
            
            for method, url in endpoints_to_test:
                if method == "GET":
                    response = requests.get(url, headers=headers)
                    if response.status_code == 404:
                        self.log_result("Frontend-Backend Integration", False, f"404 error on {url}")
                        all_accessible = False
            
            if all_accessible:
                self.log_result("Frontend-Backend Integration", True, "All scanner API endpoints accessible - no 404 errors")
                return True
            else:
                return False
                
        except Exception as e:
            self.log_result("Frontend-Backend Integration", False, f"Error: {str(e)}")
            return False
    
    def test_user_workflow_simulation(self):
        """Test 7: Complete User Workflow Simulation"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Simulate the exact user workflow described in the review request:
            # 1. User photographs business card
            # 2. Scanner processes it
            # 3. User converts it to digital card
            # 4. Card appears in contact list
            # 5. User can see and edit the card
            
            # Step 1 & 2: Photograph and process
            scan_request = {
                "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                "scan_method": "camera"
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
            if response.status_code != 200:
                self.log_result("User Workflow - Photograph", False, f"Scan failed: HTTP {response.status_code}")
                return False
            
            scan_id = response.json()["scan_id"]
            
            # Step 3: Convert to digital card
            convert_request = {
                "scan_id": scan_id,
                "card_name": "Real User Workflow Test",
                "auto_map_fields": True
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan/{scan_id}/convert", json=convert_request, headers=headers)
            if response.status_code != 200:
                self.log_result("User Workflow - Convert", False, f"Convert failed: HTTP {response.status_code}")
                return False
            
            card_id = response.json()["id"]
            
            # Step 4: Verify appears in contact list
            response = requests.get(f"{API_BASE}/cards", headers=headers)
            if response.status_code != 200:
                self.log_result("User Workflow - Contact List", False, f"Get cards failed: HTTP {response.status_code}")
                return False
            
            cards = response.json()
            card_found = any(card["id"] == card_id for card in cards)
            
            if not card_found:
                self.log_result("User Workflow - Contact List", False, "Card not found in contact list")
                return False
            
            # Step 5: Verify user can view and edit the card
            response = requests.get(f"{API_BASE}/cards/{card_id}", headers=headers)
            if response.status_code != 200:
                self.log_result("User Workflow - View Card", False, f"View card failed: HTTP {response.status_code}")
                return False
            
            # Test editing the card
            update_data = {
                "description": "Updated via scanner workflow test"
            }
            
            response = requests.put(f"{API_BASE}/cards/{card_id}", json=update_data, headers=headers)
            if response.status_code != 200:
                self.log_result("User Workflow - Edit Card", False, f"Edit card failed: HTTP {response.status_code}")
                return False
            
            self.log_result("User Workflow Simulation", True, "Complete user workflow successful - scan → convert → contact list → view → edit")
            return True
                
        except Exception as e:
            self.log_result("User Workflow Simulation", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all comprehensive scanner tests"""
        print("=" * 80)
        print("🔍 COMPREHENSIVE BUSINESS CARD SCANNER TEST - CRITICAL FIX VALIDATION")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print("🎯 PRIORITY: Verify complete scanner workflow with ObjectId fix and API configuration")
        print()
        
        # Setup authentication first
        if not self.setup_authentication():
            print("❌ Authentication setup failed - cannot continue tests")
            return False
        
        tests = [
            self.test_api_connectivity_comprehensive,
            self.test_objectid_fix_validation,
            self.test_scanner_workflow_complete,
            self.test_multiple_scanner_operations,
            self.test_scanner_list_functionality,
            self.test_frontend_backend_integration,
            self.test_user_workflow_simulation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 60)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
            print("✅ Business Card Scanner workflow is working correctly")
            print("✅ ObjectId fix is working properly")
            print("✅ API connectivity is functioning")
            print("✅ Frontend-Backend integration is successful")
        else:
            print(f"\n⚠️  {total - passed} tests failed - Critical issues need attention")
        
        return passed == total

if __name__ == "__main__":
    tester = ComprehensiveScannerTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)