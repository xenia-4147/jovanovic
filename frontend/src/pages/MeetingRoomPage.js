import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Users, Clock, Plus, Eye, Trash2, Copy, QrCode, AlertCircle, CheckCircle, Timer } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const MeetingRoomPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [userCards, setUserCards] = useState([]);
  const [activeRooms, setActiveRooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [loadingRooms, setLoadingRooms] = useState(true);
  
  // Form state
  const [selectedCard, setSelectedCard] = useState('');
  const [customCode, setCustomCode] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState(10);
  const [maxParticipants, setMaxParticipants] = useState(20);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    loadUserCards();
    loadActiveRooms();
  }, []);

  const loadUserCards = async () => {
    try {
      const response = await api.get('/cards');
      setUserCards(response.data);
      if (response.data.length > 0 && !selectedCard) {
        setSelectedCard(response.data[0].id);
      }
    } catch (error) {
      console.error('Failed to load user cards:', error);
      toast({
        variant: "destructive",
        title: "Fehler",
        description: "Visitenkarten konnten nicht geladen werden."
      });
    }
  };

  const loadActiveRooms = async () => {
    setLoadingRooms(true);
    try {
      const response = await api.get('/meeting-rooms');
      setActiveRooms(response.data);
    } catch (error) {
      console.error('Failed to load active rooms:', error);
    } finally {
      setLoadingRooms(false);
    }
  };

  const createMeetingRoom = async (e) => {
    e.preventDefault();
    
    if (!selectedCard) {
      toast({
        variant: "destructive",
        title: "Fehler",
        description: "Bitte wählen Sie eine Visitenkarte aus."
      });
      return;
    }

    setCreating(true);

    try {
      const roomData = {
        card_id: selectedCard,
        description: description.trim() || undefined,
        duration_minutes: duration,
        max_participants: maxParticipants
      };

      if (customCode.trim()) {
        roomData.code = customCode.trim();
      }

      const response = await api.post('/meeting-rooms', roomData);
      
      toast({
        title: "Meeting Room erstellt!",
        description: `Code: ${response.data.code} - Läuft für ${duration} Minuten`
      });

      // Reset form
      setCustomCode('');
      setDescription('');
      setDuration(10);
      setMaxParticipants(20);
      setShowCreateForm(false);
      
      // Reload active rooms
      loadActiveRooms();

    } catch (error) {
      console.error('Failed to create meeting room:', error);
      toast({
        variant: "destructive",
        title: "Fehler",
        description: error.response?.data?.detail || "Meeting Room konnte nicht erstellt werden."
      });
    } finally {
      setCreating(false);
    }
  };

  const closeMeetingRoom = async (roomCode) => {
    try {
      await api.delete(`/meeting-rooms/${roomCode}`);
      
      toast({
        title: "Meeting Room geschlossen",
        description: `Room "${roomCode}" wurde erfolgreich geschlossen.`
      });
      
      loadActiveRooms();
    } catch (error) {
      console.error('Failed to close meeting room:', error);
      toast({
        variant: "destructive",
        title: "Fehler",
        description: "Meeting Room konnte nicht geschlossen werden."
      });
    }
  };

  const copyRoomCode = (code) => {
    navigator.clipboard.writeText(code);
    toast({
      title: "Code kopiert!",
      description: `Meeting Room Code "${code}" wurde in die Zwischenablage kopiert.`
    });
  };

  const viewRoom = (roomCode) => {
    navigate(`/meeting-room/${roomCode}`);
  };

  const formatTimeRemaining = (minutes) => {
    if (minutes <= 0) return "Abgelaufen";
    if (minutes < 60) return `${minutes}min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}min`;
  };

  const getStatusColor = (minutes) => {
    if (minutes <= 0) return "destructive";
    if (minutes <= 5) return "secondary";
    return "default";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Zurück zum Dashboard
          </Button>
          
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
              Meeting Rooms
            </h1>
            <p className="text-gray-600">
              Erstellen Sie Meeting Rooms für einfachen Visitenkarten-Austausch bei Events
            </p>
          </div>
        </div>

        {/* Create Form */}
        <Card className="mb-8 shadow-lg border-0">
          <CardHeader className="cursor-pointer" onClick={() => setShowCreateForm(!showCreateForm)}>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <Plus className="w-5 h-5 mr-2" />
                Neuen Meeting Room erstellen
              </div>
              <Badge variant="secondary">
                {showCreateForm ? 'Schließen' : 'Öffnen'}
              </Badge>
            </CardTitle>
            <CardDescription>
              Erstellen Sie einen temporären Raum zum Austausch von Visitenkarten
            </CardDescription>
          </CardHeader>
          
          {showCreateForm && (
            <CardContent>
              <form onSubmit={createMeetingRoom} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="card">Ihre Visitenkarte</Label>
                    <Select value={selectedCard} onValueChange={setSelectedCard}>
                      <SelectTrigger>
                        <SelectValue placeholder="Visitenkarte wählen" />
                      </SelectTrigger>
                      <SelectContent>
                        {userCards.map((card) => (
                          <SelectItem key={card.id} value={card.id}>
                            {card.name} {card.company && `- ${card.company}`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="customCode">Eigener Code (optional)</Label>
                    <Input
                      id="customCode"
                      type="text"
                      placeholder="z.B. EVENT2024 (3-10 Zeichen)"
                      value={customCode}
                      onChange={(e) => setCustomCode(e.target.value.toUpperCase())}
                      maxLength={10}
                    />
                    <p className="text-xs text-gray-500">
                      Leer lassen für automatischen Code
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="duration">Laufzeit (Minuten)</Label>
                    <Select value={duration.toString()} onValueChange={(value) => setDuration(parseInt(value))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="5">5 Minuten</SelectItem>
                        <SelectItem value="10">10 Minuten</SelectItem>
                        <SelectItem value="15">15 Minuten</SelectItem>
                        <SelectItem value="30">30 Minuten</SelectItem>
                        <SelectItem value="60">60 Minuten</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="maxParticipants">Max. Teilnehmer</Label>
                    <Select value={maxParticipants.toString()} onValueChange={(value) => setMaxParticipants(parseInt(value))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="5">5 Personen</SelectItem>
                        <SelectItem value="10">10 Personen</SelectItem>
                        <SelectItem value="20">20 Personen</SelectItem>
                        <SelectItem value="30">30 Personen</SelectItem>
                        <SelectItem value="50">50 Personen</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Beschreibung (optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="z.B. Networking Event Berlin 2024"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    maxLength={200}
                  />
                </div>

                <Button 
                  type="submit" 
                  className="w-full bg-purple-600 hover:bg-purple-700"
                  disabled={creating || !selectedCard}
                >
                  {creating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Erstelle Room...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4 mr-2" />
                      Meeting Room erstellen
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          )}
        </Card>

        {/* Active Rooms */}
        <Card className="shadow-lg border-0">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Aktive Meeting Rooms
            </CardTitle>
            <CardDescription>
              Ihre laufenden Meeting Rooms
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {loadingRooms ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-4"></div>
                <p>Lade Meeting Rooms...</p>
              </div>
            ) : activeRooms.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Keine aktiven Meeting Rooms</p>
                <p className="text-sm">Erstellen Sie einen neuen Room, um zu beginnen</p>
              </div>
            ) : (
              <div className="space-y-4">
                {activeRooms.map((room) => (
                  <div key={room.id} className="border rounded-lg p-4 bg-white">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="flex items-center space-x-3">
                          <code className="bg-gray-100 px-2 py-1 rounded font-mono text-lg font-bold">
                            {room.code}
                          </code>
                          <Badge variant={getStatusColor(room.time_remaining_minutes)}>
                            <Timer className="w-3 h-3 mr-1" />
                            {formatTimeRemaining(room.time_remaining_minutes)}
                          </Badge>
                        </div>
                        {room.description && (
                          <p className="text-sm text-gray-600 mt-1">{room.description}</p>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyRoomCode(room.code)}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => viewRoom(room.code)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => closeMeetingRoom(room.code)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Teilnehmer: {room.participant_count}/{room.max_participants}</span>
                      <span>Erstellt: {new Date(room.created_at).toLocaleTimeString('de-DE')}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info Section */}
        <div className="mt-8 p-6 bg-purple-50 rounded-lg border border-purple-200">
          <h3 className="font-medium text-purple-900 mb-3">💡 Wie funktionieren Meeting Rooms?</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-purple-800">
            <ul className="space-y-2">
              <li>• Erstellen Sie einen Room mit eigenem Code</li>
              <li>• Teilen Sie den Code mit anderen Teilnehmern</li>
              <li>• Alle mit dem Code erhalten die Visitenkarten der Teilnehmer</li>
            </ul>
            <ul className="space-y-2">
              <li>• Rooms laufen automatisch nach eingestellter Zeit ab</li>
              <li>• Perfekt für Networking-Events und Konferenzen</li>
              <li>• Jeder kann nur mit einer Karte pro Room teilnehmen</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MeetingRoomPage;