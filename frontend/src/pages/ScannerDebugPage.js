/**
 * Scanner Debug Page - Test complete scanner workflow
 * FIXES: Camera shutdown + Contact list integration
 */
import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  Camera, ArrowLeft, Users, CheckCircle, AlertCircle, 
  RefreshCw, Eye, List, Plus, TestTube
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../hooks/use-toast';
import CardScanner from '../components/CardScanner';
import api from '../services/api';

const ScannerDebugPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [showScanner, setShowScanner] = useState(false);
  const [contactList, setContactList] = useState([]);
  const [isLoadingContacts, setIsLoadingContacts] = useState(false);
  const [testResults, setTestResults] = useState([]);

  // Load contacts on component mount
  useEffect(() => {
    loadContacts();
  }, []);

  // Load user's contact list
  const loadContacts = async () => {
    try {
      setIsLoadingContacts(true);
      const response = await api.get('/cards');
      setContactList(response.data || []);
      
      toast({
        title: "Kontakte geladen",
        description: `${response.data?.length || 0} Visitenkarten gefunden`,
      });
      
    } catch (error) {
      console.error('Failed to load contacts:', error);
      toast({
        title: "Fehler beim Laden",
        description: "Kontaktliste konnte nicht geladen werden",
        variant: "destructive"
      });
    } finally {
      setIsLoadingContacts(false);
    }
  };

  // Handle successful card creation from scanner
  const handleCardCreated = (cardData) => {
    console.log('Card created:', cardData);
    
    // Close scanner
    setShowScanner(false);
    
    // Reload contact list to show new card
    setTimeout(() => {
      loadContacts();
    }, 1000);
    
    // Add to test results
    const newTest = {
      id: Date.now(),
      type: 'scanner_success',
      message: `✅ Visitenkarte "${cardData.name || 'Unbekannt'}" erfolgreich zur Kontaktliste hinzugefügt`,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setTestResults(prev => [newTest, ...prev]);
    
    toast({
      title: "Scanner-Test erfolgreich! 🎉",
      description: "Karte wurde zur Kontaktliste hinzugefügt und Kamera gestoppt",
    });
    
    // Check if navigation was requested
    if (cardData.navigateToList) {
      toast({
        title: "Zur Kontaktliste navigieren?",
        description: "Scanner-Workflow abgeschlossen!",
      });
    }
  };

  // Test camera shutdown
  const testCameraShutdown = () => {
    setShowScanner(true);
    
    // Add test record
    const newTest = {
      id: Date.now(),
      type: 'camera_test',
      message: '📹 Kamera-Test gestartet - überprüfen Sie die Abschaltung nach dem Scan',
      timestamp: new Date().toLocaleTimeString()
    };
    
    setTestResults(prev => [newTest, ...prev]);
  };

  // Test contact list refresh
  const testContactRefresh = async () => {
    const oldCount = contactList.length;
    await loadContacts();
    const newCount = contactList.length;
    
    const newTest = {
      id: Date.now(),
      type: 'refresh_test',
      message: `🔄 Kontaktliste aktualisiert: ${oldCount} → ${newCount} Karten`,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setTestResults(prev => [newTest, ...prev]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-4">
      <div className="container mx-auto max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              onClick={() => navigate('/')}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Zurück</span>
            </Button>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
                Scanner Debug & Test
              </h1>
              <p className="text-gray-600">
                Vollständiger Test der Scanner-Kamera-Abschaltung und Kontaktliste-Integration
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Test Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TestTube className="w-6 h-6 text-blue-600" />
                <span>Scanner-Tests</span>
              </CardTitle>
              <CardDescription>
                Testen Sie die behobenen Scanner-Probleme
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button
                  onClick={testCameraShutdown}
                  className="w-full bg-green-600 hover:bg-green-700"
                  disabled={showScanner}
                >
                  <Camera className="w-4 h-4 mr-2" />
                  Kamera-Abschaltung testen
                </Button>
                
                <Button
                  onClick={testContactRefresh}
                  variant="outline"
                  className="w-full"
                  disabled={isLoadingContacts}
                >
                  {isLoadingContacts ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4 mr-2" />
                  )}
                  Kontaktliste neu laden
                </Button>

                <div className="p-3 bg-blue-50 rounded-lg text-sm">
                  <h4 className="font-medium text-blue-900 mb-2">Was wird getestet:</h4>
                  <ul className="text-blue-800 space-y-1">
                    <li>✅ Kamera startet bei Scanner-Öffnung</li>
                    <li>✅ Foto wird aufgenommen und verarbeitet</li>
                    <li>✅ Kamera wird nach Scan automatisch gestoppt</li>
                    <li>✅ Scanner schließt sich nach Erfolg</li>
                    <li>✅ Neue Karte erscheint in Kontaktliste</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Contact List */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Users className="w-6 h-6 text-purple-600" />
                  <span>Kontaktliste</span>
                </div>
                <Badge className="bg-purple-100 text-purple-800">
                  {contactList.length} Karten
                </Badge>
              </CardTitle>
              <CardDescription>
                Gescannte Karten sollten hier automatisch erscheinen
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {contactList.length > 0 ? (
                  contactList.map((card, index) => (
                    <div key={card.id || index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <p className="font-medium">{card.name || 'Unbekannt'}</p>
                        <p className="text-sm text-gray-600">{card.company || 'Keine Firma'}</p>
                      </div>
                      <div className="text-right">
                        {card.source === 'scanner' ? (
                          <Badge className="bg-green-100 text-green-800">
                            Gescannt
                          </Badge>
                        ) : (
                          <Badge variant="outline">
                            Manual
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <List className="w-12 h-12 mx-auto mb-2" />
                    <p>Noch keine Visitenkarten</p>
                    <p className="text-sm">Scannen Sie eine Visitenkarte zum Testen</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Test Results */}
        {testResults.length > 0 && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <span>Test-Ergebnisse</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {testResults.map((result) => (
                  <div key={result.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex-1">
                      <p className="text-sm">{result.message}</p>
                    </div>
                    <div className="text-xs text-gray-500">
                      {result.timestamp}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Scanner Modal */}
        {showScanner && (
          <div className="fixed inset-0 z-50">
            <CardScanner 
              onCardCreated={handleCardCreated}
              onClose={() => {
                setShowScanner(false);
                
                // Add test result for manual close
                const newTest = {
                  id: Date.now(),
                  type: 'manual_close',
                  message: '❌ Scanner manuell geschlossen - Kamera sollte gestoppt sein',
                  timestamp: new Date().toLocaleTimeString()
                };
                
                setTestResults(prev => [newTest, ...prev]);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default ScannerDebugPage;