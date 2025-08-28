import React, { useState, useEffect } from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { 
  Trophy, 
  Star, 
  Crown, 
  Sparkles, 
  Users, 
  Timer,
  Gift,
  Zap,
  Heart,
  CheckCircle,
  Share2
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

const EarlyAdopterBadge = ({ className = "" }) => {
  const { user } = useAuth();
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [totalUsers, setTotalUsers] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (user) {
      loadSubscriptionStatus();
    }
  }, [user]);

  const loadSubscriptionStatus = async () => {
    try {
      const response = await api.get('/subscription/status');
      setSubscriptionStatus(response.data);
      
      // Extract user number from plan name if it's an early adopter
      const planName = response.data.plan_name;
      if (planName.includes('Early Adopter #')) {
        const match = planName.match(/#(\d+)/);
        if (match) {
          setTotalUsers(parseInt(match[1]));
        }
      }
    } catch (error) {
      console.error('Failed to load subscription status:', error);
    }
  };

  const isEarlyAdopter = subscriptionStatus?.plan_name?.includes('Early Adopter');
  const remainingSpots = totalUsers ? Math.max(0, 100000 - totalUsers) : null;
  const percentageFilled = totalUsers ? (totalUsers / 100000) * 100 : 0;

  if (!subscriptionStatus || !isEarlyAdopter) {
    return null;
  }

  const handleShare = () => {
    const shareText = `🎉 Ich bin Early Adopter #${totalUsers} bei der neuen Business Card App! Die ersten 100.000 bekommen ALLES kostenlos! Noch ${remainingSpots} Plätze frei! 🚀`;
    
    if (navigator.share) {
      navigator.share({
        title: 'Early Adopter Bonus',
        text: shareText,
        url: window.location.origin
      });
    } else {
      navigator.clipboard.writeText(shareText);
    }
  };

  return (
    <div className={className}>
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogTrigger asChild>
          <Badge 
            className="bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 text-white cursor-pointer hover:from-yellow-500 hover:via-orange-600 hover:to-red-600 transition-all duration-300 transform hover:scale-105"
          >
            <Trophy className="w-3 h-3 mr-1" />
            Early Adopter #{totalUsers}
          </Badge>
        </DialogTrigger>
        
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center text-center justify-center">
              <Trophy className="w-6 h-6 mr-2 text-yellow-500" />
              <span className="bg-gradient-to-r from-yellow-500 to-orange-500 bg-clip-text text-transparent">
                Early Adopter #{totalUsers}
              </span>
            </DialogTitle>
            <DialogDescription className="text-center">
              Herzlichen Glückwunsch! Sie sind einer der ersten 100.000 Nutzer!
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Fortschritt</span>
                <span className="font-medium">{totalUsers}/100,000</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-yellow-400 to-orange-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(percentageFilled, 100)}%` }}
                ></div>
              </div>
              <p className="text-xs text-center text-gray-500">
                {remainingSpots > 0 ? (
                  <>Noch <strong>{remainingSpots.toLocaleString()}</strong> Plätze verfügbar!</>
                ) : (
                  "Das Early Adopter Programm ist voll!"
                )}
              </p>
            </div>

            {/* Benefits */}
            <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-4 rounded-lg border border-yellow-200">
              <h4 className="font-medium text-yellow-900 mb-3 flex items-center">
                <Gift className="w-4 h-4 mr-2" />
                Ihre Early Adopter Vorteile:
              </h4>
              
              <div className="grid grid-cols-1 gap-2 text-sm">
                <div className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span><strong>ALLES KOSTENLOS</strong> - Alle Premium Features inklusive!</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span><strong>Unlimited Everything</strong> - Karten, Codes, Meeting Rooms</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span><strong>Google & Apple Sync</strong> - Cloud-Synchronisation</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span><strong>Detailed Analytics</strong> - Wer verwendet Ihre Codes</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span><strong>Priority Support</strong> - VIP Behandlung</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span><strong>Custom Branding</strong> - Keine "Made with" Hinweise</span>
                </div>
              </div>
              
              <div className="mt-3 p-2 bg-yellow-100 rounded text-xs text-center text-yellow-800">
                💰 <strong>Wert: €19.99/Monat</strong> - Für Sie dauerhaft kostenlos!
              </div>
            </div>

            {/* Exclusivity Message */}
            <div className="text-center space-y-2">
              <div className="flex justify-center space-x-2">
                <Crown className="w-5 h-5 text-yellow-500" />
                <Star className="w-5 h-5 text-yellow-400" />
                <Crown className="w-5 h-5 text-yellow-500" />
              </div>
              <p className="text-sm font-medium text-gray-700">
                Exklusiver Founder's Circle Mitglied
              </p>
              <p className="text-xs text-gray-500">
                Diese Vorteile gelten dauerhaft für Ihr Konto - 
                auch wenn wir später kostenpflichtige Features einführen.
              </p>
            </div>

            {/* Share Button */}
            <Button 
              onClick={handleShare}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
            >
              <Share2 className="w-4 h-4 mr-2" />
              Early Adopter Status teilen
            </Button>

            {/* Thank You Message */}
            <div className="text-center">
              <div className="flex justify-center mb-2">
                <Heart className="w-5 h-5 text-red-500" />
              </div>
              <p className="text-sm text-gray-600">
                <strong>Vielen Dank</strong>, dass Sie uns von Anfang an vertrauen! 
                <br />
                Ihr Feedback hilft uns, die beste Business Card App zu entwickeln.
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Simple component for other locations
export const EarlyAdopterIndicator = ({ totalUsers, className = "" }) => {
  const remainingSpots = totalUsers ? Math.max(0, 100000 - totalUsers) : 100000;
  
  return (
    <div className={`text-center ${className}`}>
      <Badge 
        variant="secondary" 
        className="bg-gradient-to-r from-green-100 to-blue-100 text-green-800 border border-green-300"
      >
        <Users className="w-3 h-3 mr-1" />
        {remainingSpots > 0 ? (
          <>Noch {remainingSpots.toLocaleString()} Early Adopter Plätze frei! ⚡</>
        ) : (
          "Early Adopter Programm voll!"
        )}
      </Badge>
    </div>
  );
};

export default EarlyAdopterBadge;