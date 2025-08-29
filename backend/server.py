from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import logging
import qrcode
import io
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Dict, Dict
import uuid

# Import our models and services
from models.User import User, UserCreate, UserLogin, UserResponse, UserUpdate, PasswordChange, GDPRExport, AccountDeletion
from models.BusinessCard import BusinessCard, BusinessCardCreate, BusinessCardUpdate, BusinessCardResponse, ContactPhone, ContactEmail, SocialMedia, CardRecipient, CardAnalytics, ShareRequest, EmbedOptions
from models.MeetingRoom import MeetingRoom, MeetingRoomCreate, MeetingRoomJoin, MeetingRoomResponse, MeetingRoomListResponse, MeetingRoomJoinResponse, MeetingRoomParticipant
from models.ExpressShare import ExpressCode, ExpressMeetingRoom, ExpressShareCreate, ExpressRoomCreate, ExpressRoomJoin, ExpressCodeResponse, ExpressRoomResponse, ExpressAccessResponse
from models.ContactImport import ContactSource, ImportedContact, SyncJob, ContactImportRequest, ContactImportResponse, ContactSourceResponse, UnifiedContact, ContactSourceType, SyncStatus
from models.Subscription import UserSubscription, PlanLimits, PlanType, SubscriptionStatus, SubscriptionResponse, FeatureAccessRequest, FeatureAccessResponse, UsageTrackingEvent, UpgradePrompt, PLAN_CONFIGS
from auth import get_current_user, get_optional_user, create_access_token, create_refresh_token, AuthService
from privacy import PrivacyService, scheduled_privacy_cleanup

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'digitalcards')]

# Create the main app
app = FastAPI(
    title="Digital Business Cards API",
    description="GDPR-compliant digital business cards platform",
    version="1.0.0"
)

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure properly in production
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Configure properly in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
privacy_service = PrivacyService(db)
auth_service = AuthService()

