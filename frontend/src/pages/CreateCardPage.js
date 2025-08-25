import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Textarea } from '../components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ArrowLeft, Upload, Save, Eye, Instagram, Linkedin, Twitter, Send, Info, Globe, Palette } from 'lucide-react';
import MultiContactInput from '../components/MultiContactInput';
import { cardsApi } from '../services/api';
import { useToast } from '../hooks/use-toast';

const CreateCardPage = () => {
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
      const newCard = await cardsApi.create(formData);
      toast({
        title: "Erfolg",
        description: "Ihre Visitenkarte wurde erfolgreich erstellt.",
      });
      navigate(`/card/${newCard.id}`);
    } catch (error) {
      console.error('Card creation failed:', error);
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
    <div className="container mx-auto px-4 py-8 max-w-6xl">
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
          <h1 className="text-3xl font-bold text-gray-900">Neue Visitenkarte erstellen</h1>
          <p className="text-gray-600">Füllen Sie die Informationen aus, um Ihre digitale Visitenkarte zu erstellen.</p>
        </div>
      </header>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Form */}
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Info className="w-5 h-5 mr-2 text-blue-600" />
                  Grundinformationen
                </CardTitle>
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
                <div>
                  <Label htmlFor="description">Kurze Beschreibung / Tätigkeitsfeld</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Beschreiben Sie kurz Ihr Tätigkeitsfeld, Ihre Expertise oder was Sie Ihren Kontakten mitteilen möchten..."
                    rows={3}
                    className="resize-none"
                  />
                  <p className="text-xs text-gray-500 mt-1">Diese Beschreibung wird auf Ihrer Visitenkarte angezeigt und hilft anderen, Ihre Expertise zu verstehen.</p>
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

            {/* Contact Information */}
            <Card>
              <CardHeader>
                <CardTitle>Kontaktinformationen</CardTitle>
                <CardDescription>Telefonnummern und E-Mail-Adressen (mehrere möglich)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <MultiContactInput
                  type="phone"
                  title="Telefonnummern"
                  placeholder="+49 123 456789"
                  items={formData.phones}
                  onChange={(phones) => handleInputChange('phones', phones)}
                />
                
                <MultiContactInput
                  type="email"
                  title="E-Mail-Adressen"
                  placeholder="name@example.com"
                  items={formData.emails}
                  onChange={(emails) => handleInputChange('emails', emails)}
                />
              </CardContent>
            </Card>

            {/* Images */}
            <Card>
              <CardHeader>
                <CardTitle>Bilder</CardTitle>
                <CardDescription>Profilbild und Firmenlogo</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Profilbild</Label>
                    <div className="flex items-center space-x-4 mt-2">
                      <Avatar className="w-16 h-16">
                        <AvatarImage src={formData.profileImage} />
                        <AvatarFallback>
                          {formData.name ? formData.name.charAt(0).toUpperCase() : 'U'}
                        </AvatarFallback>
                      </Avatar>
                      <Button type="button" variant="outline" size="sm" asChild>
                        <label htmlFor="profileImage" className="cursor-pointer">
                          <Upload className="w-4 h-4 mr-2" />
                          Hochladen
                        </label>
                      </Button>
                      <input
                        id="profileImage"
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleImageUpload('profileImage', e)}
                      />
                    </div>
                  </div>
                  <div>
                    <Label>Firmenlogo</Label>
                    <div className="flex items-center space-x-4 mt-2">
                      {formData.logo && (
                        <img src={formData.logo} alt="Logo" className="w-16 h-16 object-contain border rounded" />
                      )}
                      <Button type="button" variant="outline" size="sm" asChild>
                        <label htmlFor="logo" className="cursor-pointer">
                          <Upload className="w-4 h-4 mr-2" />
                          Hochladen
                        </label>
                      </Button>
                      <input
                        id="logo"
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleImageUpload('logo', e)}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Social Media */}
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
                      value={formData.social_media.instagram}
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
                      value={formData.social_media.linkedin}
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
                      value={formData.social_media.twitter}
                      onChange={(e) => handleSocialMediaChange('twitter', e.target.value)}
                      placeholder="username"
                    />
                  </div>
                  <div>
                    <Label htmlFor="tiktok" className="flex items-center">
                      <div className="w-4 h-4 mr-2 bg-black rounded-sm"></div>
                      TikTok
                    </Label>
                    <Input
                      id="tiktok"
                      value={formData.social_media.tiktok}
                      onChange={(e) => handleSocialMediaChange('tiktok', e.target.value)}
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
                      value={formData.social_media.telegram}
                      onChange={(e) => handleSocialMediaChange('telegram', e.target.value)}
                      placeholder="username"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Settings and Customization */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Palette className="w-5 h-5 mr-2 text-purple-600" />
                  Design & Einstellungen
                </CardTitle>
                <CardDescription>Datenschutz, Darstellung und automatische Updates</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="isPublic">Öffentlich sichtbar</Label>
                        <p className="text-sm text-gray-500">Jeder mit dem Link kann Ihre Visitenkarte sehen</p>
                      </div>
                      <Switch
                        id="isPublic"
                        checked={formData.is_public}
                        onCheckedChange={(checked) => handleInputChange('is_public', checked)}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="allowEmbedding" className="flex items-center">
                          <Globe className="w-4 h-4 mr-2" />
                          Einbettung erlauben
                        </Label>
                        <p className="text-sm text-gray-500">Andere können Ihre Karte in Webseiten einbetten</p>
                      </div>
                      <Switch
                        id="allowEmbedding"
                        checked={formData.allow_embedding}
                        onCheckedChange={(checked) => handleInputChange('allow_embedding', checked)}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="autoUpdate">Auto-Update</Label>
                        <p className="text-sm text-gray-500">Änderungen werden automatisch an alle Empfänger gesendet</p>
                      </div>
                      <Switch
                        id="autoUpdate"
                        checked={formData.auto_update_enabled}
                        onCheckedChange={(checked) => handleInputChange('auto_update_enabled', checked)}
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="accentColor">Akzentfarbe</Label>
                        <Input
                          id="accentColor"
                          type="color"
                          value={formData.accent_color}
                          onChange={(e) => handleInputChange('accent_color', e.target.value)}
                        />
                      </div>
                      <div>
                        <Label htmlFor="textColor">Textfarbe</Label>
                        <Input
                          id="textColor"
                          type="color"
                          value={formData.text_color}
                          onChange={(e) => handleInputChange('text_color', e.target.value)}
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="backgroundColor">Karten-Hintergrund</Label>
                        <Input
                          id="backgroundColor"
                          type="color"
                          value={formData.background_color}
                          onChange={(e) => handleInputChange('background_color', e.target.value)}
                        />
                      </div>
                      <div>
                        <Label htmlFor="embedBackgroundColor">Einbettungs-Hintergrund</Label>
                        <Input
                          id="embedBackgroundColor"
                          type="color"
                          value={formData.embed_background_color}
                          onChange={(e) => handleInputChange('embed_background_color', e.target.value)}
                        />
                        <p className="text-xs text-gray-500 mt-1">Für Webseiten-Integration</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Submit Buttons */}
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
                    Erstelle...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Speichern
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>

        {/* Live Preview */}
        <div className="lg:col-span-1">
          <div className="sticky top-8">
            <Card>
              <CardHeader>
                <CardTitle>Live Vorschau</CardTitle>
              </CardHeader>
              <CardContent>
                <div 
                  className="rounded-lg p-4 min-h-[400px]"
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
                    
                    {formData.description && (
                      <p className="text-xs mb-3 opacity-80 leading-relaxed">
                        {formData.description.substring(0, 100)}
                        {formData.description.length > 100 ? '...' : ''}
                      </p>
                    )}
                    
                    <div className="space-y-2 text-xs">
                      {formData.emails.filter(e => e.address).slice(0, 2).map((email, idx) => (
                        <p key={idx}>{email.address}</p>
                      ))}
                      {formData.phones.filter(p => p.number).slice(0, 2).map((phone, idx) => (
                        <p key={idx}>{phone.number}</p>
                      ))}
                      {formData.website && <p>{formData.website}</p>}
                    </div>
                  </div>
                </div>
                
                {/* Auto-Update Preview */}
                {formData.autoUpdateEnabled && (
                  <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center text-green-800 text-sm">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                      Auto-Update aktiv
                    </div>
                    <p className="text-xs text-green-600 mt-1">Änderungen werden automatisch synchronisiert</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateCardPage;