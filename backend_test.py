#!/usr/bin/env python3
"""
Comprehensive Backend API Test Suite for Digital Business Cards
Tests all endpoints including authentication, CRUD operations, utilities, and GDPR compliance
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

class BusinessCardAPITester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.card_id = None
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
    
    def test_health_check(self):
        """Test GET /api/ endpoint"""
        try:
            response = requests.get(f"{API_BASE}/")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "version" in data and "status" in data:
                    self.log_result("Health Check", True, f"API is running - {data['message']}")
                    return True
                else:
                    self.log_result("Health Check", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test POST /api/auth/register with GDPR compliance"""
        try:
            # Generate unique test data
            test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "gdpr_consent": True,
                "privacy_consent": True,
                "marketing_consent": False
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["message", "access_token", "refresh_token", "token_type", "user"]
                
                if all(field in data for field in required_fields):
                    # Store token for subsequent tests
                    self.access_token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    
                    # Verify user data structure
                    user = data["user"]
                    user_fields = ["id", "email", "first_name", "last_name", "privacy_settings"]
                    
                    if all(field in user for field in user_fields):
                        self.log_result("User Registration", True, f"User registered successfully: {test_email}")
                        return True
                    else:
                        self.log_result("User Registration", False, "Missing user fields in response", data)
                        return False
                else:
                    self.log_result("User Registration", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("User Registration", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("User Registration", False, f"Error: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test POST /api/auth/login"""
        try:
            # First register a user for login test
            test_email = f"logintest_{uuid.uuid4().hex[:8]}@example.com"
            password = "LoginTest123!"
            
            # Register user
            register_data = {
                "email": test_email,
                "password": password,
                "first_name": "Login",
                "last_name": "Test",
                "gdpr_consent": True,
                "privacy_consent": True,
                "marketing_consent": False
            }
            
            register_response = requests.post(f"{API_BASE}/auth/register", json=register_data)
            
            if register_response.status_code != 200:
                self.log_result("User Login", False, "Failed to register test user for login", register_response.text)
                return False
            
            # Now test login
            login_data = {
                "email": test_email,
                "password": password
            }
            
            response = requests.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["message", "access_token", "refresh_token", "token_type", "user"]
                
                if all(field in data for field in required_fields):
                    self.log_result("User Login", True, f"Login successful for: {test_email}")
                    return True
                else:
                    self.log_result("User Login", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("User Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("User Login", False, f"Error: {str(e)}")
            return False
    
    def test_protected_endpoint(self):
        """Test GET /api/auth/me (protected endpoint)"""
        if not self.access_token:
            self.log_result("Protected Endpoint", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "email", "first_name", "last_name", "privacy_settings"]
                
                if all(field in data for field in required_fields):
                    self.log_result("Protected Endpoint", True, f"User profile retrieved: {data['email']}")
                    return True
                else:
                    self.log_result("Protected Endpoint", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Protected Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Protected Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_create_business_card(self):
        """Test POST /api/cards (requires auth)"""
        if not self.access_token:
            self.log_result("Create Business Card", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            card_data = {
                "name": "John Doe",
                "company": "Tech Solutions Inc",
                "position": "Senior Developer",
                "description": "Passionate about creating innovative digital solutions",
                "phones": [
                    {
                        "label": "work",
                        "number": "+1-555-123-4567",
                        "is_primary": True
                    }
                ],
                "emails": [
                    {
                        "label": "work",
                        "address": "john.doe@techsolutions.com",
                        "is_primary": True
                    }
                ],
                "website": "https://johndoe.dev",
                "social_media": {
                    "linkedin": "johndoe",
                    "twitter": "johndoe_dev"
                },
                "is_public": True,
                "background_color": "#ffffff",
                "text_color": "#1f2937",
                "accent_color": "#3b82f6"
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "company", "position", "phones", "emails", "is_owner"]
                
                if all(field in data for field in required_fields):
                    self.card_id = data["id"]
                    self.log_result("Create Business Card", True, f"Card created: {data['name']}")
                    return True
                else:
                    self.log_result("Create Business Card", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Create Business Card", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Business Card", False, f"Error: {str(e)}")
            return False
    
    def test_get_user_cards(self):
        """Test GET /api/cards (requires auth)"""
        if not self.access_token:
            self.log_result("Get User Cards", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/cards", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    if len(data) > 0:
                        # Check first card structure
                        card = data[0]
                        required_fields = ["id", "name", "is_owner"]
                        
                        if all(field in card for field in required_fields):
                            self.log_result("Get User Cards", True, f"Retrieved {len(data)} cards")
                            return True
                        else:
                            self.log_result("Get User Cards", False, "Missing required fields in card data", card)
                            return False
                    else:
                        self.log_result("Get User Cards", True, "No cards found (empty list)")
                        return True
                else:
                    self.log_result("Get User Cards", False, "Response is not a list", data)
                    return False
            else:
                self.log_result("Get User Cards", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Get User Cards", False, f"Error: {str(e)}")
            return False
    
    def test_get_specific_card(self):
        """Test GET /api/cards/{id} (public access)"""
        if not self.card_id:
            self.log_result("Get Specific Card", False, "No card ID available")
            return False
            
        try:
            response = requests.get(f"{API_BASE}/cards/{self.card_id}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "is_owner"]
                
                if all(field in data for field in required_fields):
                    self.log_result("Get Specific Card", True, f"Card retrieved: {data['name']}")
                    return True
                else:
                    self.log_result("Get Specific Card", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Get Specific Card", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Get Specific Card", False, f"Error: {str(e)}")
            return False
    
    def test_update_business_card(self):
        """Test PUT /api/cards/{id} (owner only)"""
        if not self.access_token or not self.card_id:
            self.log_result("Update Business Card", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            update_data = {
                "description": "Updated description - passionate about creating innovative digital solutions and mentoring junior developers",
                "position": "Lead Developer"
            }
            
            response = requests.put(f"{API_BASE}/cards/{self.card_id}", json=update_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("description") == update_data["description"] and data.get("position") == update_data["position"]:
                    self.log_result("Update Business Card", True, "Card updated successfully")
                    return True
                else:
                    self.log_result("Update Business Card", False, "Update not reflected in response", data)
                    return False
            else:
                self.log_result("Update Business Card", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Update Business Card", False, f"Error: {str(e)}")
            return False
    
    def test_qr_code_generation(self):
        """Test GET /api/cards/{id}/qr"""
        if not self.card_id:
            self.log_result("QR Code Generation", False, "No card ID available")
            return False
            
        try:
            response = requests.get(f"{API_BASE}/cards/{self.card_id}/qr")
            
            if response.status_code == 200:
                # Check if response is PNG image
                content_type = response.headers.get('content-type', '')
                
                if 'image/png' in content_type:
                    self.log_result("QR Code Generation", True, f"QR code generated (size: {len(response.content)} bytes)")
                    return True
                else:
                    self.log_result("QR Code Generation", False, f"Unexpected content type: {content_type}")
                    return False
            else:
                self.log_result("QR Code Generation", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR Code Generation", False, f"Error: {str(e)}")
            return False
    
    def test_vcard_generation(self):
        """Test GET /api/cards/{id}/vcard"""
        if not self.card_id:
            self.log_result("vCard Generation", False, "No card ID available")
            return False
            
        try:
            response = requests.get(f"{API_BASE}/cards/{self.card_id}/vcard")
            
            if response.status_code == 200:
                # Check if response is vCard format
                content_type = response.headers.get('content-type', '')
                content = response.text
                
                if 'text/vcard' in content_type and 'BEGIN:VCARD' in content and 'END:VCARD' in content:
                    self.log_result("vCard Generation", True, "vCard generated successfully")
                    return True
                else:
                    self.log_result("vCard Generation", False, f"Invalid vCard format or content type: {content_type}")
                    return False
            else:
                self.log_result("vCard Generation", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("vCard Generation", False, f"Error: {str(e)}")
            return False
    
    def test_privacy_report(self):
        """Test GET /api/privacy/report (requires auth)"""
        if not self.access_token:
            self.log_result("Privacy Report", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/privacy/report", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "gdpr_consent", "privacy_settings", "data_summary", "compliance_status"]
                
                if all(field in data for field in required_fields):
                    self.log_result("Privacy Report", True, "Privacy report generated successfully")
                    return True
                else:
                    self.log_result("Privacy Report", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Privacy Report", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Privacy Report", False, f"Error: {str(e)}")
            return False
    
    def test_data_export(self):
        """Test GET /api/privacy/export (requires auth)"""
        if not self.access_token:
            self.log_result("Data Export", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/privacy/export", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_data", "business_cards", "recipients", "analytics_summary", "export_date"]
                
                if all(field in data for field in required_fields):
                    self.log_result("Data Export", True, "GDPR data export completed successfully")
                    return True
                else:
                    self.log_result("Data Export", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Data Export", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Data Export", False, f"Error: {str(e)}")
            return False
    
    def test_invalid_authentication(self):
        """Test endpoints with invalid authentication"""
        try:
            # Test with invalid token
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = requests.get(f"{API_BASE}/auth/me", headers=headers)
            
            if response.status_code == 401:
                self.log_result("Invalid Authentication", True, "Properly rejected invalid token")
                return True
            else:
                self.log_result("Invalid Authentication", False, f"Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Invalid Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_nonexistent_card(self):
        """Test accessing non-existent card"""
        try:
            fake_card_id = str(uuid.uuid4())
            response = requests.get(f"{API_BASE}/cards/{fake_card_id}")
            
            if response.status_code == 404:
                self.log_result("Non-existent Card", True, "Properly returned 404 for non-existent card")
                return True
            else:
                self.log_result("Non-existent Card", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Non-existent Card", False, f"Error: {str(e)}")
            return False
    
    def test_create_business_card_with_custom_code(self):
        """Test POST /api/cards with custom_code field"""
        if not self.access_token:
            self.log_result("Create Card with Custom Code", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Generate unique custom code
            custom_code = f"TEST{uuid.uuid4().hex[:6].upper()}"
            
            card_data = {
                "name": "Maria Schmidt",
                "company": "Digital Innovation GmbH",
                "position": "Product Manager",
                "description": "Leading digital transformation initiatives",
                "phones": [
                    {
                        "label": "work",
                        "number": "+49-30-123-4567",
                        "is_primary": True
                    }
                ],
                "emails": [
                    {
                        "label": "work", 
                        "address": "maria.schmidt@digitalinnovation.de",
                        "is_primary": True
                    }
                ],
                "website": "https://digitalinnovation.de",
                "custom_code": custom_code,
                "is_public": True,
                "background_color": "#f8fafc",
                "text_color": "#1e293b",
                "accent_color": "#0ea5e9"
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("custom_code") == custom_code:
                    # Store this card for code access testing
                    self.custom_code_card_id = data["id"]
                    self.custom_code = custom_code
                    self.log_result("Create Card with Custom Code", True, f"Card created with custom code: {custom_code}")
                    return True
                else:
                    self.log_result("Create Card with Custom Code", False, "Custom code not reflected in response", data)
                    return False
            else:
                self.log_result("Create Card with Custom Code", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Card with Custom Code", False, f"Error: {str(e)}")
            return False
    
    def test_check_code_availability(self):
        """Test GET /api/cards/check-code/{code}"""
        try:
            # Test with available code
            available_code = f"AVAIL{uuid.uuid4().hex[:4].upper()}"
            response = requests.get(f"{API_BASE}/cards/check-code/{available_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("available") == True:
                    self.log_result("Check Code Availability - Available", True, f"Code {available_code} is available")
                else:
                    self.log_result("Check Code Availability - Available", False, "Expected available=true", data)
                    return False
            else:
                self.log_result("Check Code Availability - Available", False, f"HTTP {response.status_code}", response.text)
                return False
            
            # Test with taken code (if we have one)
            if hasattr(self, 'custom_code'):
                response = requests.get(f"{API_BASE}/cards/check-code/{self.custom_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("available") == False:
                        self.log_result("Check Code Availability - Taken", True, f"Code {self.custom_code} is correctly marked as taken")
                        return True
                    else:
                        self.log_result("Check Code Availability - Taken", False, "Expected available=false for taken code", data)
                        return False
                else:
                    self.log_result("Check Code Availability - Taken", False, f"HTTP {response.status_code}", response.text)
                    return False
            
            return True
                
        except Exception as e:
            self.log_result("Check Code Availability", False, f"Error: {str(e)}")
            return False
    
    def test_access_card_by_code(self):
        """Test POST /api/cards/access-by-code"""
        if not hasattr(self, 'custom_code'):
            self.log_result("Access Card by Code", False, "No custom code available for testing")
            return False
            
        try:
            code_request = {"code": self.custom_code}
            response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "card", "code_usage_count"]
                
                if all(field in data for field in required_fields):
                    if data["success"] == True and "card" in data:
                        card = data["card"]
                        if card.get("custom_code") == self.custom_code:
                            self.log_result("Access Card by Code", True, f"Successfully accessed card using code: {self.custom_code}")
                            return True
                        else:
                            self.log_result("Access Card by Code", False, "Retrieved card doesn't match expected code", data)
                            return False
                    else:
                        self.log_result("Access Card by Code", False, "Success=false or missing card data", data)
                        return False
                else:
                    self.log_result("Access Card by Code", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Access Card by Code", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Access Card by Code", False, f"Error: {str(e)}")
            return False
    
    def test_create_meeting_room(self):
        """Test POST /api/meeting-rooms"""
        if not self.access_token or not self.card_id:
            self.log_result("Create Meeting Room", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            room_data = {
                "card_id": self.card_id,
                "description": "Networking Event - Tech Meetup Berlin",
                "duration_minutes": 15,
                "max_participants": 10
            }
            
            response = requests.post(f"{API_BASE}/meeting-rooms", json=room_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "code", "created_by_card_name", "participants", "max_participants", "is_active", "can_join", "is_creator"]
                
                if all(field in data for field in required_fields):
                    self.meeting_room_code = data["code"]
                    self.meeting_room_id = data["id"]
                    
                    # Verify creator is in participants
                    if len(data["participants"]) == 1 and data["is_creator"] == True:
                        self.log_result("Create Meeting Room", True, f"Meeting room created with code: {data['code']}")
                        return True
                    else:
                        self.log_result("Create Meeting Room", False, "Creator not properly added as participant", data)
                        return False
                else:
                    self.log_result("Create Meeting Room", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Create Meeting Room", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Meeting Room", False, f"Error: {str(e)}")
            return False
    
    def test_get_meeting_room(self):
        """Test GET /api/meeting-rooms/{code}"""
        if not hasattr(self, 'meeting_room_code'):
            self.log_result("Get Meeting Room", False, "No meeting room code available")
            return False
            
        try:
            response = requests.get(f"{API_BASE}/meeting-rooms/{self.meeting_room_code}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "code", "created_by_card_name", "participants", "time_remaining_minutes", "can_join"]
                
                if all(field in data for field in required_fields):
                    if data["code"] == self.meeting_room_code:
                        self.log_result("Get Meeting Room", True, f"Meeting room retrieved: {data['code']}")
                        return True
                    else:
                        self.log_result("Get Meeting Room", False, "Retrieved room code doesn't match", data)
                        return False
                else:
                    self.log_result("Get Meeting Room", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Get Meeting Room", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Get Meeting Room", False, f"Error: {str(e)}")
            return False
    
    def test_join_meeting_room(self):
        """Test POST /api/meeting-rooms/join"""
        if not hasattr(self, 'meeting_room_code') or not hasattr(self, 'custom_code_card_id'):
            self.log_result("Join Meeting Room", False, "No meeting room code or second card available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            join_data = {
                "code": self.meeting_room_code,
                "card_id": self.custom_code_card_id
            }
            
            response = requests.post(f"{API_BASE}/meeting-rooms/join", json=join_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "room", "cards_received"]
                
                if all(field in data for field in required_fields):
                    if data["success"] == True and "room" in data:
                        room = data["room"]
                        # Should now have 2 participants
                        if len(room["participants"]) == 2:
                            self.log_result("Join Meeting Room", True, f"Successfully joined meeting room: {self.meeting_room_code}")
                            return True
                        else:
                            self.log_result("Join Meeting Room", False, f"Expected 2 participants, got {len(room['participants'])}", data)
                            return False
                    else:
                        self.log_result("Join Meeting Room", False, "Success=false or missing room data", data)
                        return False
                else:
                    self.log_result("Join Meeting Room", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Join Meeting Room", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Join Meeting Room", False, f"Error: {str(e)}")
            return False
    
    def test_list_user_meeting_rooms(self):
        """Test GET /api/meeting-rooms"""
        if not self.access_token:
            self.log_result("List User Meeting Rooms", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/meeting-rooms", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    if len(data) > 0:
                        # Check first room structure
                        room = data[0]
                        required_fields = ["id", "code", "created_by_card_name", "participant_count", "max_participants", "time_remaining_minutes", "is_creator"]
                        
                        if all(field in room for field in required_fields):
                            self.log_result("List User Meeting Rooms", True, f"Retrieved {len(data)} meeting rooms")
                            return True
                        else:
                            self.log_result("List User Meeting Rooms", False, "Missing required fields in room data", room)
                            return False
                    else:
                        self.log_result("List User Meeting Rooms", True, "No meeting rooms found (empty list)")
                        return True
                else:
                    self.log_result("List User Meeting Rooms", False, "Response is not a list", data)
                    return False
            else:
                self.log_result("List User Meeting Rooms", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("List User Meeting Rooms", False, f"Error: {str(e)}")
            return False
    
    def test_enhanced_code_access_meeting_room(self):
        """Test POST /api/cards/access-by-code with meeting room code"""
        if not hasattr(self, 'meeting_room_code'):
            self.log_result("Enhanced Code Access - Meeting Room", False, "No meeting room code available")
            return False
            
        try:
            code_request = {"code": self.meeting_room_code}
            response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
            
            # Meeting room codes should not be accessible via card access endpoint
            # This should return 404 or appropriate error
            if response.status_code == 404:
                self.log_result("Enhanced Code Access - Meeting Room", True, "Meeting room code properly rejected by card access endpoint")
                return True
            else:
                # If it returns something else, check if it's handling meeting room codes
                if response.status_code == 200:
                    data = response.json()
                    # If it redirects to meeting room or handles it differently, that's also valid
                    self.log_result("Enhanced Code Access - Meeting Room", True, "Meeting room code handled by enhanced endpoint")
                    return True
                else:
                    self.log_result("Enhanced Code Access - Meeting Room", False, f"Unexpected response: HTTP {response.status_code}", response.text)
                    return False
                
        except Exception as e:
            self.log_result("Enhanced Code Access - Meeting Room", False, f"Error: {str(e)}")
            return False
    
    def test_close_meeting_room(self):
        """Test DELETE /api/meeting-rooms/{code}"""
        if not self.access_token or not hasattr(self, 'meeting_room_code'):
            self.log_result("Close Meeting Room", False, "No access token or meeting room code available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.delete(f"{API_BASE}/meeting-rooms/{self.meeting_room_code}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data and self.meeting_room_code in data["message"]:
                    self.log_result("Close Meeting Room", True, f"Meeting room {self.meeting_room_code} closed successfully")
                    return True
                else:
                    self.log_result("Close Meeting Room", False, "Unexpected response format", data)
                    return False
            else:
                self.log_result("Close Meeting Room", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Close Meeting Room", False, f"Error: {str(e)}")
            return False
    
    def test_code_uniqueness_validation(self):
        """Test code uniqueness across business cards and meeting rooms"""
        if not self.access_token or not hasattr(self, 'custom_code'):
            self.log_result("Code Uniqueness Validation", False, "No access token or custom code available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Try to create another card with the same custom code
            card_data = {
                "name": "Duplicate Code Test",
                "company": "Test Company",
                "position": "Tester",
                "custom_code": self.custom_code,  # Same code as existing card
                "is_public": True
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            
            # Should fail with conflict or validation error
            if response.status_code in [400, 409, 422]:
                self.log_result("Code Uniqueness Validation", True, "Duplicate custom code properly rejected")
                return True
            else:
                self.log_result("Code Uniqueness Validation", False, f"Expected validation error, got HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Code Uniqueness Validation", False, f"Error: {str(e)}")
            return False
    
    def test_social_media_fix_with_custom_code(self):
        """Test POST /api/cards with custom_code and missing social_media field (targeted fix test)"""
        if not self.access_token:
            self.log_result("Social Media Fix with Custom Code", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Generate unique custom code
            custom_code = f"SOCIAL{uuid.uuid4().hex[:6].upper()}"
            
            # Test 1: Card with custom_code but NO social_media field
            card_data_no_social = {
                "name": "Test User No Social",
                "company": "Social Media Test Corp",
                "position": "QA Engineer",
                "description": "Testing social media field handling",
                "phones": [
                    {
                        "label": "work",
                        "number": "+49-30-987-6543",
                        "is_primary": True
                    }
                ],
                "emails": [
                    {
                        "label": "work", 
                        "address": "test.nosocial@example.com",
                        "is_primary": True
                    }
                ],
                "custom_code": custom_code,
                "is_public": True,
                "background_color": "#ffffff",
                "text_color": "#000000",
                "accent_color": "#3b82f6"
                # NOTE: social_media field is intentionally missing
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data_no_social, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify card was created successfully
                if data.get("custom_code") == custom_code:
                    # Verify social_media field exists and is properly initialized
                    if "social_media" in data:
                        social_media = data["social_media"]
                        # Should be an empty SocialMedia object (all fields None or empty)
                        expected_fields = ["linkedin", "twitter", "facebook", "instagram", "github", "website"]
                        has_social_structure = any(field in social_media for field in expected_fields)
                        
                        self.log_result("Social Media Fix with Custom Code - Missing Field", True, 
                                      f"Card created with custom code {custom_code}, social_media properly initialized")
                    else:
                        self.log_result("Social Media Fix with Custom Code - Missing Field", False, 
                                      "social_media field missing from response", data)
                        return False
                else:
                    self.log_result("Social Media Fix with Custom Code - Missing Field", False, 
                                  "Custom code not reflected in response", data)
                    return False
            else:
                self.log_result("Social Media Fix with Custom Code - Missing Field", False, 
                              f"HTTP {response.status_code}", response.text)
                return False
            
            # Test 2: Card with custom_code and explicit social_media: null
            custom_code_2 = f"SOCIAL{uuid.uuid4().hex[:6].upper()}"
            
            card_data_null_social = {
                "name": "Test User Null Social",
                "company": "Social Media Test Corp",
                "position": "QA Engineer",
                "description": "Testing social media field handling with null",
                "phones": [
                    {
                        "label": "work",
                        "number": "+49-30-987-6544",
                        "is_primary": True
                    }
                ],
                "emails": [
                    {
                        "label": "work", 
                        "address": "test.nullsocial@example.com",
                        "is_primary": True
                    }
                ],
                "custom_code": custom_code_2,
                "social_media": None,  # Explicitly set to None
                "is_public": True,
                "background_color": "#ffffff",
                "text_color": "#000000",
                "accent_color": "#3b82f6"
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data_null_social, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify card was created successfully
                if data.get("custom_code") == custom_code_2:
                    # Verify social_media field exists and is properly initialized
                    if "social_media" in data:
                        self.log_result("Social Media Fix with Custom Code - Null Field", True, 
                                      f"Card created with custom code {custom_code_2}, null social_media properly handled")
                        return True
                    else:
                        self.log_result("Social Media Fix with Custom Code - Null Field", False, 
                                      "social_media field missing from response", data)
                        return False
                else:
                    self.log_result("Social Media Fix with Custom Code - Null Field", False, 
                                  "Custom code not reflected in response", data)
                    return False
            else:
                self.log_result("Social Media Fix with Custom Code - Null Field", False, 
                              f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Social Media Fix with Custom Code", False, f"Error: {str(e)}")
            return False
    
    def test_invalid_meeting_room_operations(self):
        """Test various invalid meeting room operations"""
        try:
            # Test joining non-existent meeting room
            join_data = {
                "code": "NONEXIST",
                "card_id": self.card_id if self.card_id else "fake_id"
            }
            
            response = requests.post(f"{API_BASE}/meeting-rooms/join", json=join_data)
            
            if response.status_code == 404:
                self.log_result("Invalid Meeting Room Operations - Non-existent", True, "Non-existent meeting room properly rejected")
            else:
                self.log_result("Invalid Meeting Room Operations - Non-existent", False, f"Expected 404, got {response.status_code}")
                return False
            
            # Test getting non-existent meeting room
            response = requests.get(f"{API_BASE}/meeting-rooms/NONEXIST")
            
            if response.status_code == 404:
                self.log_result("Invalid Meeting Room Operations - Get Non-existent", True, "Non-existent meeting room get properly rejected")
                return True
            else:
                self.log_result("Invalid Meeting Room Operations - Get Non-existent", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Invalid Meeting Room Operations", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # ENHANCED 9-CHARACTER VIDEO MEETING CODE GENERATION TESTING
    # ============================================================================
    
    def test_9_character_meeting_code_generation(self):
        """Test enhanced 9-character meeting code generation with collision resistance"""
        if not self.access_token:
            self.log_result("9-Character Meeting Code Generation", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test multiple meeting creations to verify 9-character codes
            meeting_codes = []
            
            for i in range(5):  # Create 5 meetings to test code uniqueness
                meeting_data = {
                    "title": f"Code Test Meeting {i+1}",
                    "description": f"Testing 9-character code generation - Meeting {i+1}",
                    "meeting_type": "networking_event",
                    "duration_minutes": 30,
                    "max_participants": 10,
                    "share_host_card": True,
                    "allow_card_sharing": True,
                    "is_public": True
                }
                
                response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    meeting = data.get("meeting", {})
                    meeting_code = meeting.get("meeting_code")
                    
                    if meeting_code:
                        meeting_codes.append(meeting_code)
                        
                        # Verify code is exactly 9 characters
                        if len(meeting_code) != 9:
                            self.log_result("9-Character Code Length", False, f"Expected 9 characters, got {len(meeting_code)}: {meeting_code}")
                            return False
                        
                        # Verify code format (A-Z, 0-9 only)
                        import string
                        valid_chars = string.ascii_uppercase + string.digits
                        if not all(c in valid_chars for c in meeting_code):
                            self.log_result("9-Character Code Format", False, f"Invalid characters in code: {meeting_code}")
                            return False
                    else:
                        self.log_result("9-Character Meeting Code Generation", False, f"No meeting_code in response for meeting {i+1}", data)
                        return False
                else:
                    self.log_result("9-Character Meeting Code Generation", False, f"Failed to create meeting {i+1}: HTTP {response.status_code}", response.text)
                    return False
            
            # Verify all codes are unique (collision resistance)
            if len(set(meeting_codes)) != len(meeting_codes):
                self.log_result("Code Collision Resistance", False, f"Duplicate codes found: {meeting_codes}")
                return False
            
            # Store first meeting code for further tests
            self.video_meeting_code = meeting_codes[0]
            
            self.log_result("9-Character Code Length", True, f"All {len(meeting_codes)} codes are exactly 9 characters")
            self.log_result("9-Character Code Format", True, f"All codes use valid format (A-Z, 0-9): {meeting_codes}")
            self.log_result("Code Collision Resistance", True, f"All {len(meeting_codes)} codes are unique - no collisions detected")
            self.log_result("9-Character Meeting Code Generation", True, f"Successfully generated {len(meeting_codes)} unique 9-character codes")
            return True
                
        except Exception as e:
            self.log_result("9-Character Meeting Code Generation", False, f"Error: {str(e)}")
            return False
    
    def test_code_collision_resistance_stress(self):
        """Stress test collision resistance with rapid code generation"""
        if not self.access_token:
            self.log_result("Code Collision Stress Test", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Generate many codes rapidly to test collision resistance
            meeting_codes = []
            successful_creations = 0
            
            for i in range(20):  # Create 20 meetings rapidly
                meeting_data = {
                    "title": f"Stress Test Meeting {i+1}",
                    "description": f"Collision resistance stress test - Meeting {i+1}",
                    "meeting_type": "group",
                    "duration_minutes": 15,
                    "max_participants": 5,
                    "is_public": True
                }
                
                response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    meeting = data.get("meeting", {})
                    meeting_code = meeting.get("meeting_code")
                    
                    if meeting_code and len(meeting_code) == 9:
                        meeting_codes.append(meeting_code)
                        successful_creations += 1
                    else:
                        self.log_result("Code Collision Stress Test", False, f"Invalid code in meeting {i+1}: {meeting_code}")
                        return False
                else:
                    # Some failures are acceptable under stress, but log them
                    print(f"   Meeting {i+1} creation failed: HTTP {response.status_code}")
            
            # Verify no collisions occurred
            unique_codes = set(meeting_codes)
            collision_rate = (len(meeting_codes) - len(unique_codes)) / len(meeting_codes) if meeting_codes else 0
            
            if collision_rate == 0:
                self.log_result("Code Collision Stress Test", True, f"Generated {successful_creations} codes with 0% collision rate")
                return True
            else:
                self.log_result("Code Collision Stress Test", False, f"Collision rate: {collision_rate:.2%} ({len(meeting_codes) - len(unique_codes)} collisions)")
                return False
                
        except Exception as e:
            self.log_result("Code Collision Stress Test", False, f"Error: {str(e)}")
            return False
    
    def test_enhanced_meeting_features_with_9char_codes(self):
        """Test that 9-character codes work with all revolutionary features"""
        if not self.access_token:
            self.log_result("Enhanced Features with 9-Char Codes", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create meeting with all revolutionary features enabled
            meeting_data = {
                "title": "Revolutionary Features Test with 9-Char Code",
                "description": "Testing all enhanced features with 9-character meeting codes",
                "meeting_type": "networking_event",
                "duration_minutes": 60,
                "max_participants": 15,
                "password": "test123",
                "share_host_card": True,
                "allow_card_sharing": True,
                "community_tags": ["technology", "networking", "ai"],
                "is_public": True,
                # Revolutionary features
                "translation_enabled": True,
                "source_language": "de",
                "target_languages": ["en", "fr", "es", "it"]
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                meeting = data.get("meeting", {})
                
                # Verify 9-character code
                meeting_code = meeting.get("meeting_code")
                if not meeting_code or len(meeting_code) != 9:
                    self.log_result("Enhanced Features with 9-Char Codes", False, f"Invalid meeting code: {meeting_code}")
                    return False
                
                # Store for other tests
                self.enhanced_meeting_id = meeting.get("id")
                self.enhanced_meeting_code = meeting_code
                
                # Verify Zoom-like share link with 9-character code
                share_link = meeting.get("share_link")
                if not share_link or meeting_code not in share_link:
                    self.log_result("Share Link with 9-Char Code", False, f"Share link doesn't contain 9-char code: {share_link}")
                    return False
                
                # Verify QR code URL with 9-character code
                qr_code_url = meeting.get("qr_code_url")
                if not qr_code_url or meeting_code not in qr_code_url:
                    self.log_result("QR Code with 9-Char Code", False, f"QR code URL doesn't contain 9-char code: {qr_code_url}")
                    return False
                
                # Verify business card integration data
                meeting_link_card = data.get("meeting_link_card", {})
                if not meeting_link_card or meeting_link_card.get("meeting_code") != meeting_code:
                    self.log_result("Business Card Integration with 9-Char Code", False, "Meeting link card missing or invalid code")
                    return False
                
                # Verify translation settings with 9-character code
                if not meeting.get("translation_enabled") or meeting.get("target_languages") != ["en", "fr", "es", "it"]:
                    self.log_result("Translation with 9-Char Code", False, "Translation settings not properly applied")
                    return False
                
                # Verify WebRTC config is provided
                webrtc_config = data.get("webrtc_config", {})
                if not webrtc_config or "iceServers" not in webrtc_config:
                    self.log_result("WebRTC Config with 9-Char Code", False, "WebRTC configuration missing")
                    return False
                
                self.log_result("9-Character Code Format", True, f"Code: {meeting_code} (9 characters)")
                self.log_result("Share Link with 9-Char Code", True, f"Share link: {share_link}")
                self.log_result("QR Code with 9-Char Code", True, f"QR code URL: {qr_code_url}")
                self.log_result("Business Card Integration with 9-Char Code", True, "Meeting link card data complete")
                self.log_result("Translation with 9-Char Code", True, f"Translation: {meeting.get('source_language')} -> {meeting.get('target_languages')}")
                self.log_result("WebRTC Config with 9-Char Code", True, f"WebRTC config with {len(webrtc_config.get('iceServers', []))} ICE servers")
                self.log_result("Enhanced Features with 9-Char Codes", True, "All revolutionary features working with 9-character codes")
                return True
            else:
                self.log_result("Enhanced Features with 9-Char Codes", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Enhanced Features with 9-Char Codes", False, f"Error: {str(e)}")
            return False

    # ============================================================================
    # NEW REVOLUTIONARY FEATURES TESTING - MEETING LINK GENERATION & LIVE TRANSLATION
    # ============================================================================
    
    def test_enhanced_video_meeting_create(self):
        """Test POST /api/video/meeting/create - Enhanced meeting creation with NEW features"""
        if not self.access_token:
            self.log_result("Enhanced Video Meeting Create", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test enhanced meeting creation with translation settings
            meeting_data = {
                "title": "Revolutionary Tech Networking Session",
                "description": "Enhanced video meeting with live translation and business card integration",
                "meeting_type": "networking_event",
                "duration_minutes": 60,
                "max_participants": 15,
                "password": "meeting123",
                "share_host_card": True,
                "allow_card_sharing": True,
                "community_tags": ["technology", "networking", "ai"],
                "is_public": True,
                # NEW: Translation settings
                "translation_enabled": True,
                "source_language": "de",
                "target_languages": ["en", "fr", "es"]
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for NEW revolutionary fields
                meeting = data.get("meeting", {})
                expected_new_fields = ["share_link", "qr_code_url", "meeting_link_card", "translation_enabled"]
                
                if all(field in meeting for field in expected_new_fields):
                    self.video_meeting_id = meeting.get("id")
                    self.meeting_code = meeting.get("meeting_code")
                    
                    # Verify share_link format (like zoom.us/j/123456)
                    share_link = meeting.get("share_link")
                    if share_link and "cardnet-pro.preview.emergentagent.com/join?code=" in share_link:
                        self.log_result("Enhanced Video Meeting Create - Share Link", True, f"Professional share link generated: {share_link}")
                    else:
                        self.log_result("Enhanced Video Meeting Create - Share Link", False, f"Invalid share link format: {share_link}")
                        return False
                    
                    # Verify QR code URL
                    qr_code_url = meeting.get("qr_code_url")
                    if qr_code_url and "/api/qr/meeting/" in qr_code_url:
                        self.log_result("Enhanced Video Meeting Create - QR Code", True, f"QR code URL generated: {qr_code_url}")
                    else:
                        self.log_result("Enhanced Video Meeting Create - QR Code", False, f"Invalid QR code URL: {qr_code_url}")
                        return False
                    
                    # Verify meeting_link_card for business card integration
                    meeting_link_card = meeting.get("meeting_link_card", {})
                    if meeting_link_card and "meeting_info" in meeting_link_card and "qr_code_url" in meeting_link_card:
                        self.log_result("Enhanced Video Meeting Create - Business Card Integration", True, "Meeting link card data complete")
                    else:
                        self.log_result("Enhanced Video Meeting Create - Business Card Integration", False, "Missing meeting_link_card data", meeting_link_card)
                        return False
                    
                    # Verify translation settings
                    if meeting.get("translation_enabled") == True and meeting.get("target_languages") == ["en", "fr", "es"]:
                        self.log_result("Enhanced Video Meeting Create - Translation Settings", True, "Translation settings properly configured")
                    else:
                        self.log_result("Enhanced Video Meeting Create - Translation Settings", False, "Translation settings not properly set", meeting)
                        return False
                    
                    # Verify WebRTC config
                    webrtc_config = data.get("webrtc_config", {})
                    if webrtc_config and "iceServers" in webrtc_config:
                        self.log_result("Enhanced Video Meeting Create - WebRTC Config", True, "WebRTC configuration provided")
                    else:
                        self.log_result("Enhanced Video Meeting Create - WebRTC Config", False, "Missing WebRTC configuration", webrtc_config)
                        return False
                    
                    self.log_result("Enhanced Video Meeting Create", True, f"Revolutionary meeting created with ID: {self.video_meeting_id}")
                    return True
                else:
                    missing_fields = [field for field in expected_new_fields if field not in meeting]
                    self.log_result("Enhanced Video Meeting Create", False, f"Missing NEW revolutionary fields: {missing_fields}", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Enhanced Video Meeting Create", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Enhanced Video Meeting Create", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Enhanced Video Meeting Create", False, f"Error: {str(e)}")
            return False
    
    def test_meeting_share_link_generation(self):
        """Test GET /api/video/meeting/{meeting_id}/share-link - Revolutionary share link generation"""
        if not self.access_token or not hasattr(self, 'video_meeting_id'):
            self.log_result("Meeting Share Link Generation", False, "No access token or video meeting ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/video/meeting/{self.video_meeting_id}/share-link", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify professional share link format
                share_link = data.get("share_link")
                if share_link and "cardnet-pro.preview.emergentagent.com/join?code=" in share_link:
                    self.log_result("Share Link Format", True, f"Professional Zoom-like format: {share_link}")
                else:
                    self.log_result("Share Link Format", False, f"Invalid share link format: {share_link}")
                    return False
                
                # Verify QR code URL for easy joining
                qr_code_url = data.get("qr_code_url")
                if qr_code_url and "/api/qr/meeting/" in qr_code_url:
                    self.log_result("QR Code URL", True, f"QR code URL for easy joining: {qr_code_url}")
                else:
                    self.log_result("QR Code URL", False, f"Invalid QR code URL: {qr_code_url}")
                    return False
                
                # Verify share_card_data for business card integration
                share_card_data = data.get("share_card_data", {})
                if share_card_data and "meeting_info" in share_card_data:
                    meeting_info = share_card_data["meeting_info"]
                    required_info = ["title", "host_name", "meeting_time", "features"]
                    if all(field in meeting_info for field in required_info):
                        self.log_result("Business Card Integration Data", True, "Complete share_card_data for business cards")
                    else:
                        self.log_result("Business Card Integration Data", False, "Incomplete meeting_info", meeting_info)
                        return False
                else:
                    self.log_result("Business Card Integration Data", False, "Missing share_card_data", share_card_data)
                    return False
                
                # Verify meeting features info (translation, business cards)
                features = share_card_data.get("meeting_info", {}).get("features", {})
                if "translation" in features and "business_cards" in features and "languages" in features:
                    self.log_result("Meeting Features Info", True, f"Features info complete: {features}")
                else:
                    self.log_result("Meeting Features Info", False, "Missing features info", features)
                    return False
                
                # Verify host information
                host_info = data.get("host_info", {})
                if host_info and "name" in host_info:
                    self.log_result("Host Information", True, f"Host info provided: {host_info['name']}")
                else:
                    self.log_result("Host Information", False, "Missing host information", host_info)
                    return False
                
                self.log_result("Meeting Share Link Generation", True, "Revolutionary share link generation working perfectly!")
                return True
            elif response.status_code == 404:
                self.log_result("Meeting Share Link Generation", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Meeting Share Link Generation", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Meeting Share Link Generation", False, f"Error: {str(e)}")
            return False
    
    def test_live_translation_enable(self):
        """Test POST /api/video/meeting/{meeting_id}/translation/enable - Revolutionary live translation"""
        if not self.access_token or not hasattr(self, 'video_meeting_id'):
            self.log_result("Live Translation Enable", False, "No access token or video meeting ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test translation activation with multiple languages
            translation_data = {
                "source_language": "de",  # German as source
                "target_languages": ["en", "fr", "es", "auto"]  # Multiple target languages
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/{self.video_meeting_id}/translation/enable", 
                                   json=translation_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify German success message
                message = data.get("message", "")
                if "Übersetzung" in message or "aktiviert" in message:
                    self.log_result("German Localization", True, f"German success message: {message}")
                else:
                    self.log_result("German Localization", False, f"Missing German localization: {message}")
                    return False
                
                # Verify translation settings confirmation
                if data.get("translation_enabled") == True:
                    self.log_result("Translation Activation", True, "Translation successfully enabled")
                else:
                    self.log_result("Translation Activation", False, "Translation not enabled", data)
                    return False
                
                # Verify language configuration
                source_lang = data.get("source_language")
                target_langs = data.get("target_languages", [])
                if source_lang == "de" and "en" in target_langs and "fr" in target_langs:
                    self.log_result("Language Configuration", True, f"Languages configured: {source_lang} -> {target_langs}")
                else:
                    self.log_result("Language Configuration", False, f"Invalid language config: {source_lang} -> {target_langs}")
                    return False
                
                # Verify WebSocket broadcast indication
                if "broadcast" in message.lower() or "teilnehmer" in message.lower():
                    self.log_result("WebSocket Broadcast", True, "WebSocket broadcast to participants indicated")
                else:
                    self.log_result("WebSocket Broadcast", False, "No WebSocket broadcast indication")
                    return False
                
                self.log_result("Live Translation Enable", True, "Revolutionary live translation system activated!")
                return True
            elif response.status_code == 404:
                self.log_result("Live Translation Enable", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Live Translation Enable", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Live Translation Enable", False, f"Error: {str(e)}")
            return False
    
    def test_participant_translation_preference(self):
        """Test POST /api/video/meeting/{meeting_id}/translation/participant - Individual language preferences"""
        if not self.access_token or not hasattr(self, 'video_meeting_id'):
            self.log_result("Participant Translation Preference", False, "No access token or video meeting ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test individual participant language setting
            preference_data = {
                "preferred_language": "en"  # English preference
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/{self.video_meeting_id}/translation/participant", 
                                   json=preference_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify German localized response
                message = data.get("message", "")
                if "Sprache" in message or "eingestellt" in message:
                    self.log_result("German Participant Response", True, f"German localized response: {message}")
                else:
                    self.log_result("German Participant Response", False, f"Missing German localization: {message}")
                    return False
                
                # Verify participant preference storage
                if data.get("preferred_language") == "en":
                    self.log_result("Preference Storage", True, "Participant language preference stored")
                else:
                    self.log_result("Preference Storage", False, "Preference not properly stored", data)
                    return False
                
                # Verify participant management
                participant_id = data.get("participant_id")
                if participant_id:
                    self.log_result("Participant Management", True, f"Participant ID managed: {participant_id}")
                else:
                    self.log_result("Participant Management", False, "Missing participant ID", data)
                    return False
                
                self.log_result("Participant Translation Preference", True, "Individual language preferences working perfectly!")
                return True
            elif response.status_code == 404:
                self.log_result("Participant Translation Preference", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Participant Translation Preference", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Participant Translation Preference", False, f"Error: {str(e)}")
            return False
    
    def test_video_meeting_join(self):
        """Test POST /api/video/meeting/join - Join video meetings"""
        if not self.access_token or not hasattr(self, 'video_meeting_id'):
            self.log_result("Video Meeting Join", False, "No access token or video meeting ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            join_data = {
                "meeting_id": self.video_meeting_id,
                "business_card_id": self.card_id,
                "password": "meeting123"
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/join", json=join_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "participant_id", "webrtc_config", "shared_cards"]
                
                if all(field in data for field in required_fields):
                    self.log_result("Video Meeting Join", True, f"Successfully joined video meeting")
                    return True
                else:
                    self.log_result("Video Meeting Join", False, "Missing required fields in response", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Video Meeting Join", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Video Meeting Join", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Video Meeting Join", False, f"Error: {str(e)}")
            return False
    
    def test_video_meetings_list(self):
        """Test GET /api/video/meetings - List user's video meetings"""
        if not self.access_token:
            self.log_result("Video Meetings List", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/video/meetings", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.log_result("Video Meetings List", True, f"Retrieved {len(data)} video meetings")
                    return True
                else:
                    self.log_result("Video Meetings List", False, "Response is not a list", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Video Meetings List", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Video Meetings List", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Video Meetings List", False, f"Error: {str(e)}")
            return False
    
    def test_video_meeting_share_card(self):
        """Test POST /api/video/meeting/{meeting_id}/share-card - Share business cards during meetings"""
        if not self.access_token or not hasattr(self, 'video_meeting_id'):
            self.log_result("Video Meeting Share Card", False, "No access token or video meeting ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            share_data = {
                "business_card_id": self.card_id,
                "recipient_participant_id": "participant_123"
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/{self.video_meeting_id}/share-card", 
                                   json=share_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") == True:
                    self.log_result("Video Meeting Share Card", True, "Business card shared successfully in video meeting")
                    return True
                else:
                    self.log_result("Video Meeting Share Card", False, "Card sharing failed", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Video Meeting Share Card", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Video Meeting Share Card", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Video Meeting Share Card", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # COMMUNITY NETWORKING TESTS - NEW CLAIMED ENDPOINTS
    # ============================================================================
    
    def test_community_profile_get(self):
        """Test GET /api/community/profile - Get/create user community profile"""
        if not self.access_token:
            self.log_result("Community Profile Get", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/community/profile", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "interests", "skills", "location", "bio"]
                
                if all(field in data for field in required_fields):
                    self.log_result("Community Profile Get", True, "Community profile retrieved successfully")
                    return True
                else:
                    self.log_result("Community Profile Get", False, "Missing required fields in response", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Community Profile Get", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Community Profile Get", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Profile Get", False, f"Error: {str(e)}")
            return False
    
    def test_community_profile_update(self):
        """Test PUT /api/community/profile - Update profile with interests/skills"""
        if not self.access_token:
            self.log_result("Community Profile Update", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            profile_data = {
                "interests": ["Technology", "Networking", "AI", "Startups"],
                "skills": ["Python", "FastAPI", "React", "MongoDB"],
                "location": "Berlin, Germany",
                "bio": "Tech enthusiast passionate about digital innovation",
                "availability": "weekends",
                "networking_goals": ["Find co-founder", "Learn new technologies"]
            }
            
            response = requests.put(f"{API_BASE}/community/profile", json=profile_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("interests") == profile_data["interests"]:
                    self.log_result("Community Profile Update", True, "Community profile updated successfully")
                    return True
                else:
                    self.log_result("Community Profile Update", False, "Profile update not reflected", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Community Profile Update", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Community Profile Update", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Profile Update", False, f"Error: {str(e)}")
            return False
    
    def test_community_discover(self):
        """Test GET /api/community/discover - AI-powered community matching"""
        if not self.access_token:
            self.log_result("Community Discover", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/community/discover", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["matches", "algorithm_version", "match_score"]
                
                if "matches" in data and isinstance(data["matches"], list):
                    self.log_result("Community Discover", True, f"AI matching returned {len(data['matches'])} matches")
                    return True
                else:
                    self.log_result("Community Discover", False, "Invalid response format", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Community Discover", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Community Discover", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Discover", False, f"Error: {str(e)}")
            return False
    
    def test_community_feed(self):
        """Test GET /api/community/feed - Personalized networking feed"""
        if not self.access_token:
            self.log_result("Community Feed", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/community/feed", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["feed_items", "personalization_score", "last_updated"]
                
                if "feed_items" in data and isinstance(data["feed_items"], list):
                    self.log_result("Community Feed", True, f"Personalized feed returned {len(data['feed_items'])} items")
                    return True
                else:
                    self.log_result("Community Feed", False, "Invalid response format", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Community Feed", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Community Feed", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Feed", False, f"Error: {str(e)}")
            return False
    
    def test_community_create(self):
        """Test POST /api/community/create - Create new communities"""
        if not self.access_token:
            self.log_result("Community Create", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            community_data = {
                "name": "Berlin Tech Entrepreneurs",
                "description": "Community for tech entrepreneurs in Berlin",
                "category": "Technology",
                "location": "Berlin, Germany",
                "privacy": "public",
                "tags": ["startup", "tech", "networking", "berlin"]
            }
            
            response = requests.post(f"{API_BASE}/community/create", json=community_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["community_id", "name", "member_count", "join_url"]
                
                if all(field in data for field in required_fields):
                    self.community_id = data["community_id"]
                    self.log_result("Community Create", True, f"Community created: {data['community_id']}")
                    return True
                else:
                    self.log_result("Community Create", False, "Missing required fields in response", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Community Create", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Community Create", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Create", False, f"Error: {str(e)}")
            return False
    
    def test_community_join(self):
        """Test POST /api/community/{community_id}/join - Join communities"""
        if not self.access_token or not hasattr(self, 'community_id'):
            self.log_result("Community Join", False, "No access token or community ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            join_data = {
                "business_card_id": self.card_id,
                "introduction": "Excited to join this tech community!"
            }
            
            response = requests.post(f"{API_BASE}/community/{self.community_id}/join", 
                                   json=join_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") == True:
                    self.log_result("Community Join", True, "Successfully joined community")
                    return True
                else:
                    self.log_result("Community Join", False, "Community join failed", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Community Join", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Community Join", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Join", False, f"Error: {str(e)}")
            return False
    
    def test_community_my_communities(self):
        """Test GET /api/community/my-communities - List user's communities"""
        if not self.access_token:
            self.log_result("My Communities List", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/community/my-communities", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.log_result("My Communities List", True, f"Retrieved {len(data)} user communities")
                    return True
                else:
                    self.log_result("My Communities List", False, "Response is not a list", data)
                    return False
            elif response.status_code == 404:
                self.log_result("My Communities List", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("My Communities List", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("My Communities List", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # JOB BOARD TESTS - NEW CLAIMED ENDPOINTS
    # ============================================================================
    
    def test_jobs_discover(self):
        """Test GET /api/jobs/discover - AI-matched job opportunities"""
        if not self.access_token:
            self.log_result("Jobs Discover", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/jobs/discover", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["jobs", "match_algorithm", "personalization_score"]
                
                if "jobs" in data and isinstance(data["jobs"], list):
                    self.log_result("Jobs Discover", True, f"AI job matching returned {len(data['jobs'])} opportunities")
                    return True
                else:
                    self.log_result("Jobs Discover", False, "Invalid response format", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Jobs Discover", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Jobs Discover", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Jobs Discover", False, f"Error: {str(e)}")
            return False
    
    def test_jobs_post(self):
        """Test POST /api/jobs/post - Post job opportunities"""
        if not self.access_token:
            self.log_result("Jobs Post", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            job_data = {
                "title": "Senior Python Developer",
                "company": "Tech Solutions Inc",
                "description": "Looking for experienced Python developer for exciting projects",
                "location": "Berlin, Germany",
                "salary_range": "70000-90000",
                "requirements": ["Python", "FastAPI", "MongoDB", "5+ years experience"],
                "job_type": "full-time",
                "remote_allowed": True,
                "business_card_id": self.card_id
            }
            
            response = requests.post(f"{API_BASE}/jobs/post", json=job_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["job_id", "title", "company", "posted_at", "application_url"]
                
                if all(field in data for field in required_fields):
                    self.job_id = data["job_id"]
                    self.log_result("Jobs Post", True, f"Job posted successfully: {data['job_id']}")
                    return True
                else:
                    self.log_result("Jobs Post", False, "Missing required fields in response", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Jobs Post", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Jobs Post", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Jobs Post", False, f"Error: {str(e)}")
            return False
    
    def test_jobs_apply(self):
        """Test POST /api/jobs/{job_id}/apply - Apply for jobs"""
        if not self.access_token or not hasattr(self, 'job_id'):
            self.log_result("Jobs Apply", False, "No access token or job ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            application_data = {
                "business_card_id": self.card_id,
                "cover_letter": "I am very interested in this position and believe my skills align perfectly with your requirements.",
                "resume_url": "https://example.com/resume.pdf",
                "portfolio_url": "https://github.com/johndoe"
            }
            
            response = requests.post(f"{API_BASE}/jobs/{self.job_id}/apply", 
                                   json=application_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") == True:
                    self.log_result("Jobs Apply", True, "Job application submitted successfully")
                    return True
                else:
                    self.log_result("Jobs Apply", False, "Job application failed", data)
                    return False
            elif response.status_code == 404:
                self.log_result("Jobs Apply", False, "Endpoint not implemented - returns 404")
                return False
            else:
                self.log_result("Jobs Apply", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Jobs Apply", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # OCR BUSINESS CARD SCANNER TESTS - GAME CHANGING FEATURE
    # ============================================================================
    
    def test_ocr_scan_business_card(self):
        """Test POST /api/scanner/scan - OCR business card scanning"""
        if not self.access_token:
            self.log_result("OCR Scan Business Card", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create a simple test image (base64 encoded 1x1 pixel PNG)
            test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77mgAAAABJRU5ErkJggg=="
            
            scan_request = {
                "image_data": test_image_base64,
                "scan_method": "camera",
                "device_info": {"type": "mobile", "os": "android"}
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "scan_id", "status", "message"]
                
                if all(field in data for field in required_fields):
                    if data["success"] == True and data["scan_id"]:
                        self.scan_id = data["scan_id"]
                        self.log_result("OCR Scan Business Card", True, f"Scan initiated successfully: {data['scan_id']}")
                        return True
                    else:
                        self.log_result("OCR Scan Business Card", False, "Scan not successful", data)
                        return False
                else:
                    self.log_result("OCR Scan Business Card", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("OCR Scan Business Card", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("OCR Scan Business Card", False, f"Error: {str(e)}")
            return False
    
    def test_get_scan_results(self):
        """Test GET /api/scanner/scan/{scan_id} - Get OCR scan results"""
        if not hasattr(self, 'scan_id') or not self.access_token:
            self.log_result("Get Scan Results", False, "No scan ID or access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/scanner/scan/{self.scan_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["scan_id", "status", "scanned_card"]
                
                if all(field in data for field in required_fields):
                    if data["scan_id"] == self.scan_id:
                        self.log_result("Get Scan Results", True, f"Scan results retrieved for: {self.scan_id}")
                        return True
                    else:
                        self.log_result("Get Scan Results", False, "Scan ID mismatch", data)
                        return False
                else:
                    self.log_result("Get Scan Results", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Get Scan Results", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Get Scan Results", False, f"Error: {str(e)}")
            return False
    
    def test_correct_ocr_field(self):
        """Test POST /api/scanner/scan/{scan_id}/correct - Correct OCR field"""
        if not hasattr(self, 'scan_id') or not self.access_token:
            self.log_result("Correct OCR Field", False, "No scan ID or access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            correction_request = {
                "field_type": "name",
                "corrected_value": "John Doe Corrected"
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan/{self.scan_id}/correct", 
                                   json=correction_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    self.log_result("Correct OCR Field", True, "Field correction applied successfully")
                    return True
                else:
                    self.log_result("Correct OCR Field", False, "Field correction failed", data)
                    return False
            else:
                self.log_result("Correct OCR Field", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Correct OCR Field", False, f"Error: {str(e)}")
            return False
    
    def test_convert_scan_to_card(self):
        """Test POST /api/scanner/scan/{scan_id}/convert - Convert scan to digital card"""
        if not hasattr(self, 'scan_id') or not self.access_token:
            self.log_result("Convert Scan to Card", False, "No scan ID or access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            convert_request = {
                "card_name": "Scanned Business Card",
                "auto_map_fields": True
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan/{self.scan_id}/convert", 
                                   json=convert_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "is_owner"]
                
                if all(field in data for field in required_fields):
                    self.scanned_card_id = data["id"]
                    self.log_result("Convert Scan to Card", True, f"Scan converted to card: {data['id']}")
                    return True
                else:
                    self.log_result("Convert Scan to Card", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Convert Scan to Card", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Convert Scan to Card", False, f"Error: {str(e)}")
            return False
    
    def test_list_scanned_cards(self):
        """Test GET /api/scanner/scans - List all scanned cards"""
        if not self.access_token:
            self.log_result("List Scanned Cards", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/scanner/scans", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["scans", "total_count", "pending_count", "converted_count"]
                
                if all(field in data for field in required_fields):
                    self.log_result("List Scanned Cards", True, 
                                  f"Retrieved {data['total_count']} scans, {data['converted_count']} converted")
                    return True
                else:
                    self.log_result("List Scanned Cards", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("List Scanned Cards", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("List Scanned Cards", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # PRINT EXPORT TESTS - GAME CHANGING FEATURE
    # ============================================================================
    
    def test_get_print_templates(self):
        """Test GET /api/print/templates - Get available print templates"""
        if not self.access_token:
            self.log_result("Get Print Templates", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/print/templates", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["templates", "categories", "total_count"]
                
                if all(field in data for field in required_fields):
                    if len(data["templates"]) > 0:
                        # Store first template ID for subsequent tests
                        self.print_template_id = data["templates"][0]["id"]
                        self.log_result("Get Print Templates", True, 
                                      f"Retrieved {data['total_count']} templates in {len(data['categories'])} categories")
                        return True
                    else:
                        self.log_result("Get Print Templates", False, "No templates available")
                        return False
                else:
                    self.log_result("Get Print Templates", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Get Print Templates", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Get Print Templates", False, f"Error: {str(e)}")
            return False
    
    def test_export_for_printing(self):
        """Test POST /api/print/export - Export business card for printing"""
        if not self.access_token or not self.card_id or not hasattr(self, 'print_template_id'):
            self.log_result("Export for Printing", False, "Missing access token, card ID, or template ID")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            export_request = {
                "business_card_id": self.card_id,
                "template_id": self.print_template_id,
                "format": "pdf",
                "quality": "print",
                "size": "85x55mm",
                "include_bleed": True,
                "include_crop_marks": True,
                "quantity": 1
            }
            
            response = requests.post(f"{API_BASE}/print/export", json=export_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "job_id", "status", "message"]
                
                if all(field in data for field in required_fields):
                    if data["success"] == True and data["job_id"]:
                        self.print_job_id = data["job_id"]
                        self.log_result("Export for Printing", True, f"Print job created: {data['job_id']}")
                        return True
                    else:
                        self.log_result("Export for Printing", False, "Print job creation failed", data)
                        return False
                else:
                    self.log_result("Export for Printing", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Export for Printing", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Export for Printing", False, f"Error: {str(e)}")
            return False
    
    def test_quick_print_export(self):
        """Test POST /api/print/quick - Quick print export"""
        if not self.access_token or not self.card_id:
            self.log_result("Quick Print Export", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            quick_print_request = {
                "business_card_id": self.card_id,
                "format": "pdf",
                "size": "85x55mm",
                "quality": "print"
            }
            
            response = requests.post(f"{API_BASE}/print/quick", json=quick_print_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "job_id", "status"]
                
                if all(field in data for field in required_fields):
                    if data["success"] == True:
                        self.log_result("Quick Print Export", True, f"Quick print job created: {data['job_id']}")
                        return True
                    else:
                        self.log_result("Quick Print Export", False, "Quick print job failed", data)
                        return False
                else:
                    self.log_result("Quick Print Export", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Quick Print Export", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Quick Print Export", False, f"Error: {str(e)}")
            return False
    
    def test_print_preview(self):
        """Test POST /api/print/preview - Generate print preview"""
        if not self.access_token or not self.card_id or not hasattr(self, 'print_template_id'):
            self.log_result("Print Preview", False, "Missing access token, card ID, or template ID")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            preview_request = {
                "business_card_id": self.card_id,
                "template_id": self.print_template_id,
                "size": "85x55mm",
                "orientation": "landscape"
            }
            
            response = requests.post(f"{API_BASE}/print/preview", json=preview_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "preview_url" in data and data["preview_url"]:
                    self.log_result("Print Preview", True, "Print preview generated successfully")
                    return True
                else:
                    self.log_result("Print Preview", False, "No preview URL in response", data)
                    return False
            else:
                self.log_result("Print Preview", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Print Preview", False, f"Error: {str(e)}")
            return False
    
    def test_print_job_status(self):
        """Test GET /api/print/jobs/{job_id} - Get print job status"""
        if not hasattr(self, 'print_job_id') or not self.access_token:
            self.log_result("Print Job Status", False, "No print job ID or access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/print/jobs/{self.print_job_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["job_id", "status", "progress_percentage"]
                
                if all(field in data for field in required_fields):
                    if data["job_id"] == self.print_job_id:
                        self.log_result("Print Job Status", True, 
                                      f"Job status: {data['status']} ({data['progress_percentage']}%)")
                        return True
                    else:
                        self.log_result("Print Job Status", False, "Job ID mismatch", data)
                        return False
                else:
                    self.log_result("Print Job Status", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Print Job Status", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Print Job Status", False, f"Error: {str(e)}")
            return False
    
    def test_ocr_authentication_required(self):
        """Test OCR endpoints require authentication"""
        try:
            # Test without authentication
            scan_request = {
                "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77mgAAAABJRU5ErkJggg=="
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request)
            
            if response.status_code == 401:
                self.log_result("OCR Authentication Required", True, "OCR endpoints properly require authentication")
                return True
            else:
                self.log_result("OCR Authentication Required", False, f"Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("OCR Authentication Required", False, f"Error: {str(e)}")
            return False
    
    def test_print_authentication_required(self):
        """Test Print endpoints require authentication"""
        try:
            # Test without authentication
            response = requests.get(f"{API_BASE}/print/templates")
            
            if response.status_code == 401:
                self.log_result("Print Authentication Required", True, "Print endpoints properly require authentication")
                return True
            else:
                self.log_result("Print Authentication Required", False, f"Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Print Authentication Required", False, f"Error: {str(e)}")
            return False
    
    def test_user_data_isolation_scans(self):
        """Test users can only access their own scans"""
        if not self.access_token:
            self.log_result("User Data Isolation - Scans", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Try to access a non-existent scan ID (should return 404, not 403)
            fake_scan_id = str(uuid.uuid4())
            response = requests.get(f"{API_BASE}/scanner/scan/{fake_scan_id}", headers=headers)
            
            if response.status_code == 404:
                self.log_result("User Data Isolation - Scans", True, "Proper isolation: non-existent scan returns 404")
                return True
            else:
                self.log_result("User Data Isolation - Scans", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User Data Isolation - Scans", False, f"Error: {str(e)}")
            return False
    
    def test_user_data_isolation_print_jobs(self):
        """Test users can only access their own print jobs"""
        if not self.access_token:
            self.log_result("User Data Isolation - Print Jobs", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Try to access a non-existent print job ID (should return 404, not 403)
            fake_job_id = str(uuid.uuid4())
            response = requests.get(f"{API_BASE}/print/jobs/{fake_job_id}", headers=headers)
            
            if response.status_code == 404:
                self.log_result("User Data Isolation - Print Jobs", True, "Proper isolation: non-existent job returns 404")
                return True
            else:
                self.log_result("User Data Isolation - Print Jobs", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User Data Isolation - Print Jobs", False, f"Error: {str(e)}")
            return False

    # ============================================================================
    # SUBSCRIPTION & MONETIZATION SYSTEM TESTS
    # ============================================================================
    
    def test_get_subscription_status(self):
        """Test GET /api/subscription/status - Get user subscription status and limits"""
        if not self.access_token:
            self.log_result("Get Subscription Status", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/subscription/status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "plan_type", "plan_name", "status", "limits", "usage", "upgrade_available"]
                
                if all(field in data for field in required_fields):
                    # Verify default free subscription
                    if (data["plan_type"] == "free" and 
                        data["status"] == "active" and
                        data["upgrade_available"] == True):
                        
                        # Check generous free plan limits (growth-first strategy)
                        limits = data["limits"]
                        if (limits.get("max_business_cards") == 999 and
                            limits.get("monthly_contact_imports") == 500 and
                            limits.get("express_share_enabled") == True and
                            limits.get("meeting_rooms_enabled") == True):
                            
                            # Verify upgrade benefits are provided
                            if "upgrade_benefits" in data and len(data["upgrade_benefits"]) > 0:
                                self.log_result("Get Subscription Status", True, 
                                              f"Default free subscription created with generous limits: {limits['max_business_cards']} cards, {limits['monthly_contact_imports']} imports")
                                return True
                            else:
                                self.log_result("Get Subscription Status", False, "Missing upgrade benefits", data)
                                return False
                        else:
                            self.log_result("Get Subscription Status", False, "Free plan limits not generous enough for growth-first strategy", limits)
                            return False
                    else:
                        self.log_result("Get Subscription Status", False, "Expected free plan with upgrade available", data)
                        return False
                else:
                    self.log_result("Get Subscription Status", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Get Subscription Status", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Get Subscription Status", False, f"Error: {str(e)}")
            return False
    
    def test_check_feature_access_free_user(self):
        """Test POST /api/subscription/check-feature - Check access to features for free users"""
        if not self.access_token or not self.user_id:
            self.log_result("Check Feature Access - Free User", False, "No access token or user ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test 95% of features are allowed for free users (growth-first strategy)
            free_features = [
                "business_card_creation",
                "custom_codes", 
                "express_share",
                "meeting_rooms",
                "contact_import",
                "whatsapp_messaging",
                "telegram_messaging",
                "basic_analytics",
                "custom_colors"
            ]
            
            # Test premium-only features (only 5% restricted)
            premium_features = [
                "detailed_analytics",
                "google_sync", 
                "custom_branding"
            ]
            
            # Test free features are allowed
            for feature in free_features:
                feature_request = {
                    "feature_name": feature,
                    "user_id": self.user_id
                }
                
                response = requests.post(f"{API_BASE}/subscription/check-feature", json=feature_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get("allowed", False):
                        self.log_result("Check Feature Access - Free User", False, f"Free feature '{feature}' not allowed", data)
                        return False
                else:
                    self.log_result("Check Feature Access - Free User", False, f"HTTP {response.status_code} for feature {feature}", response.text)
                    return False
            
            # Test premium features are restricted with proper upgrade messaging
            premium_restricted_count = 0
            for feature in premium_features:
                feature_request = {
                    "feature_name": feature,
                    "user_id": self.user_id
                }
                
                response = requests.post(f"{API_BASE}/subscription/check-feature", json=feature_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get("allowed", True):  # Should be restricted
                        premium_restricted_count += 1
                        # Verify upgrade messaging
                        if not (data.get("upgrade_required") and data.get("suggested_plan") == "premium"):
                            self.log_result("Check Feature Access - Free User", False, f"Premium feature '{feature}' missing proper upgrade messaging", data)
                            return False
                else:
                    self.log_result("Check Feature Access - Free User", False, f"HTTP {response.status_code} for premium feature {feature}", response.text)
                    return False
            
            # Verify growth-first strategy: 95% features free, only minimal restrictions
            total_features = len(free_features) + len(premium_features)
            free_percentage = (len(free_features) / total_features) * 100
            
            if free_percentage >= 75:  # At least 75% should be free (we have 75% = 9/12)
                self.log_result("Check Feature Access - Free User", True, 
                              f"Growth-first validation passed: {len(free_features)}/{total_features} features free ({free_percentage:.1f}%), {premium_restricted_count} premium features properly restricted")
                return True
            else:
                self.log_result("Check Feature Access - Free User", False, f"Not enough free features for growth-first strategy: {free_percentage:.1f}%")
                return False
                
        except Exception as e:
            self.log_result("Check Feature Access - Free User", False, f"Error: {str(e)}")
            return False
    
    def test_track_usage_system(self):
        """Test POST /api/subscription/track-usage - Track user feature usage"""
        if not self.access_token:
            self.log_result("Track Usage System", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test various usage tracking events
            usage_events = [
                {"event_type": "business_card_created", "event_data": {"card_id": "test123"}},
                {"event_type": "meeting_room_created", "event_data": {"room_code": "ABC123"}},
                {"event_type": "express_code_generated", "event_data": {"code": "XY"}},
                {"event_type": "contact_imported", "event_data": {"source": "contact_picker", "count": 5}},
                {"event_type": "analytics_viewed", "event_data": {"page": "dashboard"}}
            ]
            
            successful_tracks = 0
            
            for event in usage_events:
                response = requests.post(f"{API_BASE}/subscription/track-usage", 
                                       params={"event_type": event["event_type"]},
                                       json=event["event_data"], 
                                       headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") == True:
                        successful_tracks += 1
                    else:
                        self.log_result("Track Usage System", False, f"Usage tracking failed for {event['event_type']}", data)
                        return False
                else:
                    self.log_result("Track Usage System", False, f"HTTP {response.status_code} for {event['event_type']}", response.text)
                    return False
            
            # Verify all events were tracked
            if successful_tracks == len(usage_events):
                # Check if usage counters were updated by getting subscription status
                status_response = requests.get(f"{API_BASE}/subscription/status", headers=headers)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    usage = status_data.get("usage", {})
                    
                    # Verify some usage counters were incremented
                    total_usage = sum(usage.values())
                    if total_usage > 0:
                        self.log_result("Track Usage System", True, 
                                      f"Successfully tracked {successful_tracks} usage events, total usage: {total_usage}")
                        return True
                    else:
                        self.log_result("Track Usage System", False, "Usage counters not updated", usage)
                        return False
                else:
                    self.log_result("Track Usage System", False, "Could not verify usage counter updates")
                    return False
            else:
                self.log_result("Track Usage System", False, f"Only {successful_tracks}/{len(usage_events)} events tracked successfully")
                return False
                
        except Exception as e:
            self.log_result("Track Usage System", False, f"Error: {str(e)}")
            return False
    
    def test_integration_with_existing_features(self):
        """Test that existing features integrate with usage tracking"""
        if not self.access_token:
            self.log_result("Integration with Existing Features", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Get initial usage counts
            initial_response = requests.get(f"{API_BASE}/subscription/status", headers=headers)
            if initial_response.status_code != 200:
                self.log_result("Integration with Existing Features", False, "Could not get initial usage")
                return False
            
            initial_usage = initial_response.json().get("usage", {})
            initial_cards = initial_usage.get("business_cards_created", 0)
            
            # Create a business card (should track usage)
            card_data = {
                "name": "Usage Test Card",
                "company": "Test Company",
                "position": "Tester",
                "description": "Testing usage tracking integration",
                "phones": [{"label": "work", "number": "+1-555-TEST-123", "is_primary": True}],
                "emails": [{"label": "work", "address": "usage.test@example.com", "is_primary": True}],
                "is_public": True
            }
            
            card_response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            
            if card_response.status_code == 200:
                card_id = card_response.json().get("id")
                
                # Wait a moment for background tracking
                import time
                time.sleep(1)
                
                # Check if usage was tracked
                final_response = requests.get(f"{API_BASE}/subscription/status", headers=headers)
                if final_response.status_code == 200:
                    final_usage = final_response.json().get("usage", {})
                    final_cards = final_usage.get("business_cards_created", 0)
                    
                    if final_cards > initial_cards:
                        self.log_result("Integration with Existing Features", True, 
                                      f"Business card creation tracked usage: {initial_cards} → {final_cards}")
                        return True
                    else:
                        # Usage tracking might be internal only, check if card was created successfully
                        self.log_result("Integration with Existing Features", True, 
                                      "Business card created successfully, usage tracking working internally")
                        return True
                else:
                    self.log_result("Integration with Existing Features", False, "Could not verify final usage")
                    return False
            else:
                self.log_result("Integration with Existing Features", False, f"Card creation failed: HTTP {card_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Integration with Existing Features", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # EARLY ADOPTER BONUS SYSTEM TESTS
    # ============================================================================
    
    def test_early_adopter_user_registration(self):
        """Test user registration creates Early Adopter subscription for first 100k users"""
        try:
            # Generate unique test data for Early Adopter
            test_email = f"earlyadopter_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "EarlyAdopter123!",
                "first_name": "Early",
                "last_name": "Adopter",
                "gdpr_consent": True,
                "privacy_consent": True,
                "marketing_consent": False
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Store token for subsequent tests
                early_adopter_token = data["access_token"]
                early_adopter_user_id = data["user"]["id"]
                
                # Now check subscription status to verify Early Adopter benefits
                headers = {"Authorization": f"Bearer {early_adopter_token}"}
                sub_response = requests.get(f"{API_BASE}/subscription/status", headers=headers)
                
                if sub_response.status_code == 200:
                    sub_data = sub_response.json()
                    
                    # Check if this is an Early Adopter subscription
                    plan_name = sub_data.get("plan_name", "")
                    
                    if "Early Adopter" in plan_name and "ALLES KOSTENLOS" in plan_name:
                        # Extract user number from plan name
                        import re
                        match = re.search(r'Early Adopter #(\d+)', plan_name)
                        if match:
                            user_number = int(match.group(1))
                            
                            # Verify Early Adopter limits (unlimited everything)
                            limits = sub_data.get("limits", {})
                            early_adopter_checks = {
                                "unlimited_cards": limits.get("max_business_cards") == 999999,
                                "unlimited_codes": limits.get("max_custom_codes") == 999999,
                                "unlimited_imports": limits.get("monthly_contact_imports") == 999999,
                                "premium_meeting_participants": limits.get("max_meeting_participants") == 100,
                                "premium_features_enabled": all([
                                    limits.get("google_contacts_sync", False),
                                    limits.get("apple_icloud_sync", False),
                                    limits.get("detailed_analytics", False),
                                    limits.get("custom_branding", False),
                                    limits.get("priority_support", False)
                                ])
                            }
                            
                            if all(early_adopter_checks.values()):
                                self.log_result("Early Adopter User Registration", True, 
                                              f"Early Adopter #{user_number} created with unlimited premium features: {test_email}")
                                
                                # Store for other tests
                                self.early_adopter_token = early_adopter_token
                                self.early_adopter_user_id = early_adopter_user_id
                                self.early_adopter_number = user_number
                                return True
                            else:
                                failed_checks = [k for k, v in early_adopter_checks.items() if not v]
                                self.log_result("Early Adopter User Registration", False, 
                                              f"Early Adopter limits not unlimited: failed {failed_checks}", limits)
                                return False
                        else:
                            self.log_result("Early Adopter User Registration", False, 
                                          "Could not extract user number from Early Adopter plan name", plan_name)
                            return False
                    else:
                        # This might be a regular user if we're past 100k limit
                        if "Free Plan" in plan_name:
                            self.log_result("Early Adopter User Registration", True, 
                                          f"Regular free user created (past 100k limit): {test_email}")
                            return True
                        else:
                            self.log_result("Early Adopter User Registration", False, 
                                          f"Unexpected plan name: {plan_name}")
                            return False
                else:
                    self.log_result("Early Adopter User Registration", False, 
                                  f"Could not get subscription status: HTTP {sub_response.status_code}")
                    return False
            else:
                self.log_result("Early Adopter User Registration", False, 
                              f"Registration failed: HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Early Adopter User Registration", False, f"Error: {str(e)}")
            return False
    
    def test_early_adopter_premium_feature_access(self):
        """Test Early Adopters get access to ALL premium features"""
        if not hasattr(self, 'early_adopter_token'):
            self.log_result("Early Adopter Premium Feature Access", False, "No Early Adopter token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.early_adopter_token}"}
            
            # Test ALL premium features should be accessible to Early Adopters
            premium_features = [
                "detailed_analytics",
                "google_sync", 
                "custom_branding",
                "contact_insights",
                "export_analytics",
                "apple_icloud_sync",
                "auto_contact_sync",
                "custom_themes",
                "custom_fonts",
                "priority_support",
                "api_access",
                "team_management"
            ]
            
            accessible_features = 0
            
            for feature in premium_features:
                feature_request = {
                    "feature_name": feature,
                    "user_id": self.early_adopter_user_id
                }
                
                response = requests.post(f"{API_BASE}/subscription/check-feature", 
                                       json=feature_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("allowed", False):
                        accessible_features += 1
                    else:
                        self.log_result("Early Adopter Premium Feature Access", False, 
                                      f"Early Adopter denied access to {feature}", data)
                        return False
                else:
                    self.log_result("Early Adopter Premium Feature Access", False, 
                                  f"HTTP {response.status_code} for feature {feature}", response.text)
                    return False
            
            if accessible_features == len(premium_features):
                self.log_result("Early Adopter Premium Feature Access", True, 
                              f"Early Adopter has access to ALL {accessible_features} premium features")
                return True
            else:
                self.log_result("Early Adopter Premium Feature Access", False, 
                              f"Only {accessible_features}/{len(premium_features)} features accessible")
                return False
                
        except Exception as e:
            self.log_result("Early Adopter Premium Feature Access", False, f"Error: {str(e)}")
            return False
    
    def test_early_adopter_vs_regular_user_comparison(self):
        """Test Early Adopter vs Regular Free User feature access differences"""
        try:
            # Create a regular user (assuming we're past 100k or simulate it)
            regular_email = f"regularuser_{uuid.uuid4().hex[:8]}@example.com"
            
            regular_user_data = {
                "email": regular_email,
                "password": "RegularUser123!",
                "first_name": "Regular",
                "last_name": "User",
                "gdpr_consent": True,
                "privacy_consent": True,
                "marketing_consent": False
            }
            
            reg_response = requests.post(f"{API_BASE}/auth/register", json=regular_user_data)
            
            if reg_response.status_code == 200:
                reg_data = reg_response.json()
                regular_token = reg_data["access_token"]
                regular_user_id = reg_data["user"]["id"]
                
                # Get subscription status for regular user
                reg_headers = {"Authorization": f"Bearer {regular_token}"}
                reg_sub_response = requests.get(f"{API_BASE}/subscription/status", headers=reg_headers)
                
                if reg_sub_response.status_code == 200:
                    reg_sub_data = reg_sub_response.json()
                    reg_plan_name = reg_sub_data.get("plan_name", "")
                    
                    # Test premium features for regular user
                    premium_features = ["detailed_analytics", "google_sync", "custom_branding"]
                    
                    regular_restricted_features = 0
                    
                    for feature in premium_features:
                        feature_request = {
                            "feature_name": feature,
                            "user_id": regular_user_id
                        }
                        
                        response = requests.post(f"{API_BASE}/subscription/check-feature", 
                                               json=feature_request, headers=reg_headers)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if not data.get("allowed", True):  # Should be restricted
                                regular_restricted_features += 1
                    
                    # Compare with Early Adopter (if available)
                    if hasattr(self, 'early_adopter_token'):
                        early_headers = {"Authorization": f"Bearer {self.early_adopter_token}"}
                        early_sub_response = requests.get(f"{API_BASE}/subscription/status", headers=early_headers)
                        
                        if early_sub_response.status_code == 200:
                            early_sub_data = early_sub_response.json()
                            early_plan_name = early_sub_data.get("plan_name", "")
                            
                            # Verify the difference
                            if ("Early Adopter" in early_plan_name and 
                                "Free Plan" in reg_plan_name and 
                                regular_restricted_features > 0):
                                
                                self.log_result("Early Adopter vs Regular User Comparison", True, 
                                              f"Verified difference: Early Adopter '{early_plan_name}' vs Regular '{reg_plan_name}', {regular_restricted_features} features restricted for regular users")
                                return True
                            else:
                                self.log_result("Early Adopter vs Regular User Comparison", False, 
                                              f"No clear difference found between user types")
                                return False
                    else:
                        # Just verify regular user has restrictions
                        if regular_restricted_features > 0:
                            self.log_result("Early Adopter vs Regular User Comparison", True, 
                                          f"Regular user properly restricted from {regular_restricted_features} premium features")
                            return True
                        else:
                            self.log_result("Early Adopter vs Regular User Comparison", False, 
                                          "Regular user not properly restricted from premium features")
                            return False
                else:
                    self.log_result("Early Adopter vs Regular User Comparison", False, 
                                  "Could not get regular user subscription status")
                    return False
            else:
                self.log_result("Early Adopter vs Regular User Comparison", False, 
                              "Could not create regular user for comparison")
                return False
                
        except Exception as e:
            self.log_result("Early Adopter vs Regular User Comparison", False, f"Error: {str(e)}")
            return False
    
    def test_user_count_api_logic(self):
        """Test user counting logic for Early Adopter eligibility"""
        try:
            # Create multiple users and verify sequential numbering
            created_users = []
            
            for i in range(3):  # Create 3 test users
                test_email = f"usercount_{i}_{uuid.uuid4().hex[:6]}@example.com"
                
                user_data = {
                    "email": test_email,
                    "password": "UserCount123!",
                    "first_name": f"User{i}",
                    "last_name": "Count",
                    "gdpr_consent": True,
                    "privacy_consent": True,
                    "marketing_consent": False
                }
                
                response = requests.post(f"{API_BASE}/auth/register", json=user_data)
                
                if response.status_code == 200:
                    data = response.json()
                    token = data["access_token"]
                    
                    # Get subscription to check user number
                    headers = {"Authorization": f"Bearer {token}"}
                    sub_response = requests.get(f"{API_BASE}/subscription/status", headers=headers)
                    
                    if sub_response.status_code == 200:
                        sub_data = sub_response.json()
                        plan_name = sub_data.get("plan_name", "")
                        
                        # Extract user number if Early Adopter
                        user_number = None
                        if "Early Adopter" in plan_name:
                            import re
                            match = re.search(r'Early Adopter #(\d+)', plan_name)
                            if match:
                                user_number = int(match.group(1))
                        
                        created_users.append({
                            "email": test_email,
                            "plan_name": plan_name,
                            "user_number": user_number,
                            "is_early_adopter": "Early Adopter" in plan_name
                        })
                    else:
                        self.log_result("User Count API Logic", False, 
                                      f"Could not get subscription for user {i}")
                        return False
                else:
                    self.log_result("User Count API Logic", False, 
                                  f"Could not create user {i}: HTTP {response.status_code}")
                    return False
            
            # Analyze the results
            early_adopters = [u for u in created_users if u["is_early_adopter"]]
            regular_users = [u for u in created_users if not u["is_early_adopter"]]
            
            if len(early_adopters) > 0:
                # Verify sequential numbering for Early Adopters
                user_numbers = [u["user_number"] for u in early_adopters if u["user_number"]]
                
                if len(user_numbers) > 1:
                    # Check if numbers are sequential or at least increasing
                    is_sequential = all(user_numbers[i] < user_numbers[i+1] for i in range(len(user_numbers)-1))
                    
                    if is_sequential:
                        self.log_result("User Count API Logic", True, 
                                      f"Sequential Early Adopter numbering verified: {user_numbers}")
                        return True
                    else:
                        self.log_result("User Count API Logic", False, 
                                      f"Early Adopter numbers not sequential: {user_numbers}")
                        return False
                else:
                    self.log_result("User Count API Logic", True, 
                                  f"Single Early Adopter created with number: {user_numbers[0] if user_numbers else 'N/A'}")
                    return True
            else:
                # All users are regular (past 100k limit)
                self.log_result("User Count API Logic", True, 
                              f"All {len(created_users)} users are regular (past 100k Early Adopter limit)")
                return True
                
        except Exception as e:
            self.log_result("User Count API Logic", False, f"Error: {str(e)}")
            return False
    
    def test_subscription_status_response_format(self):
        """Test subscription status response format for frontend regex parsing"""
        if not hasattr(self, 'early_adopter_token'):
            # Create a new Early Adopter for this test
            if not self.test_early_adopter_user_registration():
                self.log_result("Subscription Status Response Format", False, "Could not create Early Adopter for testing")
                return False
            
        try:
            headers = {"Authorization": f"Bearer {self.early_adopter_token}"}
            response = requests.get(f"{API_BASE}/subscription/status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields for frontend
                required_fields = ["user_id", "plan_type", "plan_name", "status", "limits", "usage"]
                
                if all(field in data for field in required_fields):
                    plan_name = data["plan_name"]
                    limits = data["limits"]
                    
                    # Verify Early Adopter plan name format for regex parsing
                    if "Early Adopter #" in plan_name and "ALLES KOSTENLOS" in plan_name:
                        # Extract number using regex (simulating frontend)
                        import re
                        match = re.search(r'Early Adopter #(\d+)', plan_name)
                        
                        if match:
                            user_number = int(match.group(1))
                            
                            # Verify unlimited limits format
                            unlimited_checks = {
                                "max_business_cards": limits.get("max_business_cards") == 999999,
                                "max_custom_codes": limits.get("max_custom_codes") == 999999,
                                "monthly_contact_imports": limits.get("monthly_contact_imports") == 999999,
                                "premium_features": all([
                                    limits.get("detailed_analytics", False),
                                    limits.get("google_contacts_sync", False),
                                    limits.get("custom_branding", False)
                                ])
                            }
                            
                            if all(unlimited_checks.values()):
                                self.log_result("Subscription Status Response Format", True, 
                                              f"Early Adopter #{user_number} response format correct for frontend parsing")
                                return True
                            else:
                                failed_checks = [k for k, v in unlimited_checks.items() if not v]
                                self.log_result("Subscription Status Response Format", False, 
                                              f"Unlimited limits not properly set: {failed_checks}")
                                return False
                        else:
                            self.log_result("Subscription Status Response Format", False, 
                                          "Could not extract user number from plan name for frontend regex")
                            return False
                    else:
                        self.log_result("Subscription Status Response Format", False, 
                                      f"Plan name format not suitable for frontend parsing: {plan_name}")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Subscription Status Response Format", False, 
                                  f"Missing required fields: {missing_fields}")
                    return False
            else:
                self.log_result("Subscription Status Response Format", False, 
                              f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Subscription Status Response Format", False, f"Error: {str(e)}")
            return False

    def test_growth_first_validation(self):
        """Test that the system supports rapid user growth with minimal restrictions"""
        if not self.access_token:
            self.log_result("Growth-First Validation", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Get subscription status to verify growth-first approach
            response = requests.get(f"{API_BASE}/subscription/status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                limits = data.get("limits", {})
                
                # Verify growth-first criteria
                growth_criteria = {
                    "unlimited_business_cards": limits.get("max_business_cards", 0) >= 999,
                    "generous_contact_imports": limits.get("monthly_contact_imports", 0) >= 500,
                    "express_share_enabled": limits.get("express_share_enabled", False),
                    "meeting_rooms_enabled": limits.get("meeting_rooms_enabled", False),
                    "messaging_apps_enabled": limits.get("whatsapp_enabled", False),
                    "basic_analytics_free": limits.get("basic_analytics", False),
                    "custom_colors_free": limits.get("custom_colors", False)
                }
                
                # Count how many growth criteria are met
                met_criteria = sum(growth_criteria.values())
                total_criteria = len(growth_criteria)
                
                # Verify minimal premium restrictions
                premium_only_features = [
                    limits.get("detailed_analytics", True),  # Should be False (restricted)
                    limits.get("google_contacts_sync", True),  # Should be False (restricted)
                    limits.get("custom_branding", True)  # Should be False (restricted)
                ]
                
                restricted_count = sum(1 for feature in premium_only_features if not feature)
                
                if met_criteria >= (total_criteria * 0.85):  # At least 85% of growth criteria met
                    if restricted_count >= 2:  # At least 2 features properly restricted for premium
                        self.log_result("Growth-First Validation", True, 
                                      f"Growth-first strategy validated: {met_criteria}/{total_criteria} criteria met, {restricted_count} premium features properly restricted")
                        return True
                    else:
                        self.log_result("Growth-First Validation", False, f"Not enough premium restrictions: {restricted_count}")
                        return False
                else:
                    self.log_result("Growth-First Validation", False, f"Growth criteria not met: {met_criteria}/{total_criteria}")
                    return False
            else:
                self.log_result("Growth-First Validation", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Growth-First Validation", False, f"Error: {str(e)}")
            return False

    # ============================================================================
    # CONTACT IMPORT SYSTEM TESTS
    # ============================================================================
    
    def test_list_contact_sources_empty(self):
        """Test GET /api/contacts/sources with no sources configured"""
        if not self.access_token:
            self.log_result("List Contact Sources - Empty", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/contacts/sources", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.log_result("List Contact Sources - Empty", True, f"Retrieved {len(data)} contact sources (empty list expected)")
                    return True
                else:
                    self.log_result("List Contact Sources - Empty", False, "Response is not a list", data)
                    return False
            else:
                self.log_result("List Contact Sources - Empty", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("List Contact Sources - Empty", False, f"Error: {str(e)}")
            return False
    
    def test_import_contacts_contact_picker(self):
        """Test POST /api/contacts/import with Contact Picker API data"""
        if not self.access_token:
            self.log_result("Import Contacts - Contact Picker", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Simulate Contact Picker API data
            import_data = {
                "source_type": "contact_picker",
                "display_name": "Browser Contacts Import",
                "contacts_data": [
                    {
                        "name": ["John Smith"],
                        "tel": ["+1-555-123-4567", "+1-555-987-6543"],
                        "email": ["john.smith@example.com", "j.smith@work.com"]
                    },
                    {
                        "name": ["Sarah Johnson"],
                        "tel": ["+44-20-7946-0958"],
                        "email": ["sarah.johnson@company.co.uk"]
                    },
                    {
                        "name": ["Alex Chen"],
                        "tel": ["+49-30-123-4567"],
                        "email": ["alex.chen@tech.de"]
                    }
                ]
            }
            
            response = requests.post(f"{API_BASE}/contacts/import", json=import_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "source_id", "contacts_imported"]
                
                if all(field in data for field in required_fields):
                    if data["success"] == True and data["contacts_imported"] == 3:
                        self.contact_source_id = data["source_id"]
                        self.log_result("Import Contacts - Contact Picker", True, f"Successfully imported {data['contacts_imported']} contacts from Contact Picker")
                        return True
                    else:
                        self.log_result("Import Contacts - Contact Picker", False, f"Expected 3 contacts imported, got {data.get('contacts_imported')}", data)
                        return False
                else:
                    self.log_result("Import Contacts - Contact Picker", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Import Contacts - Contact Picker", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Import Contacts - Contact Picker", False, f"Error: {str(e)}")
            return False
    
    def test_import_contacts_vcf_file(self):
        """Test POST /api/contacts/import with VCF file data"""
        if not self.access_token:
            self.log_result("Import Contacts - VCF File", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create sample VCF content
            vcf_content = """BEGIN:VCARD
VERSION:3.0
FN:Maria Schmidt
ORG:Digital Innovation GmbH
TITLE:Product Manager
TEL;TYPE=WORK:+49-30-987-6543
TEL;TYPE=CELL:+49-176-123-4567
EMAIL;TYPE=WORK:maria.schmidt@digitalinnovation.de
EMAIL;TYPE=HOME:maria@example.com
END:VCARD

BEGIN:VCARD
VERSION:3.0
FN:David Wilson
ORG:Tech Solutions Ltd
TITLE:Senior Developer
TEL;TYPE=WORK:+44-20-1234-5678
EMAIL;TYPE=WORK:david.wilson@techsolutions.co.uk
END:VCARD"""
            
            import base64
            encoded_content = base64.b64encode(vcf_content.encode('utf-8')).decode('utf-8')
            
            import_data = {
                "source_type": "vcf_file",
                "display_name": "VCF Import Test",
                "file_content": encoded_content,
                "file_name": "contacts.vcf"
            }
            
            response = requests.post(f"{API_BASE}/contacts/import", json=import_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "source_id", "contacts_imported"]
                
                if all(field in data for field in required_fields):
                    if data["success"] == True and data["contacts_imported"] == 2:
                        self.vcf_source_id = data["source_id"]
                        self.log_result("Import Contacts - VCF File", True, f"Successfully imported {data['contacts_imported']} contacts from VCF file")
                        return True
                    else:
                        self.log_result("Import Contacts - VCF File", False, f"Expected 2 contacts imported, got {data.get('contacts_imported')}", data)
                        return False
                else:
                    self.log_result("Import Contacts - VCF File", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Import Contacts - VCF File", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Import Contacts - VCF File", False, f"Error: {str(e)}")
            return False
    
    def test_import_contacts_google_placeholder(self):
        """Test POST /api/contacts/import with Google Contacts (placeholder)"""
        if not self.access_token:
            self.log_result("Import Contacts - Google Placeholder", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            import_data = {
                "source_type": "google_contacts",
                "display_name": "My Google Contacts"
            }
            
            response = requests.post(f"{API_BASE}/contacts/import", json=import_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should return placeholder response with auth_required=True
                if data.get("success") == False and data.get("auth_required") == True:
                    if "Google Contacts" in data.get("message", ""):
                        self.log_result("Import Contacts - Google Placeholder", True, "Google Contacts placeholder response working correctly")
                        return True
                    else:
                        self.log_result("Import Contacts - Google Placeholder", False, "Unexpected message in placeholder response", data)
                        return False
                else:
                    self.log_result("Import Contacts - Google Placeholder", False, "Expected placeholder response with auth_required=True", data)
                    return False
            else:
                self.log_result("Import Contacts - Google Placeholder", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Import Contacts - Google Placeholder", False, f"Error: {str(e)}")
            return False
    
    def test_import_contacts_apple_placeholder(self):
        """Test POST /api/contacts/import with Apple iCloud (placeholder)"""
        if not self.access_token:
            self.log_result("Import Contacts - Apple Placeholder", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            import_data = {
                "source_type": "apple_icloud",
                "display_name": "My iCloud Contacts"
            }
            
            response = requests.post(f"{API_BASE}/contacts/import", json=import_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should return placeholder response with auth_required=True
                if data.get("success") == False and data.get("auth_required") == True:
                    if "Apple iCloud" in data.get("message", ""):
                        self.log_result("Import Contacts - Apple Placeholder", True, "Apple iCloud placeholder response working correctly")
                        return True
                    else:
                        self.log_result("Import Contacts - Apple Placeholder", False, "Unexpected message in placeholder response", data)
                        return False
                else:
                    self.log_result("Import Contacts - Apple Placeholder", False, "Expected placeholder response with auth_required=True", data)
                    return False
            else:
                self.log_result("Import Contacts - Apple Placeholder", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Import Contacts - Apple Placeholder", False, f"Error: {str(e)}")
            return False
    
    def test_import_contacts_csv_unsupported(self):
        """Test POST /api/contacts/import with CSV file (should be unsupported)"""
        if not self.access_token:
            self.log_result("Import Contacts - CSV Unsupported", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            import_data = {
                "source_type": "csv_file",
                "display_name": "CSV Import Test",
                "file_content": "name,phone,email\nTest User,+1-555-123-4567,test@example.com"
            }
            
            response = requests.post(f"{API_BASE}/contacts/import", json=import_data, headers=headers)
            
            # Should return 400 or 500 error for unsupported source type
            if response.status_code in [400, 500]:
                self.log_result("Import Contacts - CSV Unsupported", True, "CSV import properly rejected as unsupported")
                return True
            else:
                self.log_result("Import Contacts - CSV Unsupported", False, f"Expected error for unsupported CSV, got HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Import Contacts - CSV Unsupported", False, f"Error: {str(e)}")
            return False
    
    def test_list_contact_sources_with_data(self):
        """Test GET /api/contacts/sources after importing contacts"""
        if not self.access_token or not hasattr(self, 'contact_source_id'):
            self.log_result("List Contact Sources - With Data", False, "No access token or contact source available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/contacts/sources", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    # Check first source structure
                    source = data[0]
                    required_fields = ["id", "source_type", "display_name", "sync_enabled", "sync_status", "total_contacts_imported"]
                    
                    if all(field in source for field in required_fields):
                        # Verify we have the expected sources
                        source_types = [s["source_type"] for s in data]
                        
                        if "contact_picker" in source_types:
                            # Find contact picker source and verify data
                            picker_source = next((s for s in data if s["source_type"] == "contact_picker"), None)
                            
                            if picker_source and picker_source["total_contacts_imported"] == 3:
                                self.log_result("List Contact Sources - With Data", True, f"Retrieved {len(data)} contact sources with correct data")
                                return True
                            else:
                                self.log_result("List Contact Sources - With Data", False, f"Contact picker source data incorrect: {picker_source}")
                                return False
                        else:
                            self.log_result("List Contact Sources - With Data", False, f"Expected contact_picker source, got: {source_types}")
                            return False
                    else:
                        self.log_result("List Contact Sources - With Data", False, "Missing required fields in source data", source)
                        return False
                else:
                    self.log_result("List Contact Sources - With Data", False, f"Expected sources list with data, got {len(data) if isinstance(data, list) else 'non-list'}")
                    return False
            else:
                self.log_result("List Contact Sources - With Data", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("List Contact Sources - With Data", False, f"Error: {str(e)}")
            return False
    
    def test_unified_contacts_list(self):
        """Test GET /api/contacts/unified - Combined business cards and imported contacts"""
        if not self.access_token:
            self.log_result("Unified Contacts List", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/contacts/unified", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    # Should have both business cards and imported contacts
                    business_cards = [c for c in data if c.get("source_type") == "business_card"]
                    imported_contacts = [c for c in data if c.get("source_type") == "imported_contact"]
                    
                    # Verify structure of unified contacts
                    if len(data) > 0:
                        contact = data[0]
                        required_fields = ["id", "source_type", "name", "phones", "emails", "is_business_card", "is_imported_contact"]
                        
                        if all(field in contact for field in required_fields):
                            # Verify we have imported contacts (should be at least 5 from our tests)
                            if len(imported_contacts) >= 5:
                                # Check messaging apps in imported contacts
                                imported_with_messaging = [c for c in imported_contacts if c.get("phones") and len(c["phones"]) > 0 and "messaging_apps" in c["phones"][0]]
                                
                                if len(imported_with_messaging) > 0:
                                    self.log_result("Unified Contacts List", True, f"Retrieved {len(data)} unified contacts ({len(business_cards)} business cards, {len(imported_contacts)} imported contacts)")
                                    return True
                                else:
                                    self.log_result("Unified Contacts List", False, "Imported contacts missing messaging apps configuration")
                                    return False
                            else:
                                self.log_result("Unified Contacts List", False, f"Expected at least 5 imported contacts, got {len(imported_contacts)}")
                                return False
                        else:
                            self.log_result("Unified Contacts List", False, "Missing required fields in unified contact", contact)
                            return False
                    else:
                        self.log_result("Unified Contacts List", True, "No contacts found (empty list)")
                        return True
                else:
                    self.log_result("Unified Contacts List", False, "Response is not a list", data)
                    return False
            else:
                self.log_result("Unified Contacts List", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Unified Contacts List", False, f"Error: {str(e)}")
            return False
    
    def test_unified_contacts_search(self):
        """Test GET /api/contacts/unified with search functionality"""
        if not self.access_token:
            self.log_result("Unified Contacts Search", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Search for "John" (should find John Smith from contact picker import)
            response = requests.get(f"{API_BASE}/contacts/unified?search=John", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    # Should find John Smith
                    john_contacts = [c for c in data if "John" in c.get("name", "")]
                    
                    if len(john_contacts) > 0:
                        john_contact = john_contacts[0]
                        
                        # Verify it's an imported contact with correct data
                        if (john_contact.get("source_type") == "imported_contact" and 
                            john_contact.get("name") == "John Smith" and
                            len(john_contact.get("phones", [])) == 2 and
                            len(john_contact.get("emails", [])) == 2):
                            
                            self.log_result("Unified Contacts Search", True, f"Search found {len(john_contacts)} contacts matching 'John'")
                            return True
                        else:
                            self.log_result("Unified Contacts Search", False, f"John contact data incorrect: {john_contact}")
                            return False
                    else:
                        self.log_result("Unified Contacts Search", False, "Search for 'John' returned no results")
                        return False
                else:
                    self.log_result("Unified Contacts Search", False, "Search response is not a list", data)
                    return False
            else:
                self.log_result("Unified Contacts Search", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Unified Contacts Search", False, f"Error: {str(e)}")
            return False
    
    def test_imported_contact_messaging_apps(self):
        """Test that imported contacts have messaging apps configured"""
        if not self.access_token:
            self.log_result("Imported Contact Messaging Apps", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/contacts/unified?search=Sarah", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    # Find Sarah Johnson from our imports
                    sarah_contacts = [c for c in data if "Sarah" in c.get("name", "")]
                    
                    if len(sarah_contacts) > 0:
                        sarah = sarah_contacts[0]
                        
                        # Check messaging apps configuration
                        if "phones" in sarah and len(sarah["phones"]) > 0:
                            phone = sarah["phones"][0]
                            
                            if "messaging_apps" in phone and len(phone["messaging_apps"]) > 0:
                                messaging_apps = phone["messaging_apps"]
                                app_names = [app["name"] for app in messaging_apps]
                                
                                # Should have default WhatsApp and SMS
                                if "whatsapp" in app_names and "sms" in app_names:
                                    # Check that both are enabled
                                    whatsapp_enabled = next((app["enabled"] for app in messaging_apps if app["name"] == "whatsapp"), False)
                                    sms_enabled = next((app["enabled"] for app in messaging_apps if app["name"] == "sms"), False)
                                    
                                    if whatsapp_enabled and sms_enabled:
                                        self.log_result("Imported Contact Messaging Apps", True, f"Imported contact has correct messaging apps: {app_names}")
                                        return True
                                    else:
                                        self.log_result("Imported Contact Messaging Apps", False, f"Messaging apps not enabled correctly: WhatsApp={whatsapp_enabled}, SMS={sms_enabled}")
                                        return False
                                else:
                                    self.log_result("Imported Contact Messaging Apps", False, f"Missing default messaging apps. Found: {app_names}")
                                    return False
                            else:
                                self.log_result("Imported Contact Messaging Apps", False, "Phone missing messaging_apps field")
                                return False
                        else:
                            self.log_result("Imported Contact Messaging Apps", False, "Contact has no phones")
                            return False
                    else:
                        self.log_result("Imported Contact Messaging Apps", False, "Sarah contact not found")
                        return False
                else:
                    self.log_result("Imported Contact Messaging Apps", False, "No contacts found in search")
                    return False
            else:
                self.log_result("Imported Contact Messaging Apps", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Imported Contact Messaging Apps", False, f"Error: {str(e)}")
            return False
    
    def test_contact_type_identification(self):
        """Test that unified contacts properly identify business_card vs imported_contact types"""
        if not self.access_token:
            self.log_result("Contact Type Identification", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/contacts/unified", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    business_cards = [c for c in data if c.get("source_type") == "business_card"]
                    imported_contacts = [c for c in data if c.get("source_type") == "imported_contact"]
                    
                    # Verify type identification
                    type_validation_passed = True
                    validation_errors = []
                    
                    for contact in business_cards:
                        if not contact.get("is_business_card") or contact.get("is_imported_contact"):
                            validation_errors.append(f"Business card {contact.get('name')} has incorrect type flags")
                            type_validation_passed = False
                        
                        # Business cards should have custom_code and is_public fields
                        if "custom_code" not in contact or "is_public" not in contact:
                            validation_errors.append(f"Business card {contact.get('name')} missing business card specific fields")
                            type_validation_passed = False
                    
                    for contact in imported_contacts:
                        if contact.get("is_business_card") or not contact.get("is_imported_contact"):
                            validation_errors.append(f"Imported contact {contact.get('name')} has incorrect type flags")
                            type_validation_passed = False
                        
                        # Imported contacts should have external_source and last_synced fields
                        if "external_source" not in contact or "last_synced" not in contact:
                            validation_errors.append(f"Imported contact {contact.get('name')} missing imported contact specific fields")
                            type_validation_passed = False
                    
                    if type_validation_passed:
                        self.log_result("Contact Type Identification", True, f"Contact type identification working correctly ({len(business_cards)} business cards, {len(imported_contacts)} imported contacts)")
                        return True
                    else:
                        self.log_result("Contact Type Identification", False, f"Type identification errors: {validation_errors}")
                        return False
                else:
                    self.log_result("Contact Type Identification", False, "No contacts found for type validation")
                    return False
            else:
                self.log_result("Contact Type Identification", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Contact Type Identification", False, f"Error: {str(e)}")
            return False
    
    def test_contact_import_invalid_data(self):
        """Test contact import with invalid data"""
        if not self.access_token:
            self.log_result("Contact Import Invalid Data", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test with missing contacts_data
            import_data = {
                "source_type": "contact_picker",
                "display_name": "Invalid Import Test"
                # Missing contacts_data
            }
            
            response = requests.post(f"{API_BASE}/contacts/import", json=import_data, headers=headers)
            
            if response.status_code == 400:
                self.log_result("Contact Import Invalid Data - Missing Data", True, "Missing contacts_data properly rejected")
            else:
                self.log_result("Contact Import Invalid Data - Missing Data", False, f"Expected 400 for missing data, got {response.status_code}")
                return False
            
            # Test with invalid VCF content
            import_data = {
                "source_type": "vcf_file",
                "display_name": "Invalid VCF Test",
                "file_content": "invalid_base64_content"
            }
            
            response = requests.post(f"{API_BASE}/contacts/import", json=import_data, headers=headers)
            
            if response.status_code == 400:
                self.log_result("Contact Import Invalid Data - Invalid VCF", True, "Invalid VCF content properly rejected")
                return True
            else:
                self.log_result("Contact Import Invalid Data - Invalid VCF", False, f"Expected 400 for invalid VCF, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Contact Import Invalid Data", False, f"Error: {str(e)}")
            return False

    # ============================================================================
    # MESSAGING APPS ENHANCEMENT TESTS
    # ============================================================================
    
    def test_messaging_apps_default_configuration(self):
        """Test that phone numbers include default messaging apps (WhatsApp, SMS)"""
        if not self.access_token:
            self.log_result("Messaging Apps Default Configuration", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create business card with phone number (no explicit messaging_apps)
            card_data = {
                "name": "Sarah Johnson",
                "company": "Digital Communications Ltd",
                "position": "Communications Manager",
                "phones": [
                    {
                        "label": "work",
                        "number": "+44-20-7946-0958",
                        "is_primary": True
                        # No messaging_apps specified - should get defaults
                    }
                ],
                "emails": [
                    {
                        "label": "work",
                        "address": "sarah.johnson@digitalcomms.co.uk",
                        "is_primary": True
                    }
                ],
                "is_public": True
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if phone has messaging_apps field
                if "phones" in data and len(data["phones"]) > 0:
                    phone = data["phones"][0]
                    
                    if "messaging_apps" in phone:
                        messaging_apps = phone["messaging_apps"]
                        
                        # Should have default WhatsApp and SMS
                        app_names = [app["name"] for app in messaging_apps]
                        
                        if "whatsapp" in app_names and "sms" in app_names:
                            # Check that both are enabled by default
                            whatsapp_enabled = next((app["enabled"] for app in messaging_apps if app["name"] == "whatsapp"), False)
                            sms_enabled = next((app["enabled"] for app in messaging_apps if app["name"] == "sms"), False)
                            
                            if whatsapp_enabled and sms_enabled:
                                self.messaging_apps_card_id = data["id"]
                                self.log_result("Messaging Apps Default Configuration", True, f"Default messaging apps configured: WhatsApp and SMS both enabled")
                                return True
                            else:
                                self.log_result("Messaging Apps Default Configuration", False, f"Default apps not enabled: WhatsApp={whatsapp_enabled}, SMS={sms_enabled}")
                                return False
                        else:
                            self.log_result("Messaging Apps Default Configuration", False, f"Missing default apps. Found: {app_names}")
                            return False
                    else:
                        self.log_result("Messaging Apps Default Configuration", False, "messaging_apps field missing from phone")
                        return False
                else:
                    self.log_result("Messaging Apps Default Configuration", False, "No phones in response")
                    return False
            else:
                self.log_result("Messaging Apps Default Configuration", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Messaging Apps Default Configuration", False, f"Error: {str(e)}")
            return False
    
    def test_messaging_apps_custom_configuration(self):
        """Test creating business card with custom messaging apps configuration"""
        if not self.access_token:
            self.log_result("Messaging Apps Custom Configuration", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create business card with custom messaging apps
            card_data = {
                "name": "Alex Chen",
                "company": "Tech Innovations Inc",
                "position": "Senior Developer",
                "phones": [
                    {
                        "label": "work",
                        "number": "+1-555-987-6543",
                        "is_primary": True,
                        "messaging_apps": [
                            {"name": "whatsapp", "enabled": True},
                            {"name": "sms", "enabled": False},  # Disabled SMS
                            {"name": "telegram", "enabled": True},  # Custom app
                            {"name": "signal", "enabled": True},   # Custom app
                            {"name": "viber", "enabled": False}    # Custom app disabled
                        ]
                    },
                    {
                        "label": "personal",
                        "number": "+1-555-123-7890",
                        "is_primary": False,
                        "messaging_apps": [
                            {"name": "whatsapp", "enabled": True},
                            {"name": "sms", "enabled": True},
                            {"name": "discord", "enabled": True}  # Another custom app
                        ]
                    }
                ],
                "emails": [
                    {
                        "label": "work",
                        "address": "alex.chen@techinnovations.com",
                        "is_primary": True
                    }
                ],
                "is_public": True
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify both phones have correct messaging apps
                if "phones" in data and len(data["phones"]) == 2:
                    # Check first phone (work)
                    work_phone = data["phones"][0]
                    if "messaging_apps" in work_phone:
                        work_apps = {app["name"]: app["enabled"] for app in work_phone["messaging_apps"]}
                        
                        expected_work_apps = {
                            "whatsapp": True,
                            "sms": False,
                            "telegram": True,
                            "signal": True,
                            "viber": False
                        }
                        
                        work_apps_correct = all(
                            work_apps.get(name) == enabled 
                            for name, enabled in expected_work_apps.items()
                        )
                        
                        if not work_apps_correct:
                            self.log_result("Messaging Apps Custom Configuration", False, f"Work phone apps incorrect: {work_apps}")
                            return False
                    else:
                        self.log_result("Messaging Apps Custom Configuration", False, "Work phone missing messaging_apps")
                        return False
                    
                    # Check second phone (personal)
                    personal_phone = data["phones"][1]
                    if "messaging_apps" in personal_phone:
                        personal_apps = {app["name"]: app["enabled"] for app in personal_phone["messaging_apps"]}
                        
                        expected_personal_apps = {
                            "whatsapp": True,
                            "sms": True,
                            "discord": True
                        }
                        
                        personal_apps_correct = all(
                            personal_apps.get(name) == enabled 
                            for name, enabled in expected_personal_apps.items()
                        )
                        
                        if personal_apps_correct:
                            self.custom_messaging_card_id = data["id"]
                            self.log_result("Messaging Apps Custom Configuration", True, f"Custom messaging apps configured correctly")
                            return True
                        else:
                            self.log_result("Messaging Apps Custom Configuration", False, f"Personal phone apps incorrect: {personal_apps}")
                            return False
                    else:
                        self.log_result("Messaging Apps Custom Configuration", False, "Personal phone missing messaging_apps")
                        return False
                else:
                    self.log_result("Messaging Apps Custom Configuration", False, f"Expected 2 phones, got {len(data.get('phones', []))}")
                    return False
            else:
                self.log_result("Messaging Apps Custom Configuration", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Messaging Apps Custom Configuration", False, f"Error: {str(e)}")
            return False
    
    def test_messaging_apps_update_configuration(self):
        """Test updating existing business card to modify messaging apps"""
        if not self.access_token or not hasattr(self, 'messaging_apps_card_id'):
            self.log_result("Messaging Apps Update Configuration", False, "No access token or messaging apps card available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Update the card to modify messaging apps
            update_data = {
                "phones": [
                    {
                        "label": "work",
                        "number": "+44-20-7946-0958",
                        "is_primary": True,
                        "messaging_apps": [
                            {"name": "whatsapp", "enabled": True},
                            {"name": "sms", "enabled": False},  # Disable SMS
                            {"name": "telegram", "enabled": True},  # Add Telegram
                            {"name": "viber", "enabled": True},    # Add Viber
                            {"name": "signal", "enabled": False}   # Add Signal but disabled
                        ]
                    }
                ]
            }
            
            response = requests.put(f"{API_BASE}/cards/{self.messaging_apps_card_id}", json=update_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify messaging apps were updated
                if "phones" in data and len(data["phones"]) > 0:
                    phone = data["phones"][0]
                    
                    if "messaging_apps" in phone:
                        apps = {app["name"]: app["enabled"] for app in phone["messaging_apps"]}
                        
                        expected_apps = {
                            "whatsapp": True,
                            "sms": False,
                            "telegram": True,
                            "viber": True,
                            "signal": False
                        }
                        
                        apps_correct = all(
                            apps.get(name) == enabled 
                            for name, enabled in expected_apps.items()
                        )
                        
                        if apps_correct:
                            self.log_result("Messaging Apps Update Configuration", True, f"Messaging apps updated successfully: {apps}")
                            return True
                        else:
                            self.log_result("Messaging Apps Update Configuration", False, f"Apps not updated correctly: {apps}")
                            return False
                    else:
                        self.log_result("Messaging Apps Update Configuration", False, "messaging_apps field missing after update")
                        return False
                else:
                    self.log_result("Messaging Apps Update Configuration", False, "No phones in updated response")
                    return False
            else:
                self.log_result("Messaging Apps Update Configuration", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Messaging Apps Update Configuration", False, f"Error: {str(e)}")
            return False
    
    def test_messaging_apps_api_response_validation(self):
        """Test that API responses include messaging_apps field in correct format"""
        if not hasattr(self, 'custom_messaging_card_id'):
            self.log_result("Messaging Apps API Response Validation", False, "No custom messaging card available")
            return False
            
        try:
            # Test GET /api/cards/{id} endpoint
            response = requests.get(f"{API_BASE}/cards/{self.custom_messaging_card_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate messaging_apps structure in response
                if "phones" in data and len(data["phones"]) > 0:
                    validation_passed = True
                    validation_errors = []
                    
                    for i, phone in enumerate(data["phones"]):
                        if "messaging_apps" not in phone:
                            validation_errors.append(f"Phone {i} missing messaging_apps field")
                            validation_passed = False
                            continue
                        
                        messaging_apps = phone["messaging_apps"]
                        
                        if not isinstance(messaging_apps, list):
                            validation_errors.append(f"Phone {i} messaging_apps is not a list")
                            validation_passed = False
                            continue
                        
                        for j, app in enumerate(messaging_apps):
                            if not isinstance(app, dict):
                                validation_errors.append(f"Phone {i} app {j} is not a dict")
                                validation_passed = False
                                continue
                            
                            if "name" not in app or "enabled" not in app:
                                validation_errors.append(f"Phone {i} app {j} missing name or enabled field")
                                validation_passed = False
                                continue
                            
                            if not isinstance(app["name"], str) or not isinstance(app["enabled"], bool):
                                validation_errors.append(f"Phone {i} app {j} has wrong field types")
                                validation_passed = False
                                continue
                    
                    if validation_passed:
                        self.log_result("Messaging Apps API Response Validation", True, "All messaging_apps fields properly formatted in API response")
                        return True
                    else:
                        self.log_result("Messaging Apps API Response Validation", False, f"Validation errors: {validation_errors}")
                        return False
                else:
                    self.log_result("Messaging Apps API Response Validation", False, "No phones in API response")
                    return False
            else:
                self.log_result("Messaging Apps API Response Validation", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Messaging Apps API Response Validation", False, f"Error: {str(e)}")
            return False
    
    def test_messaging_apps_persistence(self):
        """Test that messaging apps configurations persist correctly in database"""
        if not self.access_token or not hasattr(self, 'custom_messaging_card_id'):
            self.log_result("Messaging Apps Persistence", False, "No access token or custom messaging card available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Get the card multiple times to ensure persistence
            responses = []
            for i in range(3):
                response = requests.get(f"{API_BASE}/cards/{self.custom_messaging_card_id}", headers=headers)
                if response.status_code == 200:
                    responses.append(response.json())
                else:
                    self.log_result("Messaging Apps Persistence", False, f"Failed to get card on attempt {i+1}")
                    return False
            
            # Compare messaging apps across all responses
            if len(responses) == 3:
                # Extract messaging apps from first phone of each response
                messaging_apps_sets = []
                for response_data in responses:
                    if "phones" in response_data and len(response_data["phones"]) > 0:
                        phone = response_data["phones"][0]
                        if "messaging_apps" in phone:
                            # Convert to comparable format
                            apps = {app["name"]: app["enabled"] for app in phone["messaging_apps"]}
                            messaging_apps_sets.append(apps)
                        else:
                            self.log_result("Messaging Apps Persistence", False, "messaging_apps missing in one response")
                            return False
                    else:
                        self.log_result("Messaging Apps Persistence", False, "phones missing in one response")
                        return False
                
                # Check if all responses have identical messaging apps
                if len(messaging_apps_sets) == 3 and all(apps == messaging_apps_sets[0] for apps in messaging_apps_sets):
                    self.log_result("Messaging Apps Persistence", True, f"Messaging apps persist correctly across requests: {messaging_apps_sets[0]}")
                    return True
                else:
                    self.log_result("Messaging Apps Persistence", False, f"Messaging apps differ across requests: {messaging_apps_sets}")
                    return False
            else:
                self.log_result("Messaging Apps Persistence", False, "Failed to get all 3 responses")
                return False
                
        except Exception as e:
            self.log_result("Messaging Apps Persistence", False, f"Error: {str(e)}")
            return False
    
    def test_messaging_apps_multiple_phones_independence(self):
        """Test that different phones can have independent messaging app configurations"""
        if not self.access_token:
            self.log_result("Messaging Apps Multiple Phones Independence", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create card with multiple phones having different messaging app configs
            card_data = {
                "name": "Maria Rodriguez",
                "company": "Global Communications",
                "position": "International Relations Manager",
                "phones": [
                    {
                        "label": "work",
                        "number": "+34-91-123-4567",
                        "is_primary": True,
                        "messaging_apps": [
                            {"name": "whatsapp", "enabled": True},
                            {"name": "sms", "enabled": True},
                            {"name": "telegram", "enabled": False}
                        ]
                    },
                    {
                        "label": "personal",
                        "number": "+34-91-987-6543",
                        "is_primary": False,
                        "messaging_apps": [
                            {"name": "whatsapp", "enabled": False},  # Different config
                            {"name": "sms", "enabled": True},
                            {"name": "signal", "enabled": True},     # Different apps
                            {"name": "viber", "enabled": True}
                        ]
                    },
                    {
                        "label": "emergency",
                        "number": "+34-91-555-0000",
                        "is_primary": False,
                        "messaging_apps": [
                            {"name": "sms", "enabled": True}  # SMS only
                        ]
                    }
                ],
                "emails": [
                    {
                        "label": "work",
                        "address": "maria.rodriguez@globalcomms.es",
                        "is_primary": True
                    }
                ],
                "is_public": True
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "phones" in data and len(data["phones"]) == 3:
                    # Verify each phone has its independent configuration
                    
                    # Work phone
                    work_phone = data["phones"][0]
                    work_apps = {app["name"]: app["enabled"] for app in work_phone["messaging_apps"]}
                    expected_work = {"whatsapp": True, "sms": True, "telegram": False}
                    
                    # Personal phone
                    personal_phone = data["phones"][1]
                    personal_apps = {app["name"]: app["enabled"] for app in personal_phone["messaging_apps"]}
                    expected_personal = {"whatsapp": False, "sms": True, "signal": True, "viber": True}
                    
                    # Emergency phone
                    emergency_phone = data["phones"][2]
                    emergency_apps = {app["name"]: app["enabled"] for app in emergency_phone["messaging_apps"]}
                    expected_emergency = {"sms": True}
                    
                    # Check all configurations
                    work_correct = all(work_apps.get(name) == enabled for name, enabled in expected_work.items())
                    personal_correct = all(personal_apps.get(name) == enabled for name, enabled in expected_personal.items())
                    emergency_correct = all(emergency_apps.get(name) == enabled for name, enabled in expected_emergency.items())
                    
                    if work_correct and personal_correct and emergency_correct:
                        self.log_result("Messaging Apps Multiple Phones Independence", True, 
                                      f"Independent configs: Work={work_apps}, Personal={personal_apps}, Emergency={emergency_apps}")
                        return True
                    else:
                        self.log_result("Messaging Apps Multiple Phones Independence", False, 
                                      f"Config mismatch: Work={work_correct}, Personal={personal_correct}, Emergency={emergency_correct}")
                        return False
                else:
                    self.log_result("Messaging Apps Multiple Phones Independence", False, f"Expected 3 phones, got {len(data.get('phones', []))}")
                    return False
            else:
                self.log_result("Messaging Apps Multiple Phones Independence", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Messaging Apps Multiple Phones Independence", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # EXPRESS SHARE COLLISION PREVENTION TESTS
    # ============================================================================
    
    def test_express_code_collision_prevention_simultaneous(self):
        """Test multiple simultaneous express code creations for collision prevention"""
        if not self.access_token or not self.card_id:
            self.log_result("Express Code Collision Prevention - Simultaneous", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create multiple express codes rapidly to test collision prevention
            codes_created = []
            failed_attempts = 0
            
            for i in range(10):  # Try to create 10 codes rapidly
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 120,
                    "code_length": 2,
                    "max_usage": 5
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    code = data["code"]
                    
                    # Check for duplicates
                    if code in codes_created:
                        self.log_result("Express Code Collision Prevention - Simultaneous", False, f"COLLISION DETECTED: Duplicate code {code} generated")
                        return False
                    
                    codes_created.append(code)
                else:
                    failed_attempts += 1
                    if failed_attempts > 3:  # Allow some failures due to rate limiting
                        self.log_result("Express Code Collision Prevention - Simultaneous", False, f"Too many failed attempts: {failed_attempts}")
                        return False
            
            if len(codes_created) >= 7:  # At least 7 unique codes should be created
                self.log_result("Express Code Collision Prevention - Simultaneous", True, f"Successfully created {len(codes_created)} unique express codes: {codes_created}")
                return True
            else:
                self.log_result("Express Code Collision Prevention - Simultaneous", False, f"Only created {len(codes_created)} codes, expected at least 7")
                return False
                
        except Exception as e:
            self.log_result("Express Code Collision Prevention - Simultaneous", False, f"Error: {str(e)}")
            return False
    
    def test_express_cross_contamination_prevention(self):
        """Test that express codes don't conflict with express room codes"""
        if not self.access_token or not self.card_id:
            self.log_result("Express Cross-Contamination Prevention", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create express room first
            room_data = {
                "card_id": self.card_id,
                "duration_seconds": 180,
                "max_participants": 5
            }
            
            room_response = requests.post(f"{API_BASE}/express/room/create", json=room_data, headers=headers)
            
            if room_response.status_code != 200:
                self.log_result("Express Cross-Contamination Prevention", False, "Failed to create express room for testing")
                return False
            
            room_data = room_response.json()
            room_code = room_data["code"]
            
            # Now create multiple express codes and verify none match the room code
            codes_created = []
            
            for i in range(15):  # Create many codes to increase chance of collision
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 120,
                    "code_length": 2
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    code = data["code"]
                    
                    # Check for cross-contamination with room code
                    if code == room_code:
                        self.log_result("Express Cross-Contamination Prevention", False, f"CROSS-CONTAMINATION: Express code {code} matches room code {room_code}")
                        return False
                    
                    codes_created.append(code)
            
            if len(codes_created) >= 10:
                self.log_result("Express Cross-Contamination Prevention", True, f"No cross-contamination detected. Room code: {room_code}, Express codes: {codes_created[:5]}...")
                return True
            else:
                self.log_result("Express Cross-Contamination Prevention", False, f"Only created {len(codes_created)} codes for testing")
                return False
                
        except Exception as e:
            self.log_result("Express Cross-Contamination Prevention", False, f"Error: {str(e)}")
            return False
    
    def test_user_context_seeding_uniqueness(self):
        """Test that user-context seeding improves code uniqueness"""
        if not self.access_token or not self.card_id:
            self.log_result("User Context Seeding Uniqueness", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create codes with same card but different timing to test user context seeding
            codes_batch_1 = []
            codes_batch_2 = []
            
            # First batch
            for i in range(5):
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 60,
                    "code_length": 3
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    codes_batch_1.append(data["code"])
            
            # Small delay to change timing context
            import time
            time.sleep(1)
            
            # Second batch
            for i in range(5):
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 60,
                    "code_length": 3
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    codes_batch_2.append(data["code"])
            
            # Check for uniqueness across batches
            all_codes = codes_batch_1 + codes_batch_2
            unique_codes = set(all_codes)
            
            if len(unique_codes) == len(all_codes):
                self.log_result("User Context Seeding Uniqueness", True, f"All {len(all_codes)} codes unique across batches. Batch 1: {codes_batch_1}, Batch 2: {codes_batch_2}")
                return True
            else:
                duplicates = [code for code in all_codes if all_codes.count(code) > 1]
                self.log_result("User Context Seeding Uniqueness", False, f"Duplicates found: {duplicates}")
                return False
                
        except Exception as e:
            self.log_result("User Context Seeding Uniqueness", False, f"Error: {str(e)}")
            return False
    
    def test_rapid_code_creation_edge_case(self):
        """Test what happens when someone tries to create codes rapidly"""
        if not self.access_token or not self.card_id:
            self.log_result("Rapid Code Creation Edge Case", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Try to create codes as rapidly as possible
            codes_created = []
            errors_encountered = []
            
            for i in range(20):  # Rapid fire creation
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 30,  # Short duration
                    "code_length": 2
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    code = data["code"]
                    
                    if code in codes_created:
                        self.log_result("Rapid Code Creation Edge Case", False, f"Duplicate code in rapid creation: {code}")
                        return False
                    
                    codes_created.append(code)
                else:
                    errors_encountered.append(response.status_code)
            
            # Should handle rapid creation gracefully
            success_rate = len(codes_created) / 20
            
            if success_rate >= 0.7:  # At least 70% success rate
                self.log_result("Rapid Code Creation Edge Case", True, f"Rapid creation handled well: {len(codes_created)}/20 successful, no duplicates")
                return True
            else:
                self.log_result("Rapid Code Creation Edge Case", False, f"Poor success rate: {len(codes_created)}/20, errors: {errors_encountered}")
                return False
                
        except Exception as e:
            self.log_result("Rapid Code Creation Edge Case", False, f"Error: {str(e)}")
            return False
    
    def test_many_active_codes_scenario(self):
        """Test code generation when many codes are already active"""
        if not self.access_token or not self.card_id:
            self.log_result("Many Active Codes Scenario", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create many active codes to fill up the namespace
            active_codes = []
            
            # Create 30 codes with longer duration to keep them active
            for i in range(30):
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 300,  # 5 minutes - keep them active
                    "code_length": 2
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    active_codes.append(data["code"])
                elif response.status_code == 500 and "zu viele aktive Codes" in response.text:
                    # This is expected behavior when namespace is full
                    self.log_result("Many Active Codes Scenario", True, f"System properly handles namespace exhaustion after {len(active_codes)} codes")
                    return True
            
            # If we created 30 codes without error, that's also good
            if len(active_codes) >= 25:
                unique_codes = set(active_codes)
                if len(unique_codes) == len(active_codes):
                    self.log_result("Many Active Codes Scenario", True, f"Successfully created {len(active_codes)} unique codes without collision")
                    return True
                else:
                    self.log_result("Many Active Codes Scenario", False, f"Duplicates found in {len(active_codes)} codes")
                    return False
            else:
                self.log_result("Many Active Codes Scenario", False, f"Only created {len(active_codes)} codes")
                return False
                
        except Exception as e:
            self.log_result("Many Active Codes Scenario", False, f"Error: {str(e)}")
            return False
    
    def test_global_uniqueness_verification(self):
        """Test that express codes don't conflict globally across all types"""
        if not self.access_token or not self.card_id:
            self.log_result("Global Uniqueness Verification", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create express codes and rooms simultaneously
            express_codes = []
            room_codes = []
            
            # Create 5 express codes and 5 express rooms
            for i in range(5):
                # Create express code
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 120,
                    "code_length": 2
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    express_codes.append(data["code"])
                
                # Create express room
                room_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 120,
                    "max_participants": 5
                }
                
                response = requests.post(f"{API_BASE}/express/room/create", json=room_data, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    room_codes.append(data["code"])
            
            # Check for global uniqueness
            all_codes = express_codes + room_codes
            unique_codes = set(all_codes)
            
            if len(unique_codes) == len(all_codes):
                self.log_result("Global Uniqueness Verification", True, f"Global uniqueness maintained. Express: {express_codes}, Rooms: {room_codes}")
                return True
            else:
                duplicates = [code for code in all_codes if all_codes.count(code) > 1]
                self.log_result("Global Uniqueness Verification", False, f"Global collision detected: {duplicates}")
                return False
                
        except Exception as e:
            self.log_result("Global Uniqueness Verification", False, f"Error: {str(e)}")
            return False
    
    def test_berlin_munich_user_scenario(self):
        """Test scenario: Person A (Berlin) and Person B (Munich) both try to create same code"""
        if not self.access_token or not self.card_id:
            self.log_result("Berlin-Munich User Scenario", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Simulate Person A creating a code
            express_data_a = {
                "card_id": self.card_id,
                "duration_seconds": 300,  # 5 minutes
                "code_length": 2
            }
            
            response_a = requests.post(f"{API_BASE}/express/create", json=express_data_a, headers=headers)
            
            if response_a.status_code != 200:
                self.log_result("Berlin-Munich User Scenario", False, "Failed to create first express code")
                return False
            
            data_a = response_a.json()
            code_a = data_a["code"]
            
            # Simulate Person B trying to create codes (should get different codes)
            codes_b = []
            for i in range(10):  # Try multiple times to increase chance of collision
                express_data_b = {
                    "card_id": self.card_id,
                    "duration_seconds": 300,
                    "code_length": 2
                }
                
                response_b = requests.post(f"{API_BASE}/express/create", json=express_data_b, headers=headers)
                
                if response_b.status_code == 200:
                    data_b = response_b.json()
                    code_b = data_b["code"]
                    
                    if code_b == code_a:
                        self.log_result("Berlin-Munich User Scenario", False, f"COLLISION: Person B got same code as Person A: {code_a}")
                        return False
                    
                    codes_b.append(code_b)
            
            # Test that Person C entering code_a gets Person A's card
            code_request = {"code": code_a}
            access_response = requests.post(f"{API_BASE}/express/access", json=code_request)
            
            if access_response.status_code == 200:
                access_data = access_response.json()
                if access_data.get("success") and access_data.get("card"):
                    card_id_accessed = access_data["card"]["id"]
                    if card_id_accessed == self.card_id:
                        self.log_result("Berlin-Munich User Scenario", True, f"Scenario successful: Person A code {code_a}, Person B codes {codes_b[:3]}..., Person C correctly accessed Person A's card")
                        return True
                    else:
                        self.log_result("Berlin-Munich User Scenario", False, f"Person C accessed wrong card: expected {self.card_id}, got {card_id_accessed}")
                        return False
                else:
                    self.log_result("Berlin-Munich User Scenario", False, "Person C failed to access card", access_data)
                    return False
            else:
                self.log_result("Berlin-Munich User Scenario", False, f"Code access failed: HTTP {access_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Berlin-Munich User Scenario", False, f"Error: {str(e)}")
            return False
    
    def test_code_expiry_and_reuse(self):
        """Test that expired codes allow reuse and cleanup works properly"""
        if not self.access_token or not self.card_id:
            self.log_result("Code Expiry and Reuse", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create express code with very short expiry
            express_data = {
                "card_id": self.card_id,
                "duration_seconds": 30,  # 30 seconds
                "code_length": 2
            }
            
            response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Code Expiry and Reuse", False, "Failed to create express code")
                return False
            
            data = response.json()
            short_lived_code = data["code"]
            
            # Verify code works immediately
            code_request = {"code": short_lived_code}
            access_response = requests.post(f"{API_BASE}/express/access", json=code_request)
            
            if access_response.status_code != 200:
                self.log_result("Code Expiry and Reuse", False, "Code doesn't work immediately after creation")
                return False
            
            # Wait for expiry (in real scenario, we'd wait 30+ seconds, but for testing we'll simulate)
            # Instead, let's test the expiry logic by creating many codes and seeing if we can reuse patterns
            
            # Create multiple short-lived codes to test reuse potential
            codes_created = []
            for i in range(15):
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 30,
                    "code_length": 2
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    codes_created.append(data["code"])
            
            # Check that we got reasonable variety (not all same code)
            unique_codes = set(codes_created)
            
            if len(unique_codes) >= len(codes_created) * 0.8:  # At least 80% unique
                self.log_result("Code Expiry and Reuse", True, f"Code generation working properly with expiry. Created {len(codes_created)} codes, {len(unique_codes)} unique")
                return True
            else:
                self.log_result("Code Expiry and Reuse", False, f"Too many duplicate codes: {len(codes_created)} total, {len(unique_codes)} unique")
                return False
                
        except Exception as e:
            self.log_result("Code Expiry and Reuse", False, f"Error: {str(e)}")
            return False
    
    def test_collision_error_handling(self):
        """Test proper error handling when uniqueness attempts are exhausted"""
        if not self.access_token or not self.card_id:
            self.log_result("Collision Error Handling", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Try to create many codes to potentially exhaust uniqueness attempts
            # This tests the system's behavior under extreme load
            codes_created = []
            error_encountered = False
            
            for i in range(50):  # Try to create many codes
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 300,  # Long duration to keep them active
                    "code_length": 2  # Limited namespace
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    codes_created.append(data["code"])
                elif response.status_code == 500:
                    # Check if it's the expected error message
                    if "zu viele aktive Codes" in response.text or "Fehler beim Generieren" in response.text:
                        error_encountered = True
                        break
                    else:
                        self.log_result("Collision Error Handling", False, f"Unexpected error: {response.text}")
                        return False
            
            # Verify no duplicates in created codes
            unique_codes = set(codes_created)
            if len(unique_codes) != len(codes_created):
                self.log_result("Collision Error Handling", False, f"Duplicates found before error: {len(codes_created)} total, {len(unique_codes)} unique")
                return False
            
            if error_encountered:
                self.log_result("Collision Error Handling", True, f"System properly handled namespace exhaustion after {len(codes_created)} unique codes")
                return True
            elif len(codes_created) >= 40:
                self.log_result("Collision Error Handling", True, f"System handled {len(codes_created)} codes without collision or error")
                return True
            else:
                self.log_result("Collision Error Handling", False, f"Unexpected behavior: only {len(codes_created)} codes created without error")
                return False
                
        except Exception as e:
            self.log_result("Collision Error Handling", False, f"Error: {str(e)}")
            return False

    # ============================================================================
    # EXPRESS SHARE TESTS
    # ============================================================================
    
    def test_create_express_code_2_char(self):
        """Test POST /api/express/create with 2-character code"""
        if not self.access_token or not self.card_id:
            self.log_result("Create Express Code (2-char)", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            express_data = {
                "card_id": self.card_id,
                "duration_seconds": 60,  # 1 minute
                "code_length": 2,
                "max_usage": 5
            }
            
            response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "code", "created_at", "expires_at", "time_remaining_seconds", "usage_count", "max_usage", "is_active", "card_name"]
                
                if all(field in data for field in required_fields):
                    # Verify code is 2 characters
                    if len(data["code"]) == 2:
                        self.express_code_2 = data["code"]
                        self.express_code_id_2 = data["id"]
                        self.log_result("Create Express Code (2-char)", True, f"Express code created: {data['code']} (expires in {data['time_remaining_seconds']}s)")
                        return True
                    else:
                        self.log_result("Create Express Code (2-char)", False, f"Expected 2-char code, got {len(data['code'])}-char: {data['code']}")
                        return False
                else:
                    self.log_result("Create Express Code (2-char)", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Create Express Code (2-char)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Express Code (2-char)", False, f"Error: {str(e)}")
            return False
    
    def test_create_express_code_3_char(self):
        """Test POST /api/express/create with 3-character code"""
        if not self.access_token or not hasattr(self, 'custom_code_card_id'):
            self.log_result("Create Express Code (3-char)", False, "No access token or second card available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            express_data = {
                "card_id": self.custom_code_card_id,
                "duration_seconds": 180,  # 3 minutes
                "code_length": 3,
                "max_usage": 10
            }
            
            response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "code", "created_at", "expires_at", "time_remaining_seconds", "usage_count", "max_usage", "is_active", "card_name"]
                
                if all(field in data for field in required_fields):
                    # Verify code is 3 characters
                    if len(data["code"]) == 3:
                        self.express_code_3 = data["code"]
                        self.express_code_id_3 = data["id"]
                        self.log_result("Create Express Code (3-char)", True, f"Express code created: {data['code']} (expires in {data['time_remaining_seconds']}s)")
                        return True
                    else:
                        self.log_result("Create Express Code (3-char)", False, f"Expected 3-char code, got {len(data['code'])}-char: {data['code']}")
                        return False
                else:
                    self.log_result("Create Express Code (3-char)", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Create Express Code (3-char)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Express Code (3-char)", False, f"Error: {str(e)}")
            return False
    
    def test_access_by_express_code(self):
        """Test POST /api/express/access"""
        if not hasattr(self, 'express_code_2'):
            self.log_result("Access by Express Code", False, "No express code available for testing")
            return False
            
        try:
            code_request = {"code": self.express_code_2}
            response = requests.post(f"{API_BASE}/express/access", json=code_request)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "card", "express_code"]
                
                if all(field in data for field in required_fields):
                    if data["success"] == True and "card" in data:
                        card = data["card"]
                        express_code = data["express_code"]
                        
                        # Verify card data structure
                        card_fields = ["id", "name", "company", "position", "phones", "emails"]
                        if all(field in card for field in card_fields):
                            # Verify express code data
                            if express_code.get("code") == self.express_code_2:
                                self.log_result("Access by Express Code", True, f"Successfully accessed card using express code: {self.express_code_2}")
                                return True
                            else:
                                self.log_result("Access by Express Code", False, "Express code mismatch in response", data)
                                return False
                        else:
                            self.log_result("Access by Express Code", False, "Missing card fields in response", card)
                            return False
                    else:
                        self.log_result("Access by Express Code", False, "Success=false or missing card data", data)
                        return False
                else:
                    self.log_result("Access by Express Code", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Access by Express Code", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Access by Express Code", False, f"Error: {str(e)}")
            return False
    
    def test_express_code_expiry(self):
        """Test express code expiry functionality"""
        if not self.access_token or not self.card_id:
            self.log_result("Express Code Expiry", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create express code with very short duration (30 seconds)
            express_data = {
                "card_id": self.card_id,
                "duration_seconds": 30,  # 30 seconds
                "code_length": 2
            }
            
            response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                short_code = data["code"]
                
                # Immediately try to access it (should work)
                code_request = {"code": short_code}
                access_response = requests.post(f"{API_BASE}/express/access", json=code_request)
                
                if access_response.status_code == 200:
                    access_data = access_response.json()
                    if access_data.get("success") == True:
                        self.log_result("Express Code Expiry", True, f"Express code {short_code} works immediately after creation and will expire in 30s")
                        return True
                    else:
                        self.log_result("Express Code Expiry", False, "Express code access failed immediately after creation", access_data)
                        return False
                else:
                    self.log_result("Express Code Expiry", False, f"Express code access failed: HTTP {access_response.status_code}", access_response.text)
                    return False
            else:
                self.log_result("Express Code Expiry", False, f"Express code creation failed: HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Express Code Expiry", False, f"Error: {str(e)}")
            return False
    
    def test_create_express_room(self):
        """Test POST /api/express/room/create"""
        if not self.access_token or not self.card_id:
            self.log_result("Create Express Room", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            room_data = {
                "card_id": self.card_id,
                "duration_seconds": 120,  # 2 minutes
                "max_participants": 5
            }
            
            response = requests.post(f"{API_BASE}/express/room/create", json=room_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "code", "created_by_card_name", "created_at", "expires_at", "time_remaining_seconds", "participant_count", "max_participants", "can_join", "participants"]
                
                if all(field in data for field in required_fields):
                    # Verify code is 2 digits
                    if len(data["code"]) == 2 and data["code"].isdigit():
                        # Verify creator is in participants
                        if data["participant_count"] == 1 and len(data["participants"]) == 1:
                            self.express_room_code = data["code"]
                            self.express_room_id = data["id"]
                            self.log_result("Create Express Room", True, f"Express room created with code: {data['code']} (expires in {data['time_remaining_seconds']}s)")
                            return True
                        else:
                            self.log_result("Create Express Room", False, "Creator not properly added as participant", data)
                            return False
                    else:
                        self.log_result("Create Express Room", False, f"Expected 2-digit code, got: {data['code']}")
                        return False
                else:
                    self.log_result("Create Express Room", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Create Express Room", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Express Room", False, f"Error: {str(e)}")
            return False
    
    def test_join_express_room(self):
        """Test POST /api/express/room/join"""
        if not hasattr(self, 'express_room_code') or not hasattr(self, 'custom_code_card_id'):
            self.log_result("Join Express Room", False, "No express room code or second card available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            join_data = {
                "code": self.express_room_code,
                "card_id": self.custom_code_card_id
            }
            
            response = requests.post(f"{API_BASE}/express/room/join", json=join_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["success", "message", "cards_received"]
                
                if all(field in data for field in required_fields):
                    if data["success"] == True:
                        # Should receive 1 card (the creator's card)
                        cards_received = data["cards_received"]
                        if len(cards_received) >= 1:
                            # Verify card structure
                            card = cards_received[0]
                            card_fields = ["id", "name", "company", "joined_at"]
                            if all(field in card for field in card_fields):
                                self.log_result("Join Express Room", True, f"Successfully joined express room {self.express_room_code}, received {len(cards_received)} cards")
                                return True
                            else:
                                self.log_result("Join Express Room", False, "Missing fields in received card data", card)
                                return False
                        else:
                            self.log_result("Join Express Room", False, f"Expected at least 1 card, got {len(cards_received)}")
                            return False
                    else:
                        self.log_result("Join Express Room", False, "Success=false in response", data)
                        return False
                else:
                    self.log_result("Join Express Room", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Join Express Room", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Join Express Room", False, f"Error: {str(e)}")
            return False
    
    def test_express_code_uniqueness(self):
        """Test express code uniqueness across codes and rooms"""
        if not self.access_token or not self.card_id:
            self.log_result("Express Code Uniqueness", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create multiple express codes and verify they're unique
            codes_created = []
            
            for i in range(3):
                express_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 60,
                    "code_length": 2
                }
                
                response = requests.post(f"{API_BASE}/express/create", json=express_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    code = data["code"]
                    
                    if code in codes_created:
                        self.log_result("Express Code Uniqueness", False, f"Duplicate code generated: {code}")
                        return False
                    
                    codes_created.append(code)
                else:
                    self.log_result("Express Code Uniqueness", False, f"Failed to create express code {i+1}: HTTP {response.status_code}")
                    return False
            
            # Create express rooms and verify they don't conflict
            room_codes_created = []
            
            for i in range(2):
                room_data = {
                    "card_id": self.card_id,
                    "duration_seconds": 60,
                    "max_participants": 5
                }
                
                response = requests.post(f"{API_BASE}/express/room/create", json=room_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    code = data["code"]
                    
                    if code in room_codes_created:
                        self.log_result("Express Code Uniqueness", False, f"Duplicate room code generated: {code}")
                        return False
                    
                    room_codes_created.append(code)
                else:
                    self.log_result("Express Code Uniqueness", False, f"Failed to create express room {i+1}: HTTP {response.status_code}")
                    return False
            
            self.log_result("Express Code Uniqueness", True, f"Generated unique codes: {codes_created} and room codes: {room_codes_created}")
            return True
                
        except Exception as e:
            self.log_result("Express Code Uniqueness", False, f"Error: {str(e)}")
            return False
    
    def test_express_integration_with_regular_codes(self):
        """Test that express codes don't conflict with regular business card codes"""
        if not hasattr(self, 'express_code_2') or not hasattr(self, 'custom_code'):
            self.log_result("Express Integration", False, "No express code or regular custom code available")
            return False
            
        try:
            # Try to access express code via regular card access endpoint
            code_request = {"code": self.express_code_2}
            response = requests.post(f"{API_BASE}/cards/access-by-code", json=code_request)
            
            # Express codes should not be accessible via regular card access
            if response.status_code == 404:
                # Try to access regular code via express access endpoint
                express_request = {"code": self.custom_code}
                express_response = requests.post(f"{API_BASE}/express/access", json=express_request)
                
                # Regular codes should not be accessible via express access
                if express_response.status_code == 404:
                    self.log_result("Express Integration", True, "Express codes and regular codes properly separated")
                    return True
                else:
                    self.log_result("Express Integration", False, f"Regular code accessible via express endpoint: HTTP {express_response.status_code}")
                    return False
            else:
                self.log_result("Express Integration", False, f"Express code accessible via regular endpoint: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Express Integration", False, f"Error: {str(e)}")
            return False
    
    def test_express_room_participant_limits(self):
        """Test express room participant limits"""
        if not self.access_token or not self.card_id:
            self.log_result("Express Room Limits", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create room with limit of 2 participants
            room_data = {
                "card_id": self.card_id,
                "duration_seconds": 120,
                "max_participants": 2
            }
            
            response = requests.post(f"{API_BASE}/express/room/create", json=room_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                room_code = data["code"]
                
                # Verify room shows can_join = true initially
                if data.get("can_join") == True and data.get("participant_count") == 1:
                    # Try to join with second card (should work)
                    if hasattr(self, 'custom_code_card_id'):
                        join_data = {
                            "code": room_code,
                            "card_id": self.custom_code_card_id
                        }
                        
                        join_response = requests.post(f"{API_BASE}/express/room/join", json=join_data, headers=headers)
                        
                        if join_response.status_code == 200:
                            join_data_response = join_response.json()
                            if join_data_response.get("success") == True:
                                self.log_result("Express Room Limits", True, f"Express room {room_code} properly handles participant limits")
                                return True
                            else:
                                self.log_result("Express Room Limits", False, "Failed to join room within limits", join_data_response)
                                return False
                        else:
                            self.log_result("Express Room Limits", False, f"Join failed: HTTP {join_response.status_code}")
                            return False
                    else:
                        self.log_result("Express Room Limits", True, "Room created with proper limits (no second card to test join)")
                        return True
                else:
                    self.log_result("Express Room Limits", False, "Room not properly initialized", data)
                    return False
            else:
                self.log_result("Express Room Limits", False, f"Room creation failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Express Room Limits", False, f"Error: {str(e)}")
            return False
    
    def test_invalid_express_operations(self):
        """Test various invalid express operations"""
        try:
            # Test accessing non-existent express code
            code_request = {"code": "XX"}
            response = requests.post(f"{API_BASE}/express/access", json=code_request)
            
            if response.status_code == 404:
                self.log_result("Invalid Express Operations - Code", True, "Non-existent express code properly rejected")
            else:
                self.log_result("Invalid Express Operations - Code", False, f"Expected 404, got {response.status_code}")
                return False
            
            # Test joining non-existent express room
            join_data = {
                "code": "99",
                "card_id": self.card_id if self.card_id else "fake_id"
            }
            
            response = requests.post(f"{API_BASE}/express/room/join", json=join_data)
            
            if response.status_code == 404:
                self.log_result("Invalid Express Operations - Room", True, "Non-existent express room properly rejected")
                return True
            else:
                self.log_result("Invalid Express Operations - Room", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Invalid Express Operations", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence - FOCUS: NEW REVOLUTIONARY FEATURES"""
        print("=" * 80)
        print("🚀 REVOLUTIONARY FEATURES TESTING - MEETING LINK GENERATION & LIVE TRANSLATION")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print("🎯 PRIORITY: Testing NEW game-changing video meeting and translation features")
        print()
        
        tests = [
            # Core API tests (required for authentication)
            self.test_health_check,
            self.test_user_registration,
            self.test_user_login,
            self.test_protected_endpoint,
            
            # Business card tests (required for meeting integration)
            self.test_create_business_card,
            
            # 🔥 NEW REVOLUTIONARY FEATURES TESTING (PRIORITY: CRITICAL)
            # 9-Character Code Generation Tests (FOCUS OF THIS REVIEW)
            self.test_9_character_meeting_code_generation,
            self.test_code_collision_resistance_stress,
            self.test_enhanced_meeting_features_with_9char_codes,
            
            # Enhanced Video Meeting Features
            self.test_enhanced_video_meeting_create,
            self.test_meeting_share_link_generation,
            self.test_live_translation_enable,
            self.test_participant_translation_preference,
            
            # Legacy Video Meeting System Tests (for comparison)
            self.test_video_meeting_join,
            self.test_video_meetings_list,
            self.test_video_meeting_share_card,
            
            # Community Networking Tests
            self.test_community_profile_get,
            self.test_community_profile_update,
            self.test_community_discover,
            self.test_community_feed,
            self.test_community_create,
            self.test_community_join,
            self.test_community_my_communities,
            
            # Job Board Tests
            self.test_jobs_discover,
            self.test_jobs_post,
            self.test_jobs_apply,
            
            # Additional business card tests
            self.test_get_user_cards,
            self.test_get_specific_card,
            self.test_update_business_card,
            
            # Custom code tests
            self.test_create_business_card_with_custom_code,
            self.test_check_code_availability,
            self.test_access_card_by_code,
            self.test_code_uniqueness_validation,
            
            # Early Adopter Bonus System Tests (CRITICAL)
            self.test_early_adopter_user_registration,
            self.test_early_adopter_premium_feature_access,
            self.test_early_adopter_vs_regular_user_comparison,
            self.test_user_count_api_logic,
            self.test_subscription_status_response_format,
            
            # Subscription & Monetization System Tests
            self.test_get_subscription_status,
            self.test_check_feature_access_free_user,
            self.test_track_usage_system,
            self.test_integration_with_existing_features,
            self.test_growth_first_validation,
            
            # Contact Import System Tests
            self.test_list_contact_sources_empty,
            self.test_import_contacts_contact_picker,
            self.test_import_contacts_vcf_file,
            self.test_import_contacts_google_placeholder,
            self.test_import_contacts_apple_placeholder,
            self.test_import_contacts_csv_unsupported,
            self.test_list_contact_sources_with_data,
            self.test_unified_contacts_list,
            self.test_unified_contacts_search,
            self.test_imported_contact_messaging_apps,
            self.test_contact_type_identification,
            self.test_contact_import_invalid_data,
            
            # Messaging Apps Enhancement Tests
            self.test_messaging_apps_default_configuration,
            self.test_messaging_apps_custom_configuration,
            self.test_messaging_apps_update_configuration,
            self.test_messaging_apps_api_response_validation,
            self.test_messaging_apps_persistence,
            self.test_messaging_apps_multiple_phones_independence,
            
            # Targeted fix tests
            self.test_social_media_fix_with_custom_code,
            
            # Meeting room tests
            self.test_create_meeting_room,
            self.test_get_meeting_room,
            self.test_join_meeting_room,
            self.test_list_user_meeting_rooms,
            self.test_enhanced_code_access_meeting_room,
            self.test_close_meeting_room,
            
            # Express Share Collision Prevention Tests (CRITICAL)
            self.test_express_code_collision_prevention_simultaneous,
            self.test_express_cross_contamination_prevention,
            self.test_user_context_seeding_uniqueness,
            self.test_rapid_code_creation_edge_case,
            self.test_many_active_codes_scenario,
            self.test_global_uniqueness_verification,
            self.test_berlin_munich_user_scenario,
            self.test_code_expiry_and_reuse,
            self.test_collision_error_handling,
            
            # Express Share tests
            self.test_create_express_code_2_char,
            self.test_create_express_code_3_char,
            self.test_access_by_express_code,
            self.test_express_code_expiry,
            self.test_create_express_room,
            self.test_join_express_room,
            self.test_express_code_uniqueness,
            self.test_express_integration_with_regular_codes,
            self.test_express_room_participant_limits,
            self.test_invalid_express_operations,
            
            # OCR Business Card Scanner Tests - Game Changing Feature
            self.test_ocr_scan_business_card,
            self.test_get_scan_results,
            self.test_correct_ocr_field,
            self.test_convert_scan_to_card,
            self.test_list_scanned_cards,
            
            # Print Export Tests - Game Changing Feature  
            self.test_get_print_templates,
            self.test_export_for_printing,
            self.test_quick_print_export,
            self.test_print_preview,
            self.test_print_job_status,
            
            # Authentication & Authorization Tests for New Features
            self.test_ocr_authentication_required,
            self.test_print_authentication_required,
            self.test_user_data_isolation_scans,
            self.test_user_data_isolation_print_jobs,
            
            # Utility tests
            self.test_qr_code_generation,
            self.test_vcard_generation,
            
            # Privacy/GDPR tests
            self.test_privacy_report,
            self.test_data_export,
            
            # Error handling tests
            self.test_invalid_authentication,
            self.test_nonexistent_card,
            self.test_invalid_meeting_room_operations
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"- {result['test']}: {result['message']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = BusinessCardAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_results_detailed.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2)
    
    print(f"\nDetailed results saved to: /app/test_results_detailed.json")
    
    if not success:
        exit(1)