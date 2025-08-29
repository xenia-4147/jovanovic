import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Plus, QrCode, Share2, Edit, Eye, Globe, Lock, LogOut, User, Settings, BookOpen, Users, Zap, Key, Copy, Upload } from 'lucide-react';
import api, { cardsApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import ExpressShareModal from '../components/ExpressShareModal';
import EarlyAdopterBadge from '../components/EarlyAdopterBadge';

const HomePage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user, logout } = useAuth();
  const [businessCards, setBusinessCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showExpressModal, setShowExpressModal] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);

  useEffect(() => {
    loadBusinessCards();
    loadSubscriptionStatus();
  }, []);

  const loadSubscriptionStatus = async () => {
    try {
      const response = await api.get('/subscription/status');
      setSubscriptionStatus(response.data);
    } catch (error) {
      console.error('Failed to load subscription status:', error);
      // Don't show error for subscription status - it's not critical
    }
  };

  const loadBusinessCards = async () => {
    try {
      setLoading(true);
      const cards = await cardsApi.getAll();
      setBusinessCards(cards);
    } catch (error) {
      console.error('Failed to load business cards:', error);
      toast({
        title: "Fehler",
        description: "Visitenkarten konnten nicht geladen werden.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    navigate('/create');
  };

  const handleViewCard = (id) => {
    navigate(`/card/${id}`);
  };

  const handleEditCard = (id) => {
    navigate(`/edit/${id}`);
  };

  const handleGenerateQR = async (card) => {
    try {
      const qrUrl = cardsApi.generateQR(card.id);
      window.open(qrUrl, '_blank');
      toast({
        title: "QR Code geöffnet",
        description: "Der QR Code wurde in einem neuen Tab geöffnet.",
      });
    } catch (error) {
      toast({
        title: "Fehler",
        description: "QR Code konnte nicht generiert werden.",
        variant: "destructive",
      });
    }
  };

  const handleShare = async (card) => {
    const shareUrl = `${window.location.origin}/card/${card.id}`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: `${card.name} - Digitale Visitenkarte`,
          text: `Schauen Sie sich meine digitale Visitenkarte an!`,
          url: shareUrl,
        });
      } catch (error) {
        console.log('Sharing failed:', error);
      }
    } else {
      navigator.clipboard.writeText(shareUrl);
      toast({
        title: "Link kopiert",
        description: "Der Link zu Ihrer Visitenkarte wurde kopiert.",
      });
    }
  };

  const handleLogout = () => {
    logout();
    toast({
      title: "Abgemeldet",
      description: "Sie wurden erfolgreich abgemeldet.",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Lade Visitenkarten...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header with User Info */}
      <header className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            Digitale Visitenkarten
          </h1>
          <p className="text-gray-600">
            Willkommen zurück, {user?.first_name || user?.email}!
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => navigate('/addressbook')}
          >
            <BookOpen className="w-4 h-4 mr-2" />
            Adressbuch
          </Button>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => navigate('/meeting-rooms')}
          >
            <Users className="w-4 h-4 mr-2" />
            Meeting Rooms
          </Button>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => navigate('/contacts')}
          >
            <Upload className="w-4 h-4 mr-2" />
            Kontakte verwalten
          </Button>
          
          {subscriptionStatus?.plan_type === 'free' && (
            <>
              {subscriptionStatus?.plan_name?.includes('Early Adopter') ? (
                <EarlyAdopterBadge className="hidden sm:inline-flex" />
              ) : (
                <Badge 
                  variant="secondary" 
                  className="bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-800 border border-yellow-300 hidden sm:inline-flex"
                >
                  <Zap className="w-3 h-3 mr-1" />
                  Fast alles kostenlos! 🚀
                </Badge>
              )}
            </>
          )}
          
          <Button variant="outline" size="sm">
            <User className="w-4 h-4 mr-2" />
            {user?.full_name || user?.email}
          </Button>
          
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Einstellungen
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleLogout}>
            <LogOut className="w-4 h-4 mr-2" />
            Abmelden
          </Button>
        </div>
      </header>

      <div className="flex flex-col sm:flex-row justify-center gap-4 mb-8">
        <Button 
          onClick={handleCreateNew}
          size="lg"
          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
        >
          <Plus className="mr-2 h-5 w-5" />
          Neue Visitenkarte erstellen
        </Button>
        
        {businessCards.length > 0 && (
          <Button 
            onClick={() => setShowExpressModal(true)}
            size="lg"
            variant="outline"
            className="bg-gradient-to-r from-yellow-400 to-orange-400 hover:from-yellow-500 hover:to-orange-500 text-white border-0 px-8 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
          >
            <Zap className="mr-2 h-5 w-5" />
            Express Share
          </Button>
        )}
      </div>

      {/* Game-Changing Features Showcase */}
      <Card className="mb-8 bg-gradient-to-r from-purple-600 to-pink-600 text-white border-0 shadow-xl">
        <CardContent className="p-6">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold mb-2 flex items-center justify-center">
              <Sparkles className="mr-2 h-6 w-6" />
              Business Card Studio - Game-Changing Features
            </h2>
            <p className="text-purple-100">Revolutionäre Tools für moderne Visitenkarten</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* OCR Scanner Feature */}
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 hover:bg-white/20 transition-all duration-300">
              <div className="flex items-center mb-4">
                <div className="bg-white/20 p-3 rounded-full mr-4">
                  <Camera className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">KI Visitenkarten Scanner</h3>
                  <p className="text-purple-100 text-sm">Papier → Digital in Sekunden</p>
                </div>
              </div>
              <p className="text-purple-100 text-sm mb-4">
                Fotografieren Sie Papier-Visitenkarten und unsere KI wandelt sie automatisch in digitale Karten um. 
                90%+ Genauigkeit bei der Texterkennung.
              </p>
              <Button
                variant="secondary"
                size="sm"
                className="bg-white/20 hover:bg-white/30 text-white border-0"
                onClick={() => navigate('/studio?tab=scanner')}
              >
                <Scan className="w-4 h-4 mr-2" />
                Scanner öffnen
              </Button>
            </div>
            
            {/* Print Export Feature */}
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 hover:bg-white/20 transition-all duration-300">
              <div className="flex items-center mb-4">
                <div className="bg-white/20 p-3 rounded-full mr-4">
                  <Printer className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">Professioneller Druck Export</h3>
                  <p className="text-purple-100 text-sm">Digital → Druckerei-bereit</p>
                </div>
              </div>
              <p className="text-purple-100 text-sm mb-4">
                Exportieren Sie Visitenkarten als druckfertige PDF, PNG oder SVG Dateien. 
                Verschiedene Vorlagen und Qualitätsstufen verfügbar.
              </p>
              <Button
                variant="secondary"
                size="sm"
                className="bg-white/20 hover:bg-white/30 text-white border-0"
                onClick={() => navigate('/studio?tab=print')}
              >
                <FileImage className="w-4 h-4 mr-2" />
                Druck Export
              </Button>
            </div>
          </div>
          
          <div className="text-center mt-6">
            <Button
              variant="secondary"
              size="lg"
              className="bg-white text-purple-600 hover:bg-gray-100 px-8"
              onClick={() => navigate('/studio')}
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Business Card Studio öffnen
            </Button>
          </div>
        </CardContent>
      </Card>

      {businessCards.length === 0 ? (
        <Card className="max-w-md mx-auto text-center border-dashed border-2 border-gray-300">
          <CardContent className="pt-6 pb-6">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <Plus className="h-8 w-8 text-gray-400" />
            </div>
            <CardTitle className="text-xl text-gray-600 mb-2">Keine Visitenkarten vorhanden</CardTitle>
            <CardDescription className="mb-4">
              Erstellen Sie Ihre erste digitale Visitenkarte, um loszulegen.
            </CardDescription>
            <Button onClick={handleCreateNew} variant="outline">
              Jetzt erstellen
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {businessCards.map((card) => (
            <Card key={card.id} className="overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:scale-105 border-0 shadow-lg">
              <CardHeader className="relative p-0">
                <div 
                  className="h-32 bg-gradient-to-r p-4 text-white"
                  style={{
                    background: `linear-gradient(135deg, ${card.accent_color}15 0%, ${card.accent_color}25 100%)`
                  }}
                >
                  <div className="flex justify-between items-start">
                    <Badge variant={card.is_public ? "default" : "secondary"} className="mb-2">
                      {card.is_public ? (
                        <>
                          <Globe className="w-3 h-3 mr-1" />
                          Öffentlich
                        </>
                      ) : (
                        <>
                          <Lock className="w-3 h-3 mr-1" />
                          Privat
                        </>
                      )}
                    </Badge>
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleGenerateQR(card)}
                        className="text-gray-700 hover:bg-white/20 h-8 w-8 p-0"
                      >
                        <QrCode className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleShare(card)}
                        className="text-gray-700 hover:bg-white/20 h-8 w-8 p-0"
                      >
                        <Share2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3 mt-2">
                    <img
                      src={card.profile_image || `https://ui-avatars.com/api/?name=${encodeURIComponent(card.name)}&background=6366f1&color=fff`}
                      alt={card.name}
                      className="w-12 h-12 rounded-full border-2 border-white shadow-md"
                    />
                    <div>
                      <CardTitle className="text-lg text-gray-800">{card.name}</CardTitle>
                      <CardDescription className="text-gray-600">{card.position}</CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-4">
                <div className="space-y-2 text-sm text-gray-600 mb-4">
                  <p className="font-medium text-gray-800">{card.company}</p>
                  {card.emails && card.emails.length > 0 && (
                    <p>{card.emails.find(e => e.is_primary)?.address || card.emails[0].address}</p>
                  )}
                  {card.phones && card.phones.length > 0 && (
                    <p>{card.phones.find(p => p.is_primary)?.number || card.phones[0].number}</p>
                  )}
                  {(card.custom_code || card.customCode) && (
                    <div className="flex items-center space-x-2 bg-blue-50 p-2 rounded-md">
                      <Key className="w-3 h-3 text-blue-600" />
                      <span className="text-xs font-mono font-semibold text-blue-700">
                        Code: {card.custom_code || card.customCode}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          navigator.clipboard.writeText(card.custom_code || card.customCode);
                          toast({ title: "Code kopiert!", description: `"${card.custom_code || card.customCode}" wurde kopiert.` });
                        }}
                        className="h-6 w-6 p-0 hover:bg-blue-100"
                      >
                        <Copy className="w-3 h-3 text-blue-600" />
                      </Button>
                    </div>
                  )}
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleViewCard(card.id)}
                    className="flex-1"
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    Anzeigen
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleEditCard(card.id)}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    <Edit className="mr-2 h-4 w-4" />
                    Bearbeiten
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Express Share Modal */}
      <ExpressShareModal 
        isOpen={showExpressModal}
        onClose={() => setShowExpressModal(false)}
        userCards={businessCards}
      />
    </div>
  );
};

export default HomePage;