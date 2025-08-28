from pydantic import BaseModel, Field, validator
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

class MeetingRoomParticipant(BaseModel):
    user_id: Optional[str] = None  # None for anonymous participants
    card_id: str
    card_name: str
    card_company: Optional[str] = None
    card_profile_image: Optional[str] = None
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    
class MeetingRoom(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    code: str = Field(..., min_length=3, max_length=10)
    created_by_user_id: Optional[str] = None  # None for anonymous creation
    created_by_card_id: str  # The card that created the room
    created_by_card_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))
    participants: List[MeetingRoomParticipant] = []
    max_participants: int = 20
    is_active: bool = True
    description: Optional[str] = Field(None, max_length=200)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
    
    @validator('code', pre=True)
    def validate_meeting_code(cls, v):
        if not v:
            return v
        
        # Ensure v is a string
        if not isinstance(v, str):
            v = str(v)
        
        # Convert to uppercase and remove spaces
        code = v.replace(' ', '').upper()
        
        # Check if code contains only letters and numbers
        if not re.match(r'^[A-Z0-9]+$', code):
            raise ValueError('Meeting Code darf nur Buchstaben und Zahlen enthalten')
        
        # Must be between 3-10 characters for meeting rooms (shorter for easier sharing)
        if len(code) < 3 or len(code) > 10:
            raise ValueError('Meeting Code muss zwischen 3 und 10 Zeichen lang sein')
        
        return code
    
    @classmethod
    def generate_random_code(cls, length: int = 5) -> str:
        """Generate a random meeting room code"""
        characters = string.ascii_uppercase + string.digits
        # Exclude confusing characters
        characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1')
        return ''.join(random.choice(characters) for _ in range(length))
    
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
    
    def add_participant(self, participant: MeetingRoomParticipant) -> bool:
        """Add a participant to the meeting room"""
        if not self.can_join():
            return False
        
        # Check if participant already exists (by card_id)
        for existing in self.participants:
            if existing.card_id == participant.card_id:
                return False  # Already in room
        
        self.participants.append(participant)
        return True
    
    def remove_participant(self, card_id: str) -> bool:
        """Remove a participant from the meeting room"""
        for i, participant in enumerate(self.participants):
            if participant.card_id == card_id:
                self.participants.pop(i)
                return True
        return False

class MeetingRoomCreate(BaseModel):
    card_id: str
    code: Optional[str] = None  # If None, will be auto-generated
    description: Optional[str] = Field(None, max_length=200)
    duration_minutes: int = Field(10, ge=5, le=60)  # 5-60 minutes
    max_participants: int = Field(20, ge=2, le=50)

class MeetingRoomJoin(BaseModel):
    code: str = Field(..., min_length=3, max_length=10)
    card_id: str
    
    @validator('code', pre=True)
    def validate_and_clean_code(cls, v):
        if not v:
            raise ValueError('Meeting Code ist erforderlich')
        
        # Remove spaces and convert to uppercase
        code = v.replace(' ', '').upper()
        
        # Check if code contains only letters and numbers
        if not re.match(r'^[A-Z0-9]+$', code):
            raise ValueError('Meeting Code darf nur Buchstaben und Zahlen enthalten')
        
        return code

class MeetingRoomResponse(BaseModel):
    id: str
    code: str
    created_by_card_name: str
    created_at: datetime
    expires_at: datetime
    participants: List[MeetingRoomParticipant]
    max_participants: int
    is_active: bool
    description: Optional[str]
    time_remaining_minutes: int
    can_join: bool
    is_creator: bool = False
    
class MeetingRoomListResponse(BaseModel):
    id: str
    code: str
    created_by_card_name: str
    created_at: datetime
    expires_at: datetime
    participant_count: int
    max_participants: int
    description: Optional[str]
    time_remaining_minutes: int
    is_creator: bool = False

class MeetingRoomJoinResponse(BaseModel):
    success: bool
    message: str
    room: Optional[MeetingRoomResponse] = None
    cards_received: List[dict] = []