# Health check endpoint
@api_router.get("/")
async def root():
    return {"message": "Digital Business Cards API", "version": "1.0.0", "status": "running"}

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate, request: Request):
    """Register new user with GDPR compliance"""
    try:
        # Create user
        user = await auth_service.create_user(db, user_data)
        
        # Create tokens
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        
        # Log registration for audit
        logger.info(f"New user registered: {user.email}")
        
        return {
            "message": "Registration successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name,
                privacy_settings=user.privacy_settings,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                email_verified=user.email_verified
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login", response_model=dict)
async def login(user_data: UserLogin):
    """Login user"""
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(db, user_data.email, user_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        await db.users.update_one(
            {"_id": user.id},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )
        
        # Create tokens
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        
        return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name,
                privacy_settings=user.privacy_settings,
                created_at=user.created_at,
                last_login_at=datetime.utcnow(),
                email_verified=user.email_verified
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        privacy_settings=current_user.privacy_settings,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
        email_verified=current_user.email_verified
    )

@api_router.put("/auth/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate, 
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    try:
        update_dict = {}
        
        if profile_data.first_name is not None:
            update_dict["first_name"] = profile_data.first_name
        if profile_data.last_name is not None:
            update_dict["last_name"] = profile_data.last_name
        if profile_data.privacy_settings is not None:
            update_dict["privacy_settings"] = profile_data.privacy_settings.dict()
        
        if update_dict:
            await db.users.update_one(
                {"_id": current_user.id},
                {"$set": update_dict}
            )
            
            # Refresh user data
            updated_user_data = await db.users.find_one({"_id": current_user.id})
            updated_user = User(**updated_user_data)
            
            return UserResponse(
                id=str(updated_user.id),
                email=updated_user.email,
                first_name=updated_user.first_name,
                last_name=updated_user.last_name,
                full_name=updated_user.full_name,
                privacy_settings=updated_user.privacy_settings,
                created_at=updated_user.created_at,
                last_login_at=updated_user.last_login_at,
                email_verified=updated_user.email_verified
            )
        
        return get_current_user_profile(current_user)
        
    except Exception as e:
        logger.error(f"Profile update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Profile update failed")

# ============================================================================
# BUSINESS CARDS ENDPOINTS
# ============================================================================

@api_router.post("/cards", response_model=BusinessCardResponse)
async def create_business_card(
    card_data: BusinessCardCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new business card"""
    try:
        # Track usage for analytics and upgrade prompts
        await track_feature_usage_internal(str(current_user.id), "business_card_created")
        
        # Create business card with string user ID
        card_dict = card_data.dict()
        
        # Ensure social_media is properly handled
        if card_dict.get('social_media') is None:
            card_dict['social_media'] = SocialMedia()
        
        # Handle custom_code - remove if None to avoid index conflicts
        if card_dict.get('custom_code') is None:
            card_dict.pop('custom_code', None)
        
        card = BusinessCard(
            user_id=str(current_user.id),
            **card_dict
        )
        
        # Insert into database
        card_dict = card.dict(by_alias=True, exclude={"id"})
        # Remove custom_code if it's None to avoid database index conflicts
        if card_dict.get('custom_code') is None:
            card_dict.pop('custom_code', None)
        result = await db.businesscards.insert_one(card_dict)
        card.id = str(result.inserted_id)
        
        logger.info(f"Business card created: {card.name} for user {current_user.email}")
        
        return BusinessCardResponse(
            id=str(card.id),
            **card.dict(exclude={"id", "user_id"}),
            is_owner=True
        )
        
    except Exception as e:
        logger.error(f"Card creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Card creation failed: {str(e)}")

@api_router.get("/cards", response_model=List[BusinessCardResponse])
async def get_user_cards(current_user: User = Depends(get_current_user)):
    """Get user's business cards"""
    try:
        # Use string user ID for query
        user_id_str = str(current_user.id)
        cards_cursor = db.businesscards.find({"userId": user_id_str})
        cards = []
        
        async for card_data in cards_cursor:
            # Convert ObjectId to string for compatibility
            if "_id" in card_data:
                card_data["_id"] = str(card_data["_id"])
            if "userId" in card_data:
                card_data["userId"] = str(card_data["userId"])
                
            card = BusinessCard(**card_data)
            cards.append(BusinessCardResponse(
                id=str(card.id),
                **card.dict(exclude={"id", "user_id"}),
                is_owner=True
            ))
        
        return cards
        
    except Exception as e:
        logger.error(f"Failed to fetch user cards: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch cards: {str(e)}")

@api_router.get("/cards/{card_id}", response_model=BusinessCardResponse)
async def get_business_card(
    card_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get specific business card (public or owned)"""
    try:
        # Find card - try both string and ObjectId
        from bson import ObjectId
        card_data = await db.businesscards.find_one({"_id": card_id})
        if not card_data:
            # Try with ObjectId conversion for backward compatibility
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Business card not found")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Check if user can view this card
        is_owner = current_user is not None and str(card.user_id) == str(current_user.id)
        can_view = is_owner or card.is_public
        
        if not can_view:
            raise HTTPException(status_code=403, detail="Card is private and you are not the owner")
        
        # Track analytics (in background)
        if not is_owner:  # Don't track owner views
            background_tasks.add_task(
                track_card_analytics, 
                card_id, 
                "view", 
                request
            )
        
        return BusinessCardResponse(
            id=str(card.id),
            **card.dict(exclude={"id", "user_id"}),
            is_owner=is_owner
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch card {card_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch card")

@api_router.put("/cards/{card_id}", response_model=BusinessCardResponse)
async def update_business_card(
    card_id: str,
    card_update: BusinessCardUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Update business card (owner only)"""
    try:
        # Find card - try both string and ObjectId
        from bson import ObjectId
        card_data = await db.businesscards.find_one({"_id": card_id})
        if not card_data:
            # Try with ObjectId conversion for backward compatibility
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Business card not found")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Check ownership
        if str(card.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update card
        update_dict = card_update.dict(exclude_unset=True)
        if update_dict:
            update_dict["last_updated"] = datetime.utcnow()
            
            # Use the actual stored card ID for update
            stored_card_id = card_data["_id"] if isinstance(card_data["_id"], str) else ObjectId(card_id)
            
            # Convert stored_card_id to ObjectId if it's a string for MongoDB
            if isinstance(stored_card_id, str):
                try:
                    mongo_id = ObjectId(stored_card_id)
                except:
                    mongo_id = stored_card_id
            else:
                mongo_id = stored_card_id
            
            await db.businesscards.update_one(
                {"_id": mongo_id},
                {"$set": update_dict}
            )
            
            # Send auto-update notifications (in background)
            if hasattr(card, 'auto_update_enabled') and card.auto_update_enabled:
                background_tasks.add_task(
                    send_auto_update_notifications,
                    str(stored_card_id),
                    list(update_dict.keys()) if update_dict else []
                )
        else:
            # No updates, just get the stored card ID for retrieval
            stored_card_id = card_data["_id"] if isinstance(card_data["_id"], str) else ObjectId(card_id)
        
        # Return updated card
        if isinstance(stored_card_id, str):
            try:
                mongo_id = ObjectId(stored_card_id)
            except:
                mongo_id = stored_card_id
        else:
            mongo_id = stored_card_id
            
        updated_card_data = await db.businesscards.find_one({"_id": mongo_id})
        
        # Convert ObjectId to string for compatibility
        if updated_card_data:
            if "_id" in updated_card_data:
                updated_card_data["_id"] = str(updated_card_data["_id"])
            if "userId" in updated_card_data:
                updated_card_data["userId"] = str(updated_card_data["userId"])
                
            updated_card = BusinessCard(**updated_card_data)
            
            logger.info(f"Card updated: {card_id} by user {current_user.email}")
            
            return BusinessCardResponse(
                id=str(updated_card.id),
                **updated_card.dict(exclude={"id", "user_id"}),
                is_owner=True
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated card")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Card update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Card update failed: {str(e)}")
        # Convert ObjectId to string for compatibility
        if "_id" in updated_card_data:
            updated_card_data["_id"] = str(updated_card_data["_id"])
        if "userId" in updated_card_data:
            updated_card_data["userId"] = str(updated_card_data["userId"])
        updated_card = BusinessCard(**updated_card_data)
        
        logger.info(f"Card updated: {card_id} by user {current_user.email}")
        
        return BusinessCardResponse(
            id=str(updated_card.id),
            **updated_card.dict(exclude={"id", "user_id"}),
            is_owner=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Card update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Card update failed")

# ============================================================================
# CODE ACCESS ENDPOINTS
# ============================================================================

@api_router.post("/cards/access-by-code", response_model=dict)
async def access_card_by_code(
    code_request: dict,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Access business card using custom code"""
    try:
        code = code_request.get("code", "").replace(" ", "").upper()
        
        if not code:
            raise HTTPException(status_code=400, detail="Code ist erforderlich")
        
        if len(code) < 3 or len(code) > 50:
            raise HTTPException(status_code=400, detail="Code muss zwischen 3 und 50 Zeichen lang sein")
        
        # Find card by custom code
        card_data = await db.businesscards.find_one({"custom_code": code})
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Code nicht gefunden")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Check if card is public or accessible
        if not card.is_public:
            raise HTTPException(status_code=403, detail="Diese Visitenkarte ist nicht öffentlich zugänglich")
        
        # Update code usage count
        await db.businesscards.update_one(
            {"_id": card_data["_id"]},
            {"$inc": {"code_usage_count": 1}}
        )
        
        # Track analytics (in background)
        background_tasks.add_task(
            track_card_analytics,
            str(card.id),
            "code_access",
            request,
            {"access_method": "code", "code_used": code}
        )
        
        # Get updated usage count
        updated_card_data = await db.businesscards.find_one({"_id": card_data["_id"]})
        usage_count = updated_card_data.get("code_usage_count", 1) if updated_card_data else 1
        
        logger.info(f"Code access successful: {code} -> Card {card.id} (Usage: {usage_count})")
        
        return {
            "success": True,
            "message": f"Visitenkarte von {card.name} gefunden",
            "card": BusinessCardResponse(
                id=str(card.id),
                **card.dict(exclude={"id", "user_id", "code_usage_count"}),
                code_usage_count=usage_count,
                is_owner=False
            ),
            "code_usage_count": usage_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code access failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Code-Zugriff fehlgeschlagen")

@api_router.get("/cards/check-code/{code}")
async def check_code_availability(code: str):
    """Check if a custom code is available"""
    try:
        # Clean and validate code
        clean_code = code.replace(" ", "").upper()
        
        if len(clean_code) < 3 or len(clean_code) > 50:
            return {"available": False, "message": "Code muss zwischen 3 und 50 Zeichen lang sein"}
        
        if not clean_code.replace('_', '').replace('-', '').isalnum():
            return {"available": False, "message": "Code darf nur Buchstaben, Zahlen, Unterstriche und Bindestriche enthalten"}
        
        # Check if code exists
        existing_card = await db.businesscards.find_one({"custom_code": clean_code})
        
        if existing_card:
            return {
                "available": False, 
                "message": "Dieser Code ist bereits vergeben",
                "suggestion": f"{clean_code}{len(clean_code) + 1}"
            }
        
        return {
            "available": True, 
            "message": "Code ist verfügbar",
            "code": clean_code
        }
        
    except Exception as e:
        logger.error(f"Code availability check failed: {str(e)}")
        return {"available": False, "message": "Fehler bei der Code-Prüfung"}

# ============================================================================
# ENHANCED UTILITY ENDPOINTS
# ============================================================================

@api_router.get("/cards/{card_id}/qr")
async def generate_qr_code(
    card_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    size: int = 200,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Generate QR code for business card"""
    try:
        # Verify card exists and is accessible - try both string and ObjectId
        from bson import ObjectId
        card_data = await db.businesscards.find_one({"_id": card_id})
        if not card_data:
            # Try with ObjectId conversion for backward compatibility
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Business card not found")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        is_owner = current_user is not None and str(card.user_id) == str(current_user.id)
        
        if not is_owner and not card.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Generate QR code
        card_url = f"{request.base_url}card/{card_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(card_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size))
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Track analytics
        if not is_owner:
            background_tasks.add_task(
                track_card_analytics,
                card_id,
                "qr_scan",
                request
            )
        
        return StreamingResponse(
            io.BytesIO(img_buffer.read()),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=qr-{card_id}.png"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QR code generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="QR code generation failed")

@api_router.get("/cards/{card_id}/vcard")
async def generate_vcard(
    card_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Generate vCard file for business card"""
    try:
        # Verify card exists and is accessible - try both string and ObjectId
        from bson import ObjectId
        card_data = await db.businesscards.find_one({"_id": card_id})
        if not card_data:
            # Try with ObjectId conversion for backward compatibility
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Business card not found")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        is_owner = current_user is not None and str(card.user_id) == str(current_user.id)
        
        if not is_owner and not card.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Generate vCard
        vcard_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{card.name}"""
        
        if card.company:
            vcard_content += f"\nORG:{card.company}"
        if card.position:
            vcard_content += f"\nTITLE:{card.position}"
        
        # Add phone numbers
        for phone in card.phones:
            if phone.number:
                vcard_content += f"\nTEL;TYPE={phone.label}:{phone.number}"
        
        # Add email addresses
        for email in card.emails:
            if email.address:
                vcard_content += f"\nEMAIL;TYPE={email.label}:{email.address}"
        
        if card.website:
            vcard_content += f"\nURL:{card.website}"
        
        if card.description:
            vcard_content += f"\nNOTE:{card.description}"
        
        vcard_content += "\nEND:VCARD"
        
        # Track analytics
        if not is_owner:
            background_tasks.add_task(
                track_card_analytics,
                card_id,
                "download",
                request
            )
        
        return Response(
            content=vcard_content,
            media_type="text/vcard",
            headers={
                "Content-Disposition": f'attachment; filename="{card.name.replace(" ", "_")}.vcf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"vCard generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="vCard generation failed")

# ============================================================================
# MEETING ROOM ENDPOINTS
# ============================================================================

@api_router.post("/meeting-rooms", response_model=MeetingRoomResponse)
async def create_meeting_room(
    room_data: MeetingRoomCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Create a new meeting room"""
    try:
        # Track usage for potential upgrade prompts
        if current_user:
            await track_feature_usage_internal(str(current_user.id), "meeting_room_created")
        
        # Check if user exceeds meeting room participant limits (soft limit for growth)
        if current_user and room_data.max_participants > 15:
            subscription = await get_user_subscription(str(current_user.id))
            if subscription.plan_type == PlanType.FREE:
                logger.info(f"Free user {current_user.email} tried to create room with {room_data.max_participants} participants (soft limit: 15)")
                # Don't block, but log for analytics - we want growth over restrictions
                # Could show gentle upgrade hint in frontend later
        # Get the card that's creating the room
        from bson import ObjectId
        
        # Try to find card by string ID first, then ObjectId
        card_data = await db.businesscards.find_one({"_id": room_data.card_id})
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(room_data.card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Check if user owns this card (if logged in)
        if current_user:
            is_owner = str(card.user_id) == str(current_user.id)
            if not is_owner:
                raise HTTPException(status_code=403, detail="Sie können nur Meeting Rooms für Ihre eigenen Karten erstellen")
        
        # Check if card is public for anonymous users
        if not current_user and not card.is_public:
            raise HTTPException(status_code=403, detail="Diese Visitenkarte ist nicht öffentlich")
        
        # Generate code if not provided
        if not room_data.code:
            code = MeetingRoom.generate_random_code(5)
            logger.info(f"Generated meeting room code: {code} (type: {type(code)})")
            # Ensure uniqueness
            attempts = 0
            while attempts < 10:
                existing = await db.meetingrooms.find_one({
                    "code": code,
                    "is_active": True,
                    "expires_at": {"$gt": datetime.utcnow()}
                })
                if not existing:
                    break
                code = MeetingRoom.generate_random_code(5)
                attempts += 1
            
            if attempts >= 10:
                raise HTTPException(status_code=500, detail="Fehler beim Generieren des Codes")
        else:
            code = room_data.code
            # Check if code is already in use
            existing = await db.meetingrooms.find_one({
                "code": code.upper(),
                "is_active": True,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            if existing:
                raise HTTPException(status_code=400, detail="Dieser Code wird bereits für einen aktiven Meeting Room verwendet")
        
        # Create meeting room
        expires_at = datetime.utcnow() + timedelta(minutes=room_data.duration_minutes)
        
        logger.info(f"Creating meeting room with code: {code} (type: {type(code)})")
        meeting_room = MeetingRoom(
            code=code,
            created_by_user_id=str(current_user.id) if current_user else None,
            created_by_card_id=str(card.id),
            created_by_card_name=card.name,
            expires_at=expires_at,
            max_participants=room_data.max_participants,
            description=room_data.description
        )
        
        # Add creator as first participant
        creator_participant = MeetingRoomParticipant(
            user_id=str(current_user.id) if current_user else None,
            card_id=str(card.id),
            card_name=card.name,
            card_company=card.company,
            card_profile_image=card.profile_image,
            ip_address=request.client.host if request.client else None
        )
        meeting_room.participants.append(creator_participant)
        
        # Save to database
        room_dict = meeting_room.dict(by_alias=True, exclude={"id"})
        result = await db.meetingrooms.insert_one(room_dict)
        meeting_room.id = str(result.inserted_id)
        
        logger.info(f"Meeting room created: {code} by card {card.name}")
        
        time_remaining = max(0, int((meeting_room.expires_at - datetime.utcnow()).total_seconds() / 60))
        
        return MeetingRoomResponse(
            id=str(meeting_room.id),
            code=meeting_room.code,
            created_by_card_name=meeting_room.created_by_card_name,
            created_at=meeting_room.created_at,
            expires_at=meeting_room.expires_at,
            participants=meeting_room.participants,
            max_participants=meeting_room.max_participants,
            is_active=meeting_room.is_active,
            description=meeting_room.description,
            time_remaining_minutes=time_remaining,
            can_join=meeting_room.can_join(),
            is_creator=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Meeting room creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Meeting Room Erstellung fehlgeschlagen: {str(e)}")

@api_router.post("/meeting-rooms/join", response_model=MeetingRoomJoinResponse)
async def join_meeting_room(
    join_data: MeetingRoomJoin,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Join a meeting room with a card"""
    try:
        # Find the meeting room
        room_data = await db.meetingrooms.find_one({
            "code": join_data.code.upper(),
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not room_data:
            raise HTTPException(status_code=404, detail="Meeting Room nicht gefunden oder abgelaufen")
        
        # Convert ObjectId to string for compatibility
        if "_id" in room_data:
            room_data["_id"] = str(room_data["_id"])
        
        room = MeetingRoom(**room_data)
        
        # Check if room can accept new participants
        if not room.can_join():
            if room.is_expired():
                raise HTTPException(status_code=400, detail="Meeting Room ist abgelaufen")
            elif len(room.participants) >= room.max_participants:
                raise HTTPException(status_code=400, detail="Meeting Room ist voll")
            else:
                raise HTTPException(status_code=400, detail="Meeting Room ist nicht aktiv")
        
        # Get the card that wants to join
        from bson import ObjectId
        card_data = await db.businesscards.find_one({"_id": join_data.card_id})
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(join_data.card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Check if user owns this card (if logged in)
        if current_user:
            is_owner = str(card.user_id) == str(current_user.id)
            if not is_owner:
                raise HTTPException(status_code=403, detail="Sie können nur Ihre eigenen Karten in Meeting Rooms verwenden")
        
        # Check if card is public for anonymous users
        if not current_user and not card.is_public:
            raise HTTPException(status_code=403, detail="Diese Visitenkarte ist nicht öffentlich")
        
        # Create participant
        participant = MeetingRoomParticipant(
            user_id=str(current_user.id) if current_user else None,
            card_id=str(card.id),
            card_name=card.name,
            card_company=card.company,
            card_profile_image=card.profile_image,
            ip_address=request.client.host if request.client else None
        )
        
        # Check if participant already in room
        for existing in room.participants:
            if existing.card_id == str(card.id):
                # Already in room, just return the room state
                time_remaining = max(0, int((room.expires_at - datetime.utcnow()).total_seconds() / 60))
                is_creator = room.created_by_card_id == str(card.id)
                
                # Get all other participants' cards for response
                cards_received = []
                for p in room.participants:
                    if p.card_id != str(card.id):  # Exclude own card
                        participant_card_data = await db.businesscards.find_one({"_id": p.card_id})
                        if not participant_card_data:
                            try:
                                participant_card_data = await db.businesscards.find_one({"_id": ObjectId(p.card_id)})
                            except:
                                continue
                        
                        if participant_card_data:
                            # Convert ObjectId to string for compatibility
                            if "_id" in participant_card_data:
                                participant_card_data["_id"] = str(participant_card_data["_id"])
                            if "userId" in participant_card_data:
                                participant_card_data["userId"] = str(participant_card_data["userId"])
                            
                            participant_card = BusinessCard(**participant_card_data)
                            cards_received.append({
                                "id": str(participant_card.id),
                                "name": participant_card.name,
                                "company": participant_card.company,
                                "position": participant_card.position,
                                "profile_image": participant_card.profile_image,
                                "joined_at": p.joined_at.isoformat()
                            })
                
                return MeetingRoomJoinResponse(
                    success=True,
                    message=f"Sie sind bereits im Meeting Room '{room.code}'",
                    room=MeetingRoomResponse(
                        id=str(room.id),
                        code=room.code,
                        created_by_card_name=room.created_by_card_name,
                        created_at=room.created_at,
                        expires_at=room.expires_at,
                        participants=room.participants,
                        max_participants=room.max_participants,
                        is_active=room.is_active,
                        description=room.description,
                        time_remaining_minutes=time_remaining,
                        can_join=room.can_join(),
                        is_creator=is_creator
                    ),
                    cards_received=cards_received
                )
        
        # Add participant to room
        room.participants.append(participant)
        
        # Update room in database
        await db.meetingrooms.update_one(
            {"_id": ObjectId(str(room.id))},
            {"$set": {"participants": [p.dict() for p in room.participants]}}
        )
        
        logger.info(f"Card {card.name} joined meeting room {room.code}")
        
        time_remaining = max(0, int((room.expires_at - datetime.utcnow()).total_seconds() / 60))
        is_creator = room.created_by_card_id == str(card.id)
        
        # Get all other participants' cards for response
        cards_received = []
        for p in room.participants:
            if p.card_id != str(card.id):  # Exclude own card
                participant_card_data = await db.businesscards.find_one({"_id": p.card_id})
                if not participant_card_data:
                    try:
                        participant_card_data = await db.businesscards.find_one({"_id": ObjectId(p.card_id)})
                    except:
                        continue
                
                if participant_card_data:
                    # Convert ObjectId to string for compatibility
                    if "_id" in participant_card_data:
                        participant_card_data["_id"] = str(participant_card_data["_id"])
                    if "userId" in participant_card_data:
                        participant_card_data["userId"] = str(participant_card_data["userId"])
                    
                    participant_card = BusinessCard(**participant_card_data)
                    cards_received.append({
                        "id": str(participant_card.id),
                        "name": participant_card.name,
                        "company": participant_card.company,
                        "position": participant_card.position,
                        "profile_image": participant_card.profile_image,
                        "joined_at": p.joined_at.isoformat()
                    })
        
        return MeetingRoomJoinResponse(
            success=True,
            message=f"Sie sind dem Meeting Room '{room.code}' beigetreten! Sie haben {len(cards_received)} neue Kontakte erhalten.",
            room=MeetingRoomResponse(
                id=str(room.id),
                code=room.code,
                created_by_card_name=room.created_by_card_name,
                created_at=room.created_at,
                expires_at=room.expires_at,
                participants=room.participants,
                max_participants=room.max_participants,
                is_active=room.is_active,
                description=room.description,
                time_remaining_minutes=time_remaining,
                can_join=room.can_join(),
                is_creator=is_creator
            ),
            cards_received=cards_received
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Meeting room join failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Meeting Room Beitritt fehlgeschlagen: {str(e)}")

@api_router.get("/meeting-rooms/{room_code}", response_model=MeetingRoomResponse)
async def get_meeting_room(
    room_code: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get meeting room details"""
    try:
        room_data = await db.meetingrooms.find_one({
            "code": room_code.upper(),
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not room_data:
            raise HTTPException(status_code=404, detail="Meeting Room nicht gefunden oder abgelaufen")
        
        # Convert ObjectId to string for compatibility
        if "_id" in room_data:
            room_data["_id"] = str(room_data["_id"])
        
        room = MeetingRoom(**room_data)
        
        time_remaining = max(0, int((room.expires_at - datetime.utcnow()).total_seconds() / 60))
        
        # Check if current user created this room
        is_creator = False
        if current_user:
            is_creator = (
                room.created_by_user_id == str(current_user.id) or
                any(p.user_id == str(current_user.id) and p.card_id == room.created_by_card_id for p in room.participants)
            )
        
        return MeetingRoomResponse(
            id=str(room.id),
            code=room.code,
            created_by_card_name=room.created_by_card_name,
            created_at=room.created_at,
            expires_at=room.expires_at,
            participants=room.participants,
            max_participants=room.max_participants,
            is_active=room.is_active,
            description=room.description,
            time_remaining_minutes=time_remaining,
            can_join=room.can_join(),
            is_creator=is_creator
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail="Meeting Room konnte nicht geladen werden")

@api_router.get("/meeting-rooms", response_model=List[MeetingRoomListResponse])
async def list_user_meeting_rooms(current_user: User = Depends(get_current_user)):
    """Get user's active meeting rooms"""
    try:
        # Find rooms created by user's cards
        user_cards = await db.businesscards.find({"userId": str(current_user.id)}).to_list(length=100)
        user_card_ids = [str(card["_id"]) for card in user_cards]
        
        # Find active meeting rooms created by user's cards
        rooms_cursor = db.meetingrooms.find({
            "created_by_card_id": {"$in": user_card_ids},
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        }).sort("created_at", -1)
        
        rooms = []
        async for room_data in rooms_cursor:
            # Convert ObjectId to string for compatibility
            if "_id" in room_data:
                room_data["_id"] = str(room_data["_id"])
            
            room = MeetingRoom(**room_data)
            time_remaining = max(0, int((room.expires_at - datetime.utcnow()).total_seconds() / 60))
            
            rooms.append(MeetingRoomListResponse(
                id=str(room.id),
                code=room.code,
                created_by_card_name=room.created_by_card_name,
                created_at=room.created_at,
                expires_at=room.expires_at,
                participant_count=len(room.participants),
                max_participants=room.max_participants,
                description=room.description,
                time_remaining_minutes=time_remaining,
                is_creator=True
            ))
        
        return rooms
        
    except Exception as e:
        logger.error(f"Failed to list meeting rooms: {str(e)}")
        raise HTTPException(status_code=500, detail="Meeting Rooms konnten nicht geladen werden")

@api_router.delete("/meeting-rooms/{room_code}")
async def close_meeting_room(
    room_code: str,
    current_user: User = Depends(get_current_user)
):
    """Close/deactivate a meeting room (creator only)"""
    try:
        from bson import ObjectId
        room_data = await db.meetingrooms.find_one({
            "code": room_code.upper(),
            "is_active": True
        })
        
        if not room_data:
            raise HTTPException(status_code=404, detail="Meeting Room nicht gefunden")
        
        # Convert ObjectId to string for compatibility
        if "_id" in room_data:
            room_data["_id"] = str(room_data["_id"])
        
        room = MeetingRoom(**room_data)
        
        # Check if user is the creator
        if room.created_by_user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Nur der Ersteller kann den Meeting Room schließen")
        
        # Deactivate room
        await db.meetingrooms.update_one(
            {"_id": ObjectId(str(room.id))},
            {"$set": {"is_active": False}}
        )
        
        logger.info(f"Meeting room {room.code} closed by {current_user.email}")
        
        return {"message": f"Meeting Room '{room.code}' wurde geschlossen"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close meeting room: {str(e)}")
        raise HTTPException(status_code=500, detail="Meeting Room konnte nicht geschlossen werden")

# ============================================================================
# EXPRESS SHARE ENDPOINTS
# ============================================================================

@api_router.post("/express/create", response_model=ExpressCodeResponse)
async def create_express_code(
    express_data: ExpressShareCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Create ultra-short express code for quick sharing"""
    try:
        # Track usage for analytics 
        if current_user:
            await track_feature_usage_internal(str(current_user.id), "express_code_generated")
        # Get the business card
        from bson import ObjectId
        card_data = await db.businesscards.find_one({"_id": express_data.card_id})
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(express_data.card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Check if user owns this card (if logged in)
        if current_user:
            is_owner = str(card.user_id) == str(current_user.id)
            if not is_owner:
                raise HTTPException(status_code=403, detail="Sie können nur Express Codes für Ihre eigenen Karten erstellen")
        
        # Check if card is public for anonymous users
        if not current_user and not card.is_public:
            raise HTTPException(status_code=403, detail="Diese Visitenkarte ist nicht öffentlich")
        
        # Generate simple express code
        code = ExpressCode.generate_express_code(express_data.code_length)
        attempts = 0
        while attempts < 5:  # Simple collision handling
            existing = await db.expresscodes.find_one({
                "code": code,
                "is_active": True,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            if not existing:
                break
            code = ExpressCode.generate_express_code(express_data.code_length)
            attempts += 1
        
        if attempts >= 5:
            raise HTTPException(status_code=500, detail="Fehler beim Generieren des Express-Codes")
        
        # Create express code
        expires_at = datetime.utcnow() + timedelta(seconds=express_data.duration_seconds)
        
        express_code = ExpressCode(
            code=code,
            card_id=str(card.id),
            user_id=str(current_user.id) if current_user else None,
            expires_at=expires_at,
            max_usage=express_data.max_usage
        )
        
        # Save to database
        code_dict = express_code.dict(by_alias=True, exclude={"id"})
        result = await db.expresscodes.insert_one(code_dict)
        express_code.id = str(result.inserted_id)
        
        logger.info(f"Express code created: {code} for card {card.name} (expires in {express_data.duration_seconds}s)")
        
        time_remaining = max(0, int((express_code.expires_at - datetime.utcnow()).total_seconds()))
        
        return ExpressCodeResponse(
            id=str(express_code.id),
            code=express_code.code,
            created_at=express_code.created_at,
            expires_at=express_code.expires_at,
            time_remaining_seconds=time_remaining,
            usage_count=express_code.usage_count,
            max_usage=express_code.max_usage,
            is_active=express_code.is_active,
            card_name=card.name,
            card_company=card.company
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Express code creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Express Code Erstellung fehlgeschlagen: {str(e)}")

@api_router.post("/express/access", response_model=ExpressAccessResponse)
async def access_by_express_code(
    code_request: dict,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Access business card using express code"""
    try:
        code = code_request.get("code", "").upper().strip()
        
        if not code:
            raise HTTPException(status_code=400, detail="Express Code ist erforderlich")
        
        # Find active express code
        express_data = await db.expresscodes.find_one({
            "code": code,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not express_data:
            raise HTTPException(status_code=404, detail="Express Code nicht gefunden oder abgelaufen")
        
        # Convert ObjectId to string for compatibility
        if "_id" in express_data:
            express_data["_id"] = str(express_data["_id"])
        
        express_code = ExpressCode(**express_data)
        
        # Check if code is valid
        if not express_code.is_valid():
            raise HTTPException(status_code=400, detail="Express Code ist nicht mehr gültig")
        
        # Get associated business card
        from bson import ObjectId
        card_data = await db.businesscards.find_one({"_id": express_code.card_id})
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(express_code.card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Zugeordnete Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Check if card is public
        if not card.is_public:
            raise HTTPException(status_code=403, detail="Diese Visitenkarte ist nicht öffentlich zugänglich")
        
        # Update usage count
        await db.expresscodes.update_one(
            {"_id": ObjectId(str(express_code.id))},
            {"$inc": {"usage_count": 1}}
        )
        
        # Track analytics (in background)
        background_tasks.add_task(
            track_card_analytics,
            str(card.id),
            "express_access",
            request,
            {"access_method": "express_code", "code_used": code}
        )
        
        logger.info(f"Express code access successful: {code} -> Card {card.name}")
        
        time_remaining = max(0, int((express_code.expires_at - datetime.utcnow()).total_seconds()))
        
        return ExpressAccessResponse(
            success=True,
            message=f"Visitenkarte von {card.name} über Express Code erhalten",
            card={
                "id": str(card.id),
                "name": card.name,
                "company": card.company,
                "position": card.position,
                "phones": [{"label": p.label, "number": p.number, "is_primary": p.is_primary} for p in card.phones],
                "emails": [{"label": e.label, "address": e.address, "is_primary": e.is_primary} for e in card.emails],
                "website": card.website,
                "profile_image": card.profile_image,
                "social_media": card.social_media.dict() if card.social_media else {}
            },
            express_code=ExpressCodeResponse(
                id=str(express_code.id),
                code=express_code.code,
                created_at=express_code.created_at,
                expires_at=express_code.expires_at,
                time_remaining_seconds=time_remaining,
                usage_count=express_code.usage_count + 1,
                max_usage=express_code.max_usage,
                is_active=express_code.is_active,
                card_name=card.name,
                card_company=card.company
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Express code access failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Express Code-Zugriff fehlgeschlagen")

@api_router.post("/express/room/create", response_model=ExpressRoomResponse)
async def create_express_room(
    room_data: ExpressRoomCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Create express meeting room for quick group sharing"""
    try:
        # Get the business card
        from bson import ObjectId
        card_data = await db.businesscards.find_one({"_id": room_data.card_id})
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(room_data.card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Check if user owns this card (if logged in)
        if current_user:
            is_owner = str(card.user_id) == str(current_user.id)
            if not is_owner:
                raise HTTPException(status_code=403, detail="Sie können nur Express Rooms für Ihre eigenen Karten erstellen")
        
        # Check if card is public for anonymous users
        if not current_user and not card.is_public:
            raise HTTPException(status_code=403, detail="Diese Visitenkarte ist nicht öffentlich")
        
        # Generate simple 2-digit room code
        code = ExpressMeetingRoom.generate_express_room_code()
        attempts = 0
        while attempts < 5:  # Simple collision handling
            existing = await db.expressrooms.find_one({
                "code": code,
                "is_active": True,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            if not existing:
                break
            code = ExpressMeetingRoom.generate_express_room_code()
            attempts += 1
        
        if attempts >= 5:
            raise HTTPException(status_code=500, detail="Fehler beim Generieren des Express Room Codes")
        
        # Create express meeting room
        expires_at = datetime.utcnow() + timedelta(seconds=room_data.duration_seconds)
        
        express_room = ExpressMeetingRoom(
            code=code,
            created_by_card_id=str(card.id),
            created_by_card_name=card.name,
            created_by_user_id=str(current_user.id) if current_user else None,
            expires_at=expires_at,
            max_participants=room_data.max_participants,
            participants=[str(card.id)]  # Creator joins automatically
        )
        
        # Save to database
        room_dict = express_room.dict(by_alias=True, exclude={"id"})
        result = await db.expressrooms.insert_one(room_dict)
        express_room.id = str(result.inserted_id)
        
        logger.info(f"Express room created: {code} by {card.name} (expires in {room_data.duration_seconds}s)")
        
        time_remaining = max(0, int((express_room.expires_at - datetime.utcnow()).total_seconds()))
        
        return ExpressRoomResponse(
            id=str(express_room.id),
            code=express_room.code,
            created_by_card_name=express_room.created_by_card_name,
            created_at=express_room.created_at,
            expires_at=express_room.expires_at,
            time_remaining_seconds=time_remaining,
            participant_count=len(express_room.participants),
            max_participants=express_room.max_participants,
            can_join=express_room.can_join(),
            participants=[{
                "card_id": str(card.id),
                "name": card.name,
                "company": card.company,
                "joined_at": express_room.created_at.isoformat()
            }]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Express room creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Express Room Erstellung fehlgeschlagen: {str(e)}")

@api_router.post("/express/room/join", response_model=dict)
async def join_express_room(
    join_data: ExpressRoomJoin,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Join express meeting room with business card"""
    try:
        # Find active express room
        room_data = await db.expressrooms.find_one({
            "code": join_data.code,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not room_data:
            raise HTTPException(status_code=404, detail="Express Room nicht gefunden oder abgelaufen")
        
        # Convert ObjectId to string for compatibility
        if "_id" in room_data:
            room_data["_id"] = str(room_data["_id"])
        
        express_room = ExpressMeetingRoom(**room_data)
        
        # Check if room can accept new participants
        if not express_room.can_join():
            if express_room.is_expired():
                raise HTTPException(status_code=400, detail="Express Room ist abgelaufen")
            elif len(express_room.participants) >= express_room.max_participants:
                raise HTTPException(status_code=400, detail="Express Room ist voll")
            else:
                raise HTTPException(status_code=400, detail="Express Room ist nicht aktiv")
        
        # Get the business card
        from bson import ObjectId
        card_data = await db.businesscards.find_one({"_id": join_data.card_id})
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({"_id": ObjectId(join_data.card_id)})
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string for compatibility
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Check if user owns this card (if logged in)
        if current_user:
            is_owner = str(card.user_id) == str(current_user.id)
            if not is_owner:
                raise HTTPException(status_code=403, detail="Sie können nur Ihre eigenen Karten verwenden")
        
        # Check if card is public for anonymous users
        if not current_user and not card.is_public:
            raise HTTPException(status_code=403, detail="Diese Visitenkarte ist nicht öffentlich")
        
        # Check if already in room
        if str(card.id) in express_room.participants:
            # Get all participant cards for response
            participant_cards = []
            for participant_id in express_room.participants:
                if participant_id != str(card.id):
                    p_data = await db.businesscards.find_one({"_id": participant_id})
                    if not p_data:
                        try:
                            p_data = await db.businesscards.find_one({"_id": ObjectId(participant_id)})
                        except:
                            continue
                    
                    if p_data:
                        # Convert ObjectId to string
                        if "_id" in p_data:
                            p_data["_id"] = str(p_data["_id"])
                        if "userId" in p_data:
                            p_data["userId"] = str(p_data["userId"])
                        
                        p_card = BusinessCard(**p_data)
                        participant_cards.append({
                            "id": str(p_card.id),
                            "name": p_card.name,
                            "company": p_card.company,
                            "position": p_card.position,
                            "phones": [{"label": ph.label, "number": ph.number, "is_primary": ph.is_primary} for ph in p_card.phones],
                            "emails": [{"label": em.label, "address": em.address, "is_primary": em.is_primary} for em in p_card.emails],
                            "website": p_card.website,
                            "profile_image": p_card.profile_image
                        })
            
            return {
                "success": True,
                "message": f"Sie sind bereits im Express Room '{express_room.code}'",
                "cards_received": participant_cards,
                "room_info": {
                    "code": express_room.code,
                    "time_remaining_seconds": max(0, int((express_room.expires_at - datetime.utcnow()).total_seconds())),
                    "participant_count": len(express_room.participants)
                }
            }
        
        # Add participant to room
        express_room.participants.append(str(card.id))
        
        # Update room in database
        await db.expressrooms.update_one(
            {"_id": ObjectId(str(express_room.id))},
            {"$set": {"participants": express_room.participants}}
        )
        
        # Get all other participant cards for response
        participant_cards = []
        for participant_id in express_room.participants:
            if participant_id != str(card.id):
                p_data = await db.businesscards.find_one({"_id": participant_id})
                if not p_data:
                    try:
                        p_data = await db.businesscards.find_one({"_id": ObjectId(participant_id)})
                    except:
                        continue
                
                if p_data:
                    # Convert ObjectId to string
                    if "_id" in p_data:
                        p_data["_id"] = str(p_data["_id"])
                    if "userId" in p_data:
                        p_data["userId"] = str(p_data["userId"])
                    
                    p_card = BusinessCard(**p_data)
                    participant_cards.append({
                        "id": str(p_card.id),
                        "name": p_card.name,
                        "company": p_card.company,
                        "position": p_card.position,
                        "phones": [{"label": ph.label, "number": ph.number, "is_primary": ph.is_primary} for ph in p_card.phones],
                        "emails": [{"label": em.label, "address": em.address, "is_primary": em.is_primary} for em in p_card.emails],
                        "website": p_card.website,
                        "profile_image": p_card.profile_image
                    })
        
        logger.info(f"Card {card.name} joined express room {express_room.code}")
        
        return {
            "success": True,
            "message": f"Sie sind dem Express Room '{express_room.code}' beigetreten! {len(participant_cards)} Kontakte erhalten.",
            "cards_received": participant_cards,
            "room_info": {
                "code": express_room.code,
                "time_remaining_seconds": max(0, int((express_room.expires_at - datetime.utcnow()).total_seconds())),
                "participant_count": len(express_room.participants)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Express room join failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Express Room Beitritt fehlgeschlagen: {str(e)}")

# ============================================================================
# CONTACT IMPORT & SYNC ENDPOINTS
# ============================================================================

@api_router.get("/contacts/sources", response_model=List[ContactSourceResponse])
async def list_contact_sources(current_user: User = Depends(get_current_user)):
    """Get all configured contact sources for user"""
    try:
        sources_cursor = db.contactsources.find({"user_id": str(current_user.id)})
        sources = []
        
        async for source_data in sources_cursor:
            if "_id" in source_data:
                source_data["_id"] = str(source_data["_id"])
            
            source = ContactSource(**source_data)
            sources.append(ContactSourceResponse(
                id=str(source.id),
                source_type=source.source_type.value,
                display_name=source.display_name,
                sync_enabled=source.sync_enabled,
                sync_status=source.sync_status.value,
                last_sync_at=source.last_sync_at,
                next_sync_at=source.next_sync_at,
                total_contacts_imported=source.total_contacts_imported,
                last_error_message=source.last_error_message
            ))
        
        return sources
        
    except Exception as e:
        logger.error(f"Failed to list contact sources: {str(e)}")
        raise HTTPException(status_code=500, detail="Kontaktquellen konnten nicht geladen werden")

@api_router.post("/contacts/import", response_model=ContactImportResponse)
async def import_contacts(
    import_request: ContactImportRequest,
    current_user: User = Depends(get_current_user)
):
    """Import contacts from various sources"""
    try:
        logger.info(f"Starting contact import for user {current_user.email}, source: {import_request.source_type}")
        
        # Handle different import types
        if import_request.source_type == ContactSourceType.CONTACT_PICKER:
            return await import_from_contact_picker(import_request, current_user)
        elif import_request.source_type == ContactSourceType.VCF_FILE:
            return await import_from_vcf_file(import_request, current_user)
        elif import_request.source_type == ContactSourceType.CSV_FILE:
            return await import_from_csv_file(import_request, current_user)
        elif import_request.source_type == ContactSourceType.GOOGLE_CONTACTS:
            return await import_from_google_contacts(import_request, current_user)
        elif import_request.source_type == ContactSourceType.APPLE_ICLOUD:
            return await import_from_apple_icloud(import_request, current_user)
        else:
            raise HTTPException(status_code=400, detail=f"Kontaktquelle {import_request.source_type} wird noch nicht unterstützt")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contact import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Kontakt-Import fehlgeschlagen: {str(e)}")

async def import_from_contact_picker(request: ContactImportRequest, user: User) -> ContactImportResponse:
    """Import contacts from browser Contact Picker API"""
    from bson import ObjectId
    
    if not request.contacts_data:
        raise HTTPException(status_code=400, detail="Keine Kontaktdaten bereitgestellt")
    
    # Create contact source
    source = ContactSource(
        user_id=str(user.id),
        source_type=ContactSourceType.CONTACT_PICKER,
        display_name=request.display_name or "Browser Kontakte",
        sync_enabled=False,  # Contact picker is one-time only
        last_sync_at=datetime.utcnow()
    )
    
    source_dict = source.dict(by_alias=True, exclude={"id"})
    source_result = await db.contactsources.insert_one(source_dict)
    source.id = str(source_result.inserted_id)
    
    contacts_imported = 0
    
    for contact_data in request.contacts_data:
        try:
            imported_contact = await create_imported_contact_from_data(
                contact_data, str(user.id), str(source.id)
            )
            
            if imported_contact:
                contact_dict = imported_contact.dict(by_alias=True, exclude={"id"})
                await db.importedcontacts.insert_one(contact_dict)
                contacts_imported += 1
                
        except Exception as e:
            logger.warning(f"Failed to import individual contact: {str(e)}")
            continue
    
    # Update source statistics
    await db.contactsources.update_one(
        {"_id": ObjectId(str(source.id))},
        {"$set": {
            "total_contacts_imported": contacts_imported,
            "last_sync_contacts_added": contacts_imported
        }}
    )
    
    logger.info(f"Imported {contacts_imported} contacts from Contact Picker for user {user.email}")
    
    return ContactImportResponse(
        success=True,
        message=f"Erfolgreich {contacts_imported} Kontakte importiert",
        source_id=str(source.id),
        contacts_imported=contacts_imported
    )

async def import_from_vcf_file(request: ContactImportRequest, user: User) -> ContactImportResponse:
    """Import contacts from VCF file"""
    from bson import ObjectId
    
    if not request.file_content:
        raise HTTPException(status_code=400, detail="Keine Datei bereitgestellt")
    
    try:
        import base64
        import io
        
        # Decode base64 file content
        file_data = base64.b64decode(request.file_content).decode('utf-8')
        
        # Parse VCF content
        contacts = parse_vcf_content(file_data)
        
        # Create contact source
        source = ContactSource(
            user_id=str(user.id),
            source_type=ContactSourceType.VCF_FILE,
            display_name=request.display_name or f"VCF Import ({request.file_name or 'contacts.vcf'})",
            sync_enabled=False,  # File imports are one-time only
            last_sync_at=datetime.utcnow()
        )
        
        source_dict = source.dict(by_alias=True, exclude={"id"})
        source_result = await db.contactsources.insert_one(source_dict)
        source.id = str(source_result.inserted_id)
        
        contacts_imported = 0
        
        for contact_data in contacts:
            try:
                imported_contact = await create_imported_contact_from_vcf(
                    contact_data, str(user.id), str(source.id)
                )
                
                if imported_contact:
                    contact_dict = imported_contact.dict(by_alias=True, exclude={"id"})
                    await db.importedcontacts.insert_one(contact_dict)
                    contacts_imported += 1
                    
            except Exception as e:
                logger.warning(f"Failed to import VCF contact: {str(e)}")
                continue
        
        # Update source statistics
        await db.contactsources.update_one(
            {"_id": ObjectId(str(source.id))},
            {"$set": {
                "total_contacts_imported": contacts_imported,
                "last_sync_contacts_added": contacts_imported
            }}
        )
        
        logger.info(f"Imported {contacts_imported} contacts from VCF file for user {user.email}")
        
        return ContactImportResponse(
            success=True,
            message=f"Erfolgreich {contacts_imported} Kontakte aus VCF-Datei importiert",
            source_id=str(source.id),
            contacts_imported=contacts_imported
        )
        
    except Exception as e:
        logger.error(f"VCF import failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"VCF-Import fehlgeschlagen: {str(e)}")

async def import_from_csv_file(request: ContactImportRequest, user: User) -> ContactImportResponse:
    """Import contacts from CSV file"""
    from bson import ObjectId
    
    if not request.file_content:
        raise HTTPException(status_code=400, detail="Keine Datei bereitgestellt")
    
    try:
        import base64
        import io
        import csv
        
        # Decode base64 file content
        file_data = base64.b64decode(request.file_content).decode('utf-8')
        
        # Parse CSV content
        contacts = []
        csv_reader = csv.DictReader(io.StringIO(file_data))
        
        for row in csv_reader:
            # Map common CSV headers to contact fields
            contact_data = {}
            
            # Try different common header variations
            for key, value in row.items():
                key_lower = key.lower().strip()
                if key_lower in ['name', 'full name', 'display name', 'contact name']:
                    contact_data['name'] = value
                elif key_lower in ['email', 'email address', 'e-mail']:
                    contact_data['email'] = [value] if value else []
                elif key_lower in ['phone', 'phone number', 'mobile', 'tel']:
                    contact_data['tel'] = [value] if value else []
                elif key_lower in ['company', 'organization', 'org']:
                    contact_data['org'] = value
                elif key_lower in ['title', 'job title', 'position']:
                    contact_data['title'] = value
            
            if contact_data.get('name'):
                contacts.append(contact_data)
        
        # Create contact source
        source = ContactSource(
            user_id=str(user.id),
            source_type=ContactSourceType.CSV_FILE,
            name=f"CSV Import {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            total_contacts=len(contacts),
            imported_contacts=0,
            status=SyncStatus.PENDING
        )
        
        # Save source to database
        source_dict = source.dict(by_alias=True, exclude={"id"})
        result = await db.contactsources.insert_one(source_dict)
        source.id = str(result.inserted_id)
        
        # Import contacts
        contacts_imported = 0
        for contact_data in contacts:
            imported_contact = await create_imported_contact_from_data(
                contact_data, str(user.id), str(source.id)
            )
            if imported_contact:
                contacts_imported += 1
        
        # Update source with final count
        await db.contactsources.update_one(
            {"_id": ObjectId(str(source.id))},
            {"$set": {
                "imported_contacts": contacts_imported,
                "status": SyncStatus.COMPLETED.value,
                "last_sync": datetime.utcnow()
            }}
        )
        
        logger.info(f"CSV import completed: {contacts_imported} contacts imported for user {user.email}")
        
        return ContactImportResponse(
            success=True,
            message=f"Erfolgreich {contacts_imported} Kontakte aus CSV-Datei importiert",
            source_id=str(source.id),
            contacts_imported=contacts_imported
        )
        
    except Exception as e:
        logger.error(f"CSV import failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"CSV-Import fehlgeschlagen: {str(e)}")

async def import_from_google_contacts(request: ContactImportRequest, user: User) -> ContactImportResponse:
    """Import contacts from Google Contacts API"""
    # This will require OAuth implementation
    return ContactImportResponse(
        success=False,
        message="Google Contacts Import wird in der nächsten Version implementiert",
        auth_required=True,
        auth_url="https://accounts.google.com/oauth/authorize"  # Placeholder
    )

async def import_from_apple_icloud(request: ContactImportRequest, user: User) -> ContactImportResponse:
    """Import contacts from Apple iCloud"""
    # This will require CloudKit Web Services
    return ContactImportResponse(
        success=False,
        message="Apple iCloud Import wird in der nächsten Version implementiert",
        auth_required=True
    )

async def create_imported_contact_from_data(contact_data: dict, user_id: str, source_id: str) -> Optional[ImportedContact]:
    """Create ImportedContact from raw contact data"""
    try:
        # Extract basic info
        name = contact_data.get('name', [''])[0] if isinstance(contact_data.get('name'), list) else contact_data.get('name', '')
        if not name:
            return None
        
        # Parse phone numbers
        phones = []
        tel_numbers = contact_data.get('tel', [])
        if isinstance(tel_numbers, str):
            tel_numbers = [tel_numbers]
        
        for i, tel in enumerate(tel_numbers):
            phones.append({
                "number": tel,
                "label": "mobile" if i == 0 else "other",
                "is_primary": i == 0,
                "messaging_apps": [
                    {"name": "whatsapp", "enabled": True},
                    {"name": "sms", "enabled": True}
                ]
            })
        
        # Parse emails
        emails = []
        email_addresses = contact_data.get('email', [])
        if isinstance(email_addresses, str):
            email_addresses = [email_addresses]
        
        for i, email in enumerate(email_addresses):
            emails.append({
                "address": email,
                "label": "work" if i == 0 else "other",
                "is_primary": i == 0
            })
        
        imported_contact = ImportedContact(
            user_id=user_id,
            source_id=source_id,
            name=name,
            phones=phones,
            emails=emails,
            last_synced_at=datetime.utcnow()
        )
        
        return imported_contact
        
    except Exception as e:
        logger.error(f"Failed to create imported contact: {str(e)}")
        return None

def parse_vcf_content(vcf_content: str) -> List[dict]:
    """Parse VCF file content and extract contacts"""
    contacts = []
    current_contact = {}
    
    for line in vcf_content.split('\n'):
        line = line.strip()
        
        if line.startswith('BEGIN:VCARD'):
            current_contact = {}
        elif line.startswith('END:VCARD'):
            if current_contact:
                contacts.append(current_contact)
        elif ':' in line:
            key, value = line.split(':', 1)
            
            # Handle common VCF fields
            if key.startswith('FN'):
                current_contact['name'] = value
            elif key.startswith('TEL'):
                if 'tel' not in current_contact:
                    current_contact['tel'] = []
                current_contact['tel'].append(value)
            elif key.startswith('EMAIL'):
                if 'email' not in current_contact:
                    current_contact['email'] = []
                current_contact['email'].append(value)
            elif key.startswith('ORG'):
                current_contact['company'] = value
            elif key.startswith('TITLE'):
                current_contact['position'] = value
    
    return contacts

async def create_imported_contact_from_vcf(contact_data: dict, user_id: str, source_id: str) -> Optional[ImportedContact]:
    """Create ImportedContact from VCF data"""
    return await create_imported_contact_from_data(contact_data, user_id, source_id)

@api_router.get("/contacts/unified", response_model=List[UnifiedContact])
async def get_unified_contacts(
    search: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get unified contact list combining business cards and imported contacts"""
    try:
        unified_contacts = []
        
        # Get business cards
        business_cards_query = {"userId": str(current_user.id)}
        if search:
            business_cards_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"company": {"$regex": search, "$options": "i"}}
            ]
        
        cards_cursor = db.businesscards.find(business_cards_query).limit(limit // 2)
        
        async for card_data in cards_cursor:
            if "_id" in card_data:
                card_data["_id"] = str(card_data["_id"])
            if "userId" in card_data:
                card_data["userId"] = str(card_data["userId"])
            
            card = BusinessCard(**card_data)
            
            unified_contact = UnifiedContact(
                id=str(card.id),
                source_type="business_card",
                name=card.name,
                company=card.company,
                position=card.position,
                phones=[{
                    "number": phone.number,
                    "label": phone.label,
                    "is_primary": phone.is_primary,
                    "messaging_apps": getattr(phone, 'messaging_apps', [])
                } for phone in card.phones],
                emails=[{
                    "address": email.address,
                    "label": email.label, 
                    "is_primary": email.is_primary
                } for email in card.emails],
                profile_image=card.profile_image,
                is_business_card=True,
                custom_code=card.custom_code,
                is_public=card.is_public
            )
            unified_contacts.append(unified_contact)
        
        # Get imported contacts
        imported_contacts_query = {"user_id": str(current_user.id)}
        if search:
            imported_contacts_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"company": {"$regex": search, "$options": "i"}}
            ]
        
        contacts_cursor = db.importedcontacts.find(imported_contacts_query).limit(limit // 2)
        
        async for contact_data in contacts_cursor:
            if "_id" in contact_data:
                contact_data["_id"] = str(contact_data["_id"])
            
            contact = ImportedContact(**contact_data)
            
            unified_contact = UnifiedContact(
                id=str(contact.id),
                source_type="imported_contact", 
                source_id=contact.source_id,
                name=contact.name,
                first_name=contact.first_name,
                last_name=contact.last_name,
                company=contact.company,
                position=contact.position,
                phones=contact.phones,
                emails=contact.emails,
                addresses=contact.addresses,
                profile_image=contact.profile_image_url or contact.profile_image_data,
                is_imported_contact=True,
                external_source=contact.source_id,
                last_synced=contact.last_synced_at
            )
            unified_contacts.append(unified_contact)
        
        # Sort by name
        unified_contacts.sort(key=lambda c: c.name.lower())
        
        return unified_contacts[:limit]
        
    except Exception as e:
        logger.error(f"Failed to get unified contacts: {str(e)}")
        raise HTTPException(status_code=500, detail="Kontakte konnten nicht geladen werden")

# ============================================================================
# SUBSCRIPTION & MONETIZATION ENDPOINTS
# ============================================================================

@api_router.get("/subscription/status", response_model=SubscriptionResponse)
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Get current user's subscription status and limits"""
    try:
        # Get or create user subscription
        subscription = await get_user_subscription(str(current_user.id))
        
        upgrade_benefits = []
        if subscription.plan_type == PlanType.FREE:
            upgrade_benefits = [
                "Unbegrenzte Meeting Room Teilnehmer (50+ statt 15)",
                "Längere Meeting Rooms (60min statt 15min)",
                "Google & Apple Kontakte Synchronisation",
                "Detaillierte Analytics - sehen Sie wer Ihre Codes verwendet",
                "Prioritäts-Support und schnellere Antworten",
                "Custom Branding - eigenes Logo, keine 'Made with App' Hinweise"
            ]
        
        return SubscriptionResponse(
            user_id=str(current_user.id),
            plan_type=subscription.plan_type.value,
            plan_name=subscription.plan_name,
            status=subscription.status.value,
            limits=subscription.plan_limits,
            expires_at=subscription.expires_at,
            trial_ends_at=subscription.trial_ends_at,
            usage=subscription.monthly_usage,
            upgrade_available=(subscription.plan_type == PlanType.FREE),
            upgrade_benefits=upgrade_benefits
        )
        
    except Exception as e:
        logger.error(f"Failed to get subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Subscription Status konnte nicht geladen werden")

@api_router.post("/subscription/check-feature", response_model=FeatureAccessResponse)
async def check_feature_access(
    request: FeatureAccessRequest,
    current_user: User = Depends(get_current_user)
):
    """Check if user has access to a specific feature"""
    try:
        if request.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        subscription = await get_user_subscription(str(current_user.id))
        
        # Check feature access based on plan limits
        allowed = check_feature_allowed(request.feature_name, subscription.plan_limits)
        
        response = FeatureAccessResponse(allowed=allowed)
        
        if not allowed:
            response.upgrade_required = True
            response.suggested_plan = "premium"
            
            # Customize upgrade message based on feature
            if request.feature_name == "detailed_analytics":
                response.reason = "Detaillierte Analytics sind nur im Premium Plan verfügbar"
                response.upgrade_benefits = [
                    "Sehen Sie wann und wie oft Ihre Codes verwendet wurden",
                    "Kontakt-Insights und Verhaltensmuster",
                    "Export aller Daten als CSV",
                    "Erweiterte Meeting Room Statistiken"
                ]
            elif request.feature_name == "google_sync":
                response.reason = "Google Contacts Synchronisation ist nur im Premium Plan verfügbar"
                response.upgrade_benefits = [
                    "Automatische Synchronisation mit Google Contacts",
                    "Immer aktuelle Kontaktdaten",
                    "Bidirektionale Sync - Änderungen werden übertragen",
                    "Backup Ihrer Kontakte in der Cloud"
                ]
            elif request.feature_name == "custom_branding":
                response.reason = "Custom Branding ist nur im Premium Plan verfügbar" 
                response.upgrade_benefits = [
                    "Entfernung aller 'Made with App' Hinweise",
                    "Ihr eigenes Logo auf Visitenkarten",
                    "Custom Themes und Schriftarten",
                    "Professioneller Auftritt für Ihr Business"
                ]
            else:
                response.reason = f"Feature '{request.feature_name}' ist nur im Premium Plan verfügbar"
                response.upgrade_benefits = [
                    "Zugang zu allen Premium Features",
                    "Prioritäts-Support",
                    "Erweiterte Limits und Funktionen"
                ]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature access check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Feature-Zugriff konnte nicht geprüft werden")

async def track_feature_usage_internal(user_id: str, event_type: str, event_data: dict = {}):
    """Internal function to track feature usage without HTTP dependencies"""
    try:
        subscription = await get_user_subscription(user_id)
        
        # Update usage counters
        usage_key = get_usage_key_for_event(event_type)
        if usage_key and usage_key in subscription.monthly_usage:
            await db.usersubscriptions.update_one(
                {"user_id": user_id},
                {"$inc": {f"monthly_usage.{usage_key}": 1}}
            )
        
        # Log usage event
        usage_event = UsageTrackingEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            plan_type=subscription.plan_type
        )
        
        event_dict = usage_event.dict()
        await db.usageevents.insert_one(event_dict)
        
        # Check if we should show upgrade prompt
        await check_and_create_upgrade_prompt(user_id, event_type, subscription)
        
        logger.info(f"Usage tracked internally: {event_type} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Internal usage tracking failed: {str(e)}")

@api_router.post("/subscription/track-usage")
async def track_feature_usage(
    event_type: str,
    event_data: dict = {},
    current_user: User = Depends(get_current_user)
):
    """Track user feature usage for analytics and upgrade prompts"""
    try:
        subscription = await get_user_subscription(str(current_user.id))
        
        # Update usage counters
        usage_key = get_usage_key_for_event(event_type)
        if usage_key and usage_key in subscription.monthly_usage:
            await db.usersubscriptions.update_one(
                {"user_id": str(current_user.id)},
                {"$inc": {f"monthly_usage.{usage_key}": 1}}
            )
        
        # Log usage event
        usage_event = UsageTrackingEvent(
            user_id=str(current_user.id),
            event_type=event_type,
            event_data=event_data,
            plan_type=subscription.plan_type
        )
        
        event_dict = usage_event.dict()
        await db.usageevents.insert_one(event_dict)
        
        # Check if we should show upgrade prompt
        await check_and_create_upgrade_prompt(str(current_user.id), event_type, subscription)
        
        return {"success": True, "message": "Usage tracked"}
        
    except Exception as e:
        logger.error(f"Usage tracking failed: {str(e)}")
        return {"success": False, "message": "Usage tracking failed"}

async def get_user_subscription(user_id: str) -> UserSubscription:
    """Get or create user subscription with default free plan or early adopter bonus"""
    try:
        subscription_data = await db.usersubscriptions.find_one({"user_id": user_id})
        
        if not subscription_data:
            # Check if user qualifies for Early Adopter Program (first 100,000 users)
            total_users = await db.users.count_documents({})
            
            if total_users <= 100000:
                # Early Adopter gets EVERYTHING for free! 🚀
                early_adopter_limits = PlanLimits(
                    max_business_cards=999999,  # Unlimited
                    max_custom_codes=999999,    # Unlimited  
                    express_share_enabled=True,
                    meeting_rooms_enabled=True,
                    max_meeting_participants=100,  # Premium limit
                    meeting_room_duration_minutes=120,  # 2 hours
                    monthly_contact_imports=999999,  # Unlimited
                    google_contacts_sync=True,   # Premium feature FREE
                    apple_icloud_sync=True,      # Premium feature FREE
                    auto_contact_sync=True,      # Premium feature FREE
                    detailed_analytics=True,     # Premium feature FREE
                    contact_insights=True,       # Premium feature FREE
                    export_analytics=True,       # Premium feature FREE
                    custom_branding=True,        # Premium feature FREE
                    custom_themes=999,          # Unlimited
                    custom_fonts=True,          # Premium feature FREE
                    priority_support=True,      # Premium feature FREE
                    api_access=True,            # Premium feature FREE
                    team_management=True        # Premium feature FREE
                )
                
                subscription = UserSubscription(
                    user_id=user_id,
                    plan_type=PlanType.FREE,  # Still "free" but with premium benefits
                    plan_name=f"🎉 Early Adopter #{total_users} - ALLES KOSTENLOS!",
                    plan_limits=early_adopter_limits,
                    status=SubscriptionStatus.ACTIVE
                )
                
                logger.info(f"Created Early Adopter subscription for user {user_id} - #{total_users}/100,000")
                
            else:
                # Regular free subscription with normal limits
                free_limits = PLAN_CONFIGS["free"]
                
                subscription = UserSubscription(
                    user_id=user_id,
                    plan_type=PlanType.FREE,
                    plan_name="Free Plan - Fast alles kostenlos! 🚀",
                    plan_limits=free_limits,
                    status=SubscriptionStatus.ACTIVE
                )
                
                logger.info(f"Created regular free subscription for user {user_id} (after 100k limit)")
            
            sub_dict = subscription.dict(by_alias=True, exclude={"id"})
            result = await db.usersubscriptions.insert_one(sub_dict)
            subscription.id = str(result.inserted_id)
            
            return subscription
        else:
            if "_id" in subscription_data:
                subscription_data["_id"] = str(subscription_data["_id"])
            return UserSubscription(**subscription_data)
            
    except Exception as e:
        logger.error(f"Failed to get user subscription: {str(e)}")
        # Return default free subscription on error
        return UserSubscription(
            user_id=user_id,
            plan_type=PlanType.FREE,
            plan_name="Free Plan",
            plan_limits=PLAN_CONFIGS["free"]
        )

def check_feature_allowed(feature_name: str, limits: PlanLimits) -> bool:
    """Check if feature is allowed based on plan limits"""
    feature_map = {
        "detailed_analytics": limits.detailed_analytics,
        "contact_insights": limits.contact_insights,
        "export_analytics": limits.export_analytics,
        "google_sync": limits.google_contacts_sync,
        "apple_sync": limits.apple_icloud_sync,
        "custom_branding": limits.custom_branding,
        "priority_support": limits.priority_support,
        "api_access": limits.api_access,
        "team_management": limits.team_management,
        "auto_sync": limits.auto_contact_sync
    }
    
    return feature_map.get(feature_name, True)  # Default to allowed

def get_usage_key_for_event(event_type: str) -> Optional[str]:
    """Map event types to usage counter keys"""
    event_map = {
        "business_card_created": "business_cards_created",
        "custom_code_used": "custom_codes_used", 
        "meeting_room_created": "meeting_rooms_created",
        "contact_imported": "contacts_imported",
        "express_code_generated": "express_codes_generated",
        "analytics_viewed": "analytics_views"
    }
    
    return event_map.get(event_type)

async def check_and_create_upgrade_prompt(user_id: str, event_type: str, subscription: UserSubscription):
    """Check if we should show an upgrade prompt and create it"""
    if subscription.plan_type != PlanType.FREE:
        return  # Only show prompts to free users
    
    # Smart upgrade prompts based on usage
    prompt_triggers = {
        "analytics_viewed": {
            "threshold": 3,  # After 3 analytics views
            "message": "🔍 Lieben Sie die Analytics? Upgrade für detaillierte Insights - sehen Sie wer wann Ihre Codes verwendet!",
            "cooldown_hours": 24
        },
        "meeting_room_created": {
            "threshold": 5,  # After 5 meeting rooms
            "message": "🚀 Sie sind ein Meeting Room Power-User! Upgrade für 50+ Teilnehmer und 60min Rooms.",
            "cooldown_hours": 48
        },
        "contact_imported": {
            "threshold": 100,  # After 100 imports
            "message": "📱 Sie importieren viele Kontakte! Upgrade für Google/Apple Sync und unbegrenzte Imports.",
            "cooldown_hours": 72
        }
    }
    
    if event_type not in prompt_triggers:
        return
    
    trigger = prompt_triggers[event_type]
    usage_count = subscription.monthly_usage.get(get_usage_key_for_event(event_type), 0)
    
    if usage_count >= trigger["threshold"]:
        # Check cooldown
        if subscription.last_upgrade_prompt:
            hours_since_prompt = (datetime.utcnow() - subscription.last_upgrade_prompt).total_seconds() / 3600
            if hours_since_prompt < trigger["cooldown_hours"]:
                return
        
        # Create upgrade prompt
        prompt = UpgradePrompt(
            user_id=user_id,
            trigger_event=event_type,
            prompt_message=trigger["message"],
            suggested_plan=PlanType.PREMIUM
        )
        
        prompt_dict = prompt.dict(by_alias=True, exclude={"id"})
        await db.upgradeprompts.insert_one(prompt_dict)
        
        # Update last prompt timestamp
        await db.usersubscriptions.update_one(
            {"user_id": user_id},
            {"$set": {"last_upgrade_prompt": datetime.utcnow()}}
        )

# ============================================================================
# PRIVACY & GDPR ENDPOINTS
# ============================================================================

@api_router.get("/privacy/export", response_model=GDPRExport)
async def export_user_data(current_user: User = Depends(get_current_user)):
    """Export all user data (GDPR Article 15)"""
    return await privacy_service.export_user_data(current_user)

@api_router.delete("/privacy/delete")
async def delete_user_account(
    deletion_request: AccountDeletion,
    current_user: User = Depends(get_current_user)
):
    """Delete user account and all data (GDPR Article 17)"""
    success = await privacy_service.delete_user_account(current_user, deletion_request)
    
    if success:
        return {"message": "Account deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Account deletion failed")

@api_router.get("/privacy/report")
async def get_privacy_report(current_user: User = Depends(get_current_user)):
    """Get privacy compliance report"""
    return await privacy_service.get_privacy_compliance_report(current_user)

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def track_card_analytics(card_id: str, action: str, request: Request):
    """Track analytics for card interactions"""
    try:
        # Extract country from IP (simplified - use proper GeoIP in production)
        client_ip = request.client.host
        country = "DE" if client_ip.startswith("192.168") else "Unknown"
        
        # Get user agent and referrer
        user_agent = request.headers.get("user-agent", "")[:200]  # Limit length
        referrer = request.headers.get("referer", "")[:200]
        
        analytics = CardAnalytics(
            card_id=card_id,
            action=action,
            user_agent=user_agent,
            country=country,
            referrer=referrer
        )
        
        await db.cardanalytics.insert_one(analytics.dict(by_alias=True, exclude={"id"}))
        
        # Update card counters
        if action == "view":
            await db.businesscards.update_one(
                {"_id": card_id},
                {"$inc": {"view_count": 1}}
            )
        elif action in ["download", "share"]:
            await db.businesscards.update_one(
                {"_id": card_id},
                {"$inc": {"share_count": 1}}
            )
            
    except Exception as e:
        logger.error(f"Analytics tracking failed: {str(e)}")

async def send_auto_update_notifications(card_id: str, updated_fields: list):
    """Send notifications to card recipients about updates"""
    try:
        # Get card recipients
        recipients_cursor = db.cardrecipients.find({
            "card_id": card_id,
            "is_active": True
        })
        
        notification_count = 0
        
        async for recipient_data in recipients_cursor:
            recipient = CardRecipient(**recipient_data)
            
            # Send notification (implement email service)
            # await send_update_email(recipient.recipient_email, card_id, updated_fields)
            
            # Update notification timestamp
            await db.cardrecipients.update_one(
                {"_id": recipient.id},
                {"$set": {"last_notified": datetime.utcnow()}}
            )
            
            notification_count += 1
        
        logger.info(f"Sent {notification_count} auto-update notifications for card {card_id}")
        
    except Exception as e:
        logger.error(f"Auto-update notifications failed: {str(e)}")

# ============================================================================
# OCR BUSINESS CARD SCANNER ENDPOINTS - GAME CHANGING FEATURE 
# ============================================================================

from models.CardScanner import (
    CardScanRequest, ScanResponse, ScanResultResponse, ScanListResponse,
    FieldCorrectionRequest, ConvertToCardRequest, ScanBatchRequest
)
from services.OCRService import ocr_service

@api_router.post("/scanner/scan", response_model=ScanResponse)
async def scan_business_card(
    scan_request: CardScanRequest,
    current_user: User = Depends(get_current_user)
):
    """Scan business card image using OCR - Paper → Digital"""
    try:
        logger.info(f"Starting business card scan for user {current_user.email}")
        
        # Process the scan
        scan_result = await ocr_service.scan_business_card(
            image_data=scan_request.image_data,
            user_id=str(current_user.id),
            scan_method=scan_request.scan_method
        )
        
        # Save scan to database
        scan_dict = scan_result.dict(by_alias=True, exclude={"id"})
        result = await db.scannedcards.insert_one(scan_dict)
        scan_result.id = str(result.inserted_id)
        
        return ScanResponse(
            success=True,
            scan_id=str(scan_result.id),
            status=scan_result.status,
            message="Visitenkarte erfolgreich gescannt! ✨",
            estimated_completion_seconds=3 if scan_result.status == "pending" else None
        )
        
    except Exception as e:
        logger.error(f"Business card scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan fehlgeschlagen: {str(e)}")

@api_router.get("/scanner/scan/{scan_id}", response_model=ScanResultResponse)
async def get_scan_result(
    scan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get OCR scan results"""
    try:
        # Find scan
        from bson import ObjectId
        scan_data = await db.scannedcards.find_one({
            "_id": ObjectId(scan_id),
            "user_id": str(current_user.id)
        })
        
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan nicht gefunden")
        
        # Convert ObjectId to string
        if "_id" in scan_data:
            scan_data["_id"] = str(scan_data["_id"])
        
        from models.CardScanner import ScannedBusinessCard
        scan = ScannedBusinessCard(**scan_data)
        
        # Check if ready for conversion
        conversion_ready = (
            scan.status == "completed" and 
            scan.overall_confidence >= 60.0 and
            len(scan.extracted_fields) >= 2  # At least name + one contact
        )
        
        return ScanResultResponse(
            scan_id=scan_id,
            status=scan.status,
            scanned_card=scan,
            conversion_ready=conversion_ready
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan result: {str(e)}")
        raise HTTPException(status_code=500, detail="Scan-Ergebnis konnte nicht geladen werden")

@api_router.post("/scanner/scan/{scan_id}/correct")
async def correct_scan_field(
    scan_id: str,
    correction: FieldCorrectionRequest,
    current_user: User = Depends(get_current_user)
):
    """Correct OCR field extraction"""
    try:
        # Apply correction
        success = await ocr_service.correct_field(
            scan_id=scan_id,
            field_type=correction.field_type,
            corrected_value=correction.corrected_value
        )
        
        if success:
            return {"success": True, "message": "Korrektur angewendet"}
        else:
            raise HTTPException(status_code=500, detail="Korrektur fehlgeschlagen")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Field correction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Korrektur fehlgeschlagen")

@api_router.post("/scanner/scan/{scan_id}/convert", response_model=BusinessCardResponse)
async def convert_scan_to_card(
    scan_id: str,
    convert_request: ConvertToCardRequest,
    current_user: User = Depends(get_current_user)
):
    """Convert scanned card to digital business card"""
    try:
        # Get scan
        from bson import ObjectId
        scan_data = await db.scannedcards.find_one({
            "_id": ObjectId(scan_id),
            "user_id": str(current_user.id)
        })
        
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan nicht gefunden")
        
        from models.CardScanner import ScannedBusinessCard
        scan = ScannedBusinessCard(**scan_data)
        
        if scan.status != "completed":
            raise HTTPException(status_code=400, detail="Scan noch nicht abgeschlossen")
        
        # Create business card from scan
        card_data = {
            "name": convert_request.card_name,
            "phones": [],
            "emails": [],
            "social_media": SocialMedia(),
            "is_public": True,
            "accent_color": "#3B82F6"
        }
        
        # Map fields from scan
        field_mapping = convert_request.field_mapping or scan.suggested_mapping or {}
        
        for field in scan.extracted_fields:
            if field.field_type == "company" and "company" in field_mapping:
                card_data["company"] = field.value
            elif field.field_type == "position" and "position" in field_mapping:
                card_data["position"] = field.value
            elif field.field_type == "phone" and field.confidence >= 70:
                card_data["phones"].append({
                    "label": "Business",
                    "number": field.value,
                    "is_primary": True,
                    "messaging_apps": [
                        {"name": "whatsapp", "enabled": True},
                        {"name": "sms", "enabled": True}
                    ]
                })
            elif field.field_type == "email" and field.confidence >= 80:
                card_data["emails"].append({
                    "label": "Business", 
                    "address": field.value,
                    "is_primary": True
                })
            elif field.field_type == "website" and field.confidence >= 85:
                card_data["website"] = field.value
        
        # Create business card
        card = BusinessCard(
            user_id=str(current_user.id),
            **card_data
        )
        
        # Insert into database
        card_dict = card.dict(by_alias=True, exclude={"id"})
        result = await db.businesscards.insert_one(card_dict)
        card.id = str(result.inserted_id)
        
        # Update scan with conversion info
        await db.scannedcards.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$set": {
                    "converted_to_card_id": str(card.id),
                    "is_converted": True
                }
            }
        )
        
        logger.info(f"Successfully converted scan {scan_id} to business card {card.id}")
        
        return BusinessCardResponse(
            id=str(card.id),
            **card.dict(exclude={"id", "user_id"}),
            is_owner=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Konvertierung fehlgeschlagen: {str(e)}")

@api_router.get("/scanner/scans", response_model=ScanListResponse)
async def list_scanned_cards(
    current_user: User = Depends(get_current_user)
):
    """List all scanned business cards for user"""
    try:
        scans_cursor = db.scannedcards.find({"user_id": str(current_user.id)})
        scans = []
        pending_count = 0
        converted_count = 0
        
        from models.CardScanner import ScannedBusinessCard
        async for scan_data in scans_cursor:
            if "_id" in scan_data:
                scan_data["_id"] = str(scan_data["_id"])
            
            scan = ScannedBusinessCard(**scan_data)
            scans.append(scan)
            
            if scan.status == "pending":
                pending_count += 1
            if scan.is_converted:
                converted_count += 1
        
        return ScanListResponse(
            scans=scans,
            total_count=len(scans),
            pending_count=pending_count,
            converted_count=converted_count
        )
        
    except Exception as e:
        logger.error(f"Failed to list scanned cards: {str(e)}")
        raise HTTPException(status_code=500, detail="Gescannte Karten konnten nicht geladen werden")

# ============================================================================
# PRINT EXPORT ENDPOINTS - GAME CHANGING FEATURE
# ============================================================================

from models.PrintExport import (
    PrintExportRequest, QuickPrintRequest, PrintPreviewRequest,
    PrintJobResponse, PrintTemplateResponse, PrintJobStatusResponse
)
from services.PrintService import print_service

@api_router.get("/print/templates", response_model=PrintTemplateResponse)
async def get_print_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get available print templates"""
    try:
        templates = await print_service.get_templates(category)
        categories = await print_service.get_template_categories()
        
        return PrintTemplateResponse(
            templates=templates,
            categories=categories,
            total_count=len(templates)
        )
        
    except Exception as e:
        logger.error(f"Failed to get print templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Druckvorlagen konnten nicht geladen werden")

@api_router.post("/print/export", response_model=PrintJobResponse)
async def export_for_printing(
    export_request: PrintExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Export business card for professional printing"""
    try:
        # Get business card
        from bson import ObjectId
        card_data = await db.businesscards.find_one({
            "_id": export_request.business_card_id,
            "userId": str(current_user.id)
        })
        
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({
                    "_id": ObjectId(export_request.business_card_id),
                    "userId": str(current_user.id)
                })
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Create print job
        print_job = await print_service.create_print_job(
            business_card=card,
            template_id=export_request.template_id,
            format=export_request.format,
            quality=export_request.quality,
            size=export_request.size,
            orientation=export_request.orientation,
            custom_colors=export_request.custom_colors,
            include_bleed=export_request.include_bleed,
            include_crop_marks=export_request.include_crop_marks,
            double_sided=export_request.double_sided,
            quantity=export_request.quantity,
            printer_id=export_request.printer_id
        )
        
        # Save print job to database
        job_dict = print_job.dict(by_alias=True, exclude={"id"})
        result = await db.printjobs.insert_one(job_dict)
        print_job.id = str(result.inserted_id)
        
        logger.info(f"Print job created: {print_job.id} for card {card.name}")
        
        return PrintJobResponse(
            success=True,
            job_id=str(print_job.id),
            status=print_job.status,
            preview_url=print_job.preview_url,
            estimated_completion_minutes=2 if print_job.status == "pending" else None,
            message="Druckdatei wird erstellt... 🖨️"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Print export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Druckexport fehlgeschlagen: {str(e)}")

@api_router.post("/print/quick", response_model=PrintJobResponse)
async def quick_print_export(
    quick_request: QuickPrintRequest,
    current_user: User = Depends(get_current_user)
):
    """Quick print export with default settings"""
    try:
        # Use first available template
        templates = await print_service.get_templates()
        if not templates:
            raise HTTPException(status_code=500, detail="Keine Druckvorlagen verfügbar")
        
        default_template = templates[0]  # Use first template
        
        export_request = PrintExportRequest(
            business_card_id=quick_request.business_card_id,
            template_id=default_template.id,
            format=quick_request.format,
            size=quick_request.size,
            quality=quick_request.quality
        )
        
        return await export_for_printing(export_request, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick print failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Schnelldruck fehlgeschlagen")

@api_router.post("/print/preview", response_model=Dict[str, str])
async def generate_print_preview(
    preview_request: PrintPreviewRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate print preview"""
    try:
        # Get business card
        from bson import ObjectId
        card_data = await db.businesscards.find_one({
            "_id": preview_request.business_card_id,
            "userId": str(current_user.id)
        })
        
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({
                    "_id": ObjectId(preview_request.business_card_id),
                    "userId": str(current_user.id)
                })
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Get template
        templates = await print_service.get_templates()
        template = next((t for t in templates if t.id == preview_request.template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Druckvorlage nicht gefunden")
        
        # Generate preview
        from models.PrintExport import PrintJob, PrintFormat, PrintQuality
        preview_job = PrintJob(
            user_id=str(current_user.id),
            business_card_id=str(card.id),
            template_id=template.id,
            format=PrintFormat.PNG,
            quality=PrintQuality.WEB,
            size=preview_request.size,
            orientation=preview_request.orientation
        )
        
        preview_url = await print_service._generate_preview(card, template, preview_job)
        
        return {
            "preview_url": preview_url,
            "template_name": template.name,
            "size": preview_request.size.value,
            "orientation": preview_request.orientation.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Vorschau-Erstellung fehlgeschlagen")

@api_router.get("/print/jobs/{job_id}", response_model=PrintJobStatusResponse)
async def get_print_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get print job status and download URLs"""
    try:
        from bson import ObjectId
        job_data = await db.printjobs.find_one({
            "_id": ObjectId(job_id),
            "user_id": str(current_user.id)
        })
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Druckauftrag nicht gefunden")
        
        if "_id" in job_data:
            job_data["_id"] = str(job_data["_id"])
        
        from models.PrintExport import PrintJob
        job = PrintJob(**job_data)
        
        # Calculate progress
        progress = 0
        if job.status == "pending":
            progress = 10
        elif job.status == "processing":
            progress = 50
        elif job.status == "completed":
            progress = 100
        elif job.status == "failed":
            progress = 0
        
        # Get download URL if completed
        download_url = None
        if job.status == "completed" and job.generated_files:
            # In a real implementation, this would be a proper file URL
            download_url = job.generated_files[0].get("url")
        
        return PrintJobStatusResponse(
            job_id=job_id,
            status=job.status,
            progress_percentage=progress,
            download_url=download_url,
            preview_url=job.preview_url,
            error_message=job.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get print job status: {str(e)}")
        raise HTTPException(status_code=500, detail="Druckauftrags-Status konnte nicht geladen werden")

# ============================================================================
# OCR BUSINESS CARD SCANNER ENDPOINTS - GAME CHANGING FEATURE 
# ============================================================================

from models.CardScanner import (
    CardScanRequest, ScanResponse, ScanResultResponse, ScanListResponse,
    FieldCorrectionRequest, ConvertToCardRequest, ScanBatchRequest
)
from services.OCRService import ocr_service

@api_router.post("/scanner/scan", response_model=ScanResponse)
async def scan_business_card(
    scan_request: CardScanRequest,
    current_user: User = Depends(get_current_user)
):
    """Scan business card image using OCR - Paper → Digital"""
    try:
        logger.info(f"Starting business card scan for user {current_user.email}")
        
        # Process the scan
        scan_result = await ocr_service.scan_business_card(
            image_data=scan_request.image_data,
            user_id=str(current_user.id),
            scan_method=scan_request.scan_method
        )
        
        # Save scan to database
        scan_dict = scan_result.dict(by_alias=True, exclude={"id"})
        result = await db.scannedcards.insert_one(scan_dict)
        scan_result.id = str(result.inserted_id)
        
        return ScanResponse(
            success=True,
            scan_id=str(scan_result.id),
            status=scan_result.status,
            message="Visitenkarte erfolgreich gescannt! ✨",
            estimated_completion_seconds=3 if scan_result.status == "pending" else None
        )
        
    except Exception as e:
        logger.error(f"Business card scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan fehlgeschlagen: {str(e)}")

@api_router.get("/scanner/scan/{scan_id}", response_model=ScanResultResponse)
async def get_scan_result(
    scan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get OCR scan results"""
    try:
        # Find scan
        from bson import ObjectId
        scan_data = await db.scannedcards.find_one({
            "_id": ObjectId(scan_id),
            "user_id": str(current_user.id)
        })
        
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan nicht gefunden")
        
        # Convert ObjectId to string
        if "_id" in scan_data:
            scan_data["_id"] = str(scan_data["_id"])
        
        from models.CardScanner import ScannedBusinessCard
        scan = ScannedBusinessCard(**scan_data)
        
        # Check if ready for conversion
        conversion_ready = (
            scan.status == "completed" and 
            scan.overall_confidence >= 60.0 and
            len(scan.extracted_fields) >= 2  # At least name + one contact
        )
        
        return ScanResultResponse(
            scan_id=scan_id,
            status=scan.status,
            scanned_card=scan,
            conversion_ready=conversion_ready
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan result: {str(e)}")
        raise HTTPException(status_code=500, detail="Scan-Ergebnis konnte nicht geladen werden")

@api_router.post("/scanner/scan/{scan_id}/correct")
async def correct_scan_field(
    scan_id: str,
    correction: FieldCorrectionRequest,
    current_user: User = Depends(get_current_user)
):
    """Correct OCR field extraction"""
    try:
        # Apply correction
        success = await ocr_service.correct_field(
            scan_id=scan_id,
            field_type=correction.field_type,
            corrected_value=correction.corrected_value
        )
        
        if success:
            return {"success": True, "message": "Korrektur angewendet"}
        else:
            raise HTTPException(status_code=500, detail="Korrektur fehlgeschlagen")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Field correction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Korrektur fehlgeschlagen")

@api_router.post("/scanner/scan/{scan_id}/convert", response_model=BusinessCardResponse)
async def convert_scan_to_card(
    scan_id: str,
    convert_request: ConvertToCardRequest,
    current_user: User = Depends(get_current_user)
):
    """Convert scanned card to digital business card"""
    try:
        # Get scan
        from bson import ObjectId
        scan_data = await db.scannedcards.find_one({
            "_id": ObjectId(scan_id),
            "user_id": str(current_user.id)
        })
        
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan nicht gefunden")
        
        from models.CardScanner import ScannedBusinessCard
        scan = ScannedBusinessCard(**scan_data)
        
        if scan.status != "completed":
            raise HTTPException(status_code=400, detail="Scan noch nicht abgeschlossen")
        
        # Create business card from scan
        card_data = {
            "name": convert_request.card_name,
            "phones": [],
            "emails": [],
            "social_media": SocialMedia(),
            "is_public": True,
            "accent_color": "#3B82F6"
        }
        
        # Map fields from scan
        field_mapping = convert_request.field_mapping or scan.suggested_mapping or {}
        
        for field in scan.extracted_fields:
            if field.field_type == "company" and "company" in field_mapping:
                card_data["company"] = field.value
            elif field.field_type == "position" and "position" in field_mapping:
                card_data["position"] = field.value
            elif field.field_type == "phone" and field.confidence >= 70:
                card_data["phones"].append({
                    "label": "Business",
                    "number": field.value,
                    "is_primary": True,
                    "messaging_apps": [
                        {"name": "whatsapp", "enabled": True},
                        {"name": "sms", "enabled": True}
                    ]
                })
            elif field.field_type == "email" and field.confidence >= 80:
                card_data["emails"].append({
                    "label": "Business", 
                    "address": field.value,
                    "is_primary": True
                })
            elif field.field_type == "website" and field.confidence >= 85:
                card_data["website"] = field.value
        
        # Create business card
        card = BusinessCard(
            user_id=str(current_user.id),
            **card_data
        )
        
        # Insert into database
        card_dict = card.dict(by_alias=True, exclude={"id"})
        result = await db.businesscards.insert_one(card_dict)
        card.id = str(result.inserted_id)
        
        # Update scan with conversion info
        await db.scannedcards.update_one(
            {"_id": ObjectId(scan_id)},
            {
                "$set": {
                    "converted_to_card_id": str(card.id),
                    "is_converted": True
                }
            }
        )
        
        logger.info(f"Successfully converted scan {scan_id} to business card {card.id}")
        
        return BusinessCardResponse(
            id=str(card.id),
            **card.dict(exclude={"id", "user_id"}),
            is_owner=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Konvertierung fehlgeschlagen: {str(e)}")

@api_router.get("/scanner/scans", response_model=ScanListResponse)
async def list_scanned_cards(
    current_user: User = Depends(get_current_user)
):
    """List all scanned business cards for user"""
    try:
        scans_cursor = db.scannedcards.find({"user_id": str(current_user.id)})
        scans = []
        pending_count = 0
        converted_count = 0
        
        from models.CardScanner import ScannedBusinessCard
        async for scan_data in scans_cursor:
            if "_id" in scan_data:
                scan_data["_id"] = str(scan_data["_id"])
            
            scan = ScannedBusinessCard(**scan_data)
            scans.append(scan)
            
            if scan.status == "pending":
                pending_count += 1
            if scan.is_converted:
                converted_count += 1
        
        return ScanListResponse(
            scans=scans,
            total_count=len(scans),
            pending_count=pending_count,
            converted_count=converted_count
        )
        
    except Exception as e:
        logger.error(f"Failed to list scanned cards: {str(e)}")
        raise HTTPException(status_code=500, detail="Gescannte Karten konnten nicht geladen werden")

# ============================================================================
# PRINT EXPORT ENDPOINTS - GAME CHANGING FEATURE
# ============================================================================

from models.PrintExport import (
    PrintExportRequest, QuickPrintRequest, PrintPreviewRequest,
    PrintJobResponse, PrintTemplateResponse, PrintJobStatusResponse
)
from services.PrintService import print_service

@api_router.get("/print/templates", response_model=PrintTemplateResponse)
async def get_print_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get available print templates"""
    try:
        templates = await print_service.get_templates(category)
        categories = await print_service.get_template_categories()
        
        return PrintTemplateResponse(
            templates=templates,
            categories=categories,
            total_count=len(templates)
        )
        
    except Exception as e:
        logger.error(f"Failed to get print templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Druckvorlagen konnten nicht geladen werden")

@api_router.post("/print/export", response_model=PrintJobResponse)
async def export_for_printing(
    export_request: PrintExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Export business card for professional printing"""
    try:
        # Get business card
        from bson import ObjectId
        card_data = await db.businesscards.find_one({
            "_id": export_request.business_card_id,
            "userId": str(current_user.id)
        })
        
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({
                    "_id": ObjectId(export_request.business_card_id),
                    "userId": str(current_user.id)
                })
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Create print job
        print_job = await print_service.create_print_job(
            business_card=card,
            template_id=export_request.template_id,
            format=export_request.format,
            quality=export_request.quality,
            size=export_request.size,
            orientation=export_request.orientation,
            custom_colors=export_request.custom_colors,
            include_bleed=export_request.include_bleed,
            include_crop_marks=export_request.include_crop_marks,
            double_sided=export_request.double_sided,
            quantity=export_request.quantity,
            printer_id=export_request.printer_id
        )
        
        # Save print job to database
        job_dict = print_job.dict(by_alias=True, exclude={"id"})
        result = await db.printjobs.insert_one(job_dict)
        print_job.id = str(result.inserted_id)
        
        logger.info(f"Print job created: {print_job.id} for card {card.name}")
        
        return PrintJobResponse(
            success=True,
            job_id=str(print_job.id),
            status=print_job.status,
            preview_url=print_job.preview_url,
            estimated_completion_minutes=2 if print_job.status == "pending" else None,
            message="Druckdatei wird erstellt... 🖨️"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Print export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Druckexport fehlgeschlagen: {str(e)}")

@api_router.post("/print/quick", response_model=PrintJobResponse)
async def quick_print_export(
    quick_request: QuickPrintRequest,
    current_user: User = Depends(get_current_user)
):
    """Quick print export with default settings"""
    try:
        # Use first available template
        templates = await print_service.get_templates()
        if not templates:
            raise HTTPException(status_code=500, detail="Keine Druckvorlagen verfügbar")
        
        default_template = templates[0]  # Use first template
        
        export_request = PrintExportRequest(
            business_card_id=quick_request.business_card_id,
            template_id=default_template.id,
            format=quick_request.format,
            size=quick_request.size,
            quality=quick_request.quality
        )
        
        return await export_for_printing(export_request, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick print failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Schnelldruck fehlgeschlagen")

@api_router.post("/print/preview", response_model=Dict[str, str])
async def generate_print_preview(
    preview_request: PrintPreviewRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate print preview"""
    try:
        # Get business card
        from bson import ObjectId
        card_data = await db.businesscards.find_one({
            "_id": preview_request.business_card_id,
            "userId": str(current_user.id)
        })
        
        if not card_data:
            try:
                card_data = await db.businesscards.find_one({
                    "_id": ObjectId(preview_request.business_card_id),
                    "userId": str(current_user.id)
                })
            except:
                pass
        
        if not card_data:
            raise HTTPException(status_code=404, detail="Visitenkarte nicht gefunden")
        
        # Convert ObjectId to string
        if "_id" in card_data:
            card_data["_id"] = str(card_data["_id"])
        if "userId" in card_data:
            card_data["userId"] = str(card_data["userId"])
        
        card = BusinessCard(**card_data)
        
        # Get template
        templates = await print_service.get_templates()
        template = next((t for t in templates if t.id == preview_request.template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Druckvorlage nicht gefunden")
        
        # Generate preview
        from models.PrintExport import PrintJob, PrintFormat, PrintQuality
        preview_job = PrintJob(
            user_id=str(current_user.id),
            business_card_id=str(card.id),
            template_id=template.id,
            format=PrintFormat.PNG,
            quality=PrintQuality.WEB,
            size=preview_request.size,
            orientation=preview_request.orientation
        )
        
        preview_url = await print_service._generate_preview(card, template, preview_job)
        
        return {
            "preview_url": preview_url,
            "template_name": template.name,
            "size": preview_request.size.value,
            "orientation": preview_request.orientation.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Vorschau-Erstellung fehlgeschlagen")

@api_router.get("/print/jobs/{job_id}", response_model=PrintJobStatusResponse)
async def get_print_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get print job status and download URLs"""
    try:
        from bson import ObjectId
        job_data = await db.printjobs.find_one({
            "_id": ObjectId(job_id),
            "user_id": str(current_user.id)
        })
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Druckauftrag nicht gefunden")
        
        if "_id" in job_data:
            job_data["_id"] = str(job_data["_id"])
        
        from models.PrintExport import PrintJob
        job = PrintJob(**job_data)
        
        # Calculate progress
        progress = 0
        if job.status == "pending":
            progress = 10
        elif job.status == "processing":
            progress = 50
        elif job.status == "completed":
            progress = 100
        elif job.status == "failed":
            progress = 0
        
        # Get download URL if completed
        download_url = None
        if job.status == "completed" and job.generated_files:
            # In a real implementation, this would be a proper file URL
            download_url = job.generated_files[0].get("url")
        
        return PrintJobStatusResponse(
            job_id=job_id,
            status=job.status,
            progress_percentage=progress,
            download_url=download_url,
            preview_url=job.preview_url,
            error_message=job.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get print job status: {str(e)}")
        raise HTTPException(status_code=500, detail="Druckauftrags-Status konnte nicht geladen werden")

# Include the router in the main app
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database indexes and background tasks"""
    try:
        # Create indexes for better performance
        await db.users.create_index("email", unique=True)
        await db.businesscards.create_index("userId")
        # Drop existing custom_code index if it exists to fix null value conflicts
        try:
            await db.businesscards.drop_index("custom_code_1")
        except:
            pass  # Index might not exist
        
        # Create sparse unique index that only indexes non-null custom_code values
        await db.businesscards.create_index(
            "custom_code", 
            unique=True, 
            sparse=True
        )
        await db.businesscards.create_index([("is_public", 1), ("created_at", -1)])
        await db.cardrecipients.create_index("card_id")
        await db.cardanalytics.create_index([("card_id", 1), ("timestamp", -1)])
        
        # Meeting room indexes
        await db.meetingrooms.create_index("code")
        await db.meetingrooms.create_index("created_by_card_id")
        await db.meetingrooms.create_index([("is_active", 1), ("expires_at", 1)])
        
        # Express share indexes with compound uniqueness
        await db.expresscodes.create_index("code")
        await db.expresscodes.create_index("card_id")
        await db.expresscodes.create_index([("is_active", 1), ("expires_at", 1)])
        # Compound unique index to prevent duplicate active codes
        await db.expresscodes.create_index([("code", 1), ("is_active", 1), ("expires_at", 1)], sparse=True)
        
        await db.expressrooms.create_index("code")
        await db.expressrooms.create_index("created_by_card_id")
        await db.expressrooms.create_index([("is_active", 1), ("expires_at", 1)])
        # Compound unique index to prevent duplicate active room codes
        await db.expressrooms.create_index([("code", 1), ("is_active", 1), ("expires_at", 1)], sparse=True)
        
        # Contact import indexes
        await db.contactsources.create_index("user_id")
        await db.contactsources.create_index([("user_id", 1), ("source_type", 1)])
        await db.importedcontacts.create_index("user_id")
        await db.importedcontacts.create_index("source_id")
        await db.importedcontacts.create_index([("user_id", 1), ("name", 1)])
        await db.importedcontacts.create_index("external_id", sparse=True)
        await db.syncjobs.create_index("user_id")
        await db.syncjobs.create_index([("status", 1), ("scheduled_at", 1)])
        
        # Subscription and monetization indexes
        await db.usersubscriptions.create_index("user_id", unique=True)
        await db.usersubscriptions.create_index([("plan_type", 1), ("status", 1)])
        await db.usersubscriptions.create_index("expires_at", sparse=True)
        await db.usageevents.create_index("user_id")
        await db.usageevents.create_index([("user_id", 1), ("timestamp", -1)])
        await db.usageevents.create_index("event_type")
        await db.upgradeprompts.create_index("user_id")
        await db.upgradeprompts.create_index([("user_id", 1), ("shown_at", -1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Startup initialization failed: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    client.close()
    logger.info("Database connection closed")
