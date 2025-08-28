from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
import re
import string
import random

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

class ExpressCode(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    code: str = Field(..., min_length=2, max_length=3)
    card_id: str  # Associated business card
    user_id: Optional[str] = None  # Owner (optional for anonymous)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    usage_count: int = 0
    max_usage: Optional[int] = None  # Optional usage limit
    is_active: bool = True
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
    
    @classmethod
    def generate_express_code(cls, length: int = 2) -> str:
        """Generate ultra-short express code (2-3 characters)"""
        # Use only unambiguous characters
        characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        # Exclude: I, O, 0, 1 (confusing characters)
        return ''.join(random.choice(characters) for _ in range(length))
    
    def is_expired(self) -> bool:
        """Check if the express code has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if code is valid (active, not expired, usage limit not reached)"""
        if not self.is_active or self.is_expired():
            return False
        
        if self.max_usage and self.usage_count >= self.max_usage:
            return False
            
        return True

class ExpressMeetingRoom(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    code: str = Field(..., min_length=2, max_length=2)  # 2-digit codes for groups
    created_by_card_id: str
    created_by_card_name: str
    created_by_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    participants: List[str] = []  # List of card_ids
    max_participants: int = 10
    is_active: bool = True
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
    
    @classmethod
    def generate_express_room_code(cls) -> str:
        """Generate 2-digit room code (numbers only for easy speaking)"""
        # Use only numbers 23-99 (avoid 00-22 for clarity)
        return str(random.randint(23, 99))
    
    def is_expired(self) -> bool:
        """Check if the meeting room has expired"""
        return datetime.utcnow() > self.expires_at
    
    def can_join(self) -> bool:
        """Check if new participants can join"""
        return (
            self.is_active and 
            not self.is_expired() and 
            len(self.participants) < self.max_participants
        )
    
    def add_participant(self, card_id: str) -> bool:
        """Add participant to room"""
        if not self.can_join():
            return False
        
        if card_id not in self.participants:
            self.participants.append(card_id)
            return True
        
        return False  # Already in room

class ExpressShareCreate(BaseModel):
    card_id: str
    duration_seconds: int = Field(60, ge=30, le=300)  # 30 seconds to 5 minutes
    max_usage: Optional[int] = Field(None, ge=1, le=50)  # Optional usage limit
    code_length: int = Field(2, ge=2, le=3)  # 2-3 character codes

class ExpressRoomCreate(BaseModel):
    card_id: str
    duration_seconds: int = Field(120, ge=30, le=300)  # 30 seconds to 5 minutes
    max_participants: int = Field(10, ge=2, le=20)

class ExpressRoomJoin(BaseModel):
    code: str = Field(..., min_length=2, max_length=2)
    card_id: str
    
    @field_validator('code', mode='before')
    @classmethod
    def validate_room_code(cls, v):
        if not v:
            raise ValueError('Express Room Code ist erforderlich')
        
        # Ensure it's a 2-digit number
        code = str(v).strip()
        if not re.match(r'^\d{2}$', code):
            raise ValueError('Express Room Code muss eine 2-stellige Zahl sein')
        
        return code

class ExpressCodeResponse(BaseModel):
    id: str
    code: str
    created_at: datetime
    expires_at: datetime
    time_remaining_seconds: int
    usage_count: int
    max_usage: Optional[int]
    is_active: bool
    card_name: str
    card_company: Optional[str]

class ExpressRoomResponse(BaseModel):
    id: str
    code: str
    created_by_card_name: str
    created_at: datetime
    expires_at: datetime
    time_remaining_seconds: int
    participant_count: int
    max_participants: int
    can_join: bool
    participants: List[dict] = []  # Basic card info for each participant

class ExpressAccessResponse(BaseModel):
    success: bool
    message: str
    card: Optional[dict] = None
    express_code: Optional[ExpressCodeResponse] = None