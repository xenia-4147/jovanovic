#!/usr/bin/env python3
"""
Focused Test Suite for New Video Meeting, Community Networking, and Job Board Endpoints
Tests the revolutionary new features that were recently implemented
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

class NewEndpointsTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.card_id = None
        self.video_meeting_id = None
        self.community_id = None
        self.job_id = None
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
            test_email = f"newfeatures_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "Features",
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
                    "name": "New Features Tester",
                    "company": "Revolutionary Tech Inc",
                    "position": "Innovation Lead",
                    "description": "Testing the new video meeting and community features",
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
                            "address": test_email,
                            "is_primary": True
                        }
                    ],
                    "is_public": True
                }
                
                card_response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
                if card_response.status_code == 200:
                    self.card_id = card_response.json()["id"]
                    self.log_result("Setup Authentication", True, f"User and card created: {test_email}")
                    return True
                else:
                    self.log_result("Setup Authentication", False, "Failed to create business card", card_response.text)
                    return False
            else:
                self.log_result("Setup Authentication", False, f"Registration failed: HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Setup Authentication", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # VIDEO MEETING SYSTEM TESTS
    # ============================================================================
    
    def test_video_meeting_create(self):
        """Test POST /api/video/meeting/create - Create video meetings with WebRTC"""
        if not self.access_token or not self.card_id:
            self.log_result("Video Meeting Create", False, "No access token or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            meeting_data = {
                "title": "Revolutionary Tech Networking",
                "description": "Video meeting for business card sharing and networking",
                "meeting_type": "group",
                "duration_minutes": 60,
                "max_participants": 10,
                "password": "tech2025",
                "is_public": False,
                "allow_card_sharing": True,
                "share_host_card": True,
                "community_tags": ["technology", "networking"],
                "is_job_related": False
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/create", json=meeting_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it has meeting data
                if "meeting" in data and "join_url" in data:
                    meeting = data["meeting"]
                    if "id" in meeting and "meeting_code" in meeting:
                        self.video_meeting_id = meeting["id"]
                        self.meeting_code = meeting["meeting_code"]
                        self.log_result("Video Meeting Create", True, f"Video meeting created: {meeting['title']} (Code: {meeting['meeting_code']})")
                        return True
                    else:
                        self.log_result("Video Meeting Create", False, "Missing meeting ID or code in response", data)
                        return False
                else:
                    self.log_result("Video Meeting Create", False, "Missing meeting or join_url in response", data)
                    return False
            else:
                self.log_result("Video Meeting Create", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Video Meeting Create", False, f"Error: {str(e)}")
            return False
    
    def test_video_meeting_join(self):
        """Test POST /api/video/meeting/join - Join meetings"""
        if not self.access_token or not hasattr(self, 'meeting_code'):
            self.log_result("Video Meeting Join", False, "No access token or meeting code available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            join_data = {
                "meeting_code": self.meeting_code,
                "password": "tech2025",
                "share_business_card": True
            }
            
            response = requests.post(f"{API_BASE}/video/meeting/join", json=join_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") == True and "meeting" in data:
                    self.log_result("Video Meeting Join", True, f"Successfully joined video meeting: {data.get('message', '')}")
                    return True
                else:
                    self.log_result("Video Meeting Join", False, "Join failed or missing meeting data", data)
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
                
                # Check if it has the expected structure
                if "meetings" in data and "total_count" in data:
                    meetings = data["meetings"]
                    if isinstance(meetings, list):
                        self.log_result("Video Meetings List", True, f"Retrieved {len(meetings)} video meetings (Total: {data['total_count']})")
                        return True
                    else:
                        self.log_result("Video Meetings List", False, "Meetings is not a list", data)
                        return False
                else:
                    self.log_result("Video Meetings List", False, "Missing meetings or total_count in response", data)
                    return False
            else:
                self.log_result("Video Meetings List", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Video Meetings List", False, f"Error: {str(e)}")
            return False
    
    def test_video_meeting_share_card(self):
        """Test POST /api/video/meeting/{meeting_id}/share-card - Share business cards"""
        if not self.access_token or not self.video_meeting_id or not self.card_id:
            self.log_result("Video Meeting Share Card", False, "No access token, meeting ID, or card ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            share_data = {
                "business_card_id": self.card_id,
                "message": "Here's my business card from the video meeting!",
                "recipient_ids": []  # Share with all participants
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
            else:
                self.log_result("Video Meeting Share Card", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Video Meeting Share Card", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # COMMUNITY NETWORKING TESTS
    # ============================================================================
    
    def test_community_profile_get(self):
        """Test GET /api/community/profile - Get/create community profile"""
        if not self.access_token:
            self.log_result("Community Profile Get", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/community/profile", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "display_name", "interests", "skills"]
                
                if all(field in data for field in required_fields):
                    self.log_result("Community Profile Get", True, f"Community profile retrieved: {data['display_name']}")
                    return True
                else:
                    self.log_result("Community Profile Get", False, "Missing required fields in response", data)
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
                "interests": ["Technology", "AI", "Networking", "Innovation"],
                "skills": ["Python", "FastAPI", "React", "MongoDB", "WebRTC"],
                "location": "Berlin, Germany",
                "bio": "Tech innovator passionate about revolutionary digital solutions",
                "current_position": "Innovation Lead",
                "current_company": "Revolutionary Tech Inc"
            }
            
            response = requests.put(f"{API_BASE}/community/profile", json=profile_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if interests were updated (case-insensitive)
                updated_interests = [interest.lower() for interest in data.get("interests", [])]
                expected_interests = [interest.lower() for interest in profile_data["interests"]]
                
                if any(interest in updated_interests for interest in expected_interests):
                    self.log_result("Community Profile Update", True, f"Community profile updated with {len(data.get('interests', []))} interests")
                    return True
                else:
                    self.log_result("Community Profile Update", False, "Profile interests not updated correctly", data)
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
            response = requests.get(f"{API_BASE}/community/discover?limit=5", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "communities" in data and "total_matches" in data:
                    communities = data["communities"]
                    if isinstance(communities, list):
                        self.log_result("Community Discover", True, f"AI matching returned {len(communities)} communities (Total matches: {data['total_matches']})")
                        return True
                    else:
                        self.log_result("Community Discover", False, "Communities is not a list", data)
                        return False
                else:
                    self.log_result("Community Discover", False, "Missing communities or total_matches in response", data)
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
                
                expected_fields = ["events", "job_opportunities", "community_suggestions", "user_matches"]
                if all(field in data for field in expected_fields):
                    total_items = sum(len(data[field]) for field in expected_fields if isinstance(data[field], list))
                    self.log_result("Community Feed", True, f"Personalized feed retrieved with {total_items} total items")
                    return True
                else:
                    self.log_result("Community Feed", False, "Missing expected fields in feed response", data)
                    return False
            else:
                self.log_result("Community Feed", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Feed", False, f"Error: {str(e)}")
            return False
    
    def test_community_create(self):
        """Test POST /api/community/create - Create communities"""
        if not self.access_token:
            self.log_result("Community Create", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            community_data = {
                "name": "Berlin Revolutionary Tech",
                "description": "Community for revolutionary technology enthusiasts in Berlin",
                "community_type": "professional",
                "primary_interests": ["Technology", "Innovation", "AI", "Networking"],
                "location": "Berlin, Germany",
                "industry_focus": "Technology",
                "is_public": True,
                "max_members": 1000
            }
            
            response = requests.post(f"{API_BASE}/community/create", json=community_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "creator_id"]
                
                if all(field in data for field in required_fields):
                    self.community_id = data["id"]
                    self.log_result("Community Create", True, f"Community created: {data['name']} (ID: {data['id']})")
                    return True
                else:
                    self.log_result("Community Create", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Community Create", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Create", False, f"Error: {str(e)}")
            return False
    
    def test_community_join(self):
        """Test POST /api/community/{community_id}/join - Join communities"""
        if not self.access_token or not self.community_id:
            self.log_result("Community Join", False, "No access token or community ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            join_data = {
                "message": "Excited to join this revolutionary tech community!"
            }
            
            response = requests.post(f"{API_BASE}/community/{self.community_id}/join", 
                                   json=join_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data:
                    self.log_result("Community Join", True, f"Successfully joined community: {data['message']}")
                    return True
                else:
                    self.log_result("Community Join", False, "Missing message in response", data)
                    return False
            else:
                self.log_result("Community Join", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Community Join", False, f"Error: {str(e)}")
            return False
    
    def test_my_communities(self):
        """Test GET /api/community/my-communities - List user's communities"""
        if not self.access_token:
            self.log_result("My Communities List", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/community/my-communities", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "my_communities" in data and "total_count" in data:
                    my_communities = data["my_communities"]
                    if isinstance(my_communities, list):
                        self.log_result("My Communities List", True, f"Retrieved {len(my_communities)} communities (Total: {data['total_count']})")
                        return True
                    else:
                        self.log_result("My Communities List", False, "my_communities is not a list", data)
                        return False
                else:
                    self.log_result("My Communities List", False, "Missing my_communities or total_count in response", data)
                    return False
            else:
                self.log_result("My Communities List", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("My Communities List", False, f"Error: {str(e)}")
            return False
    
    # ============================================================================
    # JOB BOARD TESTS
    # ============================================================================
    
    def test_jobs_discover(self):
        """Test GET /api/jobs/discover - AI-matched job opportunities"""
        if not self.access_token:
            self.log_result("Jobs Discover", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/jobs/discover?limit=5", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.log_result("Jobs Discover", True, f"AI job matching returned {len(data)} opportunities")
                    return True
                else:
                    self.log_result("Jobs Discover", False, "Response is not a list", data)
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
                "title": "Senior Full-Stack Developer",
                "company_name": "Revolutionary Tech Inc",
                "description": "Join our team building revolutionary digital business card solutions with AI and WebRTC",
                "job_type": "full_time",
                "experience_level": "senior",
                "location": "Berlin, Germany",
                "remote_allowed": True,
                "required_skills": ["Python", "FastAPI", "React", "MongoDB", "WebRTC", "AI"],
                "salary_min": 75000,
                "salary_max": 95000
            }
            
            response = requests.post(f"{API_BASE}/jobs/post", json=job_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "title", "company_name", "posted_by"]
                
                if all(field in data for field in required_fields):
                    self.job_id = data["id"]
                    self.log_result("Jobs Post", True, f"Job posted: {data['title']} at {data['company_name']} (ID: {data['id']})")
                    return True
                else:
                    self.log_result("Jobs Post", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("Jobs Post", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Jobs Post", False, f"Error: {str(e)}")
            return False
    
    def test_jobs_apply(self):
        """Test POST /api/jobs/{job_id}/apply - Apply for jobs"""
        if not self.access_token or not self.job_id:
            self.log_result("Jobs Apply", False, "No access token or job ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            application_data = {
                "cover_message": "I'm excited to apply for this position! My experience with revolutionary tech solutions makes me a perfect fit."
            }
            
            response = requests.post(f"{API_BASE}/jobs/{self.job_id}/apply", 
                                   json=application_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data:
                    self.log_result("Jobs Apply", True, f"Job application submitted: {data['message']}")
                    return True
                else:
                    self.log_result("Jobs Apply", False, "Missing message in response", data)
                    return False
            else:
                self.log_result("Jobs Apply", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Jobs Apply", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all new endpoint tests"""
        print("=" * 80)
        print("NEW REVOLUTIONARY FEATURES TEST SUITE")
        print("Testing Video Meeting System, Community Networking & Job Board")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print()
        
        # Setup
        if not self.setup_authentication():
            print("❌ CRITICAL: Authentication setup failed. Cannot proceed with tests.")
            return
        
        # Video Meeting System Tests
        print("🎥 VIDEO MEETING SYSTEM TESTS")
        print("-" * 40)
        self.test_video_meeting_create()
        self.test_video_meeting_join()
        self.test_video_meetings_list()
        self.test_video_meeting_share_card()
        
        # Community Networking Tests
        print("\n🌐 COMMUNITY NETWORKING TESTS")
        print("-" * 40)
        self.test_community_profile_get()
        self.test_community_profile_update()
        self.test_community_discover()
        self.test_community_feed()
        self.test_community_create()
        self.test_community_join()
        self.test_my_communities()
        
        # Job Board Tests
        print("\n💼 JOB BOARD TESTS")
        print("-" * 40)
        self.test_jobs_discover()
        self.test_jobs_post()
        self.test_jobs_apply()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if total - passed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"- {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = NewEndpointsTester()
    tester.run_all_tests()