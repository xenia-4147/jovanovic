/**
 * Business Card Studio Page
 * Comprehensive hub for OCR Scanning and Print Export
 * Game-Changing Features in one place
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { 
  Scan,
  Printer,
  Sparkles,
  ArrowLeft,
  Camera,
  FileImage,
  Zap,
  Palette,
  Download,
  History,
  Star,
  TrendingUp
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { useAuth } from '../contexts/AuthContext';
import CardScanner from '../components/CardScanner';
import PrintExporter from '../components/PrintExporter';
import api from '../services/api';

const BusinessCardStudioPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();
  
  // States
  const [activeTab, setActiveTab] = useState('scanner');
  const [businessCards, setBusinessCards] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [recentScans, setRecentScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPrintExporter, setShowPrintExporter] = useState(false);
  
  // Load data on mount
  useEffect(() => {
    loadBusinessCards();
    loadRecentScans();
  }, []);
  
  // Load user's business cards
  const loadBusinessCards = async () => {
    try {
      const response = await api.get('/cards');
      setBusinessCards(response.data.cards || []);
      
      // Auto-select first card for print export
      if (response.data.cards?.length > 0) {
        setSelectedCard(response.data.cards[0]);
      }
      
    } catch (error) {
      console.error('Failed to load business cards:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Load recent scans
  const loadRecentScans = async () => {
    try {
      const response = await api.get('/scanner/scans');
      setRecentScans(response.data.scans || []);
      
    } catch (error) {
      console.error('Failed to load recent scans:', error);
    }
  };
  
  // Handle new card creation from scanner
  const handleCardCreated = (newCard) => {
    setBusinessCards(prev => [newCard, ...prev]);
    loadRecentScans(); // Refresh scans
    
    toast({
      title: "Neue Visitenkarte erstellt! 🎉",
      description: "Die gescannte Karte wurde erfolgreich zu Ihren Visitenkarten hinzugefügt.",
    });
  };
  
  // Handle print export selection
  const handlePrintExport = (card) => {
    setSelectedCard(card);
    setShowPrintExporter(true);
    setActiveTab('print');
  };

  // Stats calculation
  const stats = {
    totalScans: recentScans.length,
    successfulScans: recentScans.filter(scan => scan.status === 'completed').length,
    convertedCards: recentScans.filter(scan => scan.is_converted).length,
    averageConfidence: recentScans.length > 0 
      ? Math.round(recentScans.reduce((sum, scan) => sum + scan.overall_confidence, 0) / recentScans.length)
      : 0
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Lade Business Card Studio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Zurück zur Übersicht
          </Button>
          
          <div className="text-center mb-6">
            <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Business Card Studio
            </h1>
            <p className="text-xl text-gray-600 mb-6">
              Revolutionäre Tools für digitale Visitenkarten
            </p>
            
            {/* Feature Badges */}
            <div className="flex justify-center space-x-4 mb-6">
              <Badge variant="secondary" className="bg-blue-100 text-blue-800 px-4 py-2">
                <Camera className="w-4 h-4 mr-2" />
                KI-Scanner
              </Badge>
              <Badge variant="secondary" className="bg-purple-100 text-purple-800 px-4 py-2">
                <Printer className="w-4 h-4 mr-2" />
                Print-Export
              </Badge>
              <Badge variant="secondary" className="bg-green-100 text-green-800 px-4 py-2">
                <Sparkles className="w-4 h-4 mr-2" />
                Game-Changing
              </Badge>
            </div>
          </div>
          
          {/* Quick Stats */}
          {stats.totalScans > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="text-center p-4 bg-white rounded-lg shadow-sm border">
                <div className="text-2xl font-bold text-blue-600">{stats.totalScans}</div>
                <div className="text-sm text-gray-600">Gesamt Scans</div>
              </div>
              <div className="text-center p-4 bg-white rounded-lg shadow-sm border">
                <div className="text-2xl font-bold text-green-600">{stats.successfulScans}</div>
                <div className="text-sm text-gray-600">Erfolgreich</div>
              </div>
              <div className="text-center p-4 bg-white rounded-lg shadow-sm border">
                <div className="text-2xl font-bold text-purple-600">{stats.convertedCards}</div>
                <div className="text-sm text-gray-600">Konvertiert</div>
              </div>
              <div className="text-center p-4 bg-white rounded-lg shadow-sm border">
                <div className="text-2xl font-bold text-orange-600">{stats.averageConfidence}%</div>
                <div className="text-sm text-gray-600">Durchschn. Genauigkeit</div>
              </div>
            </div>
          )}
        </div>
        
        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-2xl mx-auto">
            <TabsTrigger value="scanner" className="flex items-center space-x-2">
              <Scan className="w-4 h-4" />
              <span>Visitenkarten Scanner</span>
            </TabsTrigger>
            <TabsTrigger value="print" className="flex items-center space-x-2">
              <Printer className="w-4 h-4" />
              <span>Druck Export</span>
            </TabsTrigger>
          </TabsList>
          
          {/* Scanner Tab */}
          <TabsContent value="scanner" className="space-y-6">
            <Card className="border-0 shadow-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white">
              <CardHeader>
                <CardTitle className="flex items-center text-white">
                  <Camera className="w-6 h-6 mr-2" />
                  OCR Visitenkarten Scanner
                </CardTitle>
                <CardDescription className="text-blue-100">
                  Fotografieren Sie Papier-Visitenkarten und wandeln Sie sie automatisch in digitale Karten um.
                  Unsere KI erkennt Namen, Telefonnummern, E-Mails und weitere Informationen.
                </CardDescription>
              </CardHeader>
            </Card>
            
            <CardScanner onCardCreated={handleCardCreated} />
            
            {/* Recent Scans */}
            {recentScans.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <History className="w-5 h-5 mr-2" />
                    Letzte Scans
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {recentScans.slice(0, 5).map((scan) => (
                      <div key={scan.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <Badge 
                              variant="outline"
                              className={
                                scan.status === 'completed' ? 'bg-green-100 text-green-800 border-green-300' :
                                scan.status === 'failed' ? 'bg-red-100 text-red-800 border-red-300' :
                                'bg-yellow-100 text-yellow-800 border-yellow-300'
                              }
                            >
                              {scan.status}
                            </Badge>
                            {scan.is_converted && (
                              <Badge variant="secondary">Konvertiert</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-1">
                            {new Date(scan.scan_timestamp).toLocaleString('de-DE')} - 
                            {Math.round(scan.overall_confidence)}% Genauigkeit
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
          
          {/* Print Tab */}
          <TabsContent value="print" className="space-y-6">
            <Card className="border-0 shadow-lg bg-gradient-to-r from-purple-500 to-pink-600 text-white">
              <CardHeader>
                <CardTitle className="flex items-center text-white">
                  <Printer className="w-6 h-6 mr-2" />
                  Professioneller Druck Export
                </CardTitle>
                <CardDescription className="text-purple-100">
                  Exportieren Sie Ihre digitalen Visitenkarten als druckfertige Dateien für professionelle Druckereien.
                  PDF, PNG und SVG Formate mit verschiedenen Qualitätsstufen verfügbar.
                </CardDescription>
              </CardHeader>
            </Card>
            
            {/* Card Selection for Print */}
            {!showPrintExporter && businessCards.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Visitenkarte auswählen</CardTitle>
                  <CardDescription>
                    Wählen Sie eine Ihrer Visitenkarten für den Druckexport aus
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {businessCards.map((card) => (
                      <div
                        key={card.id}
                        className="p-4 border-2 rounded-lg cursor-pointer hover:border-blue-400 transition-colors bg-white shadow-sm"
                        onClick={() => handlePrintExport(card)}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-medium text-gray-900">{card.name}</h3>
                          <Badge variant="outline" style={{ backgroundColor: card.accent_color + '20', color: card.accent_color }}>
                            {card.is_public ? 'Öffentlich' : 'Privat'}
                          </Badge>
                        </div>
                        
                        {card.company && (
                          <p className="text-sm text-gray-600 mb-1">{card.company}</p>
                        )}
                        
                        {card.position && (
                          <p className="text-sm text-gray-500 mb-3">{card.position}</p>
                        )}
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center text-xs text-gray-500">
                            <FileImage className="w-3 h-3 mr-1" />
                            {card.phones?.length || 0} Kontakte
                          </div>
                          <Button size="sm" variant="outline">
                            <Printer className="w-3 h-3 mr-1" />
                            Drucken
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* No cards message */}
            {businessCards.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <Printer className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">Keine Visitenkarten vorhanden</h3>
                  <p className="text-gray-600 mb-4">
                    Erstellen Sie zuerst eine Visitenkarte oder scannen Sie eine Papier-Visitenkarte ein.
                  </p>
                  <div className="flex justify-center space-x-4">
                    <Button onClick={() => navigate('/create')}>
                      Neue Karte erstellen
                    </Button>
                    <Button variant="outline" onClick={() => setActiveTab('scanner')}>
                      Karte scannen
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Print Exporter */}
            {showPrintExporter && selectedCard && (
              <PrintExporter 
                businessCard={selectedCard}
                onClose={() => {
                  setShowPrintExporter(false);
                  setSelectedCard(null);
                }}
              />
            )}
          </TabsContent>
        </Tabs>
        
        {/* Features Showcase */}
        {activeTab === 'scanner' && recentScans.length === 0 && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Star className="w-5 h-5 mr-2 text-yellow-500" />
                Warum unser Scanner revolutionär ist
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="bg-blue-100 p-3 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                    <Sparkles className="w-6 h-6 text-blue-600" />
                  </div>
                  <h3 className="font-medium mb-2">KI-Powered OCR</h3>
                  <p className="text-sm text-gray-600">
                    Fortschrittliche Texterkennung mit über 90% Genauigkeit für deutsche Visitenkarten.
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="bg-green-100 p-3 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                    <Zap className="w-6 h-6 text-green-600" />
                  </div>
                  <h3 className="font-medium mb-2">Sofortige Verarbeitung</h3>
                  <p className="text-sm text-gray-600">
                    Ergebnisse in unter 3 Sekunden mit automatischer Feldererkennung und Kategorisierung.
                  </p>
                </div>
                
                <div className="text-center">
                  <div className="bg-purple-100 p-3 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                  </div>
                  <h3 className="font-medium mb-2">Lernende Technologie</h3>
                  <p className="text-sm text-gray-600">
                    Jeder Scan verbessert die Genauigkeit und erkennt neue Visitenkarten-Layouts.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default BusinessCardStudioPage;