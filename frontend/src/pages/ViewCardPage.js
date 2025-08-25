import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Separator } from '../components/ui/separator';
import { ArrowLeft, Download, QrCode, Share2, Phone, Mail, Globe, MapPin, Instagram, Linkedin, Twitter, Send, MessageCircle, Copy, Code, RefreshCw, Clock, Users } from 'lucide-react';
import { cardsApi, downloadVCardFile } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';

const ViewCardPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();
  const [card, setCard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [qrCode, setQrCode] = useState(null);

  useEffect(() => {
    if (id === 'preview') {
      // Load preview data from sessionStorage
      const previewData = sessionStorage.getItem('previewCard');
      if (previewData) {
        setCard(JSON.parse(previewData));
      }
      setLoading(false);
    } else {
      loadCard();
    }
  }, [id]);

  const loadCard = async () => {
    try {
      setLoading(true);
      const cardData = await cardsApi.getById(id);
      setCard(cardData);
    } catch (error) {
      console.error('Failed to load card:', error);
      toast({
        title: "Fehler",
        description: "Visitenkarte konnte nicht geladen werden.",
        variant: "destructive",
      });
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadVCard = async () => {
    try {
      downloadVCardFile(card);
      toast({
        title: "Download gestartet",
        description: "Die Kontaktdatei wurde heruntergeladen.",
      });
    } catch (error) {
      toast({
        title: "Fehler",
        description: "Download konnte nicht gestartet werden.",
        variant: "destructive",
      });
    }
  };

  const handleGenerateQR = async () => {
    try {
      const qrUrl = cardsApi.generateQR(card.id || 'preview');
      setQrCode(qrUrl);
      toast({
        title: "QR Code generiert",
        description: "Der QR Code ist bereit zum Teilen.",
      });
    } catch (error) {
      toast({
        title: "Fehler",
        description: "QR Code konnte nicht generiert werden.",
        variant: "destructive",
      });
    }
  };

  const handleShare = async () => {
    const shareUrl = id === 'preview' ? window.location.origin : `${window.location.origin}/card/${id}`;
    
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
        description: "Der Link wurde in die Zwischenablage kopiert.",
      });
    }
  };

  const handleCall = (phone) => {
    window.location.href = `tel:${phone.number}`;
  };

  const handleMessage = (phone) => {
    // Check if it's a WhatsApp number or regular SMS
    if (phone.label.toLowerCase().includes('whatsapp')) {
      window.open(`https://wa.me/${phone.number.replace(/[^\d]/g, '')}`, '_blank');
    } else {
      window.location.href = `sms:${phone.number}`;
    }
  };

  const handleEmailAction = (email) => {
    window.location.href = `mailto:${email.address}`;
  };

  const handleGetEmbedCode = async () => {
    try {
      const embedCode = `<iframe 
  src="${window.location.origin}/card/${card.id}" 
  width="320" 
  height="450"
  style="border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"
  frameborder="0">
</iframe>`;
      
      navigator.clipboard.writeText(embedCode);
      toast({
        title: "Embed-Code kopiert",
        description: "Der HTML-Code wurde in die Zwischenablage kopiert.",
      });
    } catch (error) {
      toast({
        title: "Fehler",
        description: "Embed-Code konnte nicht generiert werden.",
        variant: "destructive",
      });
    }
  };

  const getSocialIcon = (platform) => {
    switch (platform) {
      case 'instagram': return <Instagram className="w-4 h-4" />;
      case 'linkedin': return <Linkedin className="w-4 h-4" />;
      case 'twitter': return <Twitter className="w-4 h-4" />;
      case 'telegram': return <Send className="w-4 h-4" />;
      case 'tiktok': return <div className="w-4 h-4 bg-current rounded-sm"></div>;
      default: return null;
    }
  };

  const getSocialUrl = (platform, username) => {
    const urls = {
      instagram: `https://instagram.com/${username}`,
      linkedin: `https://linkedin.com/in/${username}`,
      twitter: `https://twitter.com/${username}`,
      telegram: `https://t.me/${username}`,
      tiktok: `https://tiktok.com/@${username}`
    };
    return urls[platform] || '#';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Lade Visitenkarte...</p>
        </div>
      </div>
    );
  }

  if (!card) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="max-w-md mx-auto text-center">
          <CardContent className="pt-6">
            <h2 className="text-xl font-bold text-gray-800 mb-2">Visitenkarte nicht gefunden</h2>
            <p className="text-gray-600 mb-4">Die angeforderte Visitenkarte existiert nicht oder ist nicht verfügbar.</p>
            <Button onClick={() => navigate('/')}>Zur Startseite</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: `${card.backgroundColor}10` }}>
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {id !== 'preview' && (
          <header className="flex items-center mb-8">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="mr-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Zurück
            </Button>
          </header>
        )}

        <Card 
          className="overflow-hidden shadow-2xl border-0"
          style={{ 
            backgroundColor: card.background_color || card.backgroundColor,
            color: card.text_color || card.textColor,
            boxShadow: `0 25px 50px -12px ${(card.accent_color || card.accentColor)}20`
          }}
        >
          {/* Header with gradient */}
          <div 
            className="relative p-8 text-center"
            style={{
              background: `linear-gradient(135deg, ${(card.accent_color || card.accentColor)}15 0%, ${(card.accent_color || card.accentColor)}25 100%)`
            }}
          >
            {card.logo && (
              <img 
                src={card.logo} 
                alt="Logo" 
                className="absolute top-4 right-4 w-12 h-12 object-contain"
              />
            )}
            
            <Avatar className="w-32 h-32 mx-auto mb-6 ring-4 ring-white shadow-xl">
              <AvatarImage src={card.profile_image || card.profileImage} />
              <AvatarFallback 
                className="text-3xl font-bold text-white"
                style={{ backgroundColor: card.accent_color || card.accentColor }}
              >
                {card.name.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>

            <h1 className="text-3xl font-bold mb-2" style={{ color: card.text_color || card.textColor }}>
              {card.name}
            </h1>
            
            {card.position && (
              <p className="text-lg mb-2 opacity-80">{card.position}</p>
            )}
            
            {card.company && (
              <p className="text-base opacity-70 mb-4">{card.company}</p>
            )}

            {card.description && (
              <p className="text-sm opacity-75 mb-4 max-w-md mx-auto leading-relaxed">
                {card.description}
              </p>
            )}

            <div className="flex items-center justify-center space-x-3">
              {(card.is_public !== undefined || card.isPublic !== undefined) && (
                <Badge 
                  variant={(card.is_public ?? card.isPublic) ? "default" : "secondary"}
                >
                  {(card.is_public ?? card.isPublic) ? 'Öffentlich' : 'Privat'}
                </Badge>
              )}
              
              {(card.auto_update_enabled || card.autoUpdateEnabled) && (
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Auto-Update
                </Badge>
              )}
              
              {(card.last_updated || card.lastUpdated) && (
                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                  <Clock className="w-3 h-3 mr-1" />
                  Aktualisiert
                </Badge>
              )}
            </div>
          </div>

          <CardContent className="p-8">
            {/* Contact Information */}
            <div className="space-y-6 mb-8">
              {/* Phone Numbers */}
              {card.phones && card.phones.filter(p => p.number).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-4 flex items-center" style={{ color: card.text_color || card.textColor }}>
                    <Phone className="w-5 h-5 mr-2" />
                    Telefonnummern
                  </h3>
                  <div className="space-y-3">
                    {card.phones.filter(p => p.number).map((phone, index) => (
                      <div key={index} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100">
                        <div className="flex items-center space-x-3">
                          <div 
                            className="w-10 h-10 rounded-full flex items-center justify-center text-white"
                            style={{ backgroundColor: card.accent_color || card.accentColor }}
                          >
                            <Phone className="w-5 h-5" />
                          </div>
                          <div>
                            <p className="font-medium" style={{ color: card.text_color || card.textColor }}>
                              {phone.number}
                              {(phone.is_primary || phone.isPrimary) && (
                                <Badge className="ml-2 bg-yellow-100 text-yellow-800 text-xs">Primär</Badge>
                              )}
                            </p>
                            <p className="text-sm opacity-70">{phone.label}</p>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleCall(phone)}
                            className="h-8"
                          >
                            <Phone className="w-4 h-4 mr-1" />
                            Anrufen
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleMessage(phone)}
                            className="h-8"
                          >
                            <MessageCircle className="w-4 h-4 mr-1" />
                            {phone.label.toLowerCase().includes('whatsapp') ? 'WhatsApp' : 'SMS'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Email Addresses */}
              {card.emails && card.emails.filter(e => e.address).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-4 flex items-center" style={{ color: card.text_color || card.textColor }}>
                    <Mail className="w-5 h-5 mr-2" />
                    E-Mail-Adressen
                  </h3>
                  <div className="space-y-3">
                    {card.emails.filter(e => e.address).map((email, index) => (
                      <div key={index} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100">
                        <div className="flex items-center space-x-3">
                          <div 
                            className="w-10 h-10 rounded-full flex items-center justify-center text-white"
                            style={{ backgroundColor: card.accent_color || card.accentColor }}
                          >
                            <Mail className="w-5 h-5" />
                          </div>
                          <div>
                            <p className="font-medium" style={{ color: card.text_color || card.textColor }}>
                              {email.address}
                              {(email.is_primary || email.isPrimary) && (
                                <Badge className="ml-2 bg-yellow-100 text-yellow-800 text-xs">Primär</Badge>
                              )}
                            </p>
                            <p className="text-sm opacity-70">{email.label}</p>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEmailAction(email)}
                          className="h-8"
                        >
                          <Mail className="w-4 h-4 mr-1" />
                          E-Mail
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Website */}
              {card.website && (
                <div className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div 
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white"
                    style={{ backgroundColor: card.accent_color || card.accentColor }}
                  >
                    <Globe className="w-5 h-5" />
                  </div>
                  <a 
                    href={card.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-lg hover:underline flex-1"
                    style={{ color: card.text_color || card.textColor }}
                  >
                    {card.website.replace(/^https?:\/\//, '')}
                  </a>
                </div>
              )}
            </div>

            <Separator className="my-8" />

            {/* Social Media */}
            {(card.social_media || card.socialMedia) && Object.values(card.social_media || card.socialMedia).some(val => val) && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold mb-4" style={{ color: card.text_color || card.textColor }}>
                  Social Media
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {Object.entries(card.social_media || card.socialMedia).map(([platform, username]) => {
                    if (!username) return null;
                    return (
                      <a
                        key={platform}
                        href={getSocialUrl(platform, username)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100"
                      >
                        <div 
                          className="w-8 h-8 rounded-full flex items-center justify-center text-white"
                          style={{ backgroundColor: card.accent_color || card.accentColor }}
                        >
                          {getSocialIcon(platform)}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium capitalize" style={{ color: card.text_color || card.textColor }}>
                            {platform}
                          </p>
                          <p className="text-sm opacity-70">@{username}</p>
                        </div>
                      </a>
                    );
                  })}
                </div>
              </div>
            )}

            {/* QR Code */}
            {qrCode && (
              <div className="mb-8 text-center">
                <h3 className="text-xl font-semibold mb-4" style={{ color: card.textColor }}>
                  QR Code
                </h3>
                <div className="inline-block p-4 bg-white rounded-lg shadow-inner">
                  <img src={qrCode} alt="QR Code" className="mx-auto rounded-lg" />
                </div>
                <p className="text-sm mt-3 opacity-70">Scannen Sie den Code, um diese Visitenkarte zu teilen</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Button
                onClick={handleDownloadVCard}
                variant="outline"
                className="w-full"
              >
                <Download className="mr-2 h-4 w-4" />
                vCard
              </Button>
              
              <Button
                onClick={handleGenerateQR}
                variant="outline"
                className="w-full"
              >
                <QrCode className="mr-2 h-4 w-4" />
                QR Code
              </Button>
              
              {(card.allow_embedding || card.allowEmbedding) && (
                <Button
                  onClick={handleGetEmbedCode}
                  variant="outline"
                  className="w-full"
                >
                  <Code className="mr-2 h-4 w-4" />
                  Einbetten
                </Button>
              )}
              
              <Button
                onClick={handleShare}
                className="w-full text-white"
                style={{ backgroundColor: card.accent_color || card.accentColor }}
              >
                <Share2 className="mr-2 h-4 w-4" />
                Teilen
              </Button>
            </div>

            {/* Auto-Update Info */}
            {(card.auto_update_enabled || card.autoUpdateEnabled) && (card.last_updated || card.lastUpdated) && (
              <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-green-800">
                    <RefreshCw className="w-5 h-5 mr-2" />
                    <div>
                      <p className="font-medium">Automatische Updates aktiv</p>
                      <p className="text-sm text-green-600">
                        Letzte Aktualisierung: {new Date(card.last_updated || card.lastUpdated).toLocaleDateString('de-DE')}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300">
                    <Users className="w-3 h-3 mr-1" />
                    {card.share_count || 0} Empfänger
                  </Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ViewCardPage;