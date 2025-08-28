import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Crown, 
  Sparkles, 
  Zap, 
  TrendingUp, 
  Shield, 
  Users, 
  BarChart3,
  Cloud,
  CheckCircle,
  Star,
  ArrowRight,
  Gift
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const PremiumFeatureGate = ({ 
  feature, 
  children, 
  fallback = null,
  showUpgrade = true,
  className = ""
}) => {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [featureInfo, setFeatureInfo] = useState(null);
  const [showUpgradeDialog, setShowUpgradeDialog] = useState(false);

  useEffect(() => {
    checkFeatureAccess();
  }, [feature, user]);

  const checkFeatureAccess = async () => {
    if (!user || !feature) {
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/subscription/check-feature', {
        feature_name: feature,
        user_id: user.id
      });

      setHasAccess(response.data.allowed);
      setFeatureInfo(response.data);
    } catch (error) {
      console.error('Feature access check failed:', error);
      // Default to allowed on error (growth-first approach)
      setHasAccess(true);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgradeClick = () => {
    setShowUpgradeDialog(true);
    
    // Track upgrade interest
    try {
      api.post('/subscription/track-usage', {
        event_type: 'upgrade_interest',
        event_data: { 
          feature: feature,
          source: 'feature_gate'
        }
      });
    } catch (error) {
      // Silent fail for tracking
    }
  };

  const getFeatureIcon = (featureName) => {
    switch (featureName) {
      case 'detailed_analytics': return <BarChart3 className="w-5 h-5" />;
      case 'google_sync': return <Cloud className="w-5 h-5" />;
      case 'apple_sync': return <Cloud className="w-5 h-5" />;
      case 'custom_branding': return <Crown className="w-5 h-5" />;
      case 'priority_support': return <Shield className="w-5 h-5" />;
      case 'team_management': return <Users className="w-5 h-5" />;
      default: return <Sparkles className="w-5 h-5" />;
    }
  };

  const getFeatureTitle = (featureName) => {
    switch (featureName) {
      case 'detailed_analytics': return 'Detaillierte Analytics';
      case 'google_sync': return 'Google Contacts Sync';
      case 'apple_sync': return 'Apple iCloud Sync';
      case 'custom_branding': return 'Custom Branding';
      case 'priority_support': return 'Priority Support';
      case 'team_management': return 'Team Management';
      default: return 'Premium Feature';
    }
  };

  if (loading) {
    return (
      <div className={`opacity-50 ${className}`}>
        <div className="animate-pulse bg-gray-200 h-8 rounded"></div>
      </div>
    );
  }

  // If user has access, render the children
  if (hasAccess) {
    return <div className={className}>{children}</div>;
  }

  // If fallback is provided, render it instead of upgrade prompt
  if (fallback) {
    return <div className={className}>{fallback}</div>;
  }

  // If showUpgrade is false, render nothing
  if (!showUpgrade) {
    return null;
  }

  // Render premium upgrade prompt
  return (
    <div className={className}>
      <Card className="border-2 border-dashed border-yellow-300 bg-gradient-to-br from-yellow-50 to-orange-50">
        <CardContent className="p-6 text-center">
          <div className="flex justify-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
              {getFeatureIcon(feature)}
            </div>
          </div>
          
          <h3 className="font-semibold text-lg mb-2 text-gray-900">
            {getFeatureTitle(feature)}
          </h3>
          
          <p className="text-gray-600 mb-4 text-sm">
            {featureInfo?.reason || `Diese Funktion ist nur im Premium Plan verfügbar.`}
          </p>
          
          <div className="flex justify-center space-x-2 mb-4">
            <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
              <Crown className="w-3 h-3 mr-1" />
              Premium Feature
            </Badge>
          </div>

          <Dialog open={showUpgradeDialog} onOpenChange={setShowUpgradeDialog}>
            <DialogTrigger asChild>
              <Button 
                onClick={handleUpgradeClick}
                className="bg-gradient-to-r from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600 text-white font-medium"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Upgrade zu Premium
              </Button>
            </DialogTrigger>
            
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="flex items-center">
                  <Crown className="w-5 h-5 mr-2 text-yellow-500" />
                  Premium Plan - Fast alles kostenlos! 🚀
                </DialogTitle>
                <DialogDescription>
                  Schalten Sie erweiterte Features frei für noch bessere Ergebnisse
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                {/* Current feature benefits */}
                {featureInfo?.upgrade_benefits && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm text-gray-900 mb-2">
                      Mit Premium erhalten Sie:
                    </h4>
                    {featureInfo.upgrade_benefits.slice(0, 3).map((benefit, index) => (
                      <div key={index} className="flex items-start space-x-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-gray-600">{benefit}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Pricing (prepared for later) */}
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <div className="text-center">
                    <div className="flex items-center justify-center space-x-2 mb-2">
                      <Gift className="w-5 h-5 text-blue-600" />
                      <span className="font-medium text-blue-900">Bald verfügbar!</span>
                    </div>
                    <p className="text-sm text-blue-800 mb-3">
                      Premium Features werden in den nächsten Wochen freigeschaltet.
                    </p>
                    <div className="text-xs text-blue-600 bg-blue-100 px-3 py-1 rounded-full inline-block">
                      💰 Voraussichtlich €4.99/Monat
                    </div>
                  </div>
                </div>
                
                {/* Growth message */}
                <div className="text-center">
                  <p className="text-xs text-gray-500">
                    Aktuell konzentrieren wir uns auf das Wachstum der App.
                    <br />
                    Deshalb ist fast alles kostenlos! 🎉
                  </p>
                </div>
              </div>
              
              <div className="flex space-x-2 pt-4">
                <Button 
                  variant="outline" 
                  onClick={() => setShowUpgradeDialog(false)}
                  className="flex-1"
                >
                  Später
                </Button>
                <Button 
                  onClick={() => {
                    toast({
                      title: "Benachrichtigung aktiviert! 🔔",
                      description: "Wir informieren Sie, sobald Premium verfügbar ist."
                    });
                    setShowUpgradeDialog(false);
                  }}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  <Star className="w-4 h-4 mr-2" />
                  Benachrichtigen
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          
          <p className="text-xs text-gray-500 mt-3">
            Derzeit fast alles kostenlos für maximales Wachstum! 📈
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

// Higher-order component for easy premium feature wrapping
export const withPremiumGate = (WrappedComponent, feature, options = {}) => {
  return (props) => (
    <PremiumFeatureGate 
      feature={feature} 
      showUpgrade={options.showUpgrade !== false}
      fallback={options.fallback}
    >
      <WrappedComponent {...props} />
    </PremiumFeatureGate>
  );
};

// Hook for checking premium access in components
export const usePremiumAccess = (feature) => {
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    const checkAccess = async () => {
      if (!user || !feature) {
        setLoading(false);
        return;
      }

      try {
        const response = await api.post('/subscription/check-feature', {
          feature_name: feature,
          user_id: user.id
        });

        setHasAccess(response.data.allowed);
      } catch (error) {
        console.error('Premium access check failed:', error);
        setHasAccess(true); // Default to allowed
      } finally {
        setLoading(false);
      }
    };

    checkAccess();
  }, [feature, user]);

  return { hasAccess, loading };
};

export default PremiumFeatureGate;