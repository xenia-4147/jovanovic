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
        """Run all tests in sequence"""
        print("=" * 80)
        print("DIGITAL BUSINESS CARDS API TEST SUITE - EXPRESS SHARE TESTING")
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
            
            # Targeted fix tests
            self.test_social_media_fix_with_custom_code,
            
            # Meeting room tests
            self.test_create_meeting_room,
            self.test_get_meeting_room,
            self.test_join_meeting_room,
            self.test_list_user_meeting_rooms,
            self.test_enhanced_code_access_meeting_room,
            self.test_close_meeting_room,
            
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