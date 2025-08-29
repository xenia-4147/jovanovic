"""
Video Meeting Models for Real-time Communication
Revolutionary Feature: Integrated Video Meetings with Business Cards
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid


class MeetingStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class ParticipantRole(str, Enum):
    HOST = "host"
    CO_HOST = "co_host"
    PARTICIPANT = "participant"
    OBSERVER = "observer"


class CallQuality(str, Enum):
    HD = "hd"          # 720p
    STANDARD = "standard"  # 480p
    LOW = "low"        # 360p
    AUDIO_ONLY = "audio_only"


class MeetingType(str, Enum):
    ONE_ON_ONE = "one_on_one"
    GROUP = "group"
    COMMUNITY = "community"
    JOB_INTERVIEW = "job_interview"
    NETWORKING_EVENT = "networking_event"


class VideoMeetingRoom(BaseModel):
    """Enhanced video meeting room with business card integration"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic meeting info
    title: str = Field(..., description="Meeting room title")
    description: Optional[str] = Field(None, description="Meeting description")
    meeting_type: MeetingType = Field(default=MeetingType.GROUP)
    
    # Host information
    host_id: str = Field(..., description="Meeting host user ID")
    host_business_card_id: Optional[str] = Field(None, description="Host's business card for sharing")
    
    # Meeting configuration
    max_participants: int = Field(default=10, description="Maximum number of participants")
    duration_minutes: int = Field(default=45, description="Meeting duration (45min free, unlimited premium)")
    quality: CallQuality = Field(default=CallQuality.STANDARD)
    
    # Meeting access
    meeting_code: Optional[str] = Field(None, description="6-digit meeting code")
    password: Optional[str] = Field(None, description="Optional meeting password")
    is_public: bool = Field(default=False, description="Whether meeting is publicly discoverable")
    
    # Business card sharing
    shared_business_cards: List[str] = Field(default_factory=list, description="Business cards shared in meeting")
    allow_card_sharing: bool = Field(default=True, description="Allow participants to share business cards")
    
    # Community integration
    community_tags: List[str] = Field(default_factory=list, description="Community interest tags")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    
    # Job/Recruiting features
    is_job_related: bool = Field(default=False, description="Whether this is job/recruiting related")
    job_title: Optional[str] = Field(None, description="Job title if recruiting meeting")
    company_name: Optional[str] = Field(None, description="Company name if recruiting")
    
    # NEW: Meeting Link & Sharing Features
    share_link: Optional[str] = Field(None, description="Shareable meeting link")
    qr_code_url: Optional[str] = Field(None, description="QR code URL for easy joining")
    
    # NEW: Live Translation Features
    translation_enabled: bool = Field(default=False, description="Enable live translation")
    source_language: str = Field(default="auto", description="Auto-detect or specific language")
    target_languages: List[str] = Field(default_factory=list, description="Languages to translate to")
    translation_participants: Dict[str, str] = Field(default_factory=dict, description="participant_id -> preferred_language")
    
    # Meeting status
    status: MeetingStatus = Field(default=MeetingStatus.WAITING)
    started_at: Optional[datetime] = Field(None)
    ended_at: Optional[datetime] = Field(None)
    
    # Technical settings
    enable_recording: bool = Field(default=False, description="Enable meeting recording (premium)")
    enable_screen_share: bool = Field(default=True)
    enable_chat: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled meeting time")
    
    @field_validator('max_participants')
    @classmethod
    def validate_max_participants(cls, v):
        if v < 2 or v > 100:
            raise ValueError('Max participants must be between 2 and 100')
        return v
    
    @field_validator('duration_minutes')
    @classmethod
    def validate_duration(cls, v):
        if v < 5 or v > 1440:  # 5 minutes to 24 hours
            raise ValueError('Duration must be between 5 minutes and 24 hours')
        return v


