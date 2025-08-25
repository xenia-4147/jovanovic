from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from models.User import User

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token for user"""
    to_encode = {"sub": user_id, "type": "access"}
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token for user"""
    to_encode = {
        "sub": user_id, 
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(lambda: None)  # Will be replaced with actual DB dependency
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from Authorization header
        token = credentials.credentials
        
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database (will be implemented with actual DB)
    from server import db as database
    user_data = await database.users.find_one({"_id": user_id})
    
    if user_data is None:
        raise credentials_exception
    
    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated"
        )
    
    # Convert ObjectId to string for compatibility
    if "_id" in user_data:
        user_data["_id"] = str(user_data["_id"])
    
    return User(**user_data)

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db = Depends(lambda: None)
) -> Optional[User]:
    """Get current user if authenticated, None if not (for public endpoints)"""
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return user_id if valid"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            return None
            
        return user_id
        
    except JWTError:
        return None

class AuthService:
    """Service class for authentication operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    async def authenticate_user(db, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        user_data = await db.users.find_one({"email": email})
        
        if not user_data:
            return None
            
        user = User(**user_data)
        
        if not user.verify_password(password):
            return None
            
        return user
    
    @staticmethod
    async def create_user(db, user_create) -> User:
        """Create new user account"""
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_create.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user with GDPR consent
        from models.User import GDPRConsent, PrivacySettings
        
        gdpr_consent = GDPRConsent(
            consent=user_create.gdpr_consent,
            consent_date=datetime.utcnow(),
            consent_version="1.0"
        )
        
        privacy_settings = PrivacySettings(
            allow_analytics=user_create.privacy_consent,
            allow_marketing=user_create.marketing_consent
        )
        
        user = User(
            email=user_create.email,
            password_hash=user_create.password,  # Will be auto-hashed by validator
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            gdpr_consent=gdpr_consent,
            privacy_settings=privacy_settings
        )
        
        # Insert into database
        result = await db.users.insert_one(user.dict(by_alias=True, exclude={"id"}))
        user.id = result.inserted_id
        
        return user