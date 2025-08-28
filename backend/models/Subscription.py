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

class PlanType(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"

class PlanLimits(BaseModel):
    # Core Features (very generous for free users)
    max_business_cards: int = 999  # Unlimited for free
    max_custom_codes: int = 999  # Unlimited for free
    express_share_enabled: bool = True  # Free feature
    meeting_rooms_enabled: bool = True  # Free feature
    max_meeting_participants: int = 15  # 15 free, 50+ premium
    meeting_room_duration_minutes: int = 15  # 15min free, 60min+ premium
    
    # Contact Import (generous limits)
    monthly_contact_imports: int = 500  # 500/month free, unlimited premium
    google_contacts_sync: bool = False  # Premium only
    apple_icloud_sync: bool = False  # Premium only
    auto_contact_sync: bool = False  # Premium only
    
    # Messaging Apps (all free for growth)
    whatsapp_enabled: bool = True  # Free
    telegram_enabled: bool = True  # Free
    viber_enabled: bool = True  # Free
    signal_enabled: bool = True  # Free
    discord_enabled: bool = True  # Free
    
    # Analytics & Insights (main premium differentiator)
    basic_analytics: bool = True  # Free - basic usage stats
    detailed_analytics: bool = False  # Premium - who used codes when
    contact_insights: bool = False  # Premium - contact behavior
    export_analytics: bool = False  # Premium - CSV export
    
    # Customization (minimal premium features)
    custom_branding: bool = False  # Premium - remove "Made with App" 
    custom_themes: int = 10  # 10 free themes, unlimited premium
    custom_colors: bool = True  # Free
    custom_fonts: bool = False  # Premium
    
    # Support & Features
    priority_support: bool = False  # Premium only
    api_access: bool = False  # Premium/Enterprise only
    white_label: bool = False  # Enterprise only
    team_management: bool = False  # Premium+ (5+ users)

class UserSubscription(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    plan_type: PlanType = PlanType.FREE
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    
    # Plan details
    plan_name: str = "Free Plan"
    plan_limits: PlanLimits = Field(default_factory=PlanLimits)
    
    # Subscription lifecycle
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # None = no expiry (free plan)
    trial_ends_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Payment integration (prepared for later)
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    
    # Usage tracking (for analytics and upgrade prompts)
    monthly_usage: Dict[str, int] = {
        "business_cards_created": 0,
        "custom_codes_used": 0,
        "meeting_rooms_created": 0,
        "contacts_imported": 0,
        "express_codes_generated": 0,
        "analytics_views": 0
    }
    
    # Feature usage history (for intelligent upgrade suggestions)
    feature_usage_history: List[Dict[str, Any]] = []
    
    # Upgrade prompts tracking
    upgrade_prompts_shown: int = 0
    upgrade_prompts_dismissed: int = 0
    last_upgrade_prompt: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Pre-defined plan configurations
PLAN_CONFIGS = {
    "free": PlanLimits(
        max_business_cards=999,  # Unlimited
        max_custom_codes=999,    # Unlimited
        express_share_enabled=True,
        meeting_rooms_enabled=True,
        max_meeting_participants=15,  # Generous free limit
        meeting_room_duration_minutes=15,
        monthly_contact_imports=500,  # Very generous
        google_contacts_sync=False,  # Premium feature
        apple_icloud_sync=False,     # Premium feature
        detailed_analytics=False,    # Premium feature
        contact_insights=False,      # Premium feature
        custom_branding=False,       # Premium feature
        priority_support=False,      # Premium feature
        api_access=False,           # Premium feature
        team_management=False       # Premium feature
    ),
    
    "premium": PlanLimits(
        max_business_cards=999,  # Unlimited
        max_custom_codes=999,    # Unlimited
        express_share_enabled=True,
        meeting_rooms_enabled=True,
        max_meeting_participants=50,  # Increased limit
        meeting_room_duration_minutes=60,  # 1 hour
        monthly_contact_imports=999999,  # Unlimited
        google_contacts_sync=True,   # Premium feature
        apple_icloud_sync=True,      # Premium feature
        auto_contact_sync=True,      # Premium feature
        detailed_analytics=True,     # Premium feature
        contact_insights=True,       # Premium feature
        export_analytics=True,       # Premium feature
        custom_branding=True,        # Remove branding
        custom_themes=999,          # Unlimited themes
        custom_fonts=True,          # Premium fonts
        priority_support=True,       # Priority support
        api_access=True,            # API access
        team_management=True        # Team features
    )
}

class UsageTrackingEvent(BaseModel):
    user_id: str
    event_type: str  # "business_card_created", "meeting_room_used", etc.
    event_data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    plan_type: PlanType
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UpgradePrompt(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    trigger_event: str  # "meeting_room_limit_reached", "analytics_viewed", etc.
    prompt_message: str
    suggested_plan: PlanType
    shown_at: datetime = Field(default_factory=datetime.utcnow)
    dismissed: bool = False
    converted: bool = False
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class SubscriptionResponse(BaseModel):
    user_id: str
    plan_type: str
    plan_name: str
    status: str
    limits: PlanLimits
    expires_at: Optional[datetime]
    trial_ends_at: Optional[datetime]
    usage: Dict[str, int]
    upgrade_available: bool = False
    upgrade_benefits: List[str] = []

class FeatureAccessRequest(BaseModel):
    feature_name: str  # "detailed_analytics", "google_sync", etc.
    user_id: str

class FeatureAccessResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    upgrade_required: bool = False
    suggested_plan: Optional[str] = None
    upgrade_benefits: List[str] = []