import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Plus, QrCode, Share2, Edit, Eye, Globe, Lock, LogOut, User, Settings, BookOpen, Users, Zap } from 'lucide-react';
import { cardsApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';

const HomePage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user, logout } = useAuth();
  const [businessCards, setBusinessCards] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBusinessCards();
  }, []);

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
        
        <div className="flex items-center space-x-4">
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

      <div className="flex justify-center mb-8">
        <Button 
          onClick={handleCreateNew}
          size="lg"
          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
        >
          <Plus className="mr-2 h-5 w-5" />
          Neue Visitenkarte erstellen
        </Button>
      </div>

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
    </div>
  );
};

export default HomePage;