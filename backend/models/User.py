from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import bcrypt
import uuid

class GDPRConsent(BaseModel):
    consent: bool = False
    consent_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    consent_version: str = "1.0"

class PrivacySettings(BaseModel):
    allow_analytics: bool = True
    allow_marketing: bool = False
    data_retention_days: int = 365
    allow_public_search: bool = True
    allow_embedding: bool = True

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email: EmailStr
    password_hash: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)
    gdpr_consent: GDPRConsent = Field(default_factory=GDPRConsent)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    is_active: bool = True
    email_verified: bool = False
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
    
    @validator('password_hash', pre=True)
    def hash_password(cls, v):
        if isinstance(v, str) and not v.startswith('$2b$'):
            return bcrypt.hashpw(v.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        return v
    
    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gdpr_consent: bool = False
    privacy_consent: bool = False
    marketing_consent: bool = False
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    @validator('gdpr_consent')
    def validate_gdpr_consent(cls, v):
        if not v:
            raise ValueError('GDPR consent is required')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    privacy_settings: PrivacySettings
    created_at: datetime
    last_login_at: Optional[datetime]
    email_verified: bool
    
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    privacy_settings: Optional[PrivacySettings] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class GDPRExport(BaseModel):
    user_data: Dict[str, Any]
    business_cards: list
    recipients: list
    analytics_summary: Dict[str, Any]
    export_date: datetime = Field(default_factory=datetime.utcnow)
    
class AccountDeletion(BaseModel):
    password: str
    confirmation: str = Field(..., pattern="DELETE_MY_ACCOUNT")
    reason: Optional[str] = None