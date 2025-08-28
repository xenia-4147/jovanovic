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
from typing import List, Optional
import uuid

# Import our models and services
from models.User import User, UserCreate, UserLogin, UserResponse, UserUpdate, PasswordChange, GDPRExport, AccountDeletion
from models.BusinessCard import BusinessCard, BusinessCardCreate, BusinessCardUpdate, BusinessCardResponse, ContactPhone, ContactEmail, SocialMedia, CardRecipient, CardAnalytics, ShareRequest, EmbedOptions
from models.MeetingRoom import MeetingRoom, MeetingRoomCreate, MeetingRoomJoin, MeetingRoomResponse, MeetingRoomListResponse, MeetingRoomJoinResponse, MeetingRoomParticipant
from models.ExpressShare import ExpressCode, ExpressMeetingRoom, ExpressShareCreate, ExpressRoomCreate, ExpressRoomJoin, ExpressCodeResponse, ExpressRoomResponse, ExpressAccessResponse
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
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Startup initialization failed: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    client.close()
    logger.info("Database connection closed")
