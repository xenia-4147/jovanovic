#!/usr/bin/env python3
"""
Focused Camera Connection Issues Test
Tests the FIXED camera connection issues for video meetings
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

class CameraConnectionTester:
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
    
    def setup_authentication(self):
        """Setup authentication for testing"""
        try:
            # Register a test user
            test_email = f"cameratest_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "CameraTest123!",
                "first_name": "Camera",
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
                
                # Create a business card for testing
                headers = {"Authorization": f"Bearer {self.access_token}"}
                card_data = {
                    "name": "Camera Test User",
                    "company": "Camera Testing Inc",
                    "position": "Test Engineer",
                    "phones": [{"label": "work", "number": "+1-555-CAMERA", "is_primary": True}],
                    "emails": [{"label": "work", "address": test_email, "is_primary": True}],
                    "is_public": True
                }
                
                card_response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
                if card_response.status_code == 200:
                    self.card_id = card_response.json()["id"]
                    return True
                    
            return False
        except Exception as e:
            print(f"Setup failed: {str(e)}")
            return False
    
    def test_meeting_join_with_participant_id(self):
        """Test POST /api/video/meeting/join returns participant_id for camera connections"""
        if not self.access_token:
            self.log_result("Meeting Join with Participant ID", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # First create a meeting
            meeting_data = {
                "title": "Camera Connection Test Meeting",
                "description": "Testing participant_id for camera connections",
                "meeting_type": "networking_event",
                "duration_minutes": 30,
                "max_participants": 10,
                "is_public": True
            }
            
            create_response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
            
            if create_response.status_code != 200:
                self.log_result("Meeting Join with Participant ID", False, f"Failed to create meeting: HTTP {create_response.status_code}", create_response.text)
                return False
            
            create_data = create_response.json()
            meeting = create_data.get("meeting", {})
            meeting_code = meeting.get("meeting_code")
            
            if not meeting_code:
                self.log_result("Meeting Join with Participant ID", False, "No meeting code in create response", create_data)
                return False
            
            # Now test joining the meeting
            join_data = {
                "meeting_code": meeting_code,
                "display_name": "Camera Test User"
            }
            
            join_response = requests.post(f"{API_BASE}/video/meeting/join", json=join_data, headers=headers)
            
            if join_response.status_code == 200:
                join_result = join_response.json()
                
                # Check for participant_id field (critical for camera connections)
                participant_id = join_result.get("participant_id")
                participant = join_result.get("participant")
                
                if participant_id:
                    self.log_result("Meeting Join with Participant ID", True, f"participant_id returned: {participant_id}")
                    self.test_participant_id = participant_id
                    self.test_meeting_code = meeting_code
                    return True
                elif participant and participant.get("id"):
                    self.log_result("Meeting Join with Participant ID", True, f"participant object with ID returned: {participant.get('id')}")
                    self.test_participant_id = participant.get("id")
                    self.test_meeting_code = meeting_code
                    return True
                else:
                    self.log_result("Meeting Join with Participant ID", False, "Missing participant_id/participant object needed for camera connections", join_result)
                    return False
            else:
                self.log_result("Meeting Join with Participant ID", False, f"Join failed: HTTP {join_response.status_code}", join_response.text)
                return False
                
        except Exception as e:
            self.log_result("Meeting Join with Participant ID", False, f"Error: {str(e)}")
            return False
    
    def test_qr_code_endpoint_for_meetings(self):
        """Test GET /api/qr/meeting/{code} for mobile camera access"""
        if not hasattr(self, 'test_meeting_code'):
            self.log_result("QR Code Endpoint for Meetings", False, "No meeting code available for testing")
            return False
            
        try:
            # Test QR code generation for meeting
            response = requests.get(f"{API_BASE}/qr/meeting/{self.test_meeting_code}")
            
            if response.status_code == 200:
                # Check if response contains QR code data (JSON format with base64 image)
                try:
                    data = response.json()
                    if data.get("success") and "qr_code_base64" in data:
                        qr_data = data["qr_code_base64"]
                        if qr_data and qr_data.startswith("data:image/png;base64,"):
                            self.log_result("QR Code Endpoint for Meetings", True, f"QR code generated for meeting {self.test_meeting_code} (base64 format)")
                            return True
                        else:
                            self.log_result("QR Code Endpoint for Meetings", False, f"Invalid QR code format: {qr_data[:50]}...")
                            return False
                    else:
                        self.log_result("QR Code Endpoint for Meetings", False, "Missing QR code data in response", data)
                        return False
                except:
                    # Fallback: check if it's a direct PNG image
                    content_type = response.headers.get('content-type', '')
                    if 'image/png' in content_type:
                        self.log_result("QR Code Endpoint for Meetings", True, f"QR code generated for meeting {self.test_meeting_code} (PNG format, size: {len(response.content)} bytes)")
                        return True
                    else:
                        self.log_result("QR Code Endpoint for Meetings", False, f"Unexpected content type: {content_type}")
                        return False
            elif response.status_code == 404:
                self.log_result("QR Code Endpoint for Meetings", False, f"QR code endpoint not found - mobile camera access broken")
                return False
            else:
                self.log_result("QR Code Endpoint for Meetings", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR Code Endpoint for Meetings", False, f"Error: {str(e)}")
            return False
    
    def test_complete_meeting_flow_for_camera(self):
        """Test complete meeting flow: create -> join -> verify camera prerequisites"""
        if not self.access_token:
            self.log_result("Complete Meeting Flow for Camera", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Step 1: Create meeting
            meeting_data = {
                "title": "Complete Camera Flow Test",
                "description": "Testing complete flow for camera connection",
                "meeting_type": "group",
                "duration_minutes": 45,
                "max_participants": 8,
                "is_public": True
            }
            
            create_response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
            
            if create_response.status_code != 200:
                self.log_result("Complete Meeting Flow - Create", False, f"Create failed: HTTP {create_response.status_code}")
                return False
            
            create_data = create_response.json()
            meeting = create_data.get("meeting", {})
            meeting_code = meeting.get("meeting_code")
            meeting_id = meeting.get("id")
            
            self.log_result("Complete Meeting Flow - Create", True, f"Meeting created: {meeting_code}")
            
            # Step 2: Join meeting with code
            join_data = {
                "meeting_code": meeting_code,
                "display_name": "Complete Flow Test User"
            }
            
            join_response = requests.post(f"{API_BASE}/video/meeting/join", json=join_data, headers=headers)
            
            if join_response.status_code != 200:
                self.log_result("Complete Meeting Flow - Join", False, f"Join failed: HTTP {join_response.status_code}")
                return False
            
            join_result = join_response.json()
            
            # Step 3: Verify participant object includes all fields needed for camera setup
            participant = join_result.get("participant")
            participant_id = join_result.get("participant_id") or (participant.get("id") if participant else None)
            
            if not participant_id:
                self.log_result("Complete Meeting Flow - Participant ID", False, "Missing participant identification for camera setup")
                return False
            
            self.log_result("Complete Meeting Flow - Join", True, f"Joined with participant ID: {participant_id}")
            
            # Step 4: Verify WebRTC config is provided
            webrtc_config = join_result.get("webrtc_config") or create_data.get("webrtc_config")
            
            if not webrtc_config:
                self.log_result("Complete Meeting Flow - WebRTC Config", False, "Missing WebRTC configuration")
                return False
            
            # Step 5: Verify ICE servers are included
            ice_servers = webrtc_config.get("iceServers", [])
            
            if not ice_servers or len(ice_servers) == 0:
                self.log_result("Complete Meeting Flow - ICE Servers", False, "Missing ICE servers for camera connections")
                return False
            
            self.log_result("Complete Meeting Flow - WebRTC Config", True, f"WebRTC config with {len(ice_servers)} ICE servers")
            
            # Step 6: Test QR code generation for mobile access
            qr_response = requests.get(f"{API_BASE}/qr/meeting/{meeting_code}")
            
            if qr_response.status_code == 200:
                self.log_result("Complete Meeting Flow - QR Code", True, "QR code generated for mobile access")
            else:
                self.log_result("Complete Meeting Flow - QR Code", False, f"QR code generation failed: HTTP {qr_response.status_code}")
                return False
            
            self.log_result("Complete Meeting Flow for Camera", True, "All camera connection prerequisites verified")
            return True
                
        except Exception as e:
            self.log_result("Complete Meeting Flow for Camera", False, f"Error: {str(e)}")
            return False
    
    def test_camera_connection_prerequisites(self):
        """Test that all prerequisites for camera connection are met"""
        if not self.access_token:
            self.log_result("Camera Connection Prerequisites", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create a meeting to test prerequisites
            meeting_data = {
                "title": "Camera Prerequisites Test",
                "description": "Testing all camera connection prerequisites",
                "meeting_type": "networking_event",
                "duration_minutes": 30,
                "max_participants": 12,
                "is_public": True
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Camera Connection Prerequisites", False, f"Failed to create test meeting: HTTP {response.status_code}")
                return False
            
            data = response.json()
            meeting = data.get("meeting", {})
            meeting_code = meeting.get("meeting_code")
            
            # Prerequisite 1: WebRTC config properly returned
            webrtc_config = data.get("webrtc_config", {})
            
            if not webrtc_config:
                self.log_result("Camera Prerequisites - WebRTC Config", False, "WebRTC configuration missing")
                return False
            
            # Prerequisite 2: ICE servers included
            ice_servers = webrtc_config.get("iceServers", [])
            
            if not ice_servers:
                self.log_result("Camera Prerequisites - ICE Servers", False, "ICE servers missing")
                return False
            
            # Check for STUN and TURN servers
            stun_servers = []
            turn_servers = []
            
            for server in ice_servers:
                urls = server.get("urls", [])
                # Handle both string and list formats
                if isinstance(urls, str):
                    urls = [urls]
                elif isinstance(urls, list):
                    pass
                else:
                    continue
                    
                for url in urls:
                    if isinstance(url, str):
                        if url.startswith("stun:"):
                            stun_servers.append(server)
                        elif url.startswith("turn:"):
                            turn_servers.append(server)
            
            if not stun_servers:
                self.log_result("Camera Prerequisites - STUN Servers", False, "No STUN servers found")
                return False
            
            if not turn_servers:
                self.log_result("Camera Prerequisites - TURN Servers", False, "No TURN servers found")
                return False
            
            self.log_result("Camera Prerequisites - WebRTC Config", True, f"WebRTC config with {len(ice_servers)} ICE servers")
            self.log_result("Camera Prerequisites - STUN Servers", True, f"{len(stun_servers)} STUN servers configured")
            self.log_result("Camera Prerequisites - TURN Servers", True, f"{len(turn_servers)} TURN servers configured")
            
            # Prerequisite 3: Participant tracking working (test join)
            join_data = {
                "meeting_code": meeting_code,
                "display_name": "Prerequisites Test User"
            }
            
            join_response = requests.post(f"{API_BASE}/video/meeting/join", json=join_data, headers=headers)
            
            if join_response.status_code == 200:
                join_result = join_response.json()
                participant_id = join_result.get("participant_id") or (join_result.get("participant", {}).get("id"))
                
                if participant_id:
                    self.log_result("Camera Prerequisites - Participant Tracking", True, f"Participant tracking working: {participant_id}")
                else:
                    self.log_result("Camera Prerequisites - Participant Tracking", False, "Participant ID not returned")
                    return False
            else:
                self.log_result("Camera Prerequisites - Participant Tracking", False, f"Join failed: HTTP {join_response.status_code}")
                return False
            
            # Prerequisite 4: Mobile QR code access functional
            qr_response = requests.get(f"{API_BASE}/qr/meeting/{meeting_code}")
            
            if qr_response.status_code == 200:
                self.log_result("Camera Prerequisites - Mobile QR Access", True, "QR code generation working")
            else:
                self.log_result("Camera Prerequisites - Mobile QR Access", False, f"QR code failed: HTTP {qr_response.status_code}")
                return False
            
            self.log_result("Camera Connection Prerequisites", True, "All camera connection prerequisites verified")
            return True
                
        except Exception as e:
            self.log_result("Camera Connection Prerequisites", False, f"Error: {str(e)}")
            return False
    
    def run_camera_tests(self):
        """Run focused camera connection tests"""
        print("=" * 80)
        print("🎥 CAMERA CONNECTION ISSUES TESTING - FOCUSED ON FIXED ISSUES")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print("🎯 FOCUS: Testing FIXED camera connection issues for video meetings")
        print()
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Failed to setup authentication")
            return
        
        tests = [
            self.test_meeting_join_with_participant_id,
            self.test_qr_code_endpoint_for_meetings,
            self.test_complete_meeting_flow_for_camera,
            self.test_camera_connection_prerequisites,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 60)
        print("CAMERA CONNECTION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL CAMERA CONNECTION TESTS PASSED!")
            print("✅ Camera connection issues have been FIXED")
        else:
            print(f"\n⚠️  {total - passed} camera connection issues still need attention")
            
        return passed == total

if __name__ == "__main__":
    tester = CameraConnectionTester()
    tester.run_camera_tests()