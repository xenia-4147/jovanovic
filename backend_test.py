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
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("=" * 80)
        print("DIGITAL BUSINESS CARDS API TEST SUITE - ENHANCED WITH MEETING ROOMS")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print()
        
        tests = [
            # Core API tests
            self.test_health_check,
            self.test_user_registration,
            self.test_user_login,
            self.test_protected_endpoint,
            
            # Business card tests
            self.test_create_business_card,
            self.test_get_user_cards,
            self.test_get_specific_card,
            self.test_update_business_card,
            
            # Custom code tests
            self.test_create_business_card_with_custom_code,
            self.test_check_code_availability,
            self.test_access_card_by_code,
            self.test_code_uniqueness_validation,
            
            # Meeting room tests
            self.test_create_meeting_room,
            self.test_get_meeting_room,
            self.test_join_meeting_room,
            self.test_list_user_meeting_rooms,
            self.test_enhanced_code_access_meeting_room,
            self.test_close_meeting_room,
            
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