import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Zap, Users, Timer, Copy, CheckCircle, AlertCircle, Smartphone, Wifi } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const ExpressShareModal = ({ isOpen, onClose, userCards }) => {
  const { toast } = useToast();
  
  const [activeTab, setActiveTab] = useState('single'); // 'single' or 'group'
  const [selectedCard, setSelectedCard] = useState('');
  const [duration, setDuration] = useState(60);
  const [codeLength, setCodeLength] = useState(2);
  const [maxParticipants, setMaxParticipants] = useState(10);
  const [loading, setLoading] = useState(false);
  const [activeCode, setActiveCode] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [nfcSupported, setNfcSupported] = useState(false);

  useEffect(() => {
    if (userCards.length > 0 && !selectedCard) {
      setSelectedCard(userCards[0].id);
    }
  }, [userCards, selectedCard]);

  useEffect(() => {
    // Check NFC support
    if ('NDEFReader' in window) {
      setNfcSupported(true);
    }
  }, []);

  useEffect(() => {
    let interval;
    if (activeCode && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            setActiveCode(null);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [activeCode, timeRemaining]);

  const handleCreateExpressCode = async () => {
    if (!selectedCard) {
      toast({
        variant: "destructive",
        title: "Fehler",
        description: "Bitte wählen Sie eine Visitenkarte aus."
      });
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/express/create', {
        card_id: selectedCard,
        duration_seconds: duration,
        code_length: codeLength
      });

      setActiveCode(response.data);
      setTimeRemaining(response.data.time_remaining_seconds);

      toast({
        title: "Express Code erstellt!",
        description: `Code "${response.data.code}" für ${duration} Sekunden aktiv.`
      });

      // Try NFC sharing if available
      if (nfcSupported && 'NDEFReader' in window) {
        try {
          const ndef = new NDEFReader();
          await ndef.write({
            records: [{ 
              recordType: "text", 
              data: `Express Code: ${response.data.code}` 
            }]
          });
        } catch (error) {
          console.log('NFC write failed:', error);
        }
      }

    } catch (error) {
      console.error('Failed to create express code:', error);
      toast({
        variant: "destructive",
        title: "Fehler",
        description: error.response?.data?.detail || "Express Code konnte nicht erstellt werden."
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExpressRoom = async () => {
    if (!selectedCard) {
      toast({
        variant: "destructive",
        title: "Fehler",
        description: "Bitte wählen Sie eine Visitenkarte aus."
      });
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/express/room/create', {
        card_id: selectedCard,
        duration_seconds: duration,
        max_participants: maxParticipants
      });

      setActiveCode(response.data);
      setTimeRemaining(response.data.time_remaining_seconds);

      toast({
        title: "Express Room erstellt!",
        description: `Room "${response.data.code}" für ${Math.floor(duration/60)} Minuten aktiv.`
      });

    } catch (error) {
      console.error('Failed to create express room:', error);
      toast({
        variant: "destructive",
        title: "Fehler",
        description: error.response?.data?.detail || "Express Room konnte nicht erstellt werden."
      });
    } finally {
      setLoading(false);
    }
  };

  const copyCode = () => {
    if (activeCode) {
      navigator.clipboard.writeText(activeCode.code);
      toast({
        title: "Code kopiert!",
        description: `"${activeCode.code}" wurde kopiert.`
      });
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimerColor = () => {
    if (timeRemaining > 30) return "bg-green-500";
    if (timeRemaining > 10) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <Zap className="w-5 h-5 mr-2 text-yellow-500" />
            Express Share - Ultra-Schnell Teilen
          </DialogTitle>
          <DialogDescription>
            Erstellen Sie ultra-kurze Codes für sofortigen Visitenkarten-Austausch
          </DialogDescription>
        </DialogHeader>

        {!activeCode ? (
          <div className="space-y-6">
            {/* Tab Selection */}
            <div className="flex space-x-2 p-1 bg-gray-100 rounded-lg">
              <Button
                variant={activeTab === 'single' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setActiveTab('single')}
                className="flex-1"
              >
                <Zap className="w-4 h-4 mr-2" />
                Einzeln (1:1)
              </Button>
              <Button
                variant={activeTab === 'group' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setActiveTab('group')}
                className="flex-1"
              >
                <Users className="w-4 h-4 mr-2" />
                Gruppe
              </Button>
            </div>

            {/* Card Selection */}
            <div className="space-y-2">
              <Label>Ihre Visitenkarte</Label>
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

            {/* Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Laufzeit</Label>
                <Select value={duration.toString()} onValueChange={(value) => setDuration(parseInt(value))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30">30 Sekunden</SelectItem>
                    <SelectItem value="60">1 Minute</SelectItem>
                    <SelectItem value="120">2 Minuten</SelectItem>
                    <SelectItem value="300">5 Minuten</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {activeTab === 'single' ? (
                <div className="space-y-2">
                  <Label>Code-Länge</Label>
                  <Select value={codeLength.toString()} onValueChange={(value) => setCodeLength(parseInt(value))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2">2 Zeichen (A7)</SelectItem>
                      <SelectItem value="3">3 Zeichen (A7X)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <div className="space-y-2">
                  <Label>Max. Teilnehmer</Label>
                  <Select value={maxParticipants.toString()} onValueChange={(value) => setMaxParticipants(parseInt(value))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">5 Personen</SelectItem>
                      <SelectItem value="10">10 Personen</SelectItem>
                      <SelectItem value="15">15 Personen</SelectItem>
                      <SelectItem value="20">20 Personen</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            {/* NFC Info */}
            {nfcSupported && (
              <Alert className="bg-blue-50 border-blue-200">
                <Smartphone className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  NFC bereit! Nach Code-Erstellung können Sie Handys aneinanderhalten für direktes Teilen.
                </AlertDescription>
              </Alert>
            )}

            {/* Action Buttons */}
            <div className="flex space-x-3">
              {activeTab === 'single' ? (
                <Button 
                  onClick={handleCreateExpressCode}
                  disabled={loading || !selectedCard}
                  className="flex-1 bg-yellow-500 hover:bg-yellow-600"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Erstelle...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      Express Code erstellen
                    </>
                  )}
                </Button>
              ) : (
                <Button 
                  onClick={handleCreateExpressRoom}
                  disabled={loading || !selectedCard}
                  className="flex-1 bg-purple-500 hover:bg-purple-600"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Erstelle...
                    </>
                  ) : (
                    <>
                      <Users className="w-4 h-4 mr-2" />
                      Express Room erstellen
                    </>
                  )}
                </Button>
              )}
              
              <Button variant="outline" onClick={onClose}>
                Abbrechen
              </Button>
            </div>
          </div>
        ) : (
          /* Active Code Display */
          <div className="space-y-6 text-center">
            {/* Timer */}
            <div className="flex justify-center">
              <div className={`px-4 py-2 rounded-full text-white font-mono ${getTimerColor()}`}>
                <Timer className="w-4 h-4 inline mr-2" />
                {formatTime(timeRemaining)}
              </div>
            </div>

            {/* Code Display */}
            <div className="bg-gray-50 p-8 rounded-lg border-2 border-dashed border-gray-300">
              <div className="text-6xl font-mono font-bold text-blue-600 mb-4">
                {activeCode.code}
              </div>
              <p className="text-gray-600 text-lg">
                {activeTab === 'single' ? 'Sagen Sie:' : 'Alle sagen:'} <strong>"{activeCode.code}"</strong>
              </p>
              {activeTab === 'group' && (
                <p className="text-sm text-gray-500 mt-2">
                  Teilnehmer: {activeCode.participant_count || 1}/{activeCode.max_participants || maxParticipants}
                </p>
              )}
            </div>

            {/* Instructions */}
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <h3 className="font-medium text-blue-900 mb-2">💡 So funktioniert's:</h3>
              <div className="text-sm text-blue-800 text-left">
                {activeTab === 'single' ? (
                  <ul className="space-y-1">
                    <li>• Person geht auf die App und klickt "Code eingeben"</li>
                    <li>• Sie gibt "{activeCode.code}" ein</li>
                    <li>• Ihre Visitenkarte wird sofort angezeigt</li>
                    <li>• Oder: Handys aneinanderhalten (NFC)</li>
                  </ul>
                ) : (
                  <ul className="space-y-1">
                    <li>• Alle Teilnehmer gehen auf die App</li>
                    <li>• Jeder gibt "{activeCode.code}" ein</li>
                    <li>• Alle erhalten die Kontakte der anderen</li>
                    <li>• Perfekt für Gruppen-Networking</li>
                  </ul>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <Button 
                onClick={copyCode}
                variant="outline"
                className="flex-1"
              >
                <Copy className="w-4 h-4 mr-2" />
                Code kopieren
              </Button>
              
              <Button 
                onClick={() => {
                  setActiveCode(null);
                  setTimeRemaining(0);
                }}
                variant="outline"
                className="flex-1"
              >
                Neuen Code erstellen
              </Button>
              
              <Button variant="outline" onClick={onClose}>
                Schließen
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ExpressShareModal;