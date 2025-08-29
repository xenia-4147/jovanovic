"""
Community & Networking Models for Interest-Based Matching
Revolutionary Feature: LinkedIn + Meetup + Industry Matching in One Platform
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta
from enum import Enum
import uuid


class CommunityType(str, Enum):
    BUSINESS = "business"
    HOBBY = "hobby"
    PROFESSIONAL = "professional"
    INDUSTRY = "industry"
    LOCAL = "local"
    SKILL_BASED = "skill_based"
    JOB_FOCUSED = "job_focused"


class MatchingCriteria(str, Enum):
    INTERESTS = "interests"
    LOCATION = "location"
    INDUSTRY = "industry"
    SKILLS = "skills"
    JOB_LEVEL = "job_level"
    COMPANY_SIZE = "company_size"


class EventType(str, Enum):
    NETWORKING = "networking"
    SKILL_SHARING = "skill_sharing"
    JOB_FAIR = "job_fair"
    BUSINESS_MEETUP = "business_meetup"
    WORKSHOP = "workshop"
    CONFERENCE = "conference"
    CASUAL_MEETUP = "casual_meetup"


class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    FREELANCE = "freelance"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    VOLUNTEER = "volunteer"


class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class UserProfile(BaseModel):
    """Enhanced user profile for community matching"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    
    # Basic info
    display_name: str = Field(..., description="Public display name")
    bio: Optional[str] = Field(None, description="Short bio/description")
    location: Optional[str] = Field(None, description="City, Country")
    
    # Interest-based matching
    interests: List[str] = Field(default_factory=list, description="User interests (Veganer, Kieferholz, etc.)")
    industry: Optional[str] = Field(None, description="Industry (Tech, Healthcare, etc.)")
    skills: List[str] = Field(default_factory=list, description="Professional skills")
    
    # Professional info
    current_position: Optional[str] = Field(None, description="Current job title")
    current_company: Optional[str] = Field(None, description="Current company")
    experience_level: Optional[ExperienceLevel] = Field(None)
    
    # Job preferences (for job matching)
    looking_for_job: bool = Field(default=False)
    job_preferences: Optional[Dict[str, Any]] = Field(None, description="Job search preferences")
    
    # Recruiter info
    is_recruiter: bool = Field(default=False)
    recruiting_for_companies: List[str] = Field(default_factory=list)
    
    # Community preferences
    preferred_meeting_types: List[EventType] = Field(default_factory=list)
    max_distance_km: Optional[int] = Field(default=50, description="Max distance for local events")
    
    # Privacy settings
    public_profile: bool = Field(default=True)
    show_contact_info: bool = Field(default=False)
    discoverable: bool = Field(default=True)
    
    # Activity tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v):
        # Normalize interest tags
        return [interest.lower().strip() for interest in v if interest.strip()]


class Community(BaseModel):
    """Community/Group for interest-based networking"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Community info
    name: str = Field(..., description="Community name (e.g., 'Veganer München')")
    description: Optional[str] = Field(None, description="Community description")
    community_type: CommunityType = Field(..., description="Type of community")
    
    # Matching criteria
    primary_interests: List[str] = Field(..., description="Main interest tags")
    location: Optional[str] = Field(None, description="Geographic focus")
    industry_focus: Optional[str] = Field(None, description="Industry focus if business")
    
    # Community settings
    is_public: bool = Field(default=True, description="Public or invitation-only")
    auto_approve_members: bool = Field(default=True)
    max_members: Optional[int] = Field(default=None, description="Maximum number of members")
    
    # Leadership
    creator_id: str = Field(..., description="Community creator")
    moderators: List[str] = Field(default_factory=list, description="Community moderators")
    
    # Activity
    member_count: int = Field(default=0)
    meeting_count: int = Field(default=0, description="Number of meetings organized")
    
    # Meeting configuration
    default_meeting_duration: int = Field(default=60, description="Default meeting duration in minutes")
    allow_member_meetings: bool = Field(default=True, description="Allow members to create meetings")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)


class CommunityMembership(BaseModel):
    """User membership in communities"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    community_id: str = Field(..., description="Community ID")
    user_id: str = Field(..., description="User ID")
    
    # Membership info
    role: str = Field(default="member", description="Member role (member, moderator, admin)")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Engagement tracking
    meetings_attended: int = Field(default=0)
    cards_shared: int = Field(default=0)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    
    # Preferences
    notifications_enabled: bool = Field(default=True)
    auto_join_meetings: bool = Field(default=False)


