# Digitale Visitenkarten App - Backend Contracts

## API Contracts

### Authentication & Users
```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET /api/auth/me
PUT /api/auth/profile
DELETE /api/auth/account
```

### Business Cards
```
POST /api/cards                    # Create new card
GET /api/cards                     # Get user's cards
GET /api/cards/:id                 # Get specific card (public or owned)
PUT /api/cards/:id                 # Update card (owner only)
DELETE /api/cards/:id              # Delete card (owner only)
GET /api/cards/:id/embed           # Get embed-friendly version
GET /api/cards/:id/qr              # Generate QR code
GET /api/cards/:id/vcard           # Generate vCard file
POST /api/cards/:id/share          # Track sharing analytics
```

### Privacy & Updates
```
GET /api/cards/:id/recipients      # Get update recipients (owner only)
POST /api/cards/:id/notify         # Send update notifications
PUT /api/cards/:id/privacy         # Update privacy settings
GET /api/privacy/export            # Export user data (GDPR)
DELETE /api/privacy/delete         # Delete all user data (GDPR)
```

## Mock Data Migration

### Currently Mocked in frontend/src/mock.js:
- `mockBusinessCards[]` → MongoDB collection `businesscards`
- `mockUser` → MongoDB collection `users` 
- Phone/Email arrays → Embedded documents in card schema
- Auto-update settings → New tracking system
- Social media links → Embedded object
- Color customization → Card schema fields

### Real Backend Implementation:
- Replace `mockApi.createBusinessCard()` → POST /api/cards
- Replace `mockApi.updateBusinessCard()` → PUT /api/cards/:id
- Replace `mockApi.getBusinessCard()` → GET /api/cards/:id
- Replace `mockApi.generateQRCode()` → GET /api/cards/:id/qr
- Replace `mockApi.generateVCard()` → GET /api/cards/:id/vcard
- Add real authentication system
- Implement auto-update notifications via email/push
- Add analytics tracking for card views

## Backend Implementation Plan

### 1. Database Schema (MongoDB)
```javascript
// Users Collection
{
  _id: ObjectId,
  email: String (unique, required),
  password: String (hashed),
  firstName: String,
  lastName: String,
  privacySettings: {
    allowAnalytics: Boolean,
    allowMarketing: Boolean,
    dataRetention: String
  },
  createdAt: Date,
  lastLoginAt: Date,
  gdprConsent: {
    consent: Boolean,
    consentDate: Date,
    ipAddress: String
  }
}

// Business Cards Collection
{
  _id: ObjectId,
  userId: ObjectId (ref: User),
  name: String (required),
  company: String,
  position: String,
  description: String,
  phones: [{
    id: String,
    label: String,
    number: String,
    isPrimary: Boolean
  }],
  emails: [{
    id: String,
    label: String,
    address: String,
    isPrimary: Boolean
  }],
  website: String,
  profileImage: String, // URL or base64
  logo: String, // URL or base64
  socialMedia: {
    instagram: String,
    linkedin: String,
    twitter: String,
    tiktok: String,
    telegram: String
  },
  isPublic: Boolean,
  backgroundColor: String,
  textColor: String,
  accentColor: String,
  embedBackgroundColor: String,
  allowEmbedding: Boolean,
  autoUpdateEnabled: Boolean,
  createdAt: Date,
  lastUpdated: Date,
  viewCount: Number,
  shareCount: Number
}

// Card Recipients (for auto-updates)
{
  _id: ObjectId,
  cardId: ObjectId (ref: BusinessCard),
  recipientEmail: String,
  recipientName: String,
  sharedAt: Date,
  lastNotified: Date,
  notificationMethod: String, // email, sms, push
  isActive: Boolean
}

// Analytics (Privacy-aware)
{
  _id: ObjectId,
  cardId: ObjectId (ref: BusinessCard),
  action: String, // view, download, share, qr_scan
  timestamp: Date,
  userAgent: String,
  country: String, // IP-derived, no exact location
  referrer: String
}
```

### 2. Privacy & Security Measures

**GDPR Compliance:**
- Explicit consent for data collection
- Right to data export (JSON format)
- Right to data deletion (complete removal)
- Data minimization (only collect necessary data)
- Anonymized analytics (no personal IPs stored)
- Cookie consent management
- Privacy policy integration

**Security:**
- JWT token authentication
- Password hashing (bcrypt)
- Rate limiting on API endpoints
- Input validation and sanitization
- CORS configuration
- Helmet.js security headers
- File upload validation (images only)
- SQL injection prevention (using MongoDB properly)

**Data Protection:**
- Encrypted sensitive fields
- Secure file storage
- Auto-deletion of inactive accounts (configurable)
- Audit logging for sensitive operations
- Backup encryption

### 3. Auto-Update System
- Track who receives cards via sharing
- Email notifications when card data changes
- Webhook system for real-time updates
- Batch notification processing
- Unsubscribe mechanism
- Delivery tracking and analytics

### 4. File Handling
- Image optimization and compression
- CDN integration for profile pictures/logos
- Secure file upload with virus scanning
- Multiple format support (jpg, png, webp)
- Image resizing for different use cases

## Frontend-Backend Integration

### Authentication Integration:
1. Add React Context for auth state management
2. Implement login/register forms
3. Add protected routes
4. Token management in localStorage/cookies
5. Automatic token refresh

### Data Flow Changes:
1. Replace all mock API calls with real axios requests
2. Add loading states for all operations
3. Implement proper error handling
4. Add optimistic updates for better UX
5. Cache frequently accessed data

### New Features to Add:
1. User dashboard with analytics
2. Card sharing management interface
3. Privacy settings page
4. Data export functionality
5. Account deletion process
6. Notification preferences
7. Recipient management for auto-updates

### Environment Variables:
```
MONGO_URL=existing
JWT_SECRET=new
UPLOAD_SECRET=new
EMAIL_SERVICE_KEY=new
CDN_URL=new
ENCRYPTION_KEY=new
```

## Security Checklist
- [ ] Input validation on all endpoints
- [ ] Authentication middleware
- [ ] Rate limiting
- [ ] CORS configuration
- [ ] Security headers
- [ ] File upload security
- [ ] Privacy compliance
- [ ] Data encryption at rest
- [ ] Secure session management
- [ ] Audit logging

## Testing Strategy
- Unit tests for all API endpoints
- Integration tests for auth flow
- Privacy compliance testing
- File upload security testing
- Performance testing for high card volumes
- GDPR compliance verification