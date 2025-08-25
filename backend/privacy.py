from fastapi import HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from models.User import User, GDPRExport, AccountDeletion
from models.BusinessCard import BusinessCard, CardRecipient, CardAnalytics
from auth import get_current_user
import os
import json
import logging

logger = logging.getLogger(__name__)

class PrivacyService:
    """GDPR-compliant privacy service"""
    
    def __init__(self, db):
        self.db = db
    
    async def export_user_data(self, user: User) -> GDPRExport:
        """Export all user data for GDPR compliance"""
        try:
            # Get user's business cards using string user ID
            user_id_str = str(user.id)
            cards_cursor = self.db.businesscards.find({"userId": user_id_str})
            business_cards = []
            
            async for card_data in cards_cursor:
                # Convert ObjectId to string for consistency
                if "_id" in card_data:
                    card_data["_id"] = str(card_data["_id"])
                if "userId" in card_data:
                    card_data["userId"] = str(card_data["userId"])
                    
                card = BusinessCard(**card_data)
                business_cards.append(card.dict(exclude={"id", "user_id"}))
            
            # Get recipients (people who received user's cards)
            card_ids = [card["_id"] for card in business_cards]
            recipients = []
            
            if card_ids:
                recipients_cursor = self.db.cardrecipients.find({"card_id": {"$in": card_ids}})
                
                async for recipient_data in recipients_cursor:
                    # Convert ObjectId to string
                    if "_id" in recipient_data:
                        recipient_data["_id"] = str(recipient_data["_id"])
                    if "card_id" in recipient_data:
                        recipient_data["card_id"] = str(recipient_data["card_id"])
                        
                    recipient = CardRecipient(**recipient_data)
                    recipients.append(recipient.dict(exclude={"card_id"}))
            
            # Get analytics summary (anonymized)
            analytics_summary = {
                "total_views": 0,
                "total_downloads": 0,
                "total_shares": 0,
                "total_qr_scans": 0,
                "countries": {},
                "referrers": {}
            }
            
            if card_ids:
                analytics_cursor = self.db.cardanalytics.find({"card_id": {"$in": card_ids}})
                
                async for analytics_data in analytics_cursor:
                    # Convert ObjectId to string
                    if "_id" in analytics_data:
                        analytics_data["_id"] = str(analytics_data["_id"])
                    if "card_id" in analytics_data:
                        analytics_data["card_id"] = str(analytics_data["card_id"])
                        
                    analytics = CardAnalytics(**analytics_data)
                    
                    # Count actions
                    if analytics.action == "view":
                        analytics_summary["total_views"] += 1
                    elif analytics.action == "download":
                        analytics_summary["total_downloads"] += 1
                    elif analytics.action == "share":
                        analytics_summary["total_shares"] += 1
                    elif analytics.action == "qr_scan":
                        analytics_summary["total_qr_scans"] += 1
                    
                    # Count countries (anonymized)
                    if analytics.country:
                        analytics_summary["countries"][analytics.country] = \
                            analytics_summary["countries"].get(analytics.country, 0) + 1
                    
                    # Count referrers (anonymized)
                    if analytics.referrer:
                        domain = self._extract_domain(analytics.referrer)
                        analytics_summary["referrers"][domain] = \
                            analytics_summary["referrers"].get(domain, 0) + 1
            
            # Create export data
            export_data = GDPRExport(
                user_data={
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "privacy_settings": user.privacy_settings.dict(),
                    "gdpr_consent": user.gdpr_consent.dict(),
                    "created_at": user.created_at.isoformat(),
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
                },
                business_cards=business_cards,
                recipients=recipients,
                analytics_summary=analytics_summary
            )
            
            logger.info(f"Data export completed for user {user.email}")
            return export_data
            
        except Exception as e:
            logger.error(f"Data export failed for user {user.email}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Data export failed: {str(e)}")
    
    async def delete_user_account(self, user: User, deletion_request: AccountDeletion) -> bool:
        """Permanently delete user account and all associated data"""
        try:
            # Verify password
            if not user.verify_password(deletion_request.password):
                raise HTTPException(status_code=400, detail="Invalid password")
            
            # Verify confirmation
            if deletion_request.confirmation != "DELETE_MY_ACCOUNT":
                raise HTTPException(status_code=400, detail="Invalid confirmation")
            
            # Log deletion reason for compliance
            logger.info(f"Account deletion initiated for user {user.email}. Reason: {deletion_request.reason}")
            
            # Get user's business cards
            cards_cursor = self.db.businesscards.find({"userId": user.id})
            card_ids = []
            
            async for card_data in cards_cursor:
                card_ids.append(card_data["_id"])
            
            # Delete in order (foreign key constraints)
            
            # 1. Delete analytics
            if card_ids:
                await self.db.cardanalytics.delete_many({"card_id": {"$in": card_ids}})
                logger.info(f"Deleted analytics for {len(card_ids)} cards")
            
            # 2. Delete recipients
            if card_ids:
                await self.db.cardrecipients.delete_many({"card_id": {"$in": card_ids}})
                logger.info(f"Deleted recipients for {len(card_ids)} cards")
            
            # 3. Delete business cards
            if card_ids:
                await self.db.businesscards.delete_many({"userId": user.id})
                logger.info(f"Deleted {len(card_ids)} business cards")
            
            # 4. Delete user account
            await self.db.users.delete_one({"_id": user.id})
            logger.info(f"Deleted user account {user.email}")
            
            # 5. Log completion for audit trail
            audit_record = {
                "action": "account_deletion",
                "user_email": user.email,
                "user_id": str(user.id),
                "timestamp": datetime.utcnow(),
                "reason": deletion_request.reason,
                "cards_deleted": len(card_ids)
            }
            
            await self.db.audit_log.insert_one(audit_record)
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Account deletion failed for user {user.email}: {str(e)}")
            raise HTTPException(status_code=500, detail="Account deletion failed")
    
    async def anonymize_analytics(self, card_id: str, days_to_keep: int = 90) -> bool:
        """Anonymize analytics data older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Remove detailed analytics older than cutoff
            result = await self.db.cardanalytics.update_many(
                {
                    "card_id": card_id,
                    "timestamp": {"$lt": cutoff_date}
                },
                {
                    "$unset": {
                        "user_agent": "",
                        "referrer": ""
                    }
                }
            )
            
            logger.info(f"Anonymized {result.modified_count} analytics records for card {card_id}")
            return True
            
        except Exception as e:
            logger.error(f"Analytics anonymization failed for card {card_id}: {str(e)}")
            return False
    
    async def cleanup_inactive_accounts(self, days_inactive: int = 730) -> int:
        """Clean up accounts inactive for specified days (GDPR Article 5)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
            
            # Find inactive users
            inactive_users = await self.db.users.find({
                "last_login_at": {"$lt": cutoff_date},
                "is_active": True
            }).to_list(None)
            
            deleted_count = 0
            
            for user_data in inactive_users:
                user = User(**user_data)
                
                # Send notification email before deletion (implement email service)
                # await self.send_deletion_warning_email(user.email)
                
                # Mark for deletion instead of immediate deletion
                await self.db.users.update_one(
                    {"_id": user.id},
                    {
                        "$set": {
                            "is_active": False,
                            "scheduled_for_deletion": datetime.utcnow() + timedelta(days=30)
                        }
                    }
                )
                
                deleted_count += 1
                logger.info(f"Marked inactive account {user.email} for deletion")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Inactive account cleanup failed: {str(e)}")
            return 0
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for privacy-safe analytics"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc or "direct"
        except:
            return "unknown"
    
    async def get_privacy_compliance_report(self, user: User) -> Dict[str, Any]:
        """Generate privacy compliance report for user"""
        try:
            # Count user's data using string user ID
            user_id_str = str(user.id)
            cards_count = await self.db.businesscards.count_documents({"userId": user_id_str})
            
            card_ids = []
            async for card in self.db.businesscards.find({"userId": user_id_str}, {"_id": 1}):
                card_ids.append(str(card["_id"]))
            
            recipients_count = 0
            analytics_count = 0
            
            if card_ids:
                recipients_count = await self.db.cardrecipients.count_documents(
                    {"card_id": {"$in": card_ids}}
                )
                analytics_count = await self.db.cardanalytics.count_documents(
                    {"card_id": {"$in": card_ids}}
                )
            
            # Calculate data age
            account_age = (datetime.utcnow() - user.created_at).days
            
            report = {
                "user_id": str(user.id),
                "account_age_days": account_age,
                "gdpr_consent": user.gdpr_consent.dict(),
                "privacy_settings": user.privacy_settings.dict(),
                "data_summary": {
                    "business_cards": cards_count,
                    "recipients": recipients_count,
                    "analytics_records": analytics_count
                },
                "compliance_status": {
                    "gdpr_consent_given": user.gdpr_consent.consent,
                    "privacy_policy_accepted": True,  # Assume true if account exists
                    "data_retention_compliant": account_age <= user.privacy_settings.data_retention_days,
                    "can_request_export": True,
                    "can_request_deletion": True
                },
                "rights_info": {
                    "right_to_access": "You can export all your data at any time",
                    "right_to_rectification": "You can edit your data through the app",
                    "right_to_erasure": "You can delete your account permanently",
                    "right_to_portability": "Export includes all data in JSON format",
                    "right_to_object": "You can opt out of analytics and marketing"
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Privacy report generation failed for user {user.email}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Privacy report generation failed: {str(e)}")

# Background task for periodic cleanup
async def scheduled_privacy_cleanup():
    """Scheduled task for GDPR compliance cleanup"""
    from server import db
    
    privacy_service = PrivacyService(db)
    
    # Clean up inactive accounts
    deleted_count = await privacy_service.cleanup_inactive_accounts()
    logger.info(f"Privacy cleanup: marked {deleted_count} inactive accounts for deletion")
    
    # Anonymize old analytics for all cards
    cards_cursor = db.businesscards.find({}, {"_id": 1})
    anonymized_count = 0
    
    async for card in cards_cursor:
        success = await privacy_service.anonymize_analytics(str(card["_id"]))
        if success:
            anonymized_count += 1
    
    logger.info(f"Privacy cleanup: anonymized analytics for {anonymized_count} cards")