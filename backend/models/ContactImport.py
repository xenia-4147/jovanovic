from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from enum import Enum

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

class ContactSourceType(str, Enum):
    GOOGLE_CONTACTS = "google_contacts"
    APPLE_ICLOUD = "apple_icloud" 
    OUTLOOK = "outlook"
    VCF_FILE = "vcf_file"
    CSV_FILE = "csv_file"
    CONTACT_PICKER = "contact_picker"
    CARDDAV = "carddav"

class SyncStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error" 
    DISABLED = "disabled"

class ContactSource(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    source_type: ContactSourceType
    display_name: str  # "Meine Google Kontakte", "iPhone Kontakte", etc.
    
    # OAuth/API Credentials (encrypted)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    
    # Sync Configuration
    sync_enabled: bool = True
    sync_interval_hours: int = 24  # Default: daily sync
    last_sync_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    sync_status: SyncStatus = SyncStatus.ACTIVE
    
    # Statistics
    total_contacts_imported: int = 0
    last_sync_contacts_added: int = 0
    last_sync_contacts_updated: int = 0
    last_sync_contacts_deleted: int = 0
    
    # Error Handling
    last_error_message: Optional[str] = None
    error_count: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ImportedContactPhone(BaseModel):
    number: str
    label: str = "mobile"
    is_primary: bool = False
    messaging_apps: List[Dict[str, Any]] = []
    
    @field_validator('messaging_apps', mode='before')
    @classmethod
    def ensure_messaging_apps(cls, v):
        if not v:
            return [
                {"name": "whatsapp", "enabled": True},
                {"name": "sms", "enabled": True}
            ]
        return v

class ImportedContactEmail(BaseModel):
    address: str
    label: str = "work"
    is_primary: bool = False

class ImportedContactAddress(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    label: str = "work"
    is_primary: bool = False
    
    def formatted_address(self) -> str:
        parts = [self.street, self.city, self.state, self.postal_code, self.country]
        return ", ".join([part for part in parts if part])

class ImportedContact(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    source_id: str  # Reference to ContactSource
    
    # Basic Info
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    nickname: Optional[str] = None
    
    # Organization
    company: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    
    # Contact Methods
    phones: List[ImportedContactPhone] = []
    emails: List[ImportedContactEmail] = []
    addresses: List[ImportedContactAddress] = []
    
    # Profile
    profile_image_url: Optional[str] = None
    profile_image_data: Optional[str] = None  # Base64 for cached images
    
    # Social Media
    social_media: Dict[str, str] = {}
    website: Optional[str] = None
    
    # Additional Fields
    notes: Optional[str] = None
    tags: List[str] = []
    birthday: Optional[datetime] = None
    
    # Sync Metadata
    external_id: Optional[str] = None  # ID in source system
    external_etag: Optional[str] = None  # For change detection
    last_modified_external: Optional[datetime] = None
    
    # Internal Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: Optional[datetime] = None
    
    # Business Card Link (if person also has a business card)
    linked_business_card_id: Optional[str] = None
    is_business_card_owner: bool = False
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class SyncJob(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    source_id: str
    
    # Job Configuration
    job_type: str = "full_sync"  # full_sync, incremental_sync, import
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress
    status: str = "pending"  # pending, running, completed, failed
    progress_percentage: float = 0.0
    current_step: Optional[str] = None
    
    # Results
    contacts_processed: int = 0
    contacts_added: int = 0
    contacts_updated: int = 0
    contacts_deleted: int = 0
    contacts_skipped: int = 0
    
    # Error Handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ContactImportRequest(BaseModel):
    source_type: ContactSourceType
    display_name: Optional[str] = None
    
    # OAuth flow data
    authorization_code: Optional[str] = None
    
    # File upload data
    file_content: Optional[str] = None  # Base64 encoded
    file_name: Optional[str] = None
    
    # Contact picker data
    contacts_data: Optional[List[Dict[str, Any]]] = None
    
    # Sync settings
    sync_enabled: bool = True
    sync_interval_hours: int = 24

class ContactImportResponse(BaseModel):
    success: bool
    message: str
    source_id: Optional[str] = None
    contacts_imported: int = 0
    
    # OAuth flow continuation
    auth_required: bool = False
    auth_url: Optional[str] = None
    
class ContactSourceResponse(BaseModel):
    id: str
    source_type: str
    display_name: str
    sync_enabled: bool
    sync_status: str
    last_sync_at: Optional[datetime]
    next_sync_at: Optional[datetime]
    total_contacts_imported: int
    last_error_message: Optional[str]

class UnifiedContact(BaseModel):
    """Unified contact representation combining business cards and imported contacts"""
    id: str
    source_type: str  # "business_card" or "imported_contact"
    source_id: Optional[str] = None
    
    # Basic Info
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    
    # Contact Methods
    phones: List[ImportedContactPhone] = []
    emails: List[ImportedContactEmail] = []
    addresses: List[ImportedContactAddress] = []
    
    # Profile
    profile_image: Optional[str] = None
    
    # Additional
    is_business_card: bool = False
    is_imported_contact: bool = False
    
    # Business Card specific
    custom_code: Optional[str] = None
    is_public: Optional[bool] = None
    
    # Imported contact specific
    external_source: Optional[str] = None
    last_synced: Optional[datetime] = None