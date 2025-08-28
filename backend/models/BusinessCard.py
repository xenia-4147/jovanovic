from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import re

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type='string')
        return field_schema

class MessagingApp(BaseModel):
    name: str  # whatsapp, viber, telegram, signal, etc.
    enabled: bool = True
    
class ContactPhone(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    label: str
    number: str
    is_primary: bool = False
    messaging_apps: List[MessagingApp] = [
        MessagingApp(name="whatsapp", enabled=True),
        MessagingApp(name="sms", enabled=True)
    ]  # Default: WhatsApp and SMS enabled
    
    @field_validator('number')
    @classmethod
    def validate_phone_number(cls, v):
        # Basic phone validation - remove spaces and check if it's reasonable
        cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if len(cleaned) < 7 or len(cleaned) > 20:
            raise ValueError('Invalid phone number format')
        return v

class ContactEmail(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    label: str
    address: EmailStr
    is_primary: bool = False

class ContactAddress(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
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
    
    @field_validator('instagram', 'linkedin', 'twitter', 'tiktok', 'telegram', mode='before')
    @classmethod
    def clean_social_handles(cls, v):
        if v and isinstance(v, str):
            # Remove @ symbol if present
            return v.lstrip('@')
        return v

class BusinessCard(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(alias="userId")
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
    custom_code: Optional[str] = Field(None, min_length=3, max_length=50)
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
    code_usage_count: int = 0
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
    
    @field_validator('custom_code', mode='before')
    @classmethod
    def validate_custom_code(cls, v):
        if not v:
            return v
        
        # Remove spaces and convert to uppercase
        code = v.replace(' ', '').upper()
        
        # Check if code contains only letters and numbers
        if not re.match(r'^[A-Z0-9]+$', code):
            raise ValueError('Code darf nur Buchstaben und Zahlen enthalten')
        
        # Must be between 3-50 characters
        if len(code) < 3 or len(code) > 50:
            raise ValueError('Code muss zwischen 3 und 50 Zeichen lang sein')
        
        return code
    
    @field_validator('phones')
    @classmethod
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
    
    @field_validator('emails')
    @classmethod
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
    
    @field_validator('addresses')
    @classmethod
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
    
    @field_validator('website')
    @classmethod
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
    custom_code: Optional[str] = Field(None, min_length=3, max_length=50)
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
    custom_code: Optional[str] = Field(None, min_length=3, max_length=50)
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
    custom_code: Optional[str]
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
    code_usage_count: int
    is_owner: bool = False

class CardRecipient(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    card_id: PyObjectId
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    shared_at: datetime = Field(default_factory=datetime.utcnow)
    last_notified: Optional[datetime] = None
    notification_method: str = "email"  # email, sms, push
    is_active: bool = True
    access_method: str = "link"  # link, code, qr
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CardAnalytics(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    card_id: PyObjectId
    action: str  # view, download, share, qr_scan, code_access
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = None
    country: Optional[str] = None  # IP-derived, no exact location
    referrer: Optional[str] = None
    access_method: Optional[str] = None  # link, code, qr
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ShareRequest(BaseModel):
    recipient_emails: List[EmailStr]
    message: Optional[str] = None
    notification_method: str = "email"

class EmbedOptions(BaseModel):
    width: int = 320
    height: int = 450
    show_qr: bool = True
    theme: str = "auto"  # auto, light, dark

class CodeAccessRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    
    @field_validator('code', mode='before')
    @classmethod
    def validate_and_clean_code(cls, v):
        if not v:
            raise ValueError('Code ist erforderlich')
        
        # Remove spaces and convert to uppercase
        code = v.replace(' ', '').upper()
        
        # Check if code contains only letters and numbers
        if not re.match(r'^[A-Z0-9]+$', code):
            raise ValueError('Code darf nur Buchstaben und Zahlen enthalten')
        
        return code

class CodeAccessResponse(BaseModel):
    success: bool
    card: Optional[BusinessCardResponse] = None
    message: str
    code_usage_count: Optional[int] = None