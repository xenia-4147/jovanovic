#!/usr/bin/env python3
"""
CRITICAL SCANNER API RESPONSE FORMAT TESTING
Focus: Debug exact response format that frontend receives
"""

import requests
import json
import uuid
from datetime import datetime
import os
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# Backend URL
BACKEND_URL = 'http://localhost:8001'
API_BASE = f"{BACKEND_URL}/api"

class ScannerAPITester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.scan_id = None
        
    def log_result(self, test_name, success, message="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()
    
    def setup_user(self):
        """Create a test user and get access token"""
        try:
            # Generate unique test data
            test_email = f"scannertest_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "ScannerTest123!",
                "first_name": "Scanner",
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
                self.log_result("User Setup", True, f"User created: {test_email}")
                return True
            else:
                self.log_result("User Setup", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("User Setup", False, f"Error: {str(e)}")
            return False
    
    def test_scanner_api_exact_response(self):
        """Test EXACT scanner API response format that frontend receives"""
        if not self.access_token:
            self.log_result("Scanner API Exact Response", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create realistic business card image with clear text
            card_image = Image.new('RGB', (600, 350), color='white')
            draw = ImageDraw.Draw(card_image)
            
            # Try to use a font, fallback to default
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Add realistic business card text
            draw.text((50, 50), "Dr. Sarah Weber", fill='black', font=font_large)
            draw.text((50, 90), "Chief Technology Officer", fill='black', font=font_medium)
            draw.text((50, 120), "Digital Innovation GmbH", fill='black', font=font_medium)
            draw.text((50, 160), "sarah.weber@digitalinnovation.de", fill='black', font=font_small)
            draw.text((50, 190), "+49-30-555-1234", fill='black', font=font_small)
            draw.text((50, 220), "www.digitalinnovation.de", fill='black', font=font_small)
            
            # Convert to base64
            buffer = io.BytesIO()
            card_image.save(buffer, format='PNG')
            image_data = base64.b64encode(buffer.getvalue()).decode()
            
            # 1. Test POST /api/scanner/scan - CAPTURE EXACT RESPONSE
            scan_request = {
                "image_data": image_data,
                "scan_method": "test_upload"
            }
            
            print(f"\n🔍 TESTING POST /api/scanner/scan")
            response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                scan_data = response.json()
                print(f"   EXACT POST RESPONSE STRUCTURE:")
                print(f"   {json.dumps(scan_data, indent=2)}")
                
                # Check if response has required fields for frontend
                scan_id = scan_data.get("scan_id")
                if scan_id:
                    self.scan_id = scan_id
                    self.log_result("Scanner POST Request", True, f"Scan initiated with ID: {scan_id}")
                    
                    # Wait a moment for processing
                    import time
                    time.sleep(5)  # Give more time for OCR processing
                    
                    # 2. Test GET /api/scanner/scan/{scan_id} - CAPTURE EXACT RESPONSE
                    print(f"\n🔍 TESTING GET /api/scanner/scan/{scan_id}")
                    poll_response = requests.get(f"{API_BASE}/scanner/scan/{scan_id}", headers=headers)
                    
                    print(f"   Status Code: {poll_response.status_code}")
                    print(f"   Headers: {dict(poll_response.headers)}")
                    
                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        print(f"   EXACT GET RESPONSE STRUCTURE:")
                        print(f"   {json.dumps(poll_data, indent=2)}")
                        
                        # 3. CRITICAL: Check if response matches frontend expectations
                        # Frontend expects: scanResult?.scanned_card?.extracted_fields?.length > 0
                        
                        print(f"\n🎯 FRONTEND COMPATIBILITY ANALYSIS:")
                        print(f"   Frontend condition: scanResult?.scanned_card?.extracted_fields?.length > 0")
                        
                        # Check top-level structure
                        print(f"   Response keys: {list(poll_data.keys())}")
                        
                        scanned_card = poll_data.get("scanned_card")
                        print(f"   scanned_card exists: {scanned_card is not None}")
                        
                        if scanned_card:
                            print(f"   scanned_card keys: {list(scanned_card.keys()) if isinstance(scanned_card, dict) else 'Not a dict'}")
                            
                            extracted_fields = scanned_card.get("extracted_fields", [])
                            print(f"   extracted_fields exists: {'extracted_fields' in scanned_card}")
                            print(f"   extracted_fields type: {type(extracted_fields)}")
                            print(f"   extracted_fields length: {len(extracted_fields) if isinstance(extracted_fields, list) else 'Not a list'}")
                            
                            if extracted_fields:
                                print(f"   extracted_fields content:")
                                for i, field in enumerate(extracted_fields):
                                    print(f"     [{i}]: {field}")
                            
                            # Check the exact frontend condition
                            frontend_condition = (
                                scanned_card and 
                                isinstance(scanned_card, dict) and 
                                "extracted_fields" in scanned_card and 
                                isinstance(extracted_fields, list) and 
                                len(extracted_fields) > 0
                            )
                            
                            print(f"\n🚨 CRITICAL FINDING:")
                            print(f"   Frontend condition result: {frontend_condition}")
                            
                            if frontend_condition:
                                self.log_result("Scanner Response Format Check", True, 
                                              f"✅ Response format MATCHES frontend expectations: scanned_card with {len(extracted_fields)} extracted_fields")
                                
                                # Additional analysis of field quality
                                meaningful_fields = [f for f in extracted_fields if isinstance(f, dict) and f.get("value") and len(f.get("value", "").strip()) > 2]
                                print(f"   Meaningful fields: {len(meaningful_fields)}")
                                
                                if len(meaningful_fields) > 0:
                                    print(f"   ✅ OCR extracted meaningful data - frontend should show results")
                                    return True
                                else:
                                    print(f"   ⚠️  OCR extracted fields but no meaningful data")
                                    return True  # Still technically correct format
                            else:
                                self.log_result("Scanner Response Format Check", False, 
                                              f"❌ MISMATCH: Frontend expects scanned_card.extracted_fields.length > 0, got {len(extracted_fields) if isinstance(extracted_fields, list) else 'invalid'} fields")
                                
                                # Detailed diagnosis
                                print(f"\n🔧 DIAGNOSIS:")
                                if not scanned_card:
                                    print(f"   - Missing 'scanned_card' field in response")
                                elif not isinstance(scanned_card, dict):
                                    print(f"   - 'scanned_card' is not a dictionary: {type(scanned_card)}")
                                elif "extracted_fields" not in scanned_card:
                                    print(f"   - Missing 'extracted_fields' in scanned_card")
                                elif not isinstance(extracted_fields, list):
                                    print(f"   - 'extracted_fields' is not a list: {type(extracted_fields)}")
                                elif len(extracted_fields) == 0:
                                    print(f"   - 'extracted_fields' array is empty")
                                
                                return False
                        else:
                            self.log_result("Scanner Response Format Check", False, 
                                          "❌ CRITICAL: No 'scanned_card' field in response - frontend will show 'Keine Informationen erkannt'")
                            return False
                    else:
                        self.log_result("Scanner GET Request", False, f"Polling failed: HTTP {poll_response.status_code}", poll_response.text)
                        return False
                else:
                    self.log_result("Scanner POST Request", False, "No scan_id in response", scan_data)
                    return False
            else:
                self.log_result("Scanner POST Request", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Scanner API Exact Response", False, f"Error: {str(e)}")
            return False
    
    def run_tests(self):
        """Run all scanner tests"""
        print("=" * 80)
        print("🔍 CRITICAL SCANNER API RESPONSE FORMAT TESTING")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print("🎯 FOCUS: Debug 'Keine Informationen erkannt' issue")
        print()
        
        if not self.setup_user():
            print("❌ Cannot proceed without user setup")
            return
        
        self.test_scanner_api_exact_response()

if __name__ == "__main__":
    tester = ScannerAPITester()
    tester.run_tests()