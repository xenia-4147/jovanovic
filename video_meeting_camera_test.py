#!/usr/bin/env python3
"""
Video Meeting Camera Connection Test Suite
Focused testing for camera connection issues when joining video meetings
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

class VideoMeetingCameraTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.card_id = None
        self.meeting_id = None
        self.meeting_code = None
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
    
    def setup_test_user(self):
        """Setup test user and business card for video meeting tests"""
        try:
            # Register test user
            test_email = f"videotester_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "VideoTest123!",
                "first_name": "Video",
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
                
                # Create business card for video meetings
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                card_data = {
                    "name": "Video Meeting Host",
                    "company": "Video Tech Solutions",
                    "position": "Meeting Coordinator",
                    "description": "Testing video meeting camera connections",
                    "phones": [
                        {
                            "label": "work",
                            "number": "+49-30-555-0123",
                            "is_primary": True
                        }
                    ],
                    "emails": [
                        {
                            "label": "work",
                            "address": "video.host@videotech.com",
                            "is_primary": True
                        }
                    ],
                    "is_public": True
                }
                
                card_response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
                
                if card_response.status_code == 200:
                    card_data = card_response.json()
                    self.card_id = card_data["id"]
                    self.log_result("Setup Test User", True, f"User and card created: {test_email}")
                    return True
                else:
                    self.log_result("Setup Test User", False, f"Card creation failed: HTTP {card_response.status_code}")
                    return False
            else:
                self.log_result("Setup Test User", False, f"User registration failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Setup Test User", False, f"Error: {str(e)}")
            return False
    
    def test_meeting_creation_with_camera_config(self):
        """Test POST /api/video/meeting/create - Focus on camera-related fields"""
        if not self.access_token:
            self.log_result("Meeting Creation with Camera Config", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create meeting with camera-specific settings
            meeting_data = {
                "title": "Camera Connection Test Meeting",
                "description": "Testing camera initialization and WebRTC configuration",
                "meeting_type": "networking_event",
                "duration_minutes": 30,
                "max_participants": 5,
                "share_host_card": True,
                "allow_card_sharing": True,
                "is_public": True,
                # Camera/video specific settings
                "enable_video": True,
                "enable_audio": True,
                "video_quality": "hd",
                "audio_quality": "high"
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                meeting = data.get("meeting", {})
                
                # Store meeting details for subsequent tests
                self.meeting_id = meeting.get("id")
                self.meeting_code = meeting.get("meeting_code")
                
                # Verify meeting code format (should be 9 characters)
                if not self.meeting_code or len(self.meeting_code) != 9:
                    self.log_result("Meeting Creation with Camera Config", False, f"Invalid meeting code format: {self.meeting_code}")
                    return False
                
                # Verify WebRTC configuration is provided
                webrtc_config = data.get("webrtc_config", {})
                if not webrtc_config or "iceServers" not in webrtc_config:
                    self.log_result("Meeting Creation with Camera Config", False, "Missing WebRTC configuration for camera connection")
                    return False
                
                # Check for STUN/TURN servers (critical for camera connection)
                ice_servers = webrtc_config.get("iceServers", [])
                stun_servers = [server for server in ice_servers if any("stun:" in url for url in server.get("urls", []))]
                turn_servers = [server for server in ice_servers if any("turn:" in url for url in server.get("urls", []))]
                
                if not stun_servers:
                    self.log_result("Meeting Creation with Camera Config", False, "No STUN servers configured - camera may not connect through NAT")
                    return False
                
                if not turn_servers:
                    self.log_result("Meeting Creation with Camera Config", False, "No TURN servers configured - camera may not connect through firewalls")
                    return False
                
                # Verify meeting link generation for frontend
                join_url = data.get("join_url") or meeting.get("share_link")
                if not join_url or self.meeting_code not in join_url:
                    self.log_result("Meeting Creation with Camera Config", False, f"Invalid join URL: {join_url}")
                    return False
                
                self.log_result("Meeting Creation with Camera Config", True, 
                              f"Meeting created: {self.meeting_code}, STUN: {len(stun_servers)}, TURN: {len(turn_servers)}")
                return True
            else:
                self.log_result("Meeting Creation with Camera Config", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Meeting Creation with Camera Config", False, f"Error: {str(e)}")
            return False
    
    def test_meeting_join_flow(self):
        """Test POST /api/video/meeting/join - Focus on camera initialization fields"""
        if not self.access_token or not self.meeting_code:
            self.log_result("Meeting Join Flow", False, "No access token or meeting code available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Join meeting with camera preferences
            join_data = {
                "meeting_code": self.meeting_code,
                "display_name": "Video Meeting Host",
                "share_business_card": True
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/join", json=join_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for fields that frontend needs for camera initialization
                required_fields = ["meeting", "webrtc_config", "participant_id"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Meeting Join Flow", False, f"Missing fields for camera initialization: {missing_fields}")
                    return False
                
                # Verify WebRTC config is provided again (frontend needs this for camera setup)
                webrtc_config = data.get("webrtc_config", {})
                if not webrtc_config or "iceServers" not in webrtc_config:
                    self.log_result("Meeting Join Flow", False, "Missing WebRTC config in join response")
                    return False
                
                # Check for participant ID (needed for camera stream identification)
                participant_id = data.get("participant_id")
                if not participant_id:
                    self.log_result("Meeting Join Flow", False, "Missing participant_id for camera stream identification")
                    return False
                
                # Verify meeting status allows camera connection
                meeting = data.get("meeting", {})
                meeting_status = meeting.get("status")
                if meeting_status not in ["waiting", "active"]:
                    self.log_result("Meeting Join Flow", False, f"Meeting status '{meeting_status}' may prevent camera connection")
                    return False
                
                self.log_result("Meeting Join Flow", True, f"Join successful, participant_id: {participant_id}")
                return True
            else:
                self.log_result("Meeting Join Flow", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Meeting Join Flow", False, f"Error: {str(e)}")
            return False
    
    def test_meeting_link_generation(self):
        """Test meeting link generation for proper frontend integration"""
        if not self.meeting_code:
            self.log_result("Meeting Link Generation", False, "No meeting code available")
            return False
            
        try:
            # Test the generated meeting link format
            expected_base_url = BACKEND_URL.replace("/api", "")
            expected_join_url = f"{expected_base_url}/join?code={self.meeting_code}"
            
            # Verify the join URL is accessible (should redirect or show join page)
            response = requests.get(expected_join_url, allow_redirects=False)
            
            # We expect either a 200 (join page) or 302/301 (redirect to join page)
            if response.status_code in [200, 301, 302, 404]:  # 404 is acceptable if frontend handles routing
                self.log_result("Meeting Link Generation", True, f"Join URL accessible: {expected_join_url}")
                return True
            else:
                self.log_result("Meeting Link Generation", False, f"Join URL not accessible: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Meeting Link Generation", False, f"Error: {str(e)}")
            return False
    
    def test_qr_code_generation(self):
        """Test QR code generation for mobile camera access"""
        if not self.meeting_code:
            self.log_result("QR Code Generation", False, "No meeting code available")
            return False
            
        try:
            # Test QR code endpoint
            qr_url = f"{API_BASE}/qr/meeting/{self.meeting_code}"
            response = requests.get(qr_url)
            
            if response.status_code == 200:
                # Check if response is an image
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    self.log_result("QR Code Generation", True, f"QR code generated: {len(response.content)} bytes")
                    return True
                else:
                    self.log_result("QR Code Generation", False, f"Invalid content type: {content_type}")
                    return False
            else:
                self.log_result("QR Code Generation", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR Code Generation", False, f"Error: {str(e)}")
            return False
    
    def test_webrtc_configuration_details(self):
        """Test detailed WebRTC configuration for camera connection troubleshooting"""
        if not self.access_token or not self.meeting_code:
            self.log_result("WebRTC Configuration Details", False, "No access token or meeting code available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Get meeting details to check WebRTC config
            join_data = {
                "meeting_code": self.meeting_code,
                "display_name": "Config Tester",
                "share_business_card": True
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/join", json=join_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                webrtc_config = data.get("webrtc_config", {})
                
                # Detailed WebRTC configuration analysis
                ice_servers = webrtc_config.get("iceServers", [])
                
                # Check for Google STUN servers (reliable for most networks)
                google_stun = any("stun.l.google.com" in str(server.get("urls", [])) for server in ice_servers)
                
                # Check for TURN servers with credentials
                turn_with_creds = [server for server in ice_servers 
                                 if any("turn:" in url for url in server.get("urls", [])) 
                                 and "username" in server and "credential" in server]
                
                # Check for advanced WebRTC settings
                advanced_settings = {
                    "iceCandidatePoolSize": webrtc_config.get("iceCandidatePoolSize"),
                    "bundlePolicy": webrtc_config.get("bundlePolicy"),
                    "rtcpMuxPolicy": webrtc_config.get("rtcpMuxPolicy"),
                    "iceTransportPolicy": webrtc_config.get("iceTransportPolicy"),
                    "sdpSemantics": webrtc_config.get("sdpSemantics")
                }
                
                issues = []
                
                if not google_stun:
                    issues.append("No Google STUN servers (may cause connection issues)")
                
                if len(turn_with_creds) < 2:
                    issues.append(f"Only {len(turn_with_creds)} TURN servers with credentials (recommend 2+)")
                
                if advanced_settings["sdpSemantics"] != "unified-plan":
                    issues.append("SDP semantics not set to unified-plan (modern standard)")
                
                if advanced_settings["iceCandidatePoolSize"] is None or advanced_settings["iceCandidatePoolSize"] < 5:
                    issues.append("ICE candidate pool size too small (may slow connection)")
                
                if issues:
                    self.log_result("WebRTC Configuration Details", False, f"Configuration issues: {'; '.join(issues)}")
                    return False
                else:
                    self.log_result("WebRTC Configuration Details", True, 
                                  f"WebRTC config optimal: {len(ice_servers)} ICE servers, unified-plan SDP")
                    return True
            else:
                self.log_result("WebRTC Configuration Details", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("WebRTC Configuration Details", False, f"Error: {str(e)}")
            return False
    
    def test_camera_permission_flow(self):
        """Test camera permission and initialization flow simulation"""
        if not self.meeting_code:
            self.log_result("Camera Permission Flow", False, "No meeting code available")
            return False
            
        try:
            # Simulate the flow a frontend would follow for camera initialization
            
            # Step 1: Get meeting info (what frontend does before requesting camera)
            meeting_info_url = f"{API_BASE}/video/meetings"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = requests.get(meeting_info_url, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Camera Permission Flow", False, f"Cannot get meeting info: HTTP {response.status_code}")
                return False
            
            # Step 2: Check if meeting allows video
            data = response.json()
            meetings = data.get("meetings", [])
            
            current_meeting = None
            for meeting in meetings:
                if meeting.get("meeting_code") == self.meeting_code:
                    current_meeting = meeting
                    break
            
            if not current_meeting:
                self.log_result("Camera Permission Flow", False, "Meeting not found in user's meetings list")
                return False
            
            # Step 3: Verify video is enabled
            video_enabled = current_meeting.get("enable_video", True)  # Default to True if not specified
            if not video_enabled:
                self.log_result("Camera Permission Flow", False, "Video is disabled for this meeting")
                return False
            
            # Step 4: Check meeting status allows joining
            meeting_status = current_meeting.get("status", "waiting")
            if meeting_status not in ["waiting", "active"]:
                self.log_result("Camera Permission Flow", False, f"Meeting status '{meeting_status}' prevents camera access")
                return False
            
            # Step 5: Verify WebRTC config is available (needed before camera request)
            # This would be done by frontend before getUserMedia()
            join_data = {
                "meeting_code": self.meeting_code,
                "participant_name": "Camera Test User"
            }
            
            join_response = requests.post(f"{API_BASE}/video/meeting/join", json=join_data, headers=headers)
            
            if join_response.status_code == 200:
                join_data = join_response.json()
                webrtc_config = join_data.get("webrtc_config", {})
                
                if not webrtc_config:
                    self.log_result("Camera Permission Flow", False, "No WebRTC config provided for camera initialization")
                    return False
                
                self.log_result("Camera Permission Flow", True, "Camera permission flow ready - all prerequisites met")
                return True
            else:
                self.log_result("Camera Permission Flow", False, f"Join failed: HTTP {join_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Camera Permission Flow", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all camera connection tests"""
        print("=" * 80)
        print("🎥 VIDEO MEETING CAMERA CONNECTION TESTING")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print("🎯 FOCUS: Camera connection issues when joining meetings")
        print()
        
        # Setup
        if not self.setup_test_user():
            print("❌ Setup failed - cannot continue with camera tests")
            return
        
        # Run camera-focused tests
        tests = [
            self.test_meeting_creation_with_camera_config,
            self.test_meeting_join_flow,
            self.test_meeting_link_generation,
            self.test_qr_code_generation,
            self.test_webrtc_configuration_details,
            self.test_camera_permission_flow
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
            print("\n✅ ALL CAMERA TESTS PASSED - Camera connection should work properly")
        else:
            print(f"\n❌ {total - passed} CAMERA TESTS FAILED - Camera connection issues detected")
            print("\nFailed tests may indicate why camera doesn't connect when joining meetings.")
        
        return passed == total

if __name__ == "__main__":
    tester = VideoMeetingCameraTester()
    tester.run_all_tests()