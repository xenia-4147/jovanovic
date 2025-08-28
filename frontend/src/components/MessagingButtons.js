import React from 'react';
import { Button } from './ui/button';
import { Phone, MessageSquare, MessageCircle, Send, Zap, Video, Hash } from 'lucide-react';

const MessagingButtons = ({ phone, size = "sm", className = "" }) => {
  const messagingApps = phone.messaging_apps || [
    { name: "whatsapp", enabled: true },
    { name: "sms", enabled: true }
  ];

  const getMessagingIcon = (appName) => {
    switch (appName.toLowerCase()) {
      case 'whatsapp':
        return <MessageCircle className="w-4 h-4" />;
      case 'sms':
        return <MessageSquare className="w-4 h-4" />;
      case 'telegram':
        return <Send className="w-4 h-4" />;
      case 'viber':
        return <Video className="w-4 h-4" />;
      case 'signal':
        return <Zap className="w-4 h-4" />;
      case 'discord':
        return <Hash className="w-4 h-4" />;
      default:
        return <MessageSquare className="w-4 h-4" />;
    }
  };

  const getMessagingColor = (appName) => {
    switch (appName.toLowerCase()) {
      case 'whatsapp':
        return 'bg-green-600 hover:bg-green-700 text-white';
      case 'sms':
        return 'bg-blue-600 hover:bg-blue-700 text-white';
      case 'telegram':
        return 'bg-sky-500 hover:bg-sky-600 text-white';
      case 'viber':
        return 'bg-purple-600 hover:bg-purple-700 text-white';
      case 'signal':
        return 'bg-blue-800 hover:bg-blue-900 text-white';
      case 'discord':
        return 'bg-indigo-600 hover:bg-indigo-700 text-white';
      default:
        return 'bg-gray-600 hover:bg-gray-700 text-white';
    }
  };

  const getMessagingUrl = (appName, phoneNumber) => {
    const cleanNumber = phoneNumber.replace(/[^+\d]/g, '');
    
    switch (appName.toLowerCase()) {
      case 'whatsapp':
        return `https://wa.me/${cleanNumber}`;
      case 'sms':
        return `sms:${cleanNumber}`;
      case 'telegram':
        return `https://t.me/+${cleanNumber}`;
      case 'viber':
        return `viber://chat?number=${cleanNumber}`;
      case 'signal':
        return `https://signal.me/#p/${cleanNumber}`;
      case 'discord':
        return `discord://users/${cleanNumber}`;
      default:
        return `sms:${cleanNumber}`;
    }
  };

  const handleMessagingClick = (appName, phoneNumber) => {
    const url = getMessagingUrl(appName, phoneNumber);
    
    if (appName.toLowerCase() === 'sms') {
      window.location.href = url;
    } else {
      window.open(url, '_blank');
    }
  };

  const enabledApps = messagingApps.filter(app => app.enabled);

  return (
    <div className={`flex space-x-2 ${className}`}>
      {/* Call Button */}
      <Button
        size={size}
        onClick={() => window.location.href = `tel:${phone.number}`}
        className="bg-green-500 hover:bg-green-600 text-white flex-shrink-0"
        title="Anrufen"
      >
        <Phone className="w-4 h-4" />
      </Button>

      {/* Messaging App Buttons */}
      {enabledApps.map((app, index) => (
        <Button
          key={`${app.name}-${index}`}
          size={size}
          onClick={() => handleMessagingClick(app.name, phone.number)}
          className={`${getMessagingColor(app.name)} flex-shrink-0`}
          title={`${app.name.charAt(0).toUpperCase() + app.name.slice(1)} senden`}
        >
          {getMessagingIcon(app.name)}
        </Button>
      ))}
    </div>
  );
};

export default MessagingButtons;