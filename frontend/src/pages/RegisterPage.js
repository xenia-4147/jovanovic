import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Checkbox } from '../components/ui/checkbox';
import { Separator } from '../components/ui/separator';
import { Eye, EyeOff, Lock, Mail, User, ArrowLeft, Shield, Info } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    gdpr_consent: false,
    privacy_consent: false,
    marketing_consent: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'E-Mail ist erforderlich';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Ungültige E-Mail-Adresse';
    }

    if (!formData.password) {
      newErrors.password = 'Passwort ist erforderlich';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Passwort muss mindestens 8 Zeichen lang sein';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwörter stimmen nicht überein';
    }

    if (!formData.first_name) {
      newErrors.first_name = 'Vorname ist erforderlich';
    }

    if (!formData.gdpr_consent) {
      newErrors.gdpr_consent = 'DSGVO-Zustimmung ist erforderlich';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const result = await register(formData);
      
      if (result.success) {
        toast({
          title: "Willkommen!",
          description: "Ihr Konto wurde erfolgreich erstellt.",
        });
        navigate('/');
      } else {
        setErrors({ general: result.error });
      }
    } catch (err) {
      setErrors({ general: 'Ein unerwarteter Fehler ist aufgetreten.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link 
            to="/"
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Zurück zur Startseite
          </Link>
          
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Registrierung
          </h1>
          <p className="text-gray-600 mt-2">
            Erstellen Sie Ihr kostenloses Konto
          </p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center">Konto erstellen</CardTitle>
            <CardDescription className="text-center">
              Füllen Sie die Informationen aus, um loszulegen
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {errors.general && (
              <Alert variant="destructive" className="mb-6">
                <AlertDescription>{errors.general}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name Fields */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="first_name">Vorname *</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      id="first_name"
                      placeholder="Vorname"
                      value={formData.first_name}
                      onChange={(e) => handleInputChange('first_name', e.target.value)}
                      className={`pl-10 ${errors.first_name ? 'border-red-500' : ''}`}
                      required
                    />
                  </div>
                  {errors.first_name && (
                    <p className="text-sm text-red-600">{errors.first_name}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="last_name">Nachname</Label>
                  <Input
                    id="last_name"
                    placeholder="Nachname"
                    value={formData.last_name}
                    onChange={(e) => handleInputChange('last_name', e.target.value)}
                  />
                </div>
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">E-Mail-Adresse *</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="name@example.com"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className={`pl-10 ${errors.email ? 'border-red-500' : ''}`}
                    required
                  />
                </div>
                {errors.email && (
                  <p className="text-sm text-red-600">{errors.email}</p>
                )}
              </div>

              {/* Password */}
              <div className="space-y-2">
                <Label htmlFor="password">Passwort *</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Mindestens 8 Zeichen"
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    className={`pl-10 pr-10 ${errors.password ? 'border-red-500' : ''}`}
                    required
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
                {errors.password && (
                  <p className="text-sm text-red-600">{errors.password}</p>
                )}
              </div>

              {/* Confirm Password */}
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Passwort bestätigen *</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Passwort wiederholen"
                    value={formData.confirmPassword}
                    onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                    className={`pl-10 pr-10 ${errors.confirmPassword ? 'border-red-500' : ''}`}
                    required
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="text-sm text-red-600">{errors.confirmPassword}</p>
                )}
              </div>

              {/* GDPR and Privacy Consents */}
              <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-start space-x-3">
                  <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900">Datenschutz & Einverständniserklärungen</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      Bitte bestätigen Sie die folgenden Punkte, um fortzufahren.
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-start space-x-3">
                    <Checkbox 
                      id="gdpr_consent"
                      checked={formData.gdpr_consent}
                      onCheckedChange={(checked) => handleInputChange('gdpr_consent', checked)}
                      className={errors.gdpr_consent ? 'border-red-500' : ''}
                    />
                    <Label htmlFor="gdpr_consent" className="text-sm leading-relaxed">
                      Ich stimme der Verarbeitung meiner personenbezogenen Daten gemäß der{' '}
                      <Link to="/privacy" className="text-blue-600 hover:underline">
                        Datenschutzerklärung
                      </Link>{' '}
                      zu. (Erforderlich) *
                    </Label>
                  </div>
                  {errors.gdpr_consent && (
                    <p className="text-sm text-red-600 ml-6">{errors.gdpr_consent}</p>
                  )}

                  <div className="flex items-start space-x-3">
                    <Checkbox 
                      id="privacy_consent"
                      checked={formData.privacy_consent}
                      onCheckedChange={(checked) => handleInputChange('privacy_consent', checked)}
                    />
                    <Label htmlFor="privacy_consent" className="text-sm leading-relaxed">
                      Ich stimme der Verwendung von Analytics und der Verbesserung der Benutzerfreundlichkeit zu.
                    </Label>
                  </div>

                  <div className="flex items-start space-x-3">
                    <Checkbox 
                      id="marketing_consent"
                      checked={formData.marketing_consent}
                      onCheckedChange={(checked) => handleInputChange('marketing_consent', checked)}
                    />
                    <Label htmlFor="marketing_consent" className="text-sm leading-relaxed">
                      Ich möchte gelegentlich Updates und Marketinginformationen erhalten.
                    </Label>
                  </div>
                </div>

                <div className="flex items-start space-x-2 text-xs text-blue-600">
                  <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <p>
                    Sie können Ihre Einstellungen jederzeit in Ihrem Profil ändern und Ihre Daten exportieren oder löschen.
                  </p>
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full bg-blue-600 hover:bg-blue-700"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Konto erstellen...
                  </>
                ) : (
                  'Konto erstellen'
                )}
              </Button>
            </form>

            <div className="mt-6">
              <Separator className="my-4" />
              
              <p className="text-center text-sm text-gray-600">
                Bereits ein Konto?{' '}
                <Link 
                  to="/login" 
                  className="text-blue-600 hover:text-blue-700 font-medium hover:underline"
                >
                  Jetzt anmelden
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RegisterPage;