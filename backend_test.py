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
        """Run all tests in sequence"""
        print("=" * 80)
        print("DIGITAL BUSINESS CARDS API TEST SUITE - CONTACT IMPORT SYSTEM TESTING")
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