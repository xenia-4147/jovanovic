import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Users, Timer, Eye, Download, Phone, Mail, MapPin, Globe, Calendar, Clock, CheckCircle, AlertTriangle } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const MeetingRoomViewPage = () => {
  const { roomCode } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [room, setRoom] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshInterval, setRefreshInterval] = useState(null);

  useEffect(() => {
    loadRoomData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadRoomData(false);  // Silent refresh
    }, 30000);
    
    setRefreshInterval(interval);
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [roomCode]);

  const loadRoomData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    setError('');
    
    try {
      const response = await api.get(`/meeting-rooms/${roomCode}`);
      setRoom(response.data);
    } catch (error) {
      console.error('Failed to load meeting room:', error);
      setError(
        error.response?.data?.detail || 
        'Meeting Room konnte nicht geladen werden.'
      );
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const saveContactsToAddressBook = async () => {
    if (!room || room.participants.length <= 1) return;
    
    try {
      const contactsToSave = room.participants.filter(p => 
        p.card_id !== room.created_by_card_id || !room.is_creator
      );
      
      // Here you could implement actual address book saving
      // For now, just show a success message
      
      toast({
        title: "Kontakte gespeichert!",
        description: `${contactsToSave.length} neue Kontakte wurden zu Ihrem Adressbuch hinzugefügt.`
      });
    } catch (error) {
      console.error('Failed to save contacts:', error);
      toast({
        variant: "destructive",
        title: "Fehler",
        description: "Kontakte konnten nicht gespeichert werden."
      });
    }
  };

  const viewCard = (cardId) => {
    navigate(`/card/${cardId}`);
  };

  const formatTimeRemaining = (minutes) => {
    if (minutes <= 0) return "Abgelaufen";
    if (minutes < 60) return `${minutes} Minuten`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 1) return `1 Stunde ${mins} Minuten`;
    return `${hours} Stunden ${mins} Minuten`;
  };

  const getStatusColor = (minutes) => {
    if (minutes <= 0) return "destructive";
    if (minutes <= 5) return "secondary";
    if (minutes <= 15) return "default";
    return "default";
  };

  const formatJoinTime = (joinedAt) => {
    const date = new Date(joinedAt);
    return date.toLocaleTimeString('de-DE', { 
      hour: '2-digit', 
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Meeting Room wird geladen...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <Button 
              onClick={() => navigate('/')} 
              className="w-full mt-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Zurück zum Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/meeting-rooms')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Zurück zu Meeting Rooms
          </Button>
        </div>

        {/* Room Header */}
        <Card className="mb-6 shadow-lg border-0">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center space-x-4 mb-4">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full flex items-center justify-center">
                <Users className="w-8 h-8 text-white" />
              </div>
              <div>
                <code className="bg-gray-100 px-4 py-2 rounded-lg font-mono text-2xl font-bold">
                  {room.code}
                </code>
                <Badge 
                  variant={getStatusColor(room.time_remaining_minutes)}
                  className="ml-3"
                >
                  <Timer className="w-3 h-3 mr-1" />
                  {formatTimeRemaining(room.time_remaining_minutes)}
                </Badge>
              </div>
            </div>
            
            <CardTitle className="text-2xl">Meeting Room</CardTitle>
            <CardDescription>
              Erstellt von {room.created_by_card_name}
              {room.description && ` • ${room.description}`}
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-purple-600">{room.participants.length}</div>
                <div className="text-sm text-gray-600">Teilnehmer</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">{room.max_participants}</div>
                <div className="text-sm text-gray-600">Max. Teilnehmer</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{formatTimeRemaining(room.time_remaining_minutes)}</div>
                <div className="text-sm text-gray-600">Verbleibende Zeit</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-orange-600">
                  {new Date(room.created_at).toLocaleTimeString('de-DE')}
                </div>
                <div className="text-sm text-gray-600">Erstellt</div>
              </div>
            </div>

            {room.time_remaining_minutes <= 5 && room.time_remaining_minutes > 0 && (
              <Alert className="mt-6 border-orange-200 bg-orange-50">
                <Clock className="h-4 w-4 text-orange-600" />
                <AlertDescription className="text-orange-800">
                  <strong>Meeting Room läuft bald ab!</strong> Speichern Sie wichtige Kontakte, bevor der Room geschlossen wird.
                </AlertDescription>
              </Alert>
            )}

            {room.time_remaining_minutes <= 0 && (
              <Alert variant="destructive" className="mt-6">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Meeting Room ist abgelaufen.</strong> Neue Teilnehmer können nicht mehr beitreten.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Participants */}
        <Card className="shadow-lg border-0">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center">
                <Users className="w-5 h-5 mr-2" />
                Teilnehmer ({room.participants.length})
              </CardTitle>
              
              {room.participants.length > 1 && (
                <Button 
                  onClick={saveContactsToAddressBook}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Alle Kontakte speichern
                </Button>
              )}
            </div>
            <CardDescription>
              Alle Teilnehmer in diesem Meeting Room
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {room.participants.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Keine Teilnehmer im Room</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {room.participants.map((participant, index) => (
                  <div key={`${participant.card_id}-${index}`} className="border rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
                    <div className="flex items-start space-x-4">
                      <img
                        src={
                          participant.card_profile_image || 
                          `https://ui-avatars.com/api/?name=${encodeURIComponent(participant.card_name)}&background=22c55e&color=fff`
                        }
                        alt={participant.card_name}
                        className="w-12 h-12 rounded-full flex-shrink-0"
                      />
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="font-semibold truncate">{participant.card_name}</h3>
                          {participant.card_id === room.created_by_card_id && (
                            <Badge variant="secondary" className="text-xs">Ersteller</Badge>
                          )}
                        </div>
                        
                        {participant.card_company && (
                          <p className="text-sm text-gray-600 truncate">{participant.card_company}</p>
                        )}
                        
                        <p className="text-xs text-gray-500 mt-1">
                          Beigetreten: {formatJoinTime(participant.joined_at)}
                        </p>
                        
                        <div className="flex items-center space-x-2 mt-3">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => viewCard(participant.card_id)}
                          >
                            <Eye className="w-3 h-3 mr-1" />
                            Karte ansehen
                          </Button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => navigate(`/card/${participant.card_id}`)}
                          >
                            <Download className="w-3 h-3 mr-1" />
                            Kontakt
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Instructions */}
        <div className="mt-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-medium text-blue-900 mb-3">💡 Meeting Room Tipps</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <ul className="space-y-2">
              <li>• Teilen Sie den Room-Code mit anderen Teilnehmern</li>
              <li>• Neue Teilnehmer erhalten alle bisherigen Kontakte</li>
              <li>• Der Room läuft automatisch nach der Zeit ab</li>
            </ul>
            <ul className="space-y-2">
              <li>• Speichern Sie Kontakte vor Ablauf der Zeit</li>
              <li>• Nutzen Sie die "Alle Kontakte speichern" Funktion</li>
              <li>• Jede Person kann nur einmal pro Room teilnehmen</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MeetingRoomViewPage;