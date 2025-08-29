"""
Card Scanner Models for OCR and Image Processing
Game-Changing Feature: Paper Business Cards → Digital
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class ScanProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"  
    COMPLETED = "completed"
    FAILED = "failed"


class OCRConfidence(str, Enum):
    HIGH = "high"      # >90%
    MEDIUM = "medium"  # 60-90%
    LOW = "low"        # <60%
    MANUAL = "manual"  # User corrected


class ScannedField(BaseModel):
    """Individual field extracted from business card"""
    field_type: str = Field(..., description="Type of field (name, phone, email, etc.)")
    value: str = Field(..., description="Extracted text value")
    confidence: float = Field(..., description="OCR confidence score (0-100)")
    confidence_level: OCRConfidence = Field(..., description="Confidence category")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Coordinates of text on image")
    manually_corrected: bool = Field(default=False, description="Whether user corrected this field")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Confidence must be between 0 and 100')
        return v
    
    @validator('confidence_level', pre=True, always=True)
    def set_confidence_level(cls, v, values):
        if 'confidence' not in values:
            return v
        confidence = values['confidence']
        if confidence >= 90:
            return OCRConfidence.HIGH
        elif confidence >= 60:
            return OCRConfidence.MEDIUM
        else:
            return OCRConfidence.LOW


class ScannedBusinessCard(BaseModel):
    """Complete scanned business card with extracted data"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="ID of user who scanned the card")
    
    # Original scan data
    original_image_url: str = Field(..., description="URL to uploaded card image")
    processed_image_url: Optional[str] = Field(None, description="URL to processed/enhanced image")
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # OCR Results
    raw_ocr_data: Optional[Dict[str, Any]] = Field(None, description="Raw OCR response from service")
    extracted_fields: List[ScannedField] = Field(default_factory=list, description="Structured extracted data")
    overall_confidence: float = Field(default=0.0, description="Overall scan quality score")
    
    # Processing status
    status: ScanProcessingStatus = Field(default=ScanProcessingStatus.PENDING)
    processing_started_at: Optional[datetime] = Field(None)
    processing_completed_at: Optional[datetime] = Field(None)
    error_message: Optional[str] = Field(None)
    
    # Smart field mapping (AI suggestions)
    suggested_mapping: Optional[Dict[str, str]] = Field(None, description="AI suggestions for field types")
    
    # Conversion to digital card
    converted_to_card_id: Optional[str] = Field(None, description="ID of created BusinessCard")
    is_converted: bool = Field(default=False)
    
    # Metadata
    scan_method: str = Field(default="camera", description="How card was scanned (camera, upload)")
    device_info: Optional[Dict[str, str]] = Field(None, description="Device used for scanning")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CardScanRequest(BaseModel):
    """Request to scan a business card"""
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    image_url: Optional[str] = Field(None, description="URL to image file")
    scan_method: str = Field(default="camera", description="Scanning method")
    device_info: Optional[Dict[str, str]] = Field(None)
    
    @validator('image_data', 'image_url')
    def at_least_one_image_source(cls, v, values, field):
        if field.name == 'image_url' and not v and not values.get('image_data'):
            raise ValueError('Either image_data or image_url must be provided')
        return v


class FieldCorrectionRequest(BaseModel):
    """Request to correct OCR field"""
    scan_id: str = Field(..., description="ID of scanned card")
    field_type: str = Field(..., description="Type of field to correct")
    corrected_value: str = Field(..., description="User-corrected value")


class ConvertToCardRequest(BaseModel):
    """Request to convert scanned card to digital business card"""
    scan_id: str = Field(..., description="ID of scanned card")
    card_name: str = Field(..., description="Name for the new business card")
    auto_map_fields: bool = Field(default=True, description="Automatically map fields to business card")
    field_mapping: Optional[Dict[str, str]] = Field(None, description="Custom field mapping")


class ScanBatchRequest(BaseModel):
    """Request to process multiple business cards at once"""
    images: List[Dict[str, str]] = Field(..., description="List of images with metadata")
    event_tag: Optional[str] = Field(None, description="Tag for event/batch (e.g., 'Messe München 2024')")
    auto_convert: bool = Field(default=False, description="Automatically convert to digital cards")


# Response Models

class ScanResponse(BaseModel):
    """Response after initiating a scan"""
    success: bool = Field(..., description="Whether scan was initiated successfully")
    scan_id: str = Field(..., description="ID of the scan job")
    status: ScanProcessingStatus = Field(..., description="Current processing status")
    message: str = Field(..., description="Status message")
    estimated_completion_seconds: Optional[int] = Field(None, description="Estimated processing time")


class ScanResultResponse(BaseModel):
    """Response with scan results"""
    scan_id: str = Field(..., description="ID of the scan")
    status: ScanProcessingStatus = Field(..., description="Processing status")
    scanned_card: Optional[ScannedBusinessCard] = Field(None, description="Scanned card data")
    suggested_corrections: Optional[List[Dict[str, str]]] = Field(None, description="Suggested field corrections")
    conversion_ready: bool = Field(default=False, description="Whether ready to convert to business card")


class ScanListResponse(BaseModel):
    """Response with list of scanned cards"""
    scans: List[ScannedBusinessCard] = Field(..., description="List of scanned cards")
    total_count: int = Field(..., description="Total number of scans")
    pending_count: int = Field(..., description="Number of pending scans")
    converted_count: int = Field(..., description="Number converted to cards")


# Template Models for Smart Field Detection

class BusinessCardTemplate(BaseModel):
    """Template for recognizing business card layouts"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None)
    
    # Field detection patterns
    field_patterns: Dict[str, List[str]] = Field(..., description="Regex patterns for each field type")
    layout_markers: Optional[Dict[str, Any]] = Field(None, description="Visual layout indicators")
    
    # Usage statistics
    usage_count: int = Field(default=0)
    accuracy_score: float = Field(default=0.0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Smart Recognition Helpers

COMMON_FIELD_PATTERNS = {
    "name": [
        r"^[A-Z][a-z]+ [A-Z][a-z]+",  # First Last
        r"^Dr\.\s+[A-Z][a-z]+ [A-Z][a-z]+",  # Dr. First Last
        r"^[A-Z][a-z]+,\s+[A-Z][a-z]+",  # Last, First
    ],
    "email": [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    ],
    "phone": [
        r"\+49\s?\(?0?\)?\s?\d{2,4}\s?\d{3,8}",  # German format
        r"0\d{2,4}\s?\d{3,8}",  # German local
        r"\(\d{3,4}\)\s?\d{3,8}",  # Area code format
    ],
    "website": [
        r"www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        r"https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    ],
    "company": [
        r"GmbH$",
        r"AG$", 
        r"KG$",
        r"e\.V\.$",
    ]
}

DEFAULT_FIELD_CONFIDENCE_THRESHOLDS = {
    "name": 85.0,
    "email": 95.0,  # Email should be very accurate
    "phone": 80.0,
    "company": 75.0,
    "position": 70.0,
    "website": 90.0,
    "address": 60.0,  # Address can be tricky
}