class NetworkingEvent(BaseModel):
    """Networking event with video meeting integration"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Event info
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None)
    event_type: EventType = Field(..., description="Type of networking event")
    
    # Organization
    organizer_id: str = Field(..., description="Event organizer")
    community_id: Optional[str] = Field(None, description="Associated community")
    
    # Meeting integration
    video_meeting_id: Optional[str] = Field(None, description="Associated video meeting")
    
    # Event details
    scheduled_start: datetime = Field(..., description="Event start time")
    duration_minutes: int = Field(default=90, description="Event duration")
    max_attendees: Optional[int] = Field(None)
    
    # Networking features
    enable_breakout_rooms: bool = Field(default=False, description="Enable smaller networking groups")
    automatic_introductions: bool = Field(default=True, description="Auto-introduce participants")
    business_card_exchange: bool = Field(default=True)
    
    # Target audience
    target_interests: List[str] = Field(default_factory=list)
    target_location: Optional[str] = Field(None)
    target_experience_level: Optional[List[ExperienceLevel]] = Field(None)
    
    # Event status
    status: str = Field(default="planned", description="Event status")
    attendee_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobOpportunity(BaseModel):
    """Job posting integrated with networking"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Job details
    title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Hiring company")
    description: str = Field(..., description="Job description")
    
    # Job specifics
    job_type: JobType = Field(..., description="Employment type")
    experience_level: ExperienceLevel = Field(..., description="Required experience level")
    location: Optional[str] = Field(None, description="Job location")
    remote_allowed: bool = Field(default=False)
    
    # Requirements
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    industry: Optional[str] = Field(None)
    
    # Compensation (optional)
    salary_min: Optional[int] = Field(None, description="Minimum salary")
    salary_max: Optional[int] = Field(None, description="Maximum salary")
    currency: str = Field(default="EUR")
    
    # Posting info
    posted_by: str = Field(..., description="User ID who posted")
    company_business_card_id: Optional[str] = Field(None, description="Company business card")
    
    # Application process
    enable_video_interviews: bool = Field(default=True, description="Allow video interview scheduling")
    auto_schedule_interviews: bool = Field(default=False)
    
    # Status
    is_active: bool = Field(default=True)
    applications_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None)


class JobApplication(BaseModel):
    """Job application with video interview integration"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    job_id: str = Field(..., description="Job opportunity ID")
    applicant_id: str = Field(..., description="Applicant user ID")
    
    # Application details
    cover_message: Optional[str] = Field(None, description="Cover letter/message")
    applicant_business_card_id: Optional[str] = Field(None, description="Applicant's business card")
    
    # Interview scheduling
    interview_requested: bool = Field(default=False)
    interview_meeting_id: Optional[str] = Field(None, description="Scheduled video interview")
    interview_scheduled_for: Optional[datetime] = Field(None)
    
    # Application status
    status: str = Field(default="pending", description="Application status")
    reviewed_at: Optional[datetime] = Field(None)
    
    applied_at: datetime = Field(default_factory=datetime.utcnow)


class MatchingAlgorithm(BaseModel):
    """Smart matching algorithm configuration"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Matching weights
    interest_weight: float = Field(default=0.4, description="Weight for interest matching")
    location_weight: float = Field(default=0.2, description="Weight for location proximity")
    industry_weight: float = Field(default=0.2, description="Weight for industry match")
    skill_weight: float = Field(default=0.1, description="Weight for skill overlap")
    experience_weight: float = Field(default=0.1, description="Weight for experience level")
    
    # Matching thresholds
    min_match_score: float = Field(default=0.3, description="Minimum score for a match")
    max_distance_km: int = Field(default=50, description="Maximum distance for local matching")
    
    # Algorithm settings
    enable_ai_matching: bool = Field(default=True, description="Use AI for advanced matching")
    learning_enabled: bool = Field(default=True, description="Learn from user interactions")


# Request/Response Models

class CreateCommunityRequest(BaseModel):
    """Request to create a new community"""
    name: str = Field(..., description="Community name")
    description: Optional[str] = Field(None)
    community_type: CommunityType = Field(..., description="Community type")
    
    primary_interests: List[str] = Field(..., description="Main interest tags")
    location: Optional[str] = Field(None)
    industry_focus: Optional[str] = Field(None)
    
    is_public: bool = Field(default=True)
    max_members: Optional[int] = Field(None)


class JoinCommunityRequest(BaseModel):
    """Request to join a community"""
    community_id: str = Field(..., description="Community to join")
    introduction_message: Optional[str] = Field(None, description="Introduction message")


class CreateEventRequest(BaseModel):
    """Request to create networking event"""
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None)
    event_type: EventType = Field(..., description="Event type")
    
    scheduled_start: datetime = Field(..., description="Event start time")
    duration_minutes: int = Field(default=90, ge=15, le=480)
    
    community_id: Optional[str] = Field(None, description="Associated community")
    max_attendees: Optional[int] = Field(None)
    
    target_interests: List[str] = Field(default_factory=list)
    enable_video_meeting: bool = Field(default=True)


