#!/usr/bin/env python3
"""
Focused Video Meeting System Test Suite
Tests the enhanced Video Meeting System with focus on revolutionary features
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

class VideoMeetingTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.card_id = None
        self.video_meeting_id = None
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
    
    def setup_user_and_card(self):
        """Setup user and business card for testing"""
        try:
            # Register user
            test_email = f"videomeet_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "VideoMeet123!",
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
                
                # Create business card
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                card_data = {
                    "name": "Dr. Sarah Weber",
                    "company": "Tech Innovation GmbH",
                    "position": "CTO",
                    "description": "Leading revolutionary video meeting technology",
                    "phones": [
                        {
                            "label": "work",
                            "number": "+49-30-555-1234",
                            "is_primary": True
                        }
                    ],
                    "emails": [
                        {
                            "label": "work",
                            "address": "sarah.weber@techinnovation.de",
                            "is_primary": True
                        }
                    ],
                    "website": "https://techinnovation.de",
                    "is_public": True
                }
                
                card_response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
                
                if card_response.status_code == 200:
                    card_data = card_response.json()
                    self.card_id = card_data["id"]
                    self.log_result("Setup User and Card", True, f"User and card created: {test_email}")
                    return True
                else:
                    self.log_result("Setup User and Card", False, f"Card creation failed: {card_response.status_code}")
                    return False
            else:
                self.log_result("Setup User and Card", False, f"User registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Setup User and Card", False, f"Error: {str(e)}")
            return False
    
    def test_enhanced_video_meeting_create(self):
        """Test POST /api/video/meeting/create - Enhanced meeting creation with revolutionary features"""
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
                
                # Check for revolutionary fields in both meeting and response root
                meeting = data.get("meeting", {})
                
                # Check if revolutionary fields are present (either in meeting or response root)
                has_share_link = meeting.get("share_link") or data.get("share_link")
                has_qr_code = meeting.get("qr_code_url") or data.get("qr_code_url") 
                has_meeting_card = meeting.get("meeting_link_card") or data.get("meeting_link_card")
                has_translation = meeting.get("translation_enabled")
                
                if has_share_link and has_qr_code and has_meeting_card and has_translation:
                    self.video_meeting_id = meeting.get("id")
                    self.meeting_code = meeting.get("meeting_code")
                    
                    # Verify share_link format (Zoom-like)
                    share_link = has_share_link
                    if share_link and ("netlink-3.preview.emergentagent.com/join?code=" in share_link):
                        self.log_result("Enhanced Video Meeting Create - Share Link", True, f"Professional share link generated: {share_link}")
                    else:
                        self.log_result("Enhanced Video Meeting Create - Share Link", False, f"Invalid share link format: {share_link}")
                        return False
                    
                    # Verify QR code URL
                    qr_code_url = has_qr_code
                    if qr_code_url and "/api/qr/meeting/" in qr_code_url:
                        self.log_result("Enhanced Video Meeting Create - QR Code", True, f"QR code URL generated: {qr_code_url}")
                    else:
                        self.log_result("Enhanced Video Meeting Create - QR Code", False, f"Invalid QR code URL: {qr_code_url}")
                        return False
                    
                    # Verify meeting_link_card for business card integration
                    meeting_link_card = has_meeting_card
                    if meeting_link_card and "meeting_info" in meeting_link_card:
                        meeting_info = meeting_link_card["meeting_info"]
                        if "features" in meeting_info and meeting_info["features"].get("business_cards") and meeting_info["features"].get("translation"):
                            self.log_result("Enhanced Video Meeting Create - Business Card Integration", True, "Meeting link card data complete with business card and translation features")
                        else:
                            self.log_result("Enhanced Video Meeting Create - Business Card Integration", False, "Missing business card or translation features in meeting_link_card", meeting_link_card)
                            return False
                    else:
                        self.log_result("Enhanced Video Meeting Create - Business Card Integration", False, "Missing meeting_link_card data", meeting_link_card)
                        return False
                    
                    # Verify translation settings
                    if meeting.get("translation_enabled") == True and meeting.get("target_languages") == ["en", "fr", "es"]:
                        self.log_result("Enhanced Video Meeting Create - Translation Settings", True, "Translation settings properly configured")
                    else:
                        self.log_result("Enhanced Video Meeting Create - Translation Settings", False, "Translation settings not properly set", meeting)
                        return False
                    
                    # Verify WebRTC config with STUN/TURN servers
                    webrtc_config = data.get("webrtc_config", {})
                    if webrtc_config and "iceServers" in webrtc_config:
                        ice_servers = webrtc_config["iceServers"]
                        
                        # Check for 4 professional servers (Google STUN + 3 TURN)
                        stun_servers = [server for server in ice_servers if any("stun:" in url for url in server.get("urls", []))]
                        turn_servers = [server for server in ice_servers if any("turn:" in url for url in server.get("urls", []))]
                        
                        if len(stun_servers) >= 1 and len(turn_servers) >= 3:
                            self.log_result("Enhanced Video Meeting Create - STUN/TURN Servers", True, f"Professional STUN/TURN configuration: {len(stun_servers)} STUN, {len(turn_servers)} TURN servers")
                        else:
                            self.log_result("Enhanced Video Meeting Create - STUN/TURN Servers", False, f"Insufficient servers: {len(stun_servers)} STUN, {len(turn_servers)} TURN")
                            return False
                        
                        # Verify unified-plan semantics
                        if webrtc_config.get("sdpSemantics") == "unified-plan":
                            self.log_result("Enhanced Video Meeting Create - WebRTC Config", True, "WebRTC configuration with unified-plan semantics")
                        else:
                            self.log_result("Enhanced Video Meeting Create - WebRTC Config", False, "Missing unified-plan semantics", webrtc_config)
                            return False
                    else:
                        self.log_result("Enhanced Video Meeting Create - WebRTC Config", False, "Missing WebRTC configuration", webrtc_config)
                        return False
                    
                    self.log_result("Enhanced Video Meeting Create", True, f"Revolutionary meeting created with ID: {self.video_meeting_id}")
                    return True
                else:
                    missing_info = []
                    if not has_share_link:
                        missing_info.append("share_link")
                    if not has_qr_code:
                        missing_info.append("qr_code_url") 
                    if not has_meeting_card:
                        missing_info.append("meeting_link_card")
                    if not has_translation:
                        missing_info.append("translation_enabled")
                    
                    self.log_result("Enhanced Video Meeting Create", False, f"Missing revolutionary features: {missing_info}", data)
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
    
    def test_meeting_response_format(self):
        """Test that meeting creation returns proper meeting_id and ice_servers fields"""
        if not self.video_meeting_id:
            self.log_result("Meeting Response Format", False, "No video meeting ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create another meeting to test response format
            meeting_data = {
                "title": "Response Format Test Meeting",
                "description": "Testing meeting_id and ice_servers in response",
                "meeting_type": "group",
                "duration_minutes": 30,
                "max_participants": 10,
                "translation_enabled": False
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for meeting_id field
                meeting = data.get("meeting", {})
                meeting_id = meeting.get("id")
                
                if meeting_id:
                    self.log_result("Meeting Response Format - meeting_id", True, f"meeting_id field present: {meeting_id}")
                else:
                    self.log_result("Meeting Response Format - meeting_id", False, "Missing meeting_id field in response", data)
                    return False
                
                # Check for ice_servers field
                webrtc_config = data.get("webrtc_config", {})
                ice_servers = webrtc_config.get("iceServers")
                
                if ice_servers and isinstance(ice_servers, list) and len(ice_servers) > 0:
                    self.log_result("Meeting Response Format - ice_servers", True, f"ice_servers field present with {len(ice_servers)} servers")
                else:
                    self.log_result("Meeting Response Format - ice_servers", False, "Missing or invalid ice_servers field", webrtc_config)
                    return False
                
                self.log_result("Meeting Response Format", True, "Response format includes required meeting_id and ice_servers fields")
                return True
            else:
                self.log_result("Meeting Response Format", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Meeting Response Format", False, f"Error: {str(e)}")
            return False
    
    def test_community_discover_quick_check(self):
        """Quick check on community discover endpoint for response format"""
        if not self.access_token:
            self.log_result("Community Discover Quick Check", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/community/discover", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has expected format
                if "communities" in data or "matches" in data:
                    self.log_result("Community Discover Quick Check", True, "Community discover endpoint responding with expected format")
                    return True
                else:
                    self.log_result("Community Discover Quick Check", False, "Unexpected response format - missing communities/matches", data)
                    return False
            else:
                self.log_result("Community Discover Quick Check", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Discover Quick Check", False, f"Error: {str(e)}")
            return False
    
    def test_job_discover_quick_check(self):
        """Quick check on job discover endpoint for response format"""
        if not self.access_token:
            self.log_result("Job Discover Quick Check", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/jobs/discover", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has expected format
                if "jobs" in data or any(key in data for key in ["job_opportunities", "matches"]):
                    self.log_result("Job Discover Quick Check", True, "Job discover endpoint responding with expected format")
                    return True
                else:
                    self.log_result("Job Discover Quick Check", False, "Unexpected response format - missing jobs/opportunities", data)
                    return False
            else:
                self.log_result("Job Discover Quick Check", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Job Discover Quick Check", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all video meeting tests"""
        print("=" * 80)
        print("🚀 ENHANCED VIDEO MEETING SYSTEM TESTING")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print("🎯 FOCUS: Revolutionary meeting features, STUN/TURN servers, response formats")
        print()
        
        # Setup
        if not self.setup_user_and_card():
            print("❌ Setup failed, cannot continue with tests")
            return
        
        # Core video meeting tests
        self.test_enhanced_video_meeting_create()
        self.test_meeting_response_format()
        
        # Quick checks on related endpoints
        self.test_community_discover_quick_check()
        self.test_job_discover_quick_check()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("FAILED TESTS:")
            for result in failed_tests:
                print(f"- {result['test']}: {result['message']}")
        else:
            print("🎉 ALL TESTS PASSED!")
        
        return success_rate >= 75  # Consider 75%+ as success

if __name__ == "__main__":
    tester = VideoMeetingTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)