class MeetingParticipant(BaseModel):
    """Meeting participant with business card integration"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    meeting_id: str = Field(..., description="Meeting room ID")
    user_id: str = Field(..., description="Participant user ID")
    
    # Participant info
    display_name: str = Field(..., description="Display name in meeting")
    business_card_id: Optional[str] = Field(None, description="Participant's business card")
    
    # Role and permissions
    role: ParticipantRole = Field(default=ParticipantRole.PARTICIPANT)
    can_share_screen: bool = Field(default=False)
    can_share_cards: bool = Field(default=True)
    is_muted: bool = Field(default=False)
    
    # Connection info
    socket_id: Optional[str] = Field(None, description="WebSocket connection ID")
    peer_id: Optional[str] = Field(None, description="WebRTC peer ID")
    connection_quality: CallQuality = Field(default=CallQuality.STANDARD)
    
    # Timestamps
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    left_at: Optional[datetime] = Field(None)
    
    # Interaction tracking
    shared_business_cards: List[str] = Field(default_factory=list, description="Cards shared by this participant")
    received_business_cards: List[str] = Field(default_factory=list, description="Cards received by this participant")


class BusinessCardShare(BaseModel):
    """Business card sharing within video meetings"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    meeting_id: str = Field(..., description="Meeting where card was shared")
    
    # Sharing info
    sender_id: str = Field(..., description="User who shared the card")
    business_card_id: str = Field(..., description="Business card that was shared")
    
    # Recipients
    recipient_ids: List[str] = Field(default_factory=list, description="Specific recipients (empty = all participants)")
    
    # Sharing context
    sharing_message: Optional[str] = Field(None, description="Message attached to card share")
    shared_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Interaction tracking
    viewed_by: List[str] = Field(default_factory=list, description="Users who viewed the shared card")
    saved_by: List[str] = Field(default_factory=list, description="Users who saved the shared card")


class CommunityMeeting(BaseModel):
    """Community-based meeting for interest matching"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Community info
    community_name: str = Field(..., description="Community name (e.g., 'Veganer München')")
    interest_tags: List[str] = Field(..., description="Interest tags for matching")
    location: Optional[str] = Field(None, description="Location for local communities")
    
    # Meeting details
    video_meeting_id: str = Field(..., description="Associated video meeting room")
    organizer_id: str = Field(..., description="Community organizer user ID")
    
    # Community features
    is_recurring: bool = Field(default=False, description="Whether this is a recurring meeting")
    recurrence_pattern: Optional[str] = Field(None, description="Recurrence pattern (weekly, monthly)")
    
    # Discovery and matching
    auto_match_participants: bool = Field(default=True, description="Automatically invite matching users")
    min_participants: int = Field(default=3)
    max_participants: int = Field(default=20)
    
    # Business networking
    networking_focus: Optional[str] = Field(None, description="Business networking focus")
    skill_sharing: bool = Field(default=True, description="Enable skill sharing features")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobMeeting(BaseModel):
    """Job interview and recruiting meeting"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Job details
    job_title: str = Field(..., description="Job position title")
    company_name: str = Field(..., description="Hiring company name")
    job_type: str = Field(..., description="Job type (full-time, part-time, freelance, etc.)")
    
    # Meeting info
    video_meeting_id: str = Field(..., description="Associated video meeting room")
    interviewer_id: str = Field(..., description="Interviewer/HR user ID")
    candidate_id: Optional[str] = Field(None, description="Candidate user ID (if scheduled)")
    
    # Interview features
    interview_stage: str = Field(default="initial", description="Interview stage")
    expected_duration: int = Field(default=30, description="Expected interview duration")
    
    # Business card exchange
    exchange_cards_after: bool = Field(default=True, description="Exchange business cards after interview")
    
    # Evaluation (premium feature)
    enable_notes: bool = Field(default=False, description="Enable interviewer notes")
    evaluation_criteria: List[str] = Field(default_factory=list, description="Evaluation criteria")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = Field(None)


# Request/Response Models

class CreateMeetingRequest(BaseModel):
    """Request to create a new video meeting"""
    title: str = Field(..., description="Meeting title")
    description: Optional[str] = Field(None)
    meeting_type: MeetingType = Field(default=MeetingType.GROUP)
    
    # Configuration
    max_participants: int = Field(default=10, ge=2, le=100)
    duration_minutes: int = Field(default=45, ge=5, le=1440)
    password: Optional[str] = Field(None)
    
    # Business card integration
    share_host_card: bool = Field(default=True, description="Share host's business card")
    allow_card_sharing: bool = Field(default=True)
    
    # Community features
    community_tags: List[str] = Field(default_factory=list)
    is_public: bool = Field(default=False)
    
    # Job features
    is_job_related: bool = Field(default=False)
    job_title: Optional[str] = Field(None)
    company_name: Optional[str] = Field(None)
    
    # Scheduling
    scheduled_for: Optional[datetime] = Field(None)
    
    # NEW: Translation Features
    translation_enabled: Optional[bool] = Field(False, description="Enable live translation")
    source_language: Optional[str] = Field("auto", description="Source language")
    target_languages: Optional[List[str]] = Field([], description="Target languages for translation")


