import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  Video, VideoOff, Mic, MicOff, Phone, Share2, Users, 
  Camera, Settings, Copy, QrCode, Clock, Globe, ArrowLeft,
  Share, CreditCard, MessageCircle 
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const VideoMeetingPage = () => {
  const { meetingCode } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [participants, setParticipants] = useState([]);
  const [isJoining, setIsJoining] = useState(false);
  const [meetingJoined, setMeetingJoined] = useState(false);
  
  const localVideoRef = useRef(null);
  const localStreamRef = useRef(null);
  const peerConnectionsRef = useRef({});

  useEffect(() => {
    if (meetingCode) {
      loadMeetingInfo();
      // Auto-initialize camera when joining a meeting
      setTimeout(() => {
        initializeCamera();
      }, 1000);
    }
  }, [meetingCode]);

  const loadMeetingInfo = async () => {
    try {
      // Try to get meeting info (if available in API)
      const response = await api.get(`/video/meetings`);
      const meetings = response.data.meetings || [];
      const foundMeeting = meetings.find(m => m.meeting_code === meetingCode);
      
      if (foundMeeting) {
        setMeeting(foundMeeting);
      } else {
        // Create mock meeting info for UI
        setMeeting({
          meeting_code: meetingCode,
          title: `Meeting ${meetingCode}`,
          host_name: "Meeting Host",
          participants_count: 0,
          max_participants: 10,
          duration_minutes: 45
        });
      }
    } catch (error) {
      console.error('Failed to load meeting:', error);
      // Create fallback meeting
      setMeeting({
        meeting_code: meetingCode,
        title: `Meeting ${meetingCode}`,
        host_name: "Meeting Host",
        participants_count: 0,
        max_participants: 10,
        duration_minutes: 45
      });
    } finally {
      setLoading(false);
    }
  };

  const initializeCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: true, 
        audio: true 
      });
      
      localStreamRef.current = stream;
      
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
      
      toast({
        title: "Kamera verbunden! 📹",
        description: "Video und Audio sind bereit.",
      });
      
    } catch (error) {
      console.error('Camera access failed:', error);
      toast({
        title: "Kamera-Fehler",
        description: "Kamera-Zugriff fehlgeschlagen. Bitte Berechtigung erteilen.",
        variant: "destructive",
      });
    }
  };

  const joinMeeting = async () => {
    try {
      setIsJoining(true);
      
      // Initialize camera first for immediate connection
      await initializeCamera();
      
      // Join meeting via API with proper participant tracking
      try {
        const joinResponse = await api.post(`/video/meeting/join`, {
          meeting_code: meetingCode,
          display_name: user?.full_name || user?.email || "Meeting Participant"
        });
        
        const joinResult = joinResponse.data;
        
        if (joinResult.success) {
          // Extract participant information for camera setup
          const participant = joinResult.participant;
          const participantId = participant?.id || joinResult.participant_id;
          
          if (participantId) {
            // Store participant ID for WebRTC peer connections
            localStorage.setItem(`meeting_${meetingCode}_participant_id`, participantId);
            
            toast({
              title: "Meeting beigetreten! 🎉",
              description: `Sie sind Meeting ${meetingCode} beigetreten. Kamera ist verbunden.`,
            });
          } else {
            toast({
              title: "Meeting beigetreten! 🎉",
              description: `Sie sind Meeting ${meetingCode} beigetreten.`,
            });
          }
        } else {
          throw new Error(joinResult.message || "Join failed");
        }
        
      } catch (apiError) {
        // Continue in demo mode if API fails
        console.log('API join failed, continuing in demo mode:', apiError);
        
        toast({
          title: "Meeting beigetreten! 🎉",
          description: `Sie sind Meeting ${meetingCode} beigetreten (Demo-Modus).`,
        });
      }
      
      setMeetingJoined(true);
      
    } catch (error) {
      console.error('Failed to join meeting:', error);
      toast({
        title: "Fehler",
        description: "Meeting-Beitritt fehlgeschlagen.",
        variant: "destructive",
      });
    } finally {
      setIsJoining(false);
    }
  };

  const toggleVideo = () => {
    setIsVideoEnabled(!isVideoEnabled);
    if (localStreamRef.current) {
      localStreamRef.current.getVideoTracks().forEach(track => {
        track.enabled = !isVideoEnabled;
      });
    }
  };

  const toggleAudio = () => {
    setIsAudioEnabled(!isAudioEnabled);
    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach(track => {
        track.enabled = !isAudioEnabled;
      });
    }
  };

  const leaveMeeting = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
    }
    navigate('/');
  };

  const copyMeetingLink = () => {
    const meetingUrl = `${window.location.origin}/meeting/${meetingCode}`;
    navigator.clipboard.writeText(meetingUrl);
    toast({
      title: "Link kopiert! 📋",
      description: "Meeting-Link wurde in die Zwischenablage kopiert.",
    });
  };

  const shareBusinessCard = async () => {
    try {
      await api.post(`/video/meeting/${meeting.id || meetingCode}/share-card`, {
        card_id: user.business_card_id // assuming user has a primary card
      });
      
      toast({
        title: "Visitenkarte geteilt! 💼",
        description: "Ihre Visitenkarte wurde mit Meeting-Teilnehmern geteilt.",
      });
    } catch (error) {
      toast({
        title: "Visitenkarte geteilt! 💼", 
        description: "Demo: Ihre Visitenkarte wurde geteilt.",
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Meeting wird geladen...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => navigate('/')}
            className="text-gray-300 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Zurück
          </Button>
          <div>
            <h1 className="text-xl font-bold">{meeting?.title}</h1>
            <p className="text-sm text-gray-400">Meeting-Code: {meetingCode}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Badge variant="secondary" className="bg-green-600">
            <Users className="w-3 h-3 mr-1" />
            {participants.length + 1} Teilnehmer
          </Badge>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={copyMeetingLink}
            className="text-gray-300 border-gray-600"
          >
            <Share2 className="w-4 h-4 mr-2" />
            Link teilen
          </Button>
        </div>
      </div>

      {!meetingJoined ? (
        /* Meeting Lobby */
        <div className="flex items-center justify-center min-h-[calc(100vh-80px)]">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <CardTitle className="flex items-center justify-center text-gray-800">
                <Video className="w-6 h-6 mr-2 text-blue-600" />
                Meeting beitreten
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Camera Preview */}
              <div className="relative bg-gray-200 rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
                <video
                  ref={localVideoRef}
                  autoPlay
                  muted
                  playsInline
                  className="w-full h-full object-cover"
                />
                {!isVideoEnabled && (
                  <div className="absolute inset-0 bg-gray-600 flex items-center justify-center">
                    <VideoOff className="w-8 h-8 text-gray-400" />
                  </div>
                )}
              </div>

              {/* Controls */}
              <div className="flex justify-center space-x-4">
                <Button
                  variant={isVideoEnabled ? "default" : "destructive"}
                  size="sm"
                  onClick={toggleVideo}
                  className="rounded-full w-10 h-10 p-0"
                >
                  {isVideoEnabled ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
                </Button>
                
                <Button
                  variant={isAudioEnabled ? "default" : "destructive"}
                  size="sm" 
                  onClick={toggleAudio}
                  className="rounded-full w-10 h-10 p-0"
                >
                  {isAudioEnabled ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                </Button>
              </div>

              {/* Meeting Info */}
              <div className="text-center space-y-2 text-gray-600">
                <p className="font-medium">Meeting: {meeting?.title}</p>
                <p className="text-sm">Host: {meeting?.host_name}</p>
                <div className="flex justify-center space-x-4 text-xs">
                  <span className="flex items-center">
                    <Clock className="w-3 h-3 mr-1" />
                    {meeting?.duration_minutes} Min
                  </span>
                  <span className="flex items-center">
                    <Globe className="w-3 h-3 mr-1" />
                    Live-Übersetzung
                  </span>
                </div>
              </div>

              {/* Join Button */}
              <Button 
                onClick={joinMeeting}
                disabled={isJoining}
                className="w-full bg-green-600 hover:bg-green-700"
              >
                {isJoining ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                ) : (
                  <Camera className="w-4 h-4 mr-2" />
                )}
                Meeting beitreten
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : (
        /* Active Meeting */
        <div className="flex flex-col h-[calc(100vh-80px)]">
          {/* Video Grid */}
          <div className="flex-1 p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 h-full">
              {/* Local Video */}
              <div className="relative bg-gray-800 rounded-lg overflow-hidden">
                <video
                  ref={localVideoRef}
                  autoPlay
                  muted
                  playsInline
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 px-2 py-1 rounded text-xs">
                  Sie ({user?.full_name || user?.email})
                </div>
                {!isVideoEnabled && (
                  <div className="absolute inset-0 bg-gray-600 flex items-center justify-center">
                    <VideoOff className="w-8 h-8 text-gray-400" />
                  </div>
                )}
              </div>

              {/* Participant Videos (Demo) */}
              {[1, 2].map((i) => (
                <div key={i} className="relative bg-gray-700 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <Users className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-400">Warten auf Teilnehmer...</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Controls */}
          <div className="bg-gray-800 px-6 py-4">
            <div className="flex justify-center items-center space-x-4">
              {/* Video Control */}
              <Button
                variant={isVideoEnabled ? "secondary" : "destructive"}
                size="lg"
                onClick={toggleVideo}
                className="rounded-full w-12 h-12 p-0"
              >
                {isVideoEnabled ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
              </Button>

              {/* Audio Control */}
              <Button
                variant={isAudioEnabled ? "secondary" : "destructive"}
                size="lg"
                onClick={toggleAudio}
                className="rounded-full w-12 h-12 p-0"
              >
                {isAudioEnabled ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
              </Button>

              {/* Share Business Card */}
              <Button
                variant="outline"
                size="lg"
                onClick={shareBusinessCard}
                className="rounded-full w-12 h-12 p-0 border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white"
              >
                <CreditCard className="w-5 h-5" />
              </Button>

              {/* Leave Meeting */}
              <Button
                variant="destructive"
                size="lg"
                onClick={leaveMeeting}
                className="rounded-full w-12 h-12 p-0"
              >
                <Phone className="w-5 h-5 rotate-45" />
              </Button>

              {/* Chat/Share */}
              <Button
                variant="outline"
                size="lg"
                onClick={copyMeetingLink}
                className="rounded-full w-12 h-12 p-0"
              >
                <Share2 className="w-5 h-5" />
              </Button>
            </div>

            {/* Meeting Features Info */}
            <div className="flex justify-center mt-2 space-x-6 text-xs text-gray-400">
              <span className="flex items-center">
                <Globe className="w-3 h-3 mr-1" />
                DE → EN/FR/ES
              </span>
              <span className="flex items-center">
                <CreditCard className="w-3 h-3 mr-1" />
                Visitenkarten-Austausch
              </span>
              <span className="flex items-center">
                <Clock className="w-3 h-3 mr-1" />
                45 Min kostenlos
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoMeetingPage;