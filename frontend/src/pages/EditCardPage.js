import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Textarea } from '../components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ArrowLeft, Upload, Save, Eye, Instagram, Linkedin, Twitter, Send, Info, Globe, Palette } from 'lucide-react';
import MultiContactInput from '../components/MultiContactInput';
import AddressInput from '../components/AddressInput';
import { cardsApi } from '../services/api';
import { useToast } from '../hooks/use-toast';

const EditCardPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    position: '',
    description: '',
    phones: [{ id: '1', label: 'Geschäftlich', number: '', is_primary: true }],
    emails: [{ id: '1', label: 'Geschäftlich', address: '', is_primary: true }],
    addresses: [],
    website: '',
    profile_image: '',
    logo: '',
    social_media: {
      instagram: '',
      linkedin: '',
      twitter: '',
      tiktok: '',
      telegram: ''
    },
    is_public: true,
    background_color: '#ffffff',
    text_color: '#1f2937',
    accent_color: '#3b82f6',
    embed_background_color: '#f8fafc',
    allow_embedding: true,
    auto_update_enabled: true
  });

  useEffect(() => {
    loadCard();
  }, [id]);

  const loadCard = async () => {
    try {
      const card = await cardsApi.getById(id);
      if (card) {
        setFormData({
          name: card.name || '',
          company: card.company || '',
          position: card.position || '',
          description: card.description || '',
          phones: card.phones && card.phones.length > 0 ? card.phones : [{ id: '1', label: 'Geschäftlich', number: '', is_primary: true }],
          emails: card.emails && card.emails.length > 0 ? card.emails : [{ id: '1', label: 'Geschäftlich', address: '', is_primary: true }],
          addresses: card.addresses || [],
          website: card.website || '',
          profile_image: card.profile_image || '',
          logo: card.logo || '',
          social_media: card.social_media || {
            instagram: '',
            linkedin: '',
            twitter: '',
            tiktok: '',
            telegram: ''
          },
          is_public: card.is_public !== undefined ? card.is_public : true,
          background_color: card.background_color || '#ffffff',
          text_color: card.text_color || '#1f2937',
          accent_color: card.accent_color || '#3b82f6',
          embed_background_color: card.embed_background_color || '#f8fafc',
          allow_embedding: card.allow_embedding !== undefined ? card.allow_embedding : true,
          auto_update_enabled: card.auto_update_enabled !== undefined ? card.auto_update_enabled : true
        });
      } else {
        toast({
          title: "Fehler",
          description: "Visitenkarte nicht gefunden.",
          variant: "destructive",
        });
        navigate('/');
      }
    } catch (error) {
      console.error('Failed to load card for editing:', error);
      toast({
        title: "Fehler",
        description: "Visitenkarte konnte nicht geladen werden.",
        variant: "destructive",
      });
      navigate('/');
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSocialMediaChange = (platform, value) => {
    setFormData(prev => ({
      ...prev,
      social_media: {
        ...prev.social_media,
        [platform]: value
      }
    }));
  };

  const handleImageUpload = (field, event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        handleInputChange(field, e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.emails.some(email => email.address)) {
      toast({
        title: "Fehler",
        description: "Name und mindestens eine E-Mail sind Pflichtfelder.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      await cardsApi.update(id, formData);
      toast({
        title: "Erfolg",
        description: "Ihre Visitenkarte wurde erfolgreich aktualisiert.",
      });
      navigate(`/card/${id}`);
    } catch (error) {
      console.error('Card update failed:', error);
      toast({
        title: "Fehler",
        description: error.response?.data?.detail || "Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = () => {
    sessionStorage.setItem('previewCard', JSON.stringify(formData));
    navigate('/card/preview');
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <header className="flex items-center mb-8">
        <Button
          variant="ghost"
          onClick={() => navigate('/')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Zurück
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Visitenkarte bearbeiten</h1>
          <p className="text-gray-600">Aktualisieren Sie Ihre Informationen.</p>
        </div>
      </header>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Grundinformationen</CardTitle>
                <CardDescription>Ihre persönlichen und beruflichen Daten</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name">Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="Max Mustermann"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="company">Unternehmen</Label>
                    <Input
                      id="company"
                      value={formData.company}
                      onChange={(e) => handleInputChange('company', e.target.value)}
                      placeholder="Tech Solutions GmbH"
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="position">Position</Label>
                  <Input
                    id="position"
                    value={formData.position}
                    onChange={(e) => handleInputChange('position', e.target.value)}
                    placeholder="Senior Developer"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="phone">Telefon</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      placeholder="+49 123 456789"
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">E-Mail *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      placeholder="max@example.com"
                      required
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="website">Webseite</Label>
                  <Input
                    id="website"
                    type="url"
                    value={formData.website}
                    onChange={(e) => handleInputChange('website', e.target.value)}
                    placeholder="https://example.com"
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Social Media</CardTitle>
                <CardDescription>Ihre Social Media Profile</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="instagram" className="flex items-center">
                      <Instagram className="w-4 h-4 mr-2 text-pink-500" />
                      Instagram
                    </Label>
                    <Input
                      id="instagram"
                      value={formData.socialMedia?.instagram || ''}
                      onChange={(e) => handleSocialMediaChange('instagram', e.target.value)}
                      placeholder="username"
                    />
                  </div>
                  <div>
                    <Label htmlFor="linkedin" className="flex items-center">
                      <Linkedin className="w-4 h-4 mr-2 text-blue-600" />
                      LinkedIn
                    </Label>
                    <Input
                      id="linkedin"
                      value={formData.socialMedia?.linkedin || ''}
                      onChange={(e) => handleSocialMediaChange('linkedin', e.target.value)}
                      placeholder="username"
                    />
                  </div>
                  <div>
                    <Label htmlFor="twitter" className="flex items-center">
                      <Twitter className="w-4 h-4 mr-2 text-blue-400" />
                      Twitter
                    </Label>
                    <Input
                      id="twitter"
                      value={formData.socialMedia?.twitter || ''}
                      onChange={(e) => handleSocialMediaChange('twitter', e.target.value)}
                      placeholder="username"
                    />
                  </div>
                  <div>
                    <Label htmlFor="telegram" className="flex items-center">
                      <Send className="w-4 h-4 mr-2 text-blue-500" />
                      Telegram
                    </Label>
                    <Input
                      id="telegram"
                      value={formData.socialMedia?.telegram || ''}
                      onChange={(e) => handleSocialMediaChange('telegram', e.target.value)}
                      placeholder="username"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex space-x-4">
              <Button 
                type="button" 
                variant="outline" 
                onClick={handlePreview}
                className="flex-1"
              >
                <Eye className="mr-2 h-4 w-4" />
                Vorschau
              </Button>
              <Button 
                type="submit" 
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Speichere...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Aktualisieren
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>

        <div className="lg:col-span-1">
          <div className="sticky top-8">
            <Card>
              <CardHeader>
                <CardTitle>Live Vorschau</CardTitle>
              </CardHeader>
              <CardContent>
                <div 
                  className="rounded-lg p-4 min-h-[300px]"
                  style={{
                    backgroundColor: formData.backgroundColor,
                    color: formData.textColor,
                    border: `2px solid ${formData.accentColor}20`
                  }}
                >
                  <div className="text-center">
                    <Avatar className="w-20 h-20 mx-auto mb-4">
                      <AvatarImage src={formData.profileImage} />
                      <AvatarFallback style={{ backgroundColor: formData.accentColor, color: 'white' }}>
                        {formData.name ? formData.name.charAt(0).toUpperCase() : 'U'}
                      </AvatarFallback>
                    </Avatar>
                    <h3 className="text-xl font-bold mb-1">{formData.name || 'Ihr Name'}</h3>
                    {formData.position && <p className="text-sm mb-1">{formData.position}</p>}
                    {formData.company && <p className="text-sm mb-3">{formData.company}</p>}
                    {formData.email && <p className="text-xs mb-1">{formData.email}</p>}
                    {formData.phone && <p className="text-xs mb-1">{formData.phone}</p>}
                    {formData.website && <p className="text-xs">{formData.website}</p>}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditCardPage;