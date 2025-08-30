"""
OCR Service for Business Card Scanning
Game-Changing Feature: Paper → Digital Card Conversion
"""
import os
import re
import base64
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

# Image processing
from PIL import Image
import cv2
import numpy as np
from io import BytesIO

# OCR Services
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Our models
from models.CardScanner import (
    ScannedField, OCRConfidence, ScannedBusinessCard, 
    COMMON_FIELD_PATTERNS, DEFAULT_FIELD_CONFIDENCE_THRESHOLDS
)

logger = logging.getLogger(__name__)


class OCRService:
    """OCR Service for extracting text from business card images"""
    
    def __init__(self):
        self.google_client = None
        if GOOGLE_VISION_AVAILABLE and os.getenv('GOOGLE_CLOUD_CREDENTIALS'):
            try:
                self.google_client = vision.ImageAnnotatorClient()
                logger.info("Google Vision API initialized successfully")
            except Exception as e:
                logger.warning(f"Google Vision API initialization failed: {e}")
        
        self.field_patterns = COMMON_FIELD_PATTERNS
        self.confidence_thresholds = DEFAULT_FIELD_CONFIDENCE_THRESHOLDS
    
    async def scan_business_card(
        self, 
        image_data: str, 
        user_id: str, 
        scan_method: str = "camera"
    ) -> ScannedBusinessCard:
        """
        Main method to scan a business card image and extract structured data
        """
        logger.info(f"Starting business card scan for user {user_id}")
        
        # Create initial scan record
        scan = ScannedBusinessCard(
            user_id=user_id,
            original_image_url=f"temp_{datetime.utcnow().timestamp()}",  # Will be updated
            scan_method=scan_method,
            processing_started_at=datetime.utcnow()
        )
        
        try:
            # Process image
            processed_image = await self._preprocess_image(image_data)
            
            # Extract text using multiple OCR methods
            ocr_results = await self._extract_text_multiple_methods(processed_image)
            
            # Analyze and structure the extracted text
            structured_fields = await self._analyze_extracted_text(ocr_results)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(structured_fields)
            
            # Update scan with results
            scan.extracted_fields = structured_fields
            scan.overall_confidence = overall_confidence
            scan.raw_ocr_data = ocr_results
            
            # Import and use proper enum
            from models.CardScanner import ScanProcessingStatus
            scan.status = ScanProcessingStatus.COMPLETED  # Use enum instead of string
            scan.processing_completed_at = datetime.utcnow()
            
            # Generate smart field mapping suggestions
            scan.suggested_mapping = await self._generate_field_mapping(structured_fields)
            
            logger.info(f"Business card scan completed for user {user_id} with confidence {overall_confidence:.1f}%")
            
            return scan
            
        except Exception as e:
            logger.error(f"Business card scan failed for user {user_id}: {str(e)}")
            
            # Import and use proper enum
            from models.CardScanner import ScanProcessingStatus
            scan.status = ScanProcessingStatus.FAILED  # Use enum instead of string
            scan.error_message = str(e)
            scan.processing_completed_at = datetime.utcnow()
            return scan
    
    async def _preprocess_image(self, image_data: str) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy
        """
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Convert to PIL Image
        pil_image = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Image enhancement for better OCR
        # 1. Resize for optimal OCR (if too small)
        height, width = cv_image.shape[:2]
        if width < 800:
            scale_factor = 800 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            cv_image = cv2.resize(cv_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # 2. Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # 3. Noise reduction
        gray = cv2.medianBlur(gray, 3)
        
        # 4. Contrast enhancement
        gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray)
        
        # 5. Thresholding to get better text
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    async def _extract_text_multiple_methods(self, processed_image: np.ndarray) -> Dict[str, Any]:
        """
        Extract text using multiple OCR methods for best results
        """
        results = {"methods_used": [], "combined_text": "", "confidence_scores": {}}
        
        # Method 1: Google Vision API (if available)
        if self.google_client:
            try:
                google_result = await self._extract_text_google_vision(processed_image)
                results["google_vision"] = google_result
                results["methods_used"].append("google_vision")
                logger.info("Google Vision OCR completed successfully")
            except Exception as e:
                logger.warning(f"Google Vision OCR failed: {e}")
        
        # Method 2: Tesseract (fallback)
        if TESSERACT_AVAILABLE:
            try:
                tesseract_result = await self._extract_text_tesseract(processed_image)
                results["tesseract"] = tesseract_result
                results["methods_used"].append("tesseract")
                logger.info("Tesseract OCR completed successfully")
            except Exception as e:
                logger.warning(f"Tesseract OCR failed: {e}")
        
        # Combine results from multiple methods
        results["combined_text"] = self._combine_ocr_results(results)
        
        return results
    
    async def _extract_text_google_vision(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract text using Google Vision API
        """
        # Convert image to bytes
        _, buffer = cv2.imencode('.png', image)
        image_bytes = buffer.tobytes()
        
        # Create Vision API image object
        vision_image = vision.Image(content=image_bytes)
        
        # Detect text
        response = self.google_client.text_detection(image=vision_image)
        texts = response.text_annotations
        
        if response.error.message:
            raise Exception(f"Google Vision API error: {response.error.message}")
        
        result = {
            "raw_text": texts[0].description if texts else "",
            "text_blocks": [],
            "confidence": 0.0
        }
        
        # Process individual text blocks
        for text in texts[1:]:  # Skip first element (full text)
            vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
            
            text_block = {
                "text": text.description,
                "confidence": 90.0,  # Google Vision doesn't provide confidence per word
                "bounding_box": {
                    "x": min(v[0] for v in vertices),
                    "y": min(v[1] for v in vertices),
                    "width": max(v[0] for v in vertices) - min(v[0] for v in vertices),
                    "height": max(v[1] for v in vertices) - min(v[1] for v in vertices)
                }
            }
            result["text_blocks"].append(text_block)
        
        # Calculate average confidence
        if result["text_blocks"]:
            result["confidence"] = sum(block["confidence"] for block in result["text_blocks"]) / len(result["text_blocks"])
        
        return result
    
    async def _extract_text_tesseract(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract text using Tesseract OCR
        """
        # Enhanced Tesseract configuration for business cards
        custom_config = r'--oem 3 --psm 6'  # Removed restrictive whitelist for better recognition
        
        # Extract text with confidence
        data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)
        
        result = {
            "raw_text": "",
            "text_blocks": [],
            "confidence": 0.0
        }
        
        # Process OCR results with lower threshold
        confidences = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 15:  # Lowered from 30 to 15 for more text detection
                text = data['text'][i].strip()
                if text and len(text) > 1:  # Accept text with at least 2 characters
                    text_block = {
                        "text": text,
                        "confidence": float(data['conf'][i]),
                        "bounding_box": {
                            "x": data['left'][i],
                            "y": data['top'][i],
                            "width": data['width'][i],
                            "height": data['height'][i]
                        }
                    }
                    result["text_blocks"].append(text_block)
                    result["raw_text"] += text + " "
                    confidences.append(float(data['conf'][i]))
        
        # Calculate average confidence
        if confidences:
            result["confidence"] = sum(confidences) / len(confidences)
        
        return result
    
    def _combine_ocr_results(self, results: Dict[str, Any]) -> str:
        """
        Combine text from multiple OCR methods intelligently
        """
        combined_text = ""
        
        # Prioritize Google Vision if available and confident
        if "google_vision" in results and results["google_vision"]["confidence"] > 80:
            combined_text = results["google_vision"]["raw_text"]
        elif "tesseract" in results:
            combined_text = results["tesseract"]["raw_text"]
        elif "google_vision" in results:
            combined_text = results["google_vision"]["raw_text"]
        
        return combined_text.strip()
    
    async def _analyze_extracted_text(self, ocr_results: Dict[str, Any]) -> List[ScannedField]:
        """
        Analyze extracted text and create structured fields
        """
        text = ocr_results.get("combined_text", "")
        fields = []
        
        # Extract specific field types using patterns
        for field_type, patterns in self.field_patterns.items():
            extracted_values = self._extract_field_by_patterns(text, patterns, field_type)
            fields.extend(extracted_values)
        
        # Extract additional fields from individual text blocks
        if "google_vision" in ocr_results:
            block_fields = self._extract_fields_from_blocks(ocr_results["google_vision"]["text_blocks"])
            fields.extend(block_fields)
        elif "tesseract" in ocr_results:
            block_fields = self._extract_fields_from_blocks(ocr_results["tesseract"]["text_blocks"])
            fields.extend(block_fields)
        
        # Remove duplicates and validate
        fields = self._deduplicate_fields(fields)
        
        return fields
    
    def _extract_field_by_patterns(self, text: str, patterns: List[str], field_type: str) -> List[ScannedField]:
        """
        Extract fields using regex patterns
        """
        fields = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                confidence = self._calculate_pattern_confidence(match.group(), field_type)
                
                field = ScannedField(
                    field_type=field_type,
                    value=match.group().strip(),
                    confidence=confidence,
                    confidence_level=OCRConfidence.HIGH if confidence >= 90 else 
                                   OCRConfidence.MEDIUM if confidence >= 60 else 
                                   OCRConfidence.LOW
                )
                fields.append(field)
        
        return fields
    
    def _extract_fields_from_blocks(self, text_blocks: List[Dict]) -> List[ScannedField]:
        """
        Extract fields from individual text blocks with position information
        """
        fields = []
        
        for block in text_blocks:
            text = block["text"]
            confidence = block["confidence"]
            bounding_box = block.get("bounding_box")
            
            # Determine field type based on content and position
            field_type = self._determine_field_type(text, bounding_box)
            
            if field_type:
                field = ScannedField(
                    field_type=field_type,
                    value=text,
                    confidence=confidence,
                    confidence_level=OCRConfidence.HIGH if confidence >= 90 else 
                                   OCRConfidence.MEDIUM if confidence >= 60 else 
                                   OCRConfidence.LOW,
                    bounding_box=bounding_box
                )
                fields.append(field)
        
        return fields
    
    def _determine_field_type(self, text: str, bounding_box: Optional[Dict] = None) -> Optional[str]:
        """
        Determine field type based on text content and position
        """
        text_lower = text.lower().strip()
        
        # Email detection
        if "@" in text and "." in text:
            return "email"
        
        # Phone number detection
        if re.match(r"[\+\(]?[\d\s\-\(\)]{7,}", text):
            return "phone"
        
        # Website detection
        if any(domain in text_lower for domain in [".com", ".de", ".org", "www.", "http"]):
            return "website"
        
        # Company indicators
        if any(suffix in text for suffix in ["GmbH", "AG", "KG", "e.V.", "Inc.", "LLC"]):
            return "company"
        
        # Position/title indicators
        position_keywords = ["manager", "director", "ceo", "cto", "founder", "geschäftsführer", "leiter"]
        if any(keyword in text_lower for keyword in position_keywords):
            return "position"
        
        # Name detection (capitalize first letters, moderate length)
        if (text.replace(" ", "").replace(".", "").isalpha() and 
            len(text.split()) <= 3 and 
            2 <= len(text) <= 50):
            return "name"
        
        # Default to unknown
        return "other"
    
    def _calculate_pattern_confidence(self, value: str, field_type: str) -> float:
        """
        Calculate confidence score for extracted field
        """
        base_confidence = 70.0
        
        # Field-specific confidence adjustments
        if field_type == "email" and "@" in value and "." in value:
            base_confidence = 95.0
        elif field_type == "phone" and len(re.sub(r'[^\d]', '', value)) >= 7:
            base_confidence = 85.0
        elif field_type == "website" and ("www." in value or "http" in value):
            base_confidence = 90.0
        
        # Length-based adjustments
        if len(value) < 3:
            base_confidence *= 0.7
        elif len(value) > 50:
            base_confidence *= 0.8
        
        return min(100.0, base_confidence)
    
    def _deduplicate_fields(self, fields: List[ScannedField]) -> List[ScannedField]:
        """
        Remove duplicate fields, keeping highest confidence
        """
        field_groups = {}
        
        for field in fields:
            key = (field.field_type, field.value.lower().strip())
            if key not in field_groups or field.confidence > field_groups[key].confidence:
                field_groups[key] = field
        
        return list(field_groups.values())
    
    def _calculate_overall_confidence(self, fields: List[ScannedField]) -> float:
        """
        Calculate overall scan confidence score
        """
        if not fields:
            return 0.0
        
        # Weight important fields more heavily
        field_weights = {
            "name": 3.0,
            "email": 2.5,
            "phone": 2.0,
            "company": 1.5,
            "position": 1.0,
            "other": 0.5
        }
        
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for field in fields:
            weight = field_weights.get(field.field_type, 0.5)
            total_weighted_confidence += field.confidence * weight
            total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    async def _generate_field_mapping(self, fields: List[ScannedField]) -> Dict[str, str]:
        """
        Generate smart suggestions for mapping fields to business card fields
        """
        mapping = {}
        
        # Group fields by type and select best candidates
        type_groups = {}
        for field in fields:
            if field.field_type not in type_groups:
                type_groups[field.field_type] = []
            type_groups[field.field_type].append(field)
        
        # Select best field for each type
        for field_type, group in type_groups.items():
            # Sort by confidence and select highest
            best_field = max(group, key=lambda f: f.confidence)
            
            if best_field.confidence >= self.confidence_thresholds.get(field_type, 60.0):
                mapping[field_type] = best_field.value
        
        return mapping
    
    async def correct_field(self, scan_id: str, field_type: str, corrected_value: str) -> bool:
        """
        Apply user correction to a scanned field
        """
        try:
            # This would typically update the database
            # For now, we'll implement the logic structure
            logger.info(f"Field correction applied: {field_type} -> {corrected_value} for scan {scan_id}")
            return True
        except Exception as e:
            logger.error(f"Field correction failed: {e}")
            return False


# Singleton service instance
ocr_service = OCRService()