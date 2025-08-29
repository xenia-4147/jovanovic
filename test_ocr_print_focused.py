#!/usr/bin/env python3
"""
Focused test for OCR Scanner and Print Export features
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

class OCRPrintTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.card_id = None
        self.scan_id = None
        self.print_template_id = None
        self.print_job_id = None
        
    def setup_user_and_card(self):
        """Setup a test user and business card for testing"""
        print("Setting up test user and business card...")
        
        # Register user
        test_email = f"ocrprint_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": test_email,
            "password": "TestPass123!",
            "first_name": "OCR",
            "last_name": "Tester",
            "gdpr_consent": True,
            "privacy_consent": True,
            "marketing_consent": False
        }
        
        response = requests.post(f"{API_BASE}/auth/register", json=user_data)
        if response.status_code != 200:
            print(f"❌ User registration failed: {response.status_code}")
            return False
            
        data = response.json()
        self.access_token = data["access_token"]
        self.user_id = data["user"]["id"]
        print(f"✅ User registered: {test_email}")
        
        # Create business card
        headers = {"Authorization": f"Bearer {self.access_token}"}
        card_data = {
            "name": "Dr. Sarah Weber",
            "company": "Digital Innovation GmbH",
            "position": "Chief Technology Officer",
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
                    "address": "sarah.weber@digitalinnovation.de",
                    "is_primary": True
                }
            ],
            "website": "https://digitalinnovation.de",
            "is_public": True,
            "background_color": "#ffffff",
            "text_color": "#1f2937",
            "accent_color": "#3b82f6"
        }
        
        response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Card creation failed: {response.status_code}")
            return False
            
        self.card_id = response.json()["id"]
        print(f"✅ Business card created: {self.card_id}")
        return True
    
    def test_ocr_scanner_endpoints(self):
        """Test all OCR Scanner endpoints"""
        print("\n🔍 Testing OCR Scanner Endpoints...")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test 1: POST /api/scanner/scan
        print("Testing POST /api/scanner/scan...")
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77mgAAAABJRU5ErkJggg=="
        
        scan_request = {
            "image_data": test_image_base64,
            "scan_method": "camera",
            "device_info": {"type": "mobile", "os": "android"}
        }
        
        response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("scan_id"):
                self.scan_id = data["scan_id"]
                print(f"✅ Scan initiated: {self.scan_id}")
            else:
                print(f"❌ Scan response invalid: {data}")
                return False
        else:
            print(f"❌ Scan failed: {response.status_code} - {response.text}")
            return False
        
        # Test 2: GET /api/scanner/scan/{scan_id}
        print("Testing GET /api/scanner/scan/{scan_id}...")
        response = requests.get(f"{API_BASE}/scanner/scan/{self.scan_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("scan_id") == self.scan_id:
                print(f"✅ Scan results retrieved: {data.get('status')}")
            else:
                print(f"❌ Scan results invalid: {data}")
                return False
        else:
            print(f"❌ Get scan results failed: {response.status_code}")
            return False
        
        # Test 3: POST /api/scanner/scan/{scan_id}/correct
        print("Testing POST /api/scanner/scan/{scan_id}/correct...")
        correction_request = {
            "field_type": "name",
            "corrected_value": "John Doe Corrected"
        }
        
        response = requests.post(f"{API_BASE}/scanner/scan/{self.scan_id}/correct", 
                               json=correction_request, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Field correction applied")
            else:
                print(f"❌ Field correction failed: {data}")
                return False
        else:
            print(f"❌ Field correction failed: {response.status_code}")
            return False
        
        # Test 4: POST /api/scanner/scan/{scan_id}/convert
        print("Testing POST /api/scanner/scan/{scan_id}/convert...")
        convert_request = {
            "card_name": "Scanned Business Card",
            "auto_map_fields": True
        }
        
        response = requests.post(f"{API_BASE}/scanner/scan/{self.scan_id}/convert", 
                               json=convert_request, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("id"):
                print(f"✅ Scan converted to card: {data['id']}")
            else:
                print(f"❌ Conversion failed: {data}")
                return False
        else:
            print(f"❌ Conversion failed: {response.status_code}")
            return False
        
        # Test 5: GET /api/scanner/scans
        print("Testing GET /api/scanner/scans...")
        response = requests.get(f"{API_BASE}/scanner/scans", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "scans" in data and "total_count" in data:
                print(f"✅ Scanned cards listed: {data['total_count']} total")
            else:
                print(f"❌ Scan list invalid: {data}")
                return False
        else:
            print(f"❌ Scan list failed: {response.status_code}")
            return False
        
        return True
    
    def test_print_export_endpoints(self):
        """Test all Print Export endpoints"""
        print("\n🖨️ Testing Print Export Endpoints...")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Test 1: GET /api/print/templates
        print("Testing GET /api/print/templates...")
        response = requests.get(f"{API_BASE}/print/templates", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("templates") and len(data["templates"]) > 0:
                self.print_template_id = data["templates"][0]["id"]
                print(f"✅ Print templates retrieved: {len(data['templates'])} templates")
            else:
                print(f"❌ No print templates available: {data}")
                return False
        else:
            print(f"❌ Get templates failed: {response.status_code}")
            return False
        
        # Test 2: POST /api/print/export
        print("Testing POST /api/print/export...")
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
            if data.get("success") and data.get("job_id"):
                self.print_job_id = data["job_id"]
                print(f"✅ Print job created: {self.print_job_id}")
            else:
                print(f"❌ Print export failed: {data}")
                return False
        else:
            print(f"❌ Print export failed: {response.status_code}")
            return False
        
        # Test 3: POST /api/print/quick
        print("Testing POST /api/print/quick...")
        quick_print_request = {
            "business_card_id": self.card_id,
            "format": "pdf",
            "size": "85x55mm",
            "quality": "print"
        }
        
        response = requests.post(f"{API_BASE}/print/quick", json=quick_print_request, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Quick print job created: {data.get('job_id')}")
            else:
                print(f"❌ Quick print failed: {data}")
                return False
        else:
            print(f"❌ Quick print failed: {response.status_code}")
            return False
        
        # Test 4: POST /api/print/preview
        print("Testing POST /api/print/preview...")
        preview_request = {
            "business_card_id": self.card_id,
            "template_id": self.print_template_id,
            "size": "85x55mm",
            "orientation": "landscape"
        }
        
        response = requests.post(f"{API_BASE}/print/preview", json=preview_request, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("preview_url"):
                print("✅ Print preview generated")
            else:
                print(f"❌ Print preview failed: {data}")
                return False
        else:
            print(f"❌ Print preview failed: {response.status_code}")
            return False
        
        # Test 5: GET /api/print/jobs/{job_id}
        print("Testing GET /api/print/jobs/{job_id}...")
        response = requests.get(f"{API_BASE}/print/jobs/{self.print_job_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("job_id") == self.print_job_id:
                print(f"✅ Print job status: {data.get('status')} ({data.get('progress_percentage')}%)")
            else:
                print(f"❌ Print job status invalid: {data}")
                return False
        else:
            print(f"❌ Print job status failed: {response.status_code}")
            return False
        
        return True
    
    def test_authentication_and_authorization(self):
        """Test authentication and authorization for new endpoints"""
        print("\n🔐 Testing Authentication & Authorization...")
        
        # Test OCR endpoints without auth
        scan_request = {"image_data": "test"}
        response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request)
        if response.status_code == 401:
            print("✅ OCR endpoints require authentication")
        else:
            print(f"❌ OCR auth check failed: {response.status_code}")
            return False
        
        # Test Print endpoints without auth
        response = requests.get(f"{API_BASE}/print/templates")
        if response.status_code == 401:
            print("✅ Print endpoints require authentication")
        else:
            print(f"❌ Print auth check failed: {response.status_code}")
            return False
        
        # Test user data isolation
        headers = {"Authorization": f"Bearer {self.access_token}"}
        fake_scan_id = str(uuid.uuid4())
        response = requests.get(f"{API_BASE}/scanner/scan/{fake_scan_id}", headers=headers)
        if response.status_code == 404:
            print("✅ User data isolation working (scans)")
        else:
            print(f"❌ Scan isolation failed: {response.status_code}")
            return False
        
        fake_job_id = str(uuid.uuid4())
        response = requests.get(f"{API_BASE}/print/jobs/{fake_job_id}", headers=headers)
        if response.status_code == 404:
            print("✅ User data isolation working (print jobs)")
        else:
            print(f"❌ Print job isolation failed: {response.status_code}")
            return False
        
        return True
    
    def run_tests(self):
        """Run all OCR and Print tests"""
        print("🚀 Starting OCR Scanner & Print Export Feature Tests")
        print("=" * 60)
        
        if not self.setup_user_and_card():
            print("❌ Setup failed")
            return False
        
        tests = [
            ("OCR Scanner Endpoints", self.test_ocr_scanner_endpoints),
            ("Print Export Endpoints", self.test_print_export_endpoints),
            ("Authentication & Authorization", self.test_authentication_and_authorization)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    print(f"✅ {test_name}: PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAILED")
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                failed += 1
        
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        
        return failed == 0

if __name__ == "__main__":
    tester = OCRPrintTester()
    success = tester.run_tests()
    
    if success:
        print("\n🎉 All OCR Scanner & Print Export tests PASSED!")
    else:
        print("\n💥 Some tests FAILED!")
        exit(1)