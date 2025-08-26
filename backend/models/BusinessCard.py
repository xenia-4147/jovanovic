from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
import uuid

class ContactPhone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    number: str
    is_primary: bool = False
    
    @validator('number')
    def validate_phone_number(cls, v):
        # Basic phone validation - remove spaces and check if it's reasonable
        cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if len(cleaned) < 7 or len(cleaned) > 20:
            raise ValueError('Invalid phone number format')
        return v

class ContactEmail(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    address: EmailStr
    is_primary: bool = False

class ContactAddress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    street: Optional[str] = None
    house_number: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "Deutschland"
    is_primary: bool = False

class SocialMedia(BaseModel):
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    tiktok: Optional[str] = None
    telegram: Optional[str] = None
    
    @validator('*', pre=True)
    def clean_social_handles(cls, v):
        if v and isinstance(v, str):
            # Remove @ symbol if present
            return v.lstrip('@')
        return v

class BusinessCard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str = Field(alias="userId")
    name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    phones: List[ContactPhone] = []
    emails: List[ContactEmail] = []
    addresses: List[ContactAddress] = []
    website: Optional[str] = None
    profile_image: Optional[str] = None
    logo: Optional[str] = None
    social_media: SocialMedia = Field(default_factory=SocialMedia)
    is_public: bool = True
    background_color: str = "#ffffff"
    text_color: str = "#1f2937"
    accent_color: str = "#3b82f6"
    embed_background_color: str = "#f8fafc"
    allow_embedding: bool = True
    auto_update_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    view_count: int = 0
    share_count: int = 0
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
    
    @validator('phones')
    def validate_phones(cls, v):
        if not v:
            return v
        
        primary_count = sum(1 for phone in v if phone.is_primary)
        if primary_count > 1:
            # Auto-fix: make first one primary, others not
            for i, phone in enumerate(v):
                phone.is_primary = (i == 0)
        elif primary_count == 0 and v:
            # Auto-fix: make first one primary
            v[0].is_primary = True
        
        return v
    
    @validator('emails')
    def validate_emails(cls, v):
        if not v:
            return v
            
        primary_count = sum(1 for email in v if email.is_primary)
        if primary_count > 1:
            # Auto-fix: make first one primary, others not
            for i, email in enumerate(v):
                email.is_primary = (i == 0)
        elif primary_count == 0 and v:
            # Auto-fix: make first one primary
            v[0].is_primary = True
            
        return v
    
    @validator('addresses')
    def validate_addresses(cls, v):
        if not v:
            return v
            
        primary_count = sum(1 for address in v if address.is_primary)
        if primary_count > 1:
            # Auto-fix: make first one primary, others not
            for i, address in enumerate(v):
                address.is_primary = (i == 0)
        elif primary_count == 0 and v:
            # Auto-fix: make first one primary
            v[0].is_primary = True
            
        return v
    
    @validator('website')
    def validate_website(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v

class BusinessCardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    phones: List[ContactPhone] = []
    emails: List[ContactEmail] = []
    addresses: List[ContactAddress] = []
    website: Optional[str] = None
    profile_image: Optional[str] = None
    logo: Optional[str] = None
    social_media: Optional[SocialMedia] = None
    is_public: bool = True
    background_color: str = "#ffffff"
    text_color: str = "#1f2937"
    accent_color: str = "#3b82f6"
    embed_background_color: str = "#f8fafc"
    allow_embedding: bool = True
    auto_update_enabled: bool = True

class BusinessCardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    phones: Optional[List[ContactPhone]] = None
    emails: Optional[List[ContactEmail]] = None
    addresses: Optional[List[ContactAddress]] = None
    website: Optional[str] = None
    profile_image: Optional[str] = None
    logo: Optional[str] = None
    social_media: Optional[SocialMedia] = None
    is_public: Optional[bool] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    accent_color: Optional[str] = None
    embed_background_color: Optional[str] = None
    allow_embedding: Optional[bool] = None
    auto_update_enabled: Optional[bool] = None

class BusinessCardResponse(BaseModel):
    id: str
    name: str
    company: Optional[str]
    position: Optional[str]
    description: Optional[str]
    phones: List[ContactPhone]
    emails: List[ContactEmail]
    addresses: List[ContactAddress]
    website: Optional[str]
    profile_image: Optional[str]
    logo: Optional[str]
    social_media: SocialMedia
    is_public: bool
    background_color: str
    text_color: str
    accent_color: str
    embed_background_color: str
    allow_embedding: bool
    auto_update_enabled: bool
    created_at: datetime
    last_updated: datetime
    view_count: int
    share_count: int
    is_owner: bool = False

class CardRecipient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    card_id: str
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    shared_at: datetime = Field(default_factory=datetime.utcnow)
    last_notified: Optional[datetime] = None
    notification_method: str = "email"  # email, sms, push
    is_active: bool = True
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class CardAnalytics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    card_id: str
    action: str  # view, download, share, qr_scan
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = None
    country: Optional[str] = None  # IP-derived, no exact location
    referrer: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class ShareRequest(BaseModel):
    recipient_emails: List[EmailStr]
    message: Optional[str] = None
    notification_method: str = "email"

class EmbedOptions(BaseModel):
    width: int = 320
    height: int = 450
    show_qr: bool = True
    theme: str = "auto"  # auto, light, dark