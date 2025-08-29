"""
Community & Networking Service
Revolutionary Feature: Interest-based Matching with AI-powered Recommendations
"""
import asyncio
import math
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from collections import Counter

from geopy.distance import geodesic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from models.Community import (
    Community, UserProfile, CommunityMembership, NetworkingEvent, 
    JobOpportunity, JobApplication, MatchingAlgorithm,
    CommunityType, EventType, ExperienceLevel, JobType,
    INTEREST_CATEGORIES, INDUSTRY_CATEGORIES
)

logger = logging.getLogger(__name__)


class CommunityService:
    """Service for community matching and networking features"""
    
    def __init__(self, db_client):
        self.db = db_client
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2)
        )
        
        # Matching algorithm configuration
        self.matching_config = MatchingAlgorithm()
        
        # Cache for performance
        self._user_profiles_cache = {}
        self._communities_cache = {}
        self._cache_expiry = timedelta(minutes=15)
        self._last_cache_update = datetime.utcnow() - self._cache_expiry
    
    async def create_or_update_user_profile(self, user_id: str, profile_data: Dict) -> UserProfile:
        """Create or update user profile for community matching"""
        try:
            # Check if profile exists
            existing_profile = await self.db.userprofiles.find_one({"user_id": user_id})
            
            if existing_profile:
                # Update existing profile
                await self.db.userprofiles.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            **profile_data,
                            "last_active": datetime.utcnow()
                        }
                    }
                )
                
                # Get updated profile
                profile_data_db = await self.db.userprofiles.find_one({"user_id": user_id})
            else:
                # Create new profile
                profile = UserProfile(
                    user_id=user_id,
                    **profile_data
                )
                
                profile_dict = profile.dict(by_alias=True, exclude={"id"})
                result = await self.db.userprofiles.insert_one(profile_dict)
                profile.id = str(result.inserted_id)
                
                profile_data_db = profile.dict()
            
            # Convert to UserProfile object
            if "_id" in profile_data_db:
                profile_data_db["_id"] = str(profile_data_db["_id"])
            
            profile = UserProfile(**profile_data_db)
            
            # Clear cache to force refresh
            self._clear_cache()
            
            logger.info(f"User profile created/updated for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating/updating user profile: {str(e)}")
            raise
    
    async def find_matching_communities(self, user_id: str, limit: int = 20) -> List[Tuple[Community, float]]:
        """Find communities that match user's interests and profile"""
        try:
            # Get user profile
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                return []
            
            # Get all communities
            communities = await self._get_all_communities()
            
            # Calculate match scores for each community
            matches = []
            for community in communities:
                score = await self._calculate_community_match_score(user_profile, community)
                if score >= self.matching_config.min_match_score:
                    matches.append((community, score))
            
            # Sort by match score and return top results
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error finding matching communities: {str(e)}")
            return []
    
    async def find_matching_users(self, user_id: str, limit: int = 50) -> List[Tuple[UserProfile, float, List[str]]]:
        """Find users with similar interests and profiles"""
        try:
            # Get user profile
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                return []
            
            # Get all user profiles (excluding requesting user)
            all_profiles = await self._get_all_user_profiles(exclude_user_id=user_id)
            
            # Calculate match scores
            matches = []
            for other_profile in all_profiles:
                score, reasons = await self._calculate_user_match_score(user_profile, other_profile)
                if score >= self.matching_config.min_match_score:
                    matches.append((other_profile, score, reasons))
            
            # Sort by match score
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error finding matching users: {str(e)}")
            return []
    
    async def create_community(self, user_id: str, community_data: Dict) -> Community:
        """Create a new community"""
        try:
            community = Community(
                creator_id=user_id,
                **community_data
            )
            
            # Insert community
            community_dict = community.dict(by_alias=True, exclude={"id"})
            result = await self.db.communities.insert_one(community_dict)
            community.id = str(result.inserted_id)
            
            # Auto-join creator as first member
            await self._add_community_member(community.id, user_id, role="admin")
            
            # Clear cache
            self._clear_cache()
            
            logger.info(f"Community '{community.name}' created by user {user_id}")
            return community
            
        except Exception as e:
            logger.error(f"Error creating community: {str(e)}")
            raise
    
    async def join_community(self, user_id: str, community_id: str) -> bool:
        """Join a community"""
        try:
            # Check if community exists
            community = await self._get_community(community_id)
            if not community:
                return False
            
            # Check if already a member
            existing_membership = await self.db.communitymemberships.find_one({
                "community_id": community_id,
                "user_id": user_id
            })
            
            if existing_membership:
                return True  # Already a member
            
            # Add membership
            await self._add_community_member(community_id, user_id)
            
            # Update community member count
            await self.db.communities.update_one(
                {"_id": community_id},
                {"$inc": {"member_count": 1, "last_activity": datetime.utcnow()}}
            )
            
            logger.info(f"User {user_id} joined community {community_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining community: {str(e)}")
            return False
    
    async def create_networking_event(self, user_id: str, event_data: Dict) -> NetworkingEvent:
        """Create a networking event"""
        try:
            event = NetworkingEvent(
                organizer_id=user_id,
                **event_data
            )
            
            # Insert event
            event_dict = event.dict(by_alias=True, exclude={"id"})
            result = await self.db.networkingevents.insert_one(event_dict)
            event.id = str(result.inserted_id)
            
            # If community event, update community
            if event.community_id:
                await self.db.communities.update_one(
                    {"_id": event.community_id},
                    {"$inc": {"meeting_count": 1}}
                )
            
            # Find and notify matching users
            await self._notify_matching_users_about_event(event)
            
            logger.info(f"Networking event '{event.title}' created by user {user_id}")
            return event
            
        except Exception as e:
            logger.error(f"Error creating networking event: {str(e)}")
            raise
    
    async def post_job_opportunity(self, user_id: str, job_data: Dict) -> JobOpportunity:
        """Post a job opportunity"""
        try:
            job = JobOpportunity(
                posted_by=user_id,
                **job_data
            )
            
            # Insert job
            job_dict = job.dict(by_alias=True, exclude={"id"})
            result = await self.db.jobopportunities.insert_one(job_dict)
            job.id = str(result.inserted_id)
            
            # Find and notify matching candidates
            await self._notify_matching_candidates_about_job(job)
            
            logger.info(f"Job opportunity '{job.title}' posted by user {user_id}")
            return job
            
        except Exception as e:
            logger.error(f"Error posting job opportunity: {str(e)}")
            raise
    
    async def apply_for_job(self, user_id: str, job_id: str, application_data: Dict) -> JobApplication:
        """Apply for a job opportunity"""
        try:
            # Check if job exists
            job = await self._get_job_opportunity(job_id)
            if not job:
                raise ValueError("Job not found")
            
            # Check if already applied
            existing_application = await self.db.jobapplications.find_one({
                "job_id": job_id,
                "applicant_id": user_id
            })
            
            if existing_application:
                raise ValueError("Already applied for this job")
            
            application = JobApplication(
                job_id=job_id,
                applicant_id=user_id,
                **application_data
            )
            
            # Insert application
            application_dict = application.dict(by_alias=True, exclude={"id"})
            result = await self.db.jobapplications.insert_one(application_dict)
            application.id = str(result.inserted_id)
            
            # Update job applications count
            await self.db.jobopportunities.update_one(
                {"_id": job_id},
                {"$inc": {"applications_count": 1}}
            )
            
            # Notify job poster
            await self._notify_job_poster_about_application(job, application)
            
            logger.info(f"User {user_id} applied for job {job_id}")
            return application
            
        except Exception as e:
            logger.error(f"Error applying for job: {str(e)}")
            raise
    
    async def get_networking_feed(self, user_id: str) -> Dict[str, Any]:
        """Get personalized networking feed for user"""
        try:
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                return {
                    'events': [],
                    'job_opportunities': [],
                    'community_suggestions': [],
                    'user_matches': []
                }
            
            # Get upcoming events matching user interests
            events = await self._get_matching_events(user_profile, limit=10)
            
            # Get job opportunities (if looking for job)
            jobs = []
            if user_profile.looking_for_job:
                jobs = await self._get_matching_jobs(user_profile, limit=10)
            
            # Get community suggestions
            community_matches = await self.find_matching_communities(user_id, limit=5)
            communities = [match[0] for match in community_matches]
            
            # Get user matches
            user_matches = await self.find_matching_users(user_id, limit=10)
            users = [{
                'user': match[0].dict(),
                'match_score': match[1],
                'match_reasons': match[2]
            } for match in user_matches]
            
            return {
                'events': [event.dict() for event in events],
                'job_opportunities': [job.dict() for job in jobs],
                'community_suggestions': [community.dict() for community in communities],
                'user_matches': users
            }
            
        except Exception as e:
            logger.error(f"Error getting networking feed: {str(e)}")
            return {
                'events': [],
                'job_opportunities': [],
                'community_suggestions': [],
                'user_matches': []
            }
    
    async def _calculate_community_match_score(self, user_profile: UserProfile, community: Community) -> float:
        """Calculate match score between user and community"""
        try:
            score = 0.0
            max_score = 1.0
            
            # Interest matching (40% weight)
            if user_profile.interests and community.primary_interests:
                interest_overlap = len(set(user_profile.interests) & set(community.primary_interests))
                total_interests = len(set(user_profile.interests) | set(community.primary_interests))
                if total_interests > 0:
                    interest_score = interest_overlap / total_interests
                    score += interest_score * self.matching_config.interest_weight
            
            # Location matching (20% weight)
            if user_profile.location and community.location:
                if user_profile.location.lower() == community.location.lower():
                    score += self.matching_config.location_weight
                elif self._is_nearby_location(user_profile.location, community.location):
                    score += self.matching_config.location_weight * 0.5
            
            # Industry matching (20% weight)
            if user_profile.industry and community.industry_focus:
                if user_profile.industry.lower() == community.industry_focus.lower():
                    score += self.matching_config.industry_weight
            
            # Community type preference (20% weight)
            type_bonus = self._get_community_type_bonus(user_profile, community)
            score += type_bonus * 0.2
            
            return min(score, max_score)
            
        except Exception as e:
            logger.error(f"Error calculating community match score: {str(e)}")
            return 0.0
    
    async def _calculate_user_match_score(self, user1: UserProfile, user2: UserProfile) -> Tuple[float, List[str]]:
        """Calculate match score between two users"""
        try:
            score = 0.0
            reasons = []
            
            # Interest matching (40% weight)
            if user1.interests and user2.interests:
                common_interests = set(user1.interests) & set(user2.interests)
                if common_interests:
                    interest_overlap = len(common_interests)
                    total_interests = len(set(user1.interests) | set(user2.interests))
                    interest_score = interest_overlap / total_interests
                    score += interest_score * self.matching_config.interest_weight
                    
                    if interest_overlap >= 2:
                        reasons.append(f"Gemeinsame Interessen: {', '.join(list(common_interests)[:3])}")
            
            # Location proximity (20% weight)
            if user1.location and user2.location:
                if user1.location.lower() == user2.location.lower():
                    score += self.matching_config.location_weight
                    reasons.append(f"Gleicher Standort: {user1.location}")
                elif self._is_nearby_location(user1.location, user2.location):
                    score += self.matching_config.location_weight * 0.5
                    reasons.append(f"Nahegelegener Standort")
            
            # Industry matching (20% weight)
            if user1.industry and user2.industry:
                if user1.industry.lower() == user2.industry.lower():
                    score += self.matching_config.industry_weight
                    reasons.append(f"Gleiche Branche: {user1.industry}")
            
            # Skill overlap (10% weight)
            if user1.skills and user2.skills:
                common_skills = set(user1.skills) & set(user2.skills)
                if common_skills:
                    skill_overlap = len(common_skills) / len(set(user1.skills) | set(user2.skills))
                    score += skill_overlap * self.matching_config.skill_weight
                    
                    if len(common_skills) >= 2:
                        reasons.append(f"Gemeinsame Fähigkeiten: {', '.join(list(common_skills)[:2])}")
            
            # Experience level compatibility (10% weight)
            if user1.experience_level and user2.experience_level:
                exp_compatibility = self._calculate_experience_compatibility(
                    user1.experience_level, user2.experience_level
                )
                score += exp_compatibility * self.matching_config.experience_weight
                
                if exp_compatibility > 0.7:
                    reasons.append("Passendes Erfahrungslevel")
            
            # Job/recruiting match bonus
            if user1.looking_for_job and user2.is_recruiter:
                score += 0.2
                reasons.append("Job-Recruiter Match")
            elif user2.looking_for_job and user1.is_recruiter:
                score += 0.2
                reasons.append("Job-Recruiter Match")
            
            return min(score, 1.0), reasons
            
        except Exception as e:
            logger.error(f"Error calculating user match score: {str(e)}")
            return 0.0, []
    
    def _is_nearby_location(self, loc1: str, loc2: str) -> bool:
        """Check if two locations are nearby (simplified)"""
        # Simplified location matching - in production, use proper geocoding
        return (
            loc1.lower().split(',')[0].strip() == loc2.lower().split(',')[0].strip() or  # Same city
            any(word in loc2.lower() for word in loc1.lower().split()) or
            any(word in loc1.lower() for word in loc2.lower().split())
        )
    
    def _get_community_type_bonus(self, user_profile: UserProfile, community: Community) -> float:
        """Get bonus score based on community type preference"""
        # If user is looking for job, prefer job-focused communities
        if user_profile.looking_for_job and community.community_type == CommunityType.JOB_FOCUSED:
            return 0.8
        
        # If user is recruiter, prefer business communities
        if user_profile.is_recruiter and community.community_type == CommunityType.BUSINESS:
            return 0.8
        
        # Professional users prefer professional communities
        if user_profile.current_position and community.community_type == CommunityType.PROFESSIONAL:
            return 0.6
        
        return 0.4  # Base score
    
    def _calculate_experience_compatibility(self, exp1: ExperienceLevel, exp2: ExperienceLevel) -> float:
        """Calculate experience level compatibility"""
        exp_order = [
            ExperienceLevel.ENTRY,
            ExperienceLevel.JUNIOR, 
            ExperienceLevel.MID,
            ExperienceLevel.SENIOR,
            ExperienceLevel.LEAD,
            ExperienceLevel.EXECUTIVE
        ]
        
        try:
            idx1 = exp_order.index(exp1)
            idx2 = exp_order.index(exp2)
            
            # Same level = perfect match
            if idx1 == idx2:
                return 1.0
            
            # Adjacent levels = good match
            if abs(idx1 - idx2) == 1:
                return 0.8
            
            # Two levels apart = moderate match
            if abs(idx1 - idx2) == 2:
                return 0.5
            
            # More than 2 levels apart = poor match
            return 0.2
            
        except ValueError:
            return 0.5  # Default if levels not found
    
    async def _notify_matching_users_about_event(self, event: NetworkingEvent):
        """Notify matching users about new networking event"""
        # Implementation would use the video socket service to send real-time notifications
        pass
    
    async def _notify_matching_candidates_about_job(self, job: JobOpportunity):
        """Notify matching candidates about new job opportunity"""
        # Implementation would find matching candidates and send notifications
        pass
    
    async def _notify_job_poster_about_application(self, job: JobOpportunity, application: JobApplication):
        """Notify job poster about new application"""
        # Implementation would notify the job poster via socket or email
        pass
    
    # Cache and utility methods
    async def _get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile with caching"""
        try:
            if user_id in self._user_profiles_cache and self._is_cache_valid():
                return self._user_profiles_cache[user_id]
            
            profile_data = await self.db.userprofiles.find_one({"user_id": user_id})
            if profile_data:
                if "_id" in profile_data:
                    profile_data["_id"] = str(profile_data["_id"])
                
                profile = UserProfile(**profile_data)
                self._user_profiles_cache[user_id] = profile
                return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {str(e)}")
            return None
    
    async def _get_community(self, community_id: str) -> Optional[Community]:
        """Get community by ID"""
        try:
            community_data = await self.db.communities.find_one({"_id": community_id})
            if community_data:
                if "_id" in community_data:
                    community_data["_id"] = str(community_data["_id"])
                return Community(**community_data)
            return None
        except Exception as e:
            logger.error(f"Error getting community {community_id}: {str(e)}")
            return None
    
    async def _get_job_opportunity(self, job_id: str) -> Optional[JobOpportunity]:
        """Get job opportunity by ID"""
        try:
            job_data = await self.db.jobopportunities.find_one({"_id": job_id})
            if job_data:
                if "_id" in job_data:
                    job_data["_id"] = str(job_data["_id"])
                return JobOpportunity(**job_data)
            return None
        except Exception as e:
            logger.error(f"Error getting job opportunity {job_id}: {str(e)}")
            return None
    
    async def _get_all_communities(self) -> List[Community]:
        """Get all communities with caching"""
        if self._is_cache_valid() and 'communities' in self._communities_cache:
            return self._communities_cache['communities']
        
        communities = []
        try:
            cursor = self.db.communities.find({"is_public": True})
            async for community_data in cursor:
                if "_id" in community_data:
                    community_data["_id"] = str(community_data["_id"])
                communities.append(Community(**community_data))
            
            self._communities_cache['communities'] = communities
            return communities
            
        except Exception as e:
            logger.error(f"Error getting all communities: {str(e)}")
            return []
    
    async def _get_all_user_profiles(self, exclude_user_id: str = None) -> List[UserProfile]:
        """Get all user profiles for matching"""
        profiles = []
        try:
            query = {"discoverable": True}
            if exclude_user_id:
                query["user_id"] = {"$ne": exclude_user_id}
            
            cursor = self.db.userprofiles.find(query)
            async for profile_data in cursor:
                if "_id" in profile_data:
                    profile_data["_id"] = str(profile_data["_id"])
                profiles.append(UserProfile(**profile_data))
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error getting all user profiles: {str(e)}")
            return []
    
    async def _add_community_member(self, community_id: str, user_id: str, role: str = "member"):
        """Add user as community member"""
        try:
            membership = CommunityMembership(
                community_id=community_id,
                user_id=user_id,
                role=role
            )
            
            membership_dict = membership.dict(by_alias=True, exclude={"id"})
            await self.db.communitymemberships.insert_one(membership_dict)
            
        except Exception as e:
            logger.error(f"Error adding community member: {str(e)}")
            raise
    
    async def _get_matching_events(self, user_profile: UserProfile, limit: int = 10) -> List[NetworkingEvent]:
        """Get events matching user's interests"""
        events = []
        try:
            # Query for events with matching interests or location
            query = {
                "scheduled_start": {"$gte": datetime.utcnow()},
                "status": "planned"
            }
            
            # Add interest or location matching
            if user_profile.interests or user_profile.location:
                or_conditions = []
                
                if user_profile.interests:
                    or_conditions.append({
                        "target_interests": {"$in": user_profile.interests}
                    })
                
                if user_profile.location:
                    or_conditions.append({
                        "target_location": {"$regex": user_profile.location.split(',')[0], "$options": "i"}
                    })
                
                if or_conditions:
                    query["$or"] = or_conditions
            
            cursor = self.db.networkingevents.find(query).sort("scheduled_start", 1).limit(limit)
            
            async for event_data in cursor:
                if "_id" in event_data:
                    event_data["_id"] = str(event_data["_id"])
                events.append(NetworkingEvent(**event_data))
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting matching events: {str(e)}")
            return []
    
    async def _get_matching_jobs(self, user_profile: UserProfile, limit: int = 10) -> List[JobOpportunity]:
        """Get job opportunities matching user's profile"""
        jobs = []
        try:
            query = {"is_active": True}
            
            # Add matching criteria
            or_conditions = []
            
            if user_profile.skills:
                or_conditions.append({
                    "required_skills": {"$in": user_profile.skills}
                })
            
            if user_profile.industry:
                or_conditions.append({
                    "industry": {"$regex": user_profile.industry, "$options": "i"}
                })
            
            if user_profile.experience_level:
                or_conditions.append({
                    "experience_level": user_profile.experience_level.value
                })
            
            if or_conditions:
                query["$or"] = or_conditions
            
            cursor = self.db.jobopportunities.find(query).sort("created_at", -1).limit(limit)
            
            async for job_data in cursor:
                if "_id" in job_data:
                    job_data["_id"] = str(job_data["_id"])
                jobs.append(JobOpportunity(**job_data))
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting matching jobs: {str(e)}")
            return []
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        return datetime.utcnow() - self._last_cache_update < self._cache_expiry
    
    def _clear_cache(self):
        """Clear all caches"""
        self._user_profiles_cache.clear()
        self._communities_cache.clear()
        self._last_cache_update = datetime.utcnow() - self._cache_expiry


# Global service instance
community_service = None

def get_community_service(db_client) -> CommunityService:
    """Get or create community service instance"""
    global community_service
    if community_service is None:
        community_service = CommunityService(db_client)
    return community_service