"""
Print Export Models for Professional Business Card Printing
Game-Changing Feature: Digital → Professional Print Ready
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import uuid


class PrintFormat(str, Enum):
    PDF = "pdf"
    AI = "ai"  # Adobe Illustrator
    EPS = "eps"
    SVG = "svg"
    PNG = "png"
    JPG = "jpg"


class PrintSize(str, Enum):
    STANDARD_EU = "85x55mm"  # European standard
    STANDARD_US = "89x51mm"  # US standard
    SQUARE = "70x70mm"      # Instagram style
    MINI = "70x42mm"        # Compact
    LARGE = "105x65mm"      # Premium


class PrintOrientation(str, Enum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


class PrintQuality(str, Enum):
    WEB = "web"          # 72 DPI - for digital use
    PRINT = "print"      # 300 DPI - standard print
    HIGH_END = "high_end" # 600 DPI - premium printing


class PrintTemplate(BaseModel):
    """Professional print template"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None)
    category: str = Field(..., description="Template category (business, creative, minimalist, etc.)")
    
    # Template specifications
    size: PrintSize = Field(..., description="Card dimensions")
    orientation: PrintOrientation = Field(..., description="Card orientation")
    
    # Design elements
    background_color: Optional[str] = Field(None, description="Hex color code")
    background_image_url: Optional[str] = Field(None, description="Background image")
    has_bleed: bool = Field(default=True, description="Whether template includes bleed area")
    bleed_size_mm: float = Field(default=3.0, description="Bleed size in millimeters")
    
    # Layout configuration
    layout_config: Dict[str, Any] = Field(..., description="Template layout JSON")
    
    # Typography
    font_family_primary: str = Field(default="Arial", description="Primary font")
    font_family_secondary: str = Field(default="Arial", description="Secondary font")
    
    # Print specifications
    supported_formats: List[PrintFormat] = Field(default_factory=lambda: [PrintFormat.PDF, PrintFormat.PNG])
    recommended_paper: Optional[str] = Field(None, description="Recommended paper type")
    
    # Template metadata
    is_premium: bool = Field(default=False, description="Whether this is a premium template")
    price: Optional[float] = Field(None, description="Template price if premium")
    preview_image_url: Optional[str] = Field(None, description="Template preview image")
    
    # Usage and ratings
    download_count: int = Field(default=0)
    rating: float = Field(default=0.0, description="Average user rating")
    rating_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="Template creator ID")


