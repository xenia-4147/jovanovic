import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { 
  Phone, 
  Mail, 
  Globe, 
  MapPin, 
  Navigation,
  MessageCircle,
  Download,
  Share2,
  QrCode,
  Instagram,
  Linkedin,
  Twitter,
  Send,
  Building2,
  User,
  ChevronDown,
  ChevronUp,
  Info
} from 'lucide-react';

const CompactBusinessCard = ({ card, onCall, onMessage, onEmail, onNavigate, onDownloadVCard, onShare, onGenerateQR }) => {
  const [isExpanded, setIsExpanded] = useState(false);

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

  const primaryPhone = card.phones?.find(p => p.is_primary) || card.phones?.[0];
  const primaryEmail = card.emails?.find(e => e.is_primary) || card.emails?.[0];
  const primaryAddress = card.addresses?.find(a => a.is_primary) || card.addresses?.[0];

  return (
    <div className="max-w-md mx-auto">
      {/* Main Contact Card - Smartphone Style */}
      <Card className="mb-4 shadow-lg border-0 bg-white">
        <CardContent className="p-0">
          {/* Compact Header - Always Visible */}
          <div 
            className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {/* Header Row - Like Phone Contact List */}
            <div className="flex items-center space-x-4">
              {/* Profile Picture */}
              <Avatar className="w-16 h-16 ring-2 ring-gray-200">
                <AvatarImage 
                  src={card.profile_image || `https://ui-avatars.com/api/?name=${encodeURIComponent(card.name)}&background=6366f1&color=fff`} 
                />
                <AvatarFallback className="bg-blue-600 text-white text-lg font-bold">
                  {card.name.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              
              {/* Name and Company Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <h2 className="text-xl font-bold text-gray-900 truncate">{card.name}</h2>
                  {card.logo && (
                    <img 
                      src={card.logo} 
                      alt="Logo" 
                      className="w-8 h-8 object-contain flex-shrink-0"
                    />
                  )}
                </div>
                
                {card.company && (
                  <div className="flex items-center text-gray-600 mb-1">
                    <Building2 className="w-4 h-4 mr-1 flex-shrink-0" />
                    <span className="text-sm truncate">{card.company}</span>
                  </div>
                )}
                
                {card.position && (
                  <p className="text-sm text-gray-500 truncate">{card.position}</p>
                )}

                {/* Quick Contact Info - Always Visible */}
                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                  {primaryPhone && (
                    <span className="flex items-center">
                      <Phone className="w-3 h-3 mr-1" />
                      {primaryPhone.number}
                    </span>
                  )}
                  {primaryEmail && (
                    <span className="flex items-center truncate">
                      <Mail className="w-3 h-3 mr-1" />
                      {primaryEmail.address}
                    </span>
                  )}
                </div>
              </div>
              
              {/* Expand/Collapse Button */}
              <div className="flex items-center space-x-2">
                {/* Quick Actions Visible in Collapsed State */}
                {!isExpanded && (
                  <>
                    {primaryPhone && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onCall(primaryPhone);
                        }}
                        className="h-8 w-8 p-0"
                      >
                        <Phone className="w-4 h-4" />
                      </Button>
                    )}
                    
                    {primaryPhone && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onMessage(primaryPhone);
                        }}
                        className="h-8 w-8 p-0"
                      >
                        <MessageCircle className="w-4 h-4" />
                      </Button>
                    )}
                  </>
                )}
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="h-8 w-8 p-0 text-gray-400"
                >
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5" />
                  ) : (
                    <ChevronDown className="w-5 h-5" />
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Expanded Details - Collapsible */}
          {isExpanded && (
            <div className="border-t bg-gray-50">
              <div className="p-4">
                {/* Description */}
                {card.description && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                    <div className="flex items-start space-x-2">
                      <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-blue-900 leading-relaxed">{card.description}</p>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="grid grid-cols-4 gap-2 mb-6">
                  {primaryPhone && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onCall(primaryPhone)}
                      className="flex flex-col items-center h-16 p-2"
                    >
                      <Phone className="w-5 h-5 mb-1" />
                      <span className="text-xs">Anrufen</span>
                    </Button>
                  )}
                  
                  {primaryPhone && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onMessage(primaryPhone)}
                      className="flex flex-col items-center h-16 p-2"
                    >
                      <MessageCircle className="w-5 h-5 mb-1" />
                      <span className="text-xs">
                        {primaryPhone.label?.toLowerCase().includes('whatsapp') ? 'WhatsApp' : 'SMS'}
                      </span>
                    </Button>
                  )}
                  
                  {primaryEmail && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onEmail(primaryEmail)}
                      className="flex flex-col items-center h-16 p-2"
                    >
                      <Mail className="w-5 h-5 mb-1" />
                      <span className="text-xs">E-Mail</span>
                    </Button>
                  )}
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onShare}
                    className="flex flex-col items-center h-16 p-2"
                  >
                    <Share2 className="w-5 h-5 mb-1" />
                    <span className="text-xs">Teilen</span>
                  </Button>
                </div>

                {/* Detailed Contact Information */}
                <div className="space-y-4">
                  {/* Phone Numbers */}
                  {card.phones && card.phones.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                        <Phone className="w-4 h-4 mr-2" />
                        Telefonnummern
                      </h4>
                      <div className="space-y-2">
                        {card.phones.map((phone, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                            <div className="flex items-center space-x-3">
                              <Phone className="w-4 h-4 text-gray-500" />
                              <div>
                                <p className="text-sm font-medium">{phone.number}</p>
                                <p className="text-xs text-gray-500">{phone.label}</p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-1">
                              {phone.is_primary && (
                                <Badge variant="secondary" className="text-xs">Primär</Badge>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => onCall(phone)}
                                className="h-8 w-8 p-0"
                              >
                                <Phone className="w-3 h-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => onMessage(phone)}
                                className="h-8 w-8 p-0"
                              >
                                <MessageCircle className="w-3 h-3" />
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
                      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                        <Mail className="w-4 h-4 mr-2" />
                        E-Mail-Adressen
                      </h4>
                      <div className="space-y-2">
                        {card.emails.map((email, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                            <div className="flex items-center space-x-3">
                              <Mail className="w-4 h-4 text-gray-500" />
                              <div>
                                <p className="text-sm font-medium">{email.address}</p>
                                <p className="text-xs text-gray-500">{email.label}</p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-1">
                              {email.is_primary && (
                                <Badge variant="secondary" className="text-xs">Primär</Badge>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => onEmail(email)}
                                className="h-8 w-8 p-0"
                              >
                                <Mail className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Addresses */}
                  {card.addresses && card.addresses.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                        <MapPin className="w-4 h-4 mr-2" />
                        Adressen
                      </h4>
                      <div className="space-y-2">
                        {card.addresses.map((address, idx) => {
                          const fullAddress = [
                            address.street && address.house_number ? `${address.street} ${address.house_number}` : address.street,
                            address.postal_code && address.city ? `${address.postal_code} ${address.city}` : address.city,
                            address.state,
                            address.country
                          ].filter(Boolean).join(', ');
                          
                          return (
                            <div key={idx} className="p-3 bg-white rounded-lg border">
                              <div className="flex items-start justify-between">
                                <div className="flex items-start space-x-3 flex-1">
                                  <MapPin className="w-4 h-4 text-gray-500 mt-0.5" />
                                  <div className="flex-1">
                                    <div className="flex items-center space-x-2 mb-1">
                                      <p className="text-sm font-medium">{address.label}</p>
                                      {address.is_primary && (
                                        <Badge variant="secondary" className="text-xs">Primär</Badge>
                                      )}
                                    </div>
                                    <p className="text-xs text-gray-600 leading-relaxed">{fullAddress}</p>
                                  </div>
                                </div>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => onNavigate(address)}
                                  className="h-8 w-8 p-0 ml-2"
                                >
                                  <Navigation className="w-3 h-3" />
                                </Button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Website */}
                  {card.website && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                        <Globe className="w-4 h-4 mr-2" />
                        Website
                      </h4>
                      <div className="p-3 bg-white rounded-lg border">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <Globe className="w-4 h-4 text-gray-500" />
                            <a 
                              href={card.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:underline"
                            >
                              {card.website.replace(/^https?:\/\//, '')}
                            </a>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Social Media */}
                  {card.social_media && Object.values(card.social_media || {}).some(val => val) && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-3">Social Media</h4>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(card.social_media || {}).map(([platform, username]) => {
                          if (!username) return null;
                          return (
                            <a
                              key={platform}
                              href={getSocialUrl(platform, username)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center space-x-3 p-3 bg-white rounded-lg border hover:bg-gray-50 transition-colors"
                            >
                              <div className="text-gray-600">
                                {getSocialIcon(platform)}
                              </div>
                              <div>
                                <p className="text-sm font-medium capitalize">{platform}</p>
                                <p className="text-xs text-gray-500">@{username}</p>
                              </div>
                            </a>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                {/* Bottom Action Buttons */}
                <div className="grid grid-cols-2 gap-3 mt-6 pt-4 border-t">
                  <Button
                    variant="outline"
                    onClick={onDownloadVCard}
                    className="w-full"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Kontakt speichern
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={onGenerateQR}
                    className="w-full"
                  >
                    <QrCode className="w-4 h-4 mr-2" />
                    QR-Code
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CompactBusinessCard;