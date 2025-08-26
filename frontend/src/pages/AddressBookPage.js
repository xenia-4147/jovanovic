import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Separator } from '../components/ui/separator';
import { 
  ArrowLeft, 
  Search, 
  Phone, 
  Mail, 
  Globe, 
  MapPin, 
  Navigation,
  MessageCircle,
  ChevronDown,
  ChevronUp,
  User,
  Building2
} from 'lucide-react';
import { cardsApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';

const AddressBookPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();
  const [businessCards, setBusinessCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLetter, setSelectedLetter] = useState('');
  const [expandedCards, setExpandedCards] = useState(new Set());

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

  // Group cards by first letter
  const groupedCards = useMemo(() => {
    const filtered = businessCards.filter(card => {
      const searchLower = searchQuery.toLowerCase();
      const matchesSearch = card.name.toLowerCase().includes(searchLower) ||
                           (card.company && card.company.toLowerCase().includes(searchLower));
      
      if (selectedLetter) {
        const firstLetter = card.name.charAt(0).toUpperCase();
        return matchesSearch && firstLetter === selectedLetter;
      }
      
      return matchesSearch;
    });

    const grouped = {};
    filtered.forEach(card => {
      const firstLetter = card.name.charAt(0).toUpperCase();
      if (!grouped[firstLetter]) {
        grouped[firstLetter] = [];
      }
      grouped[firstLetter].push(card);
    });

    // Sort each group
    Object.keys(grouped).forEach(letter => {
      grouped[letter].sort((a, b) => a.name.localeCompare(b.name));
    });

    return grouped;
  }, [businessCards, searchQuery, selectedLetter]);

  // Get all available letters
  const availableLetters = useMemo(() => {
    const letters = businessCards.map(card => card.name.charAt(0).toUpperCase());
    return [...new Set(letters)].sort();
  }, [businessCards]);

  const toggleCardExpansion = (cardId) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(cardId)) {
      newExpanded.delete(cardId);
    } else {
      newExpanded.add(cardId);
    }
    setExpandedCards(newExpanded);
  };

  const handleCall = (phone) => {
    window.location.href = `tel:${phone.number}`;
  };

  const handleMessage = (phone) => {
    if (phone.label.toLowerCase().includes('whatsapp')) {
      window.open(`https://wa.me/${phone.number.replace(/[^\d]/g, '')}`, '_blank');
    } else {
      window.location.href = `sms:${phone.number}`;
    }
  };

  const handleEmail = (email) => {
    window.location.href = `mailto:${email.address}`;
  };

  const handleNavigate = (address) => {
    const fullAddress = [
      address.street && address.houseNumber ? `${address.street} ${address.houseNumber}` : address.street,
      address.postalCode && address.city ? `${address.postalCode} ${address.city}` : address.city,
      address.state,
      address.country
    ].filter(Boolean).join(', ');
    
    if (fullAddress) {
      const encodedAddress = encodeURIComponent(fullAddress);
      window.open(`https://www.google.com/maps/search/?api=1&query=${encodedAddress}`, '_blank');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Lade Adressbuch...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <header className="flex items-center justify-between mb-8">
        <div className="flex items-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Zurück
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Adressbuch</h1>
            <p className="text-gray-600">{businessCards.length} Kontakte</p>
          </div>
        </div>
      </header>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Suchen Sie nach Namen oder Unternehmen..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Alphabet Navigation */}
      <div className="mb-6 flex flex-wrap gap-2 justify-center">
        <Button
          size="sm"
          variant={selectedLetter === '' ? "default" : "outline"}
          onClick={() => setSelectedLetter('')}
          className="h-8 w-12"
        >
          Alle
        </Button>
        {availableLetters.map(letter => (
          <Button
            key={letter}
            size="sm"
            variant={selectedLetter === letter ? "default" : "outline"}
            onClick={() => setSelectedLetter(letter)}
            className="h-8 w-8 p-0"
          >
            {letter}
          </Button>
        ))}
      </div>

      {/* Cards List */}
      <div className="space-y-4">
        {Object.keys(groupedCards).sort().map(letter => (
          <div key={letter}>
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                {letter}
              </div>
              <Separator className="flex-1" />
            </div>
            
            <div className="space-y-3">
              {groupedCards[letter].map(card => (
                <Card key={card.id} className="overflow-hidden">
                  <CardContent className="p-0">
                    {/* Collapsed View */}
                    <div 
                      className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                      onClick={() => toggleCardExpansion(card.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <Avatar className="w-12 h-12">
                            <AvatarImage 
                              src={card.profile_image || `https://ui-avatars.com/api/?name=${encodeURIComponent(card.name)}&background=6366f1&color=fff`} 
                            />
                            <AvatarFallback>
                              {card.name.charAt(0).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <h3 className="font-semibold text-gray-900">{card.name}</h3>
                              {card.logo && (
                                <img src={card.logo} alt="Logo" className="w-6 h-6 object-contain" />
                              )}
                            </div>
                            {card.company && (
                              <p className="text-sm text-gray-600 flex items-center">
                                <Building2 className="w-3 h-3 mr-1" />
                                {card.company}
                              </p>
                            )}
                            {card.position && (
                              <p className="text-xs text-gray-500">{card.position}</p>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {/* Quick Actions */}
                          {card.phones && card.phones.length > 0 && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCall(card.phones.find(p => p.is_primary) || card.phones[0]);
                              }}
                              className="h-8 w-8 p-0"
                            >
                              <Phone className="w-4 h-4" />
                            </Button>
                          )}
                          
                          {card.emails && card.emails.length > 0 && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEmail(card.emails.find(e => e.is_primary) || card.emails[0]);
                              }}
                              className="h-8 w-8 p-0"
                            >
                              <Mail className="w-4 h-4" />
                            </Button>
                          )}
                          
                          {expandedCards.has(card.id) ? (
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Expanded View */}
                    {expandedCards.has(card.id) && (
                      <div className="border-t bg-gray-50 p-4 space-y-4">
                        {/* Description */}
                        {card.description && (
                          <p className="text-sm text-gray-600 italic">"{card.description}"</p>
                        )}

                        {/* Contact Information */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Phone Numbers */}
                          {card.phones && card.phones.length > 0 && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">Telefonnummern</h4>
                              <div className="space-y-2">
                                {card.phones.map((phone, idx) => (
                                  <div key={idx} className="flex items-center justify-between">
                                    <div>
                                      <p className="text-sm font-medium">{phone.number}</p>
                                      <p className="text-xs text-gray-500">{phone.label}</p>
                                    </div>
                                    <div className="flex space-x-1">
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleCall(phone)}
                                        className="h-7 px-2 text-xs"
                                      >
                                        <Phone className="w-3 h-3 mr-1" />
                                        Anrufen
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleMessage(phone)}
                                        className="h-7 px-2 text-xs"
                                      >
                                        <MessageCircle className="w-3 h-3 mr-1" />
                                        {phone.label.toLowerCase().includes('whatsapp') ? 'WhatsApp' : 'SMS'}
                                      </Button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Email Addresses */}
                          {card.emails && card.emails.length > 0 && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">E-Mail-Adressen</h4>
                              <div className="space-y-2">
                                {card.emails.map((email, idx) => (
                                  <div key={idx} className="flex items-center justify-between">
                                    <div>
                                      <p className="text-sm font-medium">{email.address}</p>
                                      <p className="text-xs text-gray-500">{email.label}</p>
                                    </div>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleEmail(email)}
                                      className="h-7 px-2 text-xs"
                                    >
                                      <Mail className="w-3 h-3 mr-1" />
                                      E-Mail
                                    </Button>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Addresses */}
                        {card.addresses && card.addresses.length > 0 && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Adressen</h4>
                            <div className="space-y-2">
                              {card.addresses.map((address, idx) => {
                                const fullAddress = [
                                  address.street && address.houseNumber ? `${address.street} ${address.houseNumber}` : address.street,
                                  address.postalCode && address.city ? `${address.postalCode} ${address.city}` : address.city,
                                  address.state,
                                  address.country
                                ].filter(Boolean).join(', ');
                                
                                return (
                                  <div key={idx} className="flex items-start justify-between p-2 bg-white rounded border">
                                    <div className="flex-1">
                                      <div className="flex items-center space-x-2">
                                        <MapPin className="w-4 h-4 text-gray-500" />
                                        <span className="text-sm font-medium">{address.label}</span>
                                        {address.isPrimary && (
                                          <Badge variant="secondary" className="text-xs">Primär</Badge>
                                        )}
                                      </div>
                                      <p className="text-sm text-gray-600 ml-6">{fullAddress}</p>
                                    </div>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleNavigate(address)}
                                      className="h-7 px-2 text-xs ml-2"
                                    >
                                      <Navigation className="w-3 h-3 mr-1" />
                                      Navigieren
                                    </Button>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Website */}
                        {card.website && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Website</h4>
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <Globe className="w-4 h-4 text-gray-500" />
                                <span className="text-sm">{card.website.replace(/^https?:\/\//, '')}</span>
                              </div>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => window.open(card.website, '_blank')}
                                className="h-7 px-2 text-xs"
                              >
                                <Globe className="w-3 h-3 mr-1" />
                                Öffnen
                              </Button>
                            </div>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex space-x-2 pt-2 border-t">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => navigate(`/card/${card.id}`)}
                            className="flex-1"
                          >
                            Vollständig anzeigen
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => navigate(`/edit/${card.id}`)}
                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                          >
                            Bearbeiten
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ))}
        
        {Object.keys(groupedCards).length === 0 && (
          <div className="text-center py-12">
            <User className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Keine Kontakte gefunden</h3>
            <p className="text-gray-600 mb-4">
              {searchQuery || selectedLetter 
                ? 'Versuchen Sie eine andere Suche oder wählen Sie einen anderen Buchstaben.'
                : 'Erstellen Sie Ihre erste Visitenkarte, um das Adressbuch zu füllen.'
              }
            </p>
            {!searchQuery && !selectedLetter && (
              <Button onClick={() => navigate('/create')}>
                Erste Visitenkarte erstellen
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AddressBookPage;