class PrintJob(BaseModel):
    """Print job for business card export"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User requesting the print")
    business_card_id: str = Field(..., description="Business card to print")
    
    # Print specifications
    template_id: str = Field(..., description="Selected print template")
    format: PrintFormat = Field(..., description="Export format")
    size: PrintSize = Field(..., description="Card size")
    orientation: PrintOrientation = Field(..., description="Orientation")
    quality: PrintQuality = Field(..., description="Print quality/DPI")
    
    # Customization
    custom_colors: Optional[Dict[str, str]] = Field(None, description="Custom color overrides")
    custom_fonts: Optional[Dict[str, str]] = Field(None, description="Custom font overrides")
    custom_layout: Optional[Dict[str, Any]] = Field(None, description="Custom layout modifications")
    
    # Print settings
    bleed_area: bool = Field(default=True, description="Include bleed area")
    crop_marks: bool = Field(default=True, description="Include crop marks")
    color_profile: str = Field(default="CMYK", description="Color profile (RGB/CMYK)")
    
    # Quantity and sides
    quantity: int = Field(default=1, description="Number of cards to generate")
    double_sided: bool = Field(default=False, description="Whether to generate back side")
    back_side_design: Optional[str] = Field(None, description="Back side design template")
    
    # Processing status
    status: str = Field(default="pending", description="Job status")
    processing_started_at: Optional[datetime] = Field(None)
    processing_completed_at: Optional[datetime] = Field(None)
    
    # Output files
    generated_files: List[Dict[str, str]] = Field(default_factory=list, description="Generated file URLs")
    preview_url: Optional[str] = Field(None, description="Preview image URL")
    download_url: Optional[str] = Field(None, description="Download URL for final files")
    
    # Print service integration
    print_service_provider: Optional[str] = Field(None, description="Connected print service")
    print_service_job_id: Optional[str] = Field(None, description="External print job ID")
    estimated_delivery: Optional[datetime] = Field(None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PrinterSpecifications(BaseModel):
    """Printer/print service specifications"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Printer/service name")
    description: Optional[str] = Field(None)
    
    # Technical specifications
    supported_formats: List[PrintFormat] = Field(..., description="Supported file formats")
    supported_sizes: List[PrintSize] = Field(..., description="Supported card sizes")
    max_dpi: int = Field(..., description="Maximum DPI supported")
    color_spaces: List[str] = Field(..., description="Supported color spaces")
    
    # Paper and finishing options
    paper_types: List[str] = Field(default_factory=list, description="Available paper types")
    finishing_options: List[str] = Field(default_factory=list, description="Finishing options (matte, gloss, etc.)")
    
    # Pricing and delivery
    base_price_per_card: Optional[float] = Field(None)
    minimum_quantity: int = Field(default=1)
    estimated_turnaround_days: int = Field(default=3)
    
    # API integration
    api_endpoint: Optional[str] = Field(None, description="Print service API endpoint")
    api_key_required: bool = Field(default=False)
    
    # Service metadata
    is_active: bool = Field(default=True)
    location: Optional[str] = Field(None, description="Printer location/region")
    rating: float = Field(default=0.0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Request/Response Models

class PrintExportRequest(BaseModel):
    """Request to export business card for printing"""
    business_card_id: str = Field(..., description="Business card to export")
    template_id: str = Field(..., description="Print template to use")
    format: PrintFormat = Field(default=PrintFormat.PDF, description="Export format")
    quality: PrintQuality = Field(default=PrintQuality.PRINT, description="Export quality")
    
    # Customization options
    size: Optional[PrintSize] = Field(None, description="Override template size")
    orientation: Optional[PrintOrientation] = Field(None, description="Override orientation")
    custom_colors: Optional[Dict[str, str]] = Field(None, description="Custom colors")
    
    # Print options
    include_bleed: bool = Field(default=True)
    include_crop_marks: bool = Field(default=True)
    double_sided: bool = Field(default=False)
    quantity: int = Field(default=1, ge=1, le=1000)
    
    # Print service
    printer_id: Optional[str] = Field(None, description="Specific printer to use")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('Quantity must be between 1 and 1000')
        return v


class QuickPrintRequest(BaseModel):
    """Quick print request with minimal customization"""
    business_card_id: str = Field(..., description="Business card to print")
    format: PrintFormat = Field(default=PrintFormat.PDF)
    size: PrintSize = Field(default=PrintSize.STANDARD_EU)
    quality: PrintQuality = Field(default=PrintQuality.PRINT)


class PrintPreviewRequest(BaseModel):
    """Request to generate print preview"""
    business_card_id: str = Field(..., description="Business card to preview")
    template_id: str = Field(..., description="Template for preview")
    size: PrintSize = Field(default=PrintSize.STANDARD_EU)
    orientation: PrintOrientation = Field(default=PrintOrientation.LANDSCAPE)


class PrintJobResponse(BaseModel):
    """Response after creating print job"""
    success: bool = Field(..., description="Whether job was created successfully")
    job_id: str = Field(..., description="Print job ID")
    status: str = Field(..., description="Job status")
    preview_url: Optional[str] = Field(None, description="Preview image URL")
    estimated_completion_minutes: Optional[int] = Field(None)
    message: str = Field(..., description="Status message")


class PrintTemplateResponse(BaseModel):
    """Response with print template data"""
    templates: List[PrintTemplate] = Field(..., description="Available print templates")
    categories: List[str] = Field(..., description="Template categories")
    total_count: int = Field(..., description="Total number of templates")


class PrintJobStatusResponse(BaseModel):
    """Response with print job status"""
    job_id: str = Field(..., description="Print job ID")
    status: str = Field(..., description="Current status")
    progress_percentage: int = Field(..., description="Progress percentage (0-100)")
    download_url: Optional[str] = Field(None, description="Download URL if completed")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Print service integration
    external_tracking_id: Optional[str] = Field(None, description="External print service tracking ID")
    estimated_delivery: Optional[datetime] = Field(None)


# Default Templates Configuration

DEFAULT_TEMPLATES = [
    {
        "name": "Classic Business",
        "category": "business",
        "description": "Clean, professional template perfect for any industry",
        "size": PrintSize.STANDARD_EU,
        "orientation": PrintOrientation.LANDSCAPE,
        "background_color": "#FFFFFF",
        "layout_config": {
            "name_position": {"x": 20, "y": 15},
            "company_position": {"x": 20, "y": 30},
            "contact_position": {"x": 20, "y": 45},
            "logo_position": {"x": 200, "y": 10},
            "logo_size": {"width": 60, "height": 30}
        },
        "font_family_primary": "Arial",
        "is_premium": False
    },
    {
        "name": "Modern Gradient", 
        "category": "creative",
        "description": "Eye-catching gradient design for creative professionals",
        "size": PrintSize.STANDARD_EU,
        "orientation": PrintOrientation.LANDSCAPE,
        "background_color": "#667eea",
        "layout_config": {
            "name_position": {"x": 25, "y": 20},
            "company_position": {"x": 25, "y": 35},
            "contact_position": {"x": 25, "y": 50},
            "accent_color": "#764ba2"
        },
        "font_family_primary": "Helvetica",
        "is_premium": True,
        "price": 2.99
    },
    {
        "name": "Minimalist White",
        "category": "minimalist", 
        "description": "Ultra-clean design with maximum white space",
        "size": PrintSize.STANDARD_EU,
        "orientation": PrintOrientation.LANDSCAPE,
        "background_color": "#FFFFFF",
        "layout_config": {
            "name_position": {"x": 30, "y": 25},
            "contact_position": {"x": 30, "y": 40},
            "border_width": 1,
            "border_color": "#E0E0E0"
        },
        "font_family_primary": "Lato",
        "is_premium": False
    }
]

# Print Quality Configurations
QUALITY_SETTINGS = {
    PrintQuality.WEB: {"dpi": 72, "compression": "medium"},
    PrintQuality.PRINT: {"dpi": 300, "compression": "low"},
    PrintQuality.HIGH_END: {"dpi": 600, "compression": "none"}
}

# Size Specifications in mm
SIZE_SPECIFICATIONS = {
    PrintSize.STANDARD_EU: {"width": 85, "height": 55, "bleed": 3},
    PrintSize.STANDARD_US: {"width": 89, "height": 51, "bleed": 3},
    PrintSize.SQUARE: {"width": 70, "height": 70, "bleed": 3},
    PrintSize.MINI: {"width": 70, "height": 42, "bleed": 2},
    PrintSize.LARGE: {"width": 105, "height": 65, "bleed": 4}
}