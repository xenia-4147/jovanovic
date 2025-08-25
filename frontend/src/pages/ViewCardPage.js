import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Separator } from '../components/ui/separator';
import { ArrowLeft, Download, QrCode, Share2, Phone, Mail, Globe, MapPin, Instagram, Linkedin, Twitter, Send, MessageCircle, Copy, Code, RefreshCw, Clock, Users } from 'lucide-react';
import { mockApi, mockBusinessCards } from '../mock';
import { useToast } from '../hooks/use-toast';

const ViewCardPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
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
      const cardData = await mockApi.getBusinessCard(id);
      setCard(cardData);
    } catch (error) {
      toast({
        title: "Fehler",
        description: "Visitenkarte konnte nicht geladen werden.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadVCard = async () => {
    try {
      const vcard = await mockApi.generateVCard(card);
      const blob = new Blob([vcard], { type: 'text/vcard' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${card.name.replace(/\s+/g, '_')}.vcf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
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
      const qrUrl = await mockApi.generateQRCode(card.id || 'preview');
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
            backgroundColor: card.backgroundColor,
            color: card.textColor,
            boxShadow: `0 25px 50px -12px ${card.accentColor}20`
          }}
        >
          {/* Header with gradient */}
          <div 
            className="relative p-8 text-center"
            style={{
              background: `linear-gradient(135deg, ${card.accentColor}15 0%, ${card.accentColor}25 100%)`
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
              <AvatarImage src={card.profileImage} />
              <AvatarFallback 
                className="text-3xl font-bold text-white"
                style={{ backgroundColor: card.accentColor }}
              >
                {card.name.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>

            <h1 className="text-3xl font-bold mb-2" style={{ color: card.textColor }}>
              {card.name}
            </h1>
            
            {card.position && (
              <p className="text-lg mb-2 opacity-80">{card.position}</p>
            )}
            
            {card.company && (
              <p className="text-base opacity-70 mb-4">{card.company}</p>
            )}

            {card.isPublic !== undefined && (
              <Badge 
                variant={card.isPublic ? "default" : "secondary"}
                className="mb-4"
              >
                {card.isPublic ? 'Öffentlich' : 'Privat'}
              </Badge>
            )}
          </div>

          <CardContent className="p-8">
            {/* Contact Information */}
            <div className="space-y-4 mb-8">
              {card.phone && (
                <div className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div 
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white"
                    style={{ backgroundColor: card.accentColor }}
                  >
                    <Phone className="w-5 h-5" />
                  </div>
                  <a 
                    href={`tel:${card.phone}`}
                    className="text-lg hover:underline"
                    style={{ color: card.textColor }}
                  >
                    {card.phone}
                  </a>
                </div>
              )}

              {card.email && (
                <div className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div 
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white"
                    style={{ backgroundColor: card.accentColor }}
                  >
                    <Mail className="w-5 h-5" />
                  </div>
                  <a 
                    href={`mailto:${card.email}`}
                    className="text-lg hover:underline"
                    style={{ color: card.textColor }}
                  >
                    {card.email}
                  </a>
                </div>
              )}

              {card.website && (
                <div className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div 
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white"
                    style={{ backgroundColor: card.accentColor }}
                  >
                    <Globe className="w-5 h-5" />
                  </div>
                  <a 
                    href={card.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-lg hover:underline"
                    style={{ color: card.textColor }}
                  >
                    {card.website.replace(/^https?:\/\//, '')}
                  </a>
                </div>
              )}
            </div>

            {/* Social Media */}
            {card.socialMedia && Object.values(card.socialMedia).some(val => val) && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold mb-4" style={{ color: card.textColor }}>
                  Social Media
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(card.socialMedia).map(([platform, username]) => {
                    if (!username) return null;
                    return (
                      <a
                        key={platform}
                        href={getSocialUrl(platform, username)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-2 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <div 
                          className="w-8 h-8 rounded-full flex items-center justify-center text-white"
                          style={{ backgroundColor: card.accentColor }}
                        >
                          {getSocialIcon(platform)}
                        </div>
                        <span className="capitalize font-medium" style={{ color: card.textColor }}>
                          {platform}
                        </span>
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
                <img src={qrCode} alt="QR Code" className="mx-auto rounded-lg shadow-lg" />
                <p className="text-sm mt-2 opacity-70">Scannen Sie den Code, um diese Visitenkarte zu teilen</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Button
                onClick={handleDownloadVCard}
                variant="outline"
                className="w-full"
              >
                <Download className="mr-2 h-4 w-4" />
                Kontakt speichern
              </Button>
              
              <Button
                onClick={handleGenerateQR}
                variant="outline"
                className="w-full"
              >
                <QrCode className="mr-2 h-4 w-4" />
                QR Code
              </Button>
              
              <Button
                onClick={handleShare}
                className="w-full text-white"
                style={{ backgroundColor: card.accentColor }}
              >
                <Share2 className="mr-2 h-4 w-4" />
                Teilen
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ViewCardPage;