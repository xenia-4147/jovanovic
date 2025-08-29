"""
Community Matching Service for Interest-Based Networking
Revolutionary Feature: Smart AI-Powered Community & User Matching
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter
from geopy.distance import geodesic
import json

from models.Community import (
    Community, UserProfile, CommunityMembership, NetworkingEvent,
    JobOpportunity, JobApplication, MatchingAlgorithm,
    CommunityType, EventType, JobType, ExperienceLevel,
    INTEREST_CATEGORIES, INDUSTRY_CATEGORIES
)

logger = logging.getLogger(__name__)


class CommunityMatchingService:
    """AI-powered community and user matching service"""
    
    def __init__(self, db_client):
        self.db = db_client
        self.matching_algorithm = MatchingAlgorithm()
        self._interest_graph = defaultdict(set)  # Interest -> Users with that interest
        self._location_index = defaultdict(list)  # Location -> Users in that location
        self._skill_index = defaultdict(set)  # Skill -> Users with that skill
    
    async def initialize(self):
        """Initialize matching indices for better performance"""
        try:
            await self._build_matching_indices()
            logger.info("Community matching service initialized")
        except Exception as e:
            logger.error(f"Error initializing community matching service: {str(e)}")
    
    async def _build_matching_indices(self):
        """Build in-memory indices for fast matching"""
        try:
            # Build user profiles index
            cursor = self.db.userprofiles.find({})
            async for profile_data in cursor:
                profile = UserProfile(**profile_data)
                
                # Index by interests
                for interest in profile.interests:
                    self._interest_graph[interest.lower()].add(profile.user_id)
                
                # Index by location
                if profile.location:
                    self._location_index[profile.location.lower()].append({
                        'user_id': profile.user_id,
                        'location': profile.location
                    })
                
                # Index by skills
                for skill in profile.skills:
                    self._skill_index[skill.lower()].add(profile.user_id)
            
            logger.info(f"Built matching indices: {len(self._interest_graph)} interests, "
                       f"{len(self._location_index)} locations, {len(self._skill_index)} skills")
        
        except Exception as e:
            logger.error(f"Error building matching indices: {str(e)}")
    
    # Community Discovery & Matching
    
    async def find_matching_communities(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find communities matching user's interests and profile"""
        try:
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                return []
            
            # Get all communities
            communities = []
            cursor = self.db.communities.find({"is_public": True})
            
            # Score each community
            community_scores = []
            async for community_data in cursor:
                community = Community(**community_data)
                score = await self._calculate_community_match_score(user_profile, community)
                
                if score >= self.matching_algorithm.min_match_score:
                    community_scores.append({
                        'community': community,
                        'score': score,
                        'match_reasons': await self._get_community_match_reasons(user_profile, community)
                    })
            
            # Sort by score and return top matches
            community_scores.sort(key=lambda x: x['score'], reverse=True)
            
            result = []
            for item in community_scores[:limit]:
                community_dict = item['community'].dict()
                community_dict['match_score'] = item['score']
                community_dict['match_reasons'] = item['match_reasons']
                result.append(community_dict)
            
            return result
        
        except Exception as e:
            logger.error(f"Error finding matching communities: {str(e)}")
            return []
    
    async def _calculate_community_match_score(self, user_profile: UserProfile, community: Community) -> float:
        """Calculate how well a community matches a user's profile"""
        score = 0.0
        
        # Interest matching (40% weight)
        interest_score = self._calculate_interest_overlap(
            user_profile.interests, community.primary_interests
        )
        score += interest_score * self.matching_algorithm.interest_weight
        
        # Location matching (20% weight)
        location_score = self._calculate_location_match(
            user_profile.location, community.location
        )
        score += location_score * self.matching_algorithm.location_weight
        
        # Industry matching (20% weight)
        if user_profile.industry and community.industry_focus:
            industry_score = 1.0 if user_profile.industry.lower() == community.industry_focus.lower() else 0.0
            score += industry_score * self.matching_algorithm.industry_weight
        
        # Activity level bonus
        if community.member_count > 5:  # Active community bonus
            score += 0.1
        
        return min(score, 1.0)
    
    async def _get_community_match_reasons(self, user_profile: UserProfile, community: Community) -> List[str]:
        """Generate human-readable match reasons"""
        reasons = []
        
        # Interest overlap
        common_interests = set(user_profile.interests) & set(community.primary_interests)
        if common_interests:
            reasons.append(f"Gemeinsame Interessen: {', '.join(list(common_interests)[:3])}")
        
        # Location match
        if user_profile.location and community.location:
            if user_profile.location.lower() == community.location.lower():
                reasons.append(f"Gleiche Stadt: {community.location}")
            elif self._is_nearby_location(user_profile.location, community.location):
                reasons.append(f"Nahe Umgebung: {community.location}")
        
        # Industry match
        if user_profile.industry and community.industry_focus:
            if user_profile.industry.lower() == community.industry_focus.lower():
                reasons.append(f"Gleiche Branche: {community.industry_focus}")
        
        # Community type appeal
        if community.community_type == CommunityType.BUSINESS and user_profile.current_company:
            reasons.append("Business-orientierte Community")
        elif community.community_type == CommunityType.JOB_FOCUSED and user_profile.looking_for_job:
            reasons.append("Job-fokussierte Community")
        
        return reasons
    
    # User Matching & Networking
    
    async def find_similar_users(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Find users with similar interests, skills, or background"""
        try:
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                return []
            
            # Find users with overlapping interests
            candidate_users = set()
            
            # Interest-based matching
            for interest in user_profile.interests:
                candidate_users.update(self._interest_graph.get(interest.lower(), set()))
            
            # Skill-based matching
            for skill in user_profile.skills:
                candidate_users.update(self._skill_index.get(skill.lower(), set()))
            
            # Location-based matching
            if user_profile.location:
                location_users = self._location_index.get(user_profile.location.lower(), [])
                candidate_users.update([u['user_id'] for u in location_users])
            
            # Remove self
            candidate_users.discard(user_id)
            
            # Score each candidate
            user_scores = []
            for candidate_user_id in candidate_users:
                candidate_profile = await self._get_user_profile(candidate_user_id)
                if candidate_profile and candidate_profile.discoverable:
                    score = await self._calculate_user_match_score(user_profile, candidate_profile)
                    
                    if score >= self.matching_algorithm.min_match_score:
                        user_scores.append({
                            'profile': candidate_profile,
                            'score': score,
                            'match_reasons': await self._get_user_match_reasons(user_profile, candidate_profile)
                        })
            
            # Sort by score and return top matches
            user_scores.sort(key=lambda x: x['score'], reverse=True)
            
            result = []
            for item in user_scores[:limit]:
                profile_dict = item['profile'].dict()
                profile_dict['match_score'] = item['score']
                profile_dict['match_reasons'] = item['match_reasons']
                result.append(profile_dict)
            
            return result
        
        except Exception as e:
            logger.error(f"Error finding similar users: {str(e)}")
            return []
    
    async def _calculate_user_match_score(self, user1: UserProfile, user2: UserProfile) -> float:
        """Calculate match score between two users"""
        score = 0.0
        
        # Interest overlap (40% weight)
        interest_score = self._calculate_interest_overlap(user1.interests, user2.interests)
        score += interest_score * self.matching_algorithm.interest_weight
        
        # Location proximity (20% weight)
        location_score = self._calculate_location_match(user1.location, user2.location)
        score += location_score * self.matching_algorithm.location_weight
        
        # Industry match (20% weight)
        if user1.industry and user2.industry:
            industry_score = 1.0 if user1.industry.lower() == user2.industry.lower() else 0.0
            score += industry_score * self.matching_algorithm.industry_weight
        
        # Skill overlap (10% weight)
        skill_score = self._calculate_interest_overlap(user1.skills, user2.skills)
        score += skill_score * self.matching_algorithm.skill_weight
        
        # Experience level compatibility (10% weight)
        if user1.experience_level and user2.experience_level:
            exp_score = self._calculate_experience_compatibility(user1.experience_level, user2.experience_level)
            score += exp_score * self.matching_algorithm.experience_weight
        
        return min(score, 1.0)
    
    async def _get_user_match_reasons(self, user1: UserProfile, user2: UserProfile) -> List[str]:
        """Generate human-readable user match reasons"""
        reasons = []
        
        # Common interests
        common_interests = set(user1.interests) & set(user2.interests)
        if common_interests:
            reasons.append(f"Gemeinsame Interessen: {', '.join(list(common_interests)[:3])}")
        
        # Common skills
        common_skills = set(user1.skills) & set(user2.skills)
        if common_skills:
            reasons.append(f"Ähnliche Skills: {', '.join(list(common_skills)[:2])}")
        
        # Location
        if user1.location and user2.location:
            if user1.location.lower() == user2.location.lower():
                reasons.append(f"Gleiche Stadt: {user1.location}")
            elif self._is_nearby_location(user1.location, user2.location):
                reasons.append("Nahe Umgebung")
        
        # Industry
        if user1.industry and user2.industry and user1.industry.lower() == user2.industry.lower():
            reasons.append(f"Gleiche Branche: {user1.industry}")
        
        # Professional level
        if user1.experience_level and user2.experience_level:
            if user1.experience_level == user2.experience_level:
                reasons.append(f"Ähnliches Level: {user1.experience_level.value}")
        
        return reasons
    
    # Job Matching & Recruiting
    
    async def find_job_matches(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find job opportunities matching user's profile"""
        try:
            user_profile = await self._get_user_profile(user_id)
            if not user_profile or not user_profile.looking_for_job:
                return []
            
            # Get active jobs
            job_scores = []
            cursor = self.db.jobopportunities.find({"is_active": True})
            
            async for job_data in cursor:
                job = JobOpportunity(**job_data)
                score = await self._calculate_job_match_score(user_profile, job)
                
                if score >= 0.3:  # Minimum job match threshold
                    job_scores.append({
                        'job': job,
                        'score': score,
                        'match_reasons': await self._get_job_match_reasons(user_profile, job)
                    })
            
            # Sort by score
            job_scores.sort(key=lambda x: x['score'], reverse=True)
            
            result = []
            for item in job_scores[:limit]:
                job_dict = item['job'].dict()
                job_dict['match_score'] = item['score']
                job_dict['match_reasons'] = item['match_reasons']
                result.append(job_dict)
            
            return result
        
        except Exception as e:
            logger.error(f"Error finding job matches: {str(e)}")
            return []
    
    async def _calculate_job_match_score(self, user_profile: UserProfile, job: JobOpportunity) -> float:
        """Calculate job match score"""
        score = 0.0
        
        # Skills match (50% weight)
        user_skills = set([skill.lower() for skill in user_profile.skills])
        required_skills = set([skill.lower() for skill in job.required_skills])
        preferred_skills = set([skill.lower() for skill in job.preferred_skills])
        
        if required_skills:
            required_match = len(user_skills & required_skills) / len(required_skills)
            score += required_match * 0.3
        
        if preferred_skills:
            preferred_match = len(user_skills & preferred_skills) / len(preferred_skills)
            score += preferred_match * 0.2
        
        # Experience level match (20% weight)
        if user_profile.experience_level and job.experience_level:
            exp_score = self._calculate_experience_job_match(user_profile.experience_level, job.experience_level)
            score += exp_score * 0.2
        
        # Location match (15% weight)
        if job.location and user_profile.location:
            location_score = self._calculate_location_match(user_profile.location, job.location)
            score += location_score * 0.15
        elif job.remote_allowed:
            score += 0.15  # Full location score for remote jobs
        
        # Industry match (15% weight)
        if user_profile.industry and job.industry:
            industry_score = 1.0 if user_profile.industry.lower() == job.industry.lower() else 0.0
            score += industry_score * 0.15
        
        return min(score, 1.0)
    
    async def _get_job_match_reasons(self, user_profile: UserProfile, job: JobOpportunity) -> List[str]:
        """Generate job match reasons"""
        reasons = []
        
        # Skills match
        user_skills = set([skill.lower() for skill in user_profile.skills])
        required_skills = set([skill.lower() for skill in job.required_skills])
        preferred_skills = set([skill.lower() for skill in job.preferred_skills])
        
        matching_required = user_skills & required_skills
        if matching_required:
            reasons.append(f"Erfüllt Anforderungen: {', '.join(list(matching_required)[:3])}")
        
        matching_preferred = user_skills & preferred_skills
        if matching_preferred:
            reasons.append(f"Zusätzliche Skills: {', '.join(list(matching_preferred)[:2])}")
        
        # Experience level
        if user_profile.experience_level == job.experience_level:
            reasons.append(f"Passende Erfahrung: {job.experience_level.value}")
        
        # Location
        if job.remote_allowed:
            reasons.append("Remote-Arbeit möglich")
        elif job.location and user_profile.location:
            if self._calculate_location_match(user_profile.location, job.location) > 0.8:
                reasons.append(f"Lokale Position: {job.location}")
        
        return reasons
    
    # Networking Events & Community Events
    
    async def suggest_networking_events(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Suggest networking events based on user interests"""
        try:
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                return []
            
            # Get upcoming events
            future_date = datetime.utcnow()
            cursor = self.db.networkingevents.find({
                "scheduled_start": {"$gte": future_date}
            })
            
            event_scores = []
            async for event_data in cursor:
                event = NetworkingEvent(**event_data)
                score = await self._calculate_event_match_score(user_profile, event)
                
                if score >= 0.3:
                    event_scores.append({
                        'event': event,
                        'score': score,
                        'match_reasons': await self._get_event_match_reasons(user_profile, event)
                    })
            
            # Sort by score
            event_scores.sort(key=lambda x: x['score'], reverse=True)
            
            result = []
            for item in event_scores[:limit]:
                event_dict = item['event'].dict()
                event_dict['match_score'] = item['score']
                event_dict['match_reasons'] = item['match_reasons']
                result.append(event_dict)
            
            return result
        
        except Exception as e:
            logger.error(f"Error suggesting networking events: {str(e)}")
            return []
    
    async def _calculate_event_match_score(self, user_profile: UserProfile, event: NetworkingEvent) -> float:
        """Calculate event match score"""
        score = 0.0
        
        # Interest matching (50% weight)
        interest_score = self._calculate_interest_overlap(user_profile.interests, event.target_interests)
        score += interest_score * 0.5
        
        # Event type preference (20% weight)
        if event.event_type in user_profile.preferred_meeting_types:
            score += 0.2
        
        # Location match (20% weight)
        if event.target_location and user_profile.location:
            location_score = self._calculate_location_match(user_profile.location, event.target_location)
            score += location_score * 0.2
        
        # Experience level match (10% weight)
        if event.target_experience_level and user_profile.experience_level:
            if user_profile.experience_level in event.target_experience_level:
                score += 0.1
        
        return min(score, 1.0)
    
    async def _get_event_match_reasons(self, user_profile: UserProfile, event: NetworkingEvent) -> List[str]:
        """Generate event match reasons"""
        reasons = []
        
        # Interest match
        common_interests = set(user_profile.interests) & set(event.target_interests)
        if common_interests:
            reasons.append(f"Relevante Themen: {', '.join(list(common_interests)[:3])}")
        
        # Event type
        if event.event_type in user_profile.preferred_meeting_types:
            reasons.append(f"Bevorzugter Event-Typ: {event.event_type.value}")
        
        # Location
        if event.target_location and user_profile.location:
            if self._calculate_location_match(user_profile.location, event.target_location) > 0.8:
                reasons.append(f"Lokales Event: {event.target_location}")
        
        return reasons
    
    # Community Creation & Management
    
    async def suggest_community_creation(self, user_id: str) -> Dict[str, Any]:
        """Suggest creating a new community based on user's unique interests"""
        try:
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                return {}
            
            suggestions = []
            
            # Find underserved interests
            for interest in user_profile.interests:
                # Count existing communities for this interest
                community_count = await self.db.communities.count_documents({
                    "primary_interests": {"$in": [interest]}
                })
                
                if community_count < 3:  # Underserved interest
                    suggestions.append({
                        'suggested_name': self._generate_community_name(interest, user_profile.location),
                        'interest': interest,
                        'reason': f'Wenige Communities für "{interest}" vorhanden',
                        'potential_members': len(self._interest_graph.get(interest.lower(), set()))
                    })
            
            # Location-based suggestions
            if user_profile.location:
                location_communities = await self.db.communities.count_documents({
                    "location": user_profile.location
                })
                
                if location_communities < 5:  # Few local communities
                    suggestions.append({
                        'suggested_name': f'Business Netzwerk {user_profile.location}',
                        'interest': 'local_business',
                        'reason': f'Wenige lokale Communities in {user_profile.location}',
                        'potential_members': len(self._location_index.get(user_profile.location.lower(), []))
                    })
            
            return {
                'suggestions': suggestions[:5],
                'user_interests': user_profile.interests,
                'recommended_types': self._recommend_community_types(user_profile)
            }
        
        except Exception as e:
            logger.error(f"Error suggesting community creation: {str(e)}")
            return {}
    
    def _generate_community_name(self, interest: str, location: Optional[str] = None) -> str:
        """Generate a community name based on interest and location"""
        if location:
            return f"{interest.title()} {location}"
        return f"{interest.title()} Community"
    
    def _recommend_community_types(self, user_profile: UserProfile) -> List[str]:
        """Recommend community types based on user profile"""
        recommendations = []
        
        if user_profile.current_company:
            recommendations.append(CommunityType.BUSINESS.value)
        
        if user_profile.looking_for_job or user_profile.is_recruiter:
            recommendations.append(CommunityType.JOB_FOCUSED.value)
        
        if user_profile.skills:
            recommendations.append(CommunityType.SKILL_BASED.value)
        
        if user_profile.industry:
            recommendations.append(CommunityType.INDUSTRY.value)
        
        recommendations.append(CommunityType.HOBBY.value)
        
        return recommendations
    
    # Utility Functions
    
    def _calculate_interest_overlap(self, interests1: List[str], interests2: List[str]) -> float:
        """Calculate overlap between two interest lists"""
        if not interests1 or not interests2:
            return 0.0
        
        set1 = set([i.lower() for i in interests1])
        set2 = set([i.lower() for i in interests2])
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_location_match(self, location1: Optional[str], location2: Optional[str]) -> float:
        """Calculate location match score"""
        if not location1 or not location2:
            return 0.0
        
        loc1 = location1.lower().strip()
        loc2 = location2.lower().strip()
        
        # Exact match
        if loc1 == loc2:
            return 1.0
        
        # City match (handle "City, Country" format)
        city1 = loc1.split(',')[0].strip()
        city2 = loc2.split(',')[0].strip()
        
        if city1 == city2:
            return 0.8
        
        # Nearby cities (simplified - could use actual geolocation)
        if self._is_nearby_location(location1, location2):
            return 0.6
        
        # Country match
        if ',' in loc1 and ',' in loc2:
            country1 = loc1.split(',')[-1].strip()
            country2 = loc2.split(',')[-1].strip()
            if country1 == country2:
                return 0.3
        
        return 0.0
    
    def _is_nearby_location(self, location1: str, location2: str) -> bool:
        """Check if two locations are nearby (simplified)"""
        # This is a simplified version. In production, you'd use proper geocoding
        german_cities = {
            'münchen': ['augsburg', 'ingolstadt', 'nürnberg'],
            'berlin': ['potsdam', 'brandenburg', 'cottbus'],
            'hamburg': ['bremen', 'lübeck', 'kiel'],
            'köln': ['düsseldorf', 'bonn', 'aachen'],
        }
        
        loc1 = location1.lower().split(',')[0].strip()
        loc2 = location2.lower().split(',')[0].strip()
        
        for city, nearby in german_cities.items():
            if loc1 == city and loc2 in nearby:
                return True
            if loc2 == city and loc1 in nearby:
                return True
        
        return False
    
    def _calculate_experience_compatibility(self, exp1: ExperienceLevel, exp2: ExperienceLevel) -> float:
        """Calculate experience level compatibility"""
        exp_order = {
            ExperienceLevel.ENTRY: 0,
            ExperienceLevel.JUNIOR: 1,
            ExperienceLevel.MID: 2,
            ExperienceLevel.SENIOR: 3,
            ExperienceLevel.LEAD: 4,
            ExperienceLevel.EXECUTIVE: 5
        }
        
        diff = abs(exp_order.get(exp1, 2) - exp_order.get(exp2, 2))
        
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.8
        elif diff == 2:
            return 0.5
        else:
            return 0.2
    
    def _calculate_experience_job_match(self, user_exp: ExperienceLevel, job_exp: ExperienceLevel) -> float:
        """Calculate if user experience matches job requirements"""
        exp_order = {
            ExperienceLevel.ENTRY: 0,
            ExperienceLevel.JUNIOR: 1,
            ExperienceLevel.MID: 2,
            ExperienceLevel.SENIOR: 3,
            ExperienceLevel.LEAD: 4,
            ExperienceLevel.EXECUTIVE: 5
        }
        
        user_level = exp_order.get(user_exp, 2)
        job_level = exp_order.get(job_exp, 2)
        
        if user_level >= job_level:
            return 1.0  # User meets or exceeds requirements
        else:
            diff = job_level - user_level
            if diff == 1:
                return 0.7  # One level below
            elif diff == 2:
                return 0.4  # Two levels below
            else:
                return 0.1  # Too junior
    
    async def _get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from database"""
        try:
            profile_data = await self.db.userprofiles.find_one({"user_id": user_id})
            if profile_data:
                profile_data["_id"] = str(profile_data["_id"])
                return UserProfile(**profile_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {str(e)}")
            return None
    
    # Real-time Matching Updates
    
    async def update_user_indices(self, user_id: str):
        """Update matching indices when user profile changes"""
        try:
            # Remove old entries
            for interest_set in self._interest_graph.values():
                interest_set.discard(user_id)
            
            for skill_set in self._skill_index.values():
                skill_set.discard(user_id)
            
            # Update location index
            for location_list in self._location_index.values():
                self._location_index[location_list] = [
                    u for u in location_list if u['user_id'] != user_id
                ]
            
            # Add new entries
            user_profile = await self._get_user_profile(user_id)
            if user_profile:
                for interest in user_profile.interests:
                    self._interest_graph[interest.lower()].add(user_id)
                
                for skill in user_profile.skills:
                    self._skill_index[skill.lower()].add(user_id)
                
                if user_profile.location:
                    self._location_index[user_profile.location.lower()].append({
                        'user_id': user_id,
                        'location': user_profile.location
                    })
            
            logger.info(f"Updated matching indices for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error updating user indices: {str(e)}")
    
    async def get_community_recommendations_feed(self, user_id: str) -> Dict[str, Any]:
        """Get personalized community networking feed"""
        try:
            # Get all recommendations in parallel
            communities, users, events, jobs = await asyncio.gather(
                self.find_matching_communities(user_id, limit=5),
                self.find_similar_users(user_id, limit=10),
                self.suggest_networking_events(user_id, limit=5),
                self.find_job_matches(user_id, limit=5),
                return_exceptions=True
            )
            
            return {
                'recommended_communities': communities if not isinstance(communities, Exception) else [],
                'suggested_connections': users if not isinstance(users, Exception) else [],
                'upcoming_events': events if not isinstance(events, Exception) else [],
                'job_matches': jobs if not isinstance(jobs, Exception) else [],
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error generating community feed: {str(e)}")
            return {}


# Global instance
community_matching_service = None

def get_community_matching_service(db_client) -> CommunityMatchingService:
    """Get or create community matching service instance"""
    global community_matching_service
    if community_matching_service is None:
        community_matching_service = CommunityMatchingService(db_client)
    return community_matching_service