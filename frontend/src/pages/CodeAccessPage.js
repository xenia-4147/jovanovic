import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';
import { ArrowLeft, Search, Key, CheckCircle, AlertCircle, Users, Zap } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const CodeAccessPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!code.trim()) {
      setError('Bitte geben Sie einen Code ein.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const cleanCode = code.trim().toUpperCase();
      
      // First try as express code
      try {
        const response = await api.post('/express/access', { code: cleanCode });
        
        if (response.data.success) {
          setResult({
            ...response.data,
            type: 'express_code'
          });
          toast({
            title: "Express Code gefunden!",
            description: `Visitenkarte von ${response.data.card.name} über Express Code erhalten.`,
          });
          return;
        }
      } catch (expressError) {
        // If express code fails, try as business card code
        if (expressError.response?.status === 404) {
          try {
            const response = await api.post('/cards/access-by-code', { code: cleanCode });
            
            if (response.data.success) {
              setResult({
                ...response.data,
                type: 'business_card'
              });
              toast({
                title: "Visitenkarte gefunden!",
                description: `Visitenkarte von ${response.data.card.name} gefunden.`,
              });
              return;
            }
          } catch (cardError) {
            // If business card code fails, try as meeting room code
            if (cardError.response?.status === 404) {
              try {
                const roomResponse = await api.get(`/meeting-rooms/${cleanCode}`);
                
                if (roomResponse.data) {
                  setResult({
                    success: true,
                    type: 'meeting_room',
                    room: roomResponse.data,
                    message: `Meeting Room "${roomResponse.data.code}" gefunden`
                  });
                  toast({
                    title: "Meeting Room gefunden!",
                    description: `Meeting Room "${roomResponse.data.code}" mit ${roomResponse.data.participants.length} Teilnehmern gefunden.`,
                  });
                  return;
                }
              } catch (roomError) {
                // All failed, show generic error
              }
            }
          }
        }
      }
      
      // If both methods failed
      setError('Code nicht gefunden oder ungültig.');
      
    } catch (err) {
      console.error('Code access failed:', err);
      setError(
        err.response?.data?.detail || 
        err.response?.data?.message || 
        'Code nicht gefunden oder ungültig.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleViewCard = () => {
    if (result && result.card) {
      navigate(`/card/${result.card.id}`);
    }
  };

  const handleViewMeetingRoom = () => {
    if (result && result.room) {
      navigate(`/meeting-room/${result.room.code}`);
    }
  };

  const handleJoinMeetingRoom = () => {
    if (result && result.room) {
      // For now, redirect to meeting room view
      // Later, we could implement a card selection dialog for joining
      navigate(`/meeting-room/${result.room.code}`);
    }
  };

  const handleClearResults = () => {
    setResult(null);
    setError('');
    setCode('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Zurück
          </Button>
          
          <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Key className="w-8 h-8 text-white" />
          </div>
          
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            Code eingeben
          </h1>
          <p className="text-gray-600">
            Geben Sie den Code einer Visitenkarte ein, um den Kontakt zu erhalten
          </p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center">
              <Search className="w-5 h-5 mr-2" />
              Visitenkarten-Code
            </CardTitle>
            <CardDescription>
              Codes sind eindeutige Bezeichnungen wie "WerbegiganCH" oder "MaxMustermann2024"
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {result && result.success && result.type === 'express_code' && (
              <Alert className="mb-6 bg-yellow-50 border-yellow-200">
                <Zap className="h-4 w-4 text-yellow-600" />
                <AlertDescription className="text-yellow-800">
                  <div className="font-medium mb-2">Express Code gefunden! ⚡</div>
                  <div className="flex items-center space-x-3">
                    <img
                      src={result.card.profile_image || `https://ui-avatars.com/api/?name=${encodeURIComponent(result.card.name)}&background=f59e0b&color=fff`}
                      alt={result.card.name}
                      className="w-10 h-10 rounded-full"
                    />
                    <div>
                      <p className="font-semibold">{result.card.name}</p>
                      {result.card.company && <p className="text-sm">{result.card.company}</p>}
                    </div>
                  </div>
                  <div className="mt-2 text-sm">
                    Express Code: <strong>{result.express_code?.code}</strong> | 
                    Verwendungen: <strong>{result.express_code?.usage_count}</strong>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {result && result.success && result.type === 'business_card' && (
              <Alert className="mb-6 bg-green-50 border-green-200">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  <div className="font-medium mb-2">Visitenkarte gefunden!</div>
                  <div className="flex items-center space-x-3">
                    <img
                      src={result.card.profile_image || `https://ui-avatars.com/api/?name=${encodeURIComponent(result.card.name)}&background=22c55e&color=fff`}
                      alt={result.card.name}
                      className="w-10 h-10 rounded-full"
                    />
                    <div>
                      <p className="font-semibold">{result.card.name}</p>
                      {result.card.company && <p className="text-sm">{result.card.company}</p>}
                    </div>
                  </div>
                  <div className="mt-2 text-sm">
                    Code verwendet: <strong>{result.code_usage_count}</strong> Mal
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {result && result.success && result.type === 'meeting_room' && (
              <Alert className="mb-6 bg-blue-50 border-blue-200">
                <Users className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  <div className="font-medium mb-2">Meeting Room gefunden!</div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <code className="bg-blue-100 px-2 py-1 rounded font-mono font-bold">
                        {result.room.code}
                      </code>
                      <span className="text-sm">von {result.room.created_by_card_name}</span>
                    </div>
                    {result.room.description && (
                      <p className="text-sm">{result.room.description}</p>
                    )}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>Teilnehmer: <strong>{result.room.participants.length}/{result.room.max_participants}</strong></div>
                      <div>Zeit übrig: <strong>{result.room.time_remaining_minutes} min</strong></div>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="code">Visitenkarten-Code</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    id="code"
                    type="text"
                    placeholder="z.B. WerbegiganCH oder MaxMustermann2024"
                    value={code}
                    onChange={(e) => {
                      setCode(e.target.value);
                      if (error) setError('');
                      if (result) setResult(null);
                    }}
                    className="pl-10 uppercase"
                    style={{ textTransform: 'uppercase' }}
                    disabled={loading}
                  />
                </div>
                <p className="text-xs text-gray-500">
                  Codes bestehen aus Buchstaben und Zahlen (3-50 Zeichen)
                </p>
              </div>

              <div className="space-y-3">
                <Button 
                  type="submit" 
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  disabled={loading || !code.trim()}
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Suche...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Code suchen
                    </>
                  )}
                </Button>

                {result && result.success && (result.type === 'express_code' || result.type === 'business_card') && (
                  <div className="grid grid-cols-2 gap-3">
                    <Button 
                      variant="outline" 
                      onClick={handleViewCard}
                      className="w-full"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      Visitenkarte anzeigen
                    </Button>
                    
                    <Button 
                      variant="outline" 
                      onClick={handleClearResults}
                      className="w-full"
                    >
                      Neuer Code
                    </Button>
                  </div>
                )}

                {result && result.success && result.type === 'meeting_room' && (
                  <div className="grid grid-cols-2 gap-3">
                    <Button 
                      variant="outline" 
                      onClick={handleViewMeetingRoom}
                      className="w-full"
                    >
                      <Users className="w-4 h-4 mr-1" />
                      Meeting Room anzeigen
                    </Button>
                    
                    <Button 
                      variant="outline" 
                      onClick={handleClearResults}
                      className="w-full"
                    >
                      Neuer Code
                    </Button>
                  </div>
                )}
              </div>
            </form>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h3 className="font-medium text-blue-900 mb-2">💡 Wie funktioniert es?</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium text-blue-900 mb-2">Visitenkarten-Codes</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Persönliche Codes für einzelne Visitenkarten</li>
                    <li>• Dauerhaft gültig bis geändert</li>
                    <li>• Ideal für Einzelkontakte</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium text-blue-900 mb-2">Meeting Room Codes</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Temporäre Räume für Gruppen-Austausch</li>
                    <li>• Automatischer Ablauf nach 10-60 Minuten</li>
                    <li>• Perfekt für Events und Netzwerken</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CodeAccessPage;