class JoinMeetingRequest(BaseModel):
    """Request to join a video meeting"""
    meeting_code: str = Field(..., description="6-digit meeting code or meeting ID")
    password: Optional[str] = Field(None)
    display_name: str = Field(..., description="Display name in meeting")
    share_business_card: bool = Field(default=True, description="Whether to share business card")


class ShareBusinessCardRequest(BaseModel):
    """Request to share business card in meeting"""
    meeting_id: str = Field(..., description="Meeting ID")
    business_card_id: str = Field(..., description="Business card to share")
    recipient_ids: List[str] = Field(default_factory=list, description="Specific recipients (empty = all)")
    message: Optional[str] = Field(None, description="Message to attach")


# Response Models

class MeetingResponse(BaseModel):
    """Video meeting response"""
    meeting: VideoMeetingRoom = Field(..., description="Meeting room details")
    participants: List[MeetingParticipant] = Field(default_factory=list, description="Current participants")
    shared_cards: List[BusinessCardShare] = Field(default_factory=list, description="Shared business cards")
    
    # Join info
    join_url: Optional[str] = Field(None, description="Meeting join URL")
    webrtc_config: Optional[Dict[str, Any]] = Field(None, description="WebRTC configuration")
    
    # NEW: Enhanced Meeting Link Features
    share_link: Optional[str] = None
    qr_code_url: Optional[str] = None
    meeting_link_card: Optional[Dict[str, Any]] = None


class MeetingListResponse(BaseModel):
    """List of meetings"""
    meetings: List[VideoMeetingRoom] = Field(..., description="Meeting rooms")
    community_meetings: List[CommunityMeeting] = Field(default_factory=list, description="Community meetings")
    job_meetings: List[JobMeeting] = Field(default_factory=list, description="Job interview meetings")
    total_count: int = Field(..., description="Total number of meetings")


class MeetingJoinResponse(BaseModel):
    """Response when joining a meeting"""
    success: bool = Field(..., description="Whether join was successful")
    meeting: Optional[VideoMeetingRoom] = Field(None, description="Meeting room details")
    participant: Optional[MeetingParticipant] = Field(None, description="Participant info")
    webrtc_config: Dict[str, Any] = Field(..., description="WebRTC connection configuration")
    ice_servers: List[Dict[str, Any]] = Field(..., description="STUN/TURN servers")
    message: str = Field(..., description="Join status message")


# WebRTC Configuration
DEFAULT_ICE_SERVERS = [
    # High-quality STUN servers for NAT traversal
    {
        "urls": [
            "stun:stun.l.google.com:19302", 
            "stun:stun1.l.google.com:19302",
            "stun:stun2.l.google.com:19302",
            "stun:stun3.l.google.com:19302"
        ]
    },
    # Professional TURN servers for enterprise connectivity
    {
        "urls": ["turn:openrelay.metered.ca:80"],
        "username": "openrelayproject", 
        "credential": "openrelayproject"
    },
    {
        "urls": ["turn:openrelay.metered.ca:443"],
        "username": "openrelayproject", 
        "credential": "openrelayproject"
    },
    # Backup TURN server for reliability
    {
        "urls": ["turn:turn.bistri.com:80"],
        "username": "homeo",
        "credential": "homeo"
    }
]

WEBRTC_CONFIG = {
    "iceServers": DEFAULT_ICE_SERVERS,
    "iceCandidatePoolSize": 10,
    "bundlePolicy": "balanced",
    "rtcpMuxPolicy": "require"
}

# Meeting Limits Based on User Tier
MEETING_LIMITS = {
    "free": {
        "max_duration_minutes": 45,  # Generous 45 minutes (better than Zoom's 40min!)
        "max_participants": 10,
        "max_meetings_per_day": 10,
        "recording_enabled": False,
        "screen_share_enabled": True,
        "business_card_sharing": True
    },
    "premium": {
        "max_duration_minutes": 1440,  # 24 hours
        "max_participants": 100,
        "max_meetings_per_day": 999,
        "recording_enabled": True,
        "screen_share_enabled": True,
        "business_card_sharing": True,
        "custom_backgrounds": True,
        "meeting_analytics": True
    },
    "early_adopter": {
        "max_duration_minutes": 1440,  # Unlimited like premium
        "max_participants": 100,
        "max_meetings_per_day": 999,
        "recording_enabled": True,
        "screen_share_enabled": True,
        "business_card_sharing": True,
        "custom_backgrounds": True,
        "meeting_analytics": True,
        "priority_support": True
    }
}