class PostJobRequest(BaseModel):
    """Request to post a job opportunity"""
    title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    
    job_type: JobType = Field(..., description="Employment type")
    experience_level: ExperienceLevel = Field(..., description="Required experience")
    
    location: Optional[str] = Field(None)
    remote_allowed: bool = Field(default=False)
    
    required_skills: List[str] = Field(default_factory=list)
    salary_min: Optional[int] = Field(None)
    salary_max: Optional[int] = Field(None)


class UpdateProfileRequest(BaseModel):
    """Request to update user profile"""
    display_name: Optional[str] = Field(None)
    bio: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    
    interests: Optional[List[str]] = Field(None)
    industry: Optional[str] = Field(None)
    skills: Optional[List[str]] = Field(None)
    
    current_position: Optional[str] = Field(None)
    current_company: Optional[str] = Field(None)
    experience_level: Optional[ExperienceLevel] = Field(None)
    
    looking_for_job: Optional[bool] = Field(None)
    is_recruiter: Optional[bool] = Field(None)


# Response Models

class CommunityMatchResponse(BaseModel):
    """Response with matching communities"""
    communities: List[Community] = Field(..., description="Matching communities")
    recommended_interests: List[str] = Field(default_factory=list, description="Suggested interests")
    total_matches: int = Field(..., description="Total number of matches")


class UserMatchResponse(BaseModel):
    """Response with matching users"""
    users: List[Dict[str, Any]] = Field(..., description="Matching user profiles")
    match_reasons: List[str] = Field(default_factory=list, description="Why these users matched")
    total_matches: int = Field(..., description="Total number of matches")


class NetworkingFeedResponse(BaseModel):
    """Networking feed with opportunities"""
    events: List[NetworkingEvent] = Field(default_factory=list, description="Upcoming events")
    job_opportunities: List[JobOpportunity] = Field(default_factory=list, description="Job matches")
    community_suggestions: List[Community] = Field(default_factory=list, description="Suggested communities")
    user_matches: List[Dict[str, Any]] = Field(default_factory=list, description="User matches")


class CommunityListResponse(BaseModel):
    """List of communities"""
    communities: List[Community] = Field(..., description="Communities")
    my_communities: List[Community] = Field(default_factory=list, description="User's communities")
    suggested_communities: List[Community] = Field(default_factory=list, description="Suggested communities")
    total_count: int = Field(..., description="Total communities")


# Pre-defined Interest Categories for Auto-suggestions

INTEREST_CATEGORIES = {
    "Business & Entrepreneurship": [
        "startup", "entrepreneur", "business development", "sales", "marketing", 
        "fintech", "e-commerce", "consulting", "networking", "investor"
    ],
    "Technology": [
        "software development", "ai", "machine learning", "blockchain", "cybersecurity",
        "data science", "web development", "mobile apps", "cloud computing", "devops"
    ],
    "Creative & Design": [
        "graphic design", "ui/ux", "photography", "video production", "content creation",
        "branding", "advertising", "web design", "illustration", "animation"
    ],
    "Health & Wellness": [
        "fitness", "nutrition", "mental health", "yoga", "meditation", "healthcare",
        "wellness coaching", "alternative medicine", "sports", "mindfulness"
    ],
    "Environment & Sustainability": [
        "sustainability", "renewable energy", "environmental protection", "organic farming",
        "green technology", "climate change", "recycling", "eco-friendly", "conservation"
    ],
    "Food & Lifestyle": [
        "vegan", "vegetarian", "organic food", "cooking", "food photography", 
        "restaurant", "catering", "wine", "coffee", "healthy eating"
    ],
    "Crafts & Traditional Skills": [
        "woodworking", "kieferholz", "handwerk", "traditional crafts", "furniture making",
        "restoration", "artisan", "blacksmithing", "pottery", "textile"
    ],
    "Agriculture & Farming": [
        "organic farming", "permaculture", "seed saving", "alte saatgut sorten", 
        "sustainable agriculture", "livestock", "beekeeping", "gardening", "farming"
    ]
}

INDUSTRY_CATEGORIES = [
    "Technology", "Healthcare", "Finance", "Education", "Manufacturing",
    "Retail", "Real Estate", "Consulting", "Media & Entertainment", 
    "Transportation", "Energy", "Agriculture", "Construction", "Legal",
    "Marketing & Advertising", "Food & Beverage", "Fashion", "Travel & Tourism"
]