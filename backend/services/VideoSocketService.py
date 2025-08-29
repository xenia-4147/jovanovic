"""
Real-time Video Communication Service using Socket.IO
Revolutionary Feature: WebRTC Signaling with Business Card Integration
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import socketio
from fastapi import FastAPI
from aiohttp import web
from aiohttp_cors import setup as cors_setup, ResourceOptions

from models.VideoMeeting import (
    VideoMeetingRoom, MeetingParticipant, BusinessCardShare,
    MeetingStatus, WEBRTC_CONFIG, MEETING_LIMITS
)
from models.Community import UserProfile

logger = logging.getLogger(__name__)


class VideoSocketService:
    """Socket.IO service for real-time video communication"""
    
    def __init__(self, db_client):
        self.db = db_client
        self.sio = socketio.AsyncServer(
            async_mode='aiohttp',
            cors_allowed_origins="*",
            logger=logger,
            engineio_logger=logger
        )
        
        # Active connections tracking
        self.active_connections: Dict[str, Dict] = {}  # socket_id -> connection_info
        self.meeting_participants: Dict[str, List[str]] = {}  # meeting_id -> [socket_ids]
        self.user_sockets: Dict[str, str] = {}  # user_id -> socket_id
        
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle client connection"""
            logger.info(f"Client connected: {sid}")
            
            # Verify authentication
            if not auth or 'user_id' not in auth:
                logger.warning(f"Unauthenticated connection rejected: {sid}")
                await self.sio.disconnect(sid)
                return False
            
            user_id = auth['user_id']
            self.active_connections[sid] = {
                'user_id': user_id,
                'connected_at': datetime.utcnow(),
                'meeting_id': None
            }
            self.user_sockets[user_id] = sid
            
            logger.info(f"User {user_id} connected with socket {sid}")
            return True
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            if sid in self.active_connections:
                connection = self.active_connections[sid]
                user_id = connection['user_id']
                meeting_id = connection.get('meeting_id')
                
                # Leave meeting if in one
                if meeting_id:
                    await self._leave_meeting(sid, meeting_id, user_id)
                
                # Clean up connection tracking
                del self.active_connections[sid]
                if user_id in self.user_sockets:
                    del self.user_sockets[user_id]
                
                logger.info(f"User {user_id} disconnected (socket {sid})")
        
        @self.sio.event
        async def join_meeting(sid, data):
            """Handle joining a video meeting"""
            try:
                meeting_id = data.get('meeting_id')
                display_name = data.get('display_name', 'Unknown')
                
                if sid not in self.active_connections:
                    await self.sio.emit('error', {'message': 'Not authenticated'}, room=sid)
                    return
                
                user_id = self.active_connections[sid]['user_id']
                
                # Validate meeting exists and user can join
                meeting = await self._get_meeting(meeting_id)
                if not meeting:
                    await self.sio.emit('error', {'message': 'Meeting not found'}, room=sid)
                    return
                
                # Check meeting capacity
                current_participants = len(self.meeting_participants.get(meeting_id, []))
                if current_participants >= meeting.max_participants:
                    await self.sio.emit('error', {'message': 'Meeting is full'}, room=sid)
                    return
                
                # Add participant to meeting
                participant = await self._add_participant_to_meeting(
                    meeting_id, user_id, sid, display_name
                )
                
                # Join Socket.IO room
                await self.sio.enter_room(sid, meeting_id)
                
                # Track participant in meeting
                if meeting_id not in self.meeting_participants:
                    self.meeting_participants[meeting_id] = []
                self.meeting_participants[meeting_id].append(sid)
                self.active_connections[sid]['meeting_id'] = meeting_id
                
                # Notify other participants
                await self.sio.emit('participant_joined', {
                    'participant': participant.dict(),
                    'total_participants': len(self.meeting_participants[meeting_id])
                }, room=meeting_id, skip_sid=sid)
                
                # Send meeting info and WebRTC config to new participant
                participants = await self._get_meeting_participants(meeting_id)
                shared_cards = await self._get_shared_business_cards(meeting_id)
                
                await self.sio.emit('meeting_joined', {
                    'meeting': meeting.dict(),
                    'participant': participant.dict(),
                    'participants': [p.dict() for p in participants],
                    'shared_cards': [c.dict() for c in shared_cards],
                    'webrtc_config': WEBRTC_CONFIG
                }, room=sid)
                
                # Update meeting status to active if first participant
                if len(self.meeting_participants[meeting_id]) == 1:
                    await self._update_meeting_status(meeting_id, MeetingStatus.ACTIVE)
                
                logger.info(f"User {user_id} joined meeting {meeting_id}")
                
            except Exception as e:
                logger.error(f"Error joining meeting: {str(e)}")
                await self.sio.emit('error', {'message': 'Failed to join meeting'}, room=sid)
        
        @self.sio.event
        async def leave_meeting(sid, data):
            """Handle leaving a video meeting"""
            if sid not in self.active_connections:
                return
            
            connection = self.active_connections[sid]
            meeting_id = connection.get('meeting_id')
            user_id = connection['user_id']
            
            if meeting_id:
                await self._leave_meeting(sid, meeting_id, user_id)
        
        @self.sio.event
        async def webrtc_offer(sid, data):
            """Handle WebRTC offer signaling"""
            await self._relay_webrtc_signal('webrtc_offer', sid, data)
        
        @self.sio.event
        async def webrtc_answer(sid, data):
            """Handle WebRTC answer signaling"""
            await self._relay_webrtc_signal('webrtc_answer', sid, data)
        
        @self.sio.event
        async def webrtc_candidate(sid, data):
            """Handle WebRTC ICE candidate signaling"""
            await self._relay_webrtc_signal('webrtc_candidate', sid, data)
        
        @self.sio.event
        async def share_business_card(sid, data):
            """Handle business card sharing in meeting"""
            try:
                if sid not in self.active_connections:
                    return
                
                connection = self.active_connections[sid]
                meeting_id = connection.get('meeting_id')
                user_id = connection['user_id']
                
                if not meeting_id:
                    await self.sio.emit('error', {'message': 'Not in a meeting'}, room=sid)
                    return
                
                business_card_id = data.get('business_card_id')
                message = data.get('message', '')
                recipient_ids = data.get('recipient_ids', [])  # Empty = all participants
                
                # Create business card share record
                share = await self._create_business_card_share(
                    meeting_id, user_id, business_card_id, message, recipient_ids
                )
                
                # Get business card details
                business_card = await self._get_business_card(business_card_id)
                
                if business_card:
                    share_data = {
                        'share': share.dict(),
                        'business_card': business_card,
                        'sender_name': self.active_connections[sid].get('display_name', 'Unknown')
                    }
                    
                    # Send to specific recipients or all participants
                    if recipient_ids:
                        for recipient_id in recipient_ids:
                            if recipient_id in self.user_sockets:
                                recipient_sid = self.user_sockets[recipient_id]
                                await self.sio.emit('business_card_shared', share_data, room=recipient_sid)
                    else:
                        # Send to all meeting participants except sender
                        await self.sio.emit('business_card_shared', share_data, room=meeting_id, skip_sid=sid)
                    
                    logger.info(f"Business card {business_card_id} shared by {user_id} in meeting {meeting_id}")
                
            except Exception as e:
                logger.error(f"Error sharing business card: {str(e)}")
                await self.sio.emit('error', {'message': 'Failed to share business card'}, room=sid)
        
        @self.sio.event
        async def toggle_audio(sid, data):
            """Handle audio mute/unmute"""
            await self._relay_participant_action('audio_toggled', sid, data)
        
        @self.sio.event
        async def toggle_video(sid, data):
            """Handle video on/off"""
            await self._relay_participant_action('video_toggled', sid, data)
        
        @self.sio.event
        async def start_screen_share(sid, data):
            """Handle screen sharing start"""
            await self._relay_participant_action('screen_share_started', sid, data)
        
        @self.sio.event
        async def stop_screen_share(sid, data):
            """Handle screen sharing stop"""
            await self._relay_participant_action('screen_share_stopped', sid, data)
        
        @self.sio.event
        async def send_chat_message(sid, data):
            """Handle chat messages in meeting"""
            try:
                if sid not in self.active_connections:
                    return
                
                connection = self.active_connections[sid]
                meeting_id = connection.get('meeting_id')
                user_id = connection['user_id']
                
                if not meeting_id:
                    return
                
                message_data = {
                    'user_id': user_id,
                    'display_name': data.get('display_name', 'Unknown'),
                    'message': data.get('message', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Relay chat message to all meeting participants
                await self.sio.emit('chat_message', message_data, room=meeting_id)
                
            except Exception as e:
                logger.error(f"Error sending chat message: {str(e)}")
    
    async def _relay_webrtc_signal(self, signal_type: str, sender_sid: str, data: Dict):
        """Relay WebRTC signaling between participants"""
        try:
            target_user_id = data.get('target_user_id')
            if target_user_id and target_user_id in self.user_sockets:
                target_sid = self.user_sockets[target_user_id]
                
                # Add sender info
                sender_connection = self.active_connections.get(sender_sid, {})
                data['sender_user_id'] = sender_connection.get('user_id')
                
                await self.sio.emit(signal_type, data, room=target_sid)
                
        except Exception as e:
            logger.error(f"Error relaying WebRTC signal {signal_type}: {str(e)}")
    
    async def _relay_participant_action(self, action_type: str, sender_sid: str, data: Dict):
        """Relay participant actions (mute, video, etc.) to meeting"""
        try:
            if sender_sid not in self.active_connections:
                return
            
            connection = self.active_connections[sender_sid]
            meeting_id = connection.get('meeting_id')
            
            if meeting_id:
                # Add sender info
                data['user_id'] = connection['user_id']
                data['timestamp'] = datetime.utcnow().isoformat()
                
                # Relay to all participants except sender
                await self.sio.emit(action_type, data, room=meeting_id, skip_sid=sender_sid)
                
        except Exception as e:
            logger.error(f"Error relaying participant action {action_type}: {str(e)}")
    
    async def _leave_meeting(self, sid: str, meeting_id: str, user_id: str):
        """Handle participant leaving meeting"""
        try:
            # Remove from meeting tracking
            if meeting_id in self.meeting_participants:
                if sid in self.meeting_participants[meeting_id]:
                    self.meeting_participants[meeting_id].remove(sid)
                
                # Update participant record
                await self._remove_participant_from_meeting(meeting_id, user_id)
                
                # Leave Socket.IO room
                await self.sio.leave_room(sid, meeting_id)
                
                # Clear meeting from connection
                self.active_connections[sid]['meeting_id'] = None
                
                # Notify other participants
                await self.sio.emit('participant_left', {
                    'user_id': user_id,
                    'total_participants': len(self.meeting_participants[meeting_id])
                }, room=meeting_id)
                
                # End meeting if no participants left
                if len(self.meeting_participants[meeting_id]) == 0:
                    await self._update_meeting_status(meeting_id, MeetingStatus.ENDED)
                    del self.meeting_participants[meeting_id]
                
                logger.info(f"User {user_id} left meeting {meeting_id}")
                
        except Exception as e:
            logger.error(f"Error leaving meeting: {str(e)}")
    
    # Database operations
    async def _get_meeting(self, meeting_id: str) -> Optional[VideoMeetingRoom]:
        """Get meeting from database"""
        try:
            meeting_data = await self.db.videomeetings.find_one({"_id": meeting_id})
            if meeting_data:
                meeting_data["_id"] = str(meeting_data["_id"])
                return VideoMeetingRoom(**meeting_data)
            return None
        except Exception as e:
            logger.error(f"Error getting meeting {meeting_id}: {str(e)}")
            return None
    
    async def _add_participant_to_meeting(self, meeting_id: str, user_id: str, socket_id: str, display_name: str) -> MeetingParticipant:
        """Add participant to meeting"""
        try:
            participant = MeetingParticipant(
                meeting_id=meeting_id,
                user_id=user_id,
                display_name=display_name,
                socket_id=socket_id
            )
            
            participant_dict = participant.dict(by_alias=True, exclude={"id"})
            result = await self.db.meetingparticipants.insert_one(participant_dict)
            participant.id = str(result.inserted_id)
            
            return participant
            
        except Exception as e:
            logger.error(f"Error adding participant to meeting: {str(e)}")
            raise
    
    async def _remove_participant_from_meeting(self, meeting_id: str, user_id: str):
        """Remove participant from meeting"""
        try:
            await self.db.meetingparticipants.update_one(
                {"meeting_id": meeting_id, "user_id": user_id},
                {"$set": {"left_at": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Error removing participant from meeting: {str(e)}")
    
    async def _get_meeting_participants(self, meeting_id: str) -> List[MeetingParticipant]:
        """Get all participants in meeting"""
        try:
            participants = []
            cursor = self.db.meetingparticipants.find({
                "meeting_id": meeting_id,
                "left_at": {"$exists": False}
            })
            
            async for participant_data in cursor:
                participant_data["_id"] = str(participant_data["_id"])
                participants.append(MeetingParticipant(**participant_data))
            
            return participants
            
        except Exception as e:
            logger.error(f"Error getting meeting participants: {str(e)}")
            return []
    
    async def _create_business_card_share(self, meeting_id: str, sender_id: str, card_id: str, message: str, recipient_ids: List[str]) -> BusinessCardShare:
        """Create business card share record"""
        try:
            share = BusinessCardShare(
                meeting_id=meeting_id,
                sender_id=sender_id,
                business_card_id=card_id,
                sharing_message=message,
                recipient_ids=recipient_ids
            )
            
            share_dict = share.dict(by_alias=True, exclude={"id"})
            result = await self.db.businesscardshares.insert_one(share_dict)
            share.id = str(result.inserted_id)
            
            return share
            
        except Exception as e:
            logger.error(f"Error creating business card share: {str(e)}")
            raise
    
    async def _get_shared_business_cards(self, meeting_id: str) -> List[BusinessCardShare]:
        """Get all business cards shared in meeting"""
        try:
            shares = []
            cursor = self.db.businesscardshares.find({"meeting_id": meeting_id})
            
            async for share_data in cursor:
                share_data["_id"] = str(share_data["_id"])
                shares.append(BusinessCardShare(**share_data))
            
            return shares
            
        except Exception as e:
            logger.error(f"Error getting shared business cards: {str(e)}")
            return []
    
    async def _get_business_card(self, card_id: str) -> Optional[Dict]:
        """Get business card details"""
        try:
            card_data = await self.db.businesscards.find_one({"_id": card_id})
            if card_data:
                card_data["_id"] = str(card_data["_id"])
                return card_data
            return None
        except Exception as e:
            logger.error(f"Error getting business card {card_id}: {str(e)}")
            return None
    
    async def _update_meeting_status(self, meeting_id: str, status: MeetingStatus):
        """Update meeting status"""
        try:
            update_data = {"status": status.value}
            
            if status == MeetingStatus.ACTIVE:
                update_data["started_at"] = datetime.utcnow()
            elif status == MeetingStatus.ENDED:
                update_data["ended_at"] = datetime.utcnow()
            
            await self.db.videomeetings.update_one(
                {"_id": meeting_id},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"Error updating meeting status: {str(e)}")
    
    async def get_app(self) -> web.Application:
        """Get aiohttp application with Socket.IO"""
        app = web.Application()
        self.sio.attach(app)
        
        # Setup CORS
        cors = cors_setup(app, defaults={
            "*": ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        return app
    
    async def send_meeting_invitation(self, user_id: str, meeting_data: Dict):
        """Send meeting invitation to user"""
        if user_id in self.user_sockets:
            socket_id = self.user_sockets[user_id]
            await self.sio.emit('meeting_invitation', meeting_data, room=socket_id)
    
    async def notify_community_event(self, user_ids: List[str], event_data: Dict):
        """Notify users about community events"""
        for user_id in user_ids:
            if user_id in self.user_sockets:
                socket_id = self.user_sockets[user_id]
                await self.sio.emit('community_event', event_data, room=socket_id)
    
    async def broadcast_job_match(self, user_id: str, job_data: Dict):
        """Broadcast job match to user"""
        if user_id in self.user_sockets:
            socket_id = self.user_sockets[user_id]
            await self.sio.emit('job_match', job_data, room=socket_id)


# Global instance
video_socket_service = None

def get_video_socket_service(db_client) -> VideoSocketService:
    """Get or create video socket service instance"""
    global video_socket_service
    if video_socket_service is None:
        video_socket_service = VideoSocketService(db_client)
    return video_socket_service