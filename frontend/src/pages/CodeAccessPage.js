import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';
import { ArrowLeft, Search, Key, CheckCircle, AlertCircle } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const CodeAccessPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!code.trim()) {
      setError('Bitte geben Sie einen Code ein.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await api.post('/cards/access-by-code', { code: code.trim() });
      
      if (response.data.success) {
        setResult(response.data);
        toast({
          title: "Code gefunden!",
          description: `Visitenkarte von ${response.data.card.name} gefunden.`,
        });
      } else {
        setError(response.data.message || 'Code nicht gefunden.');
      }
    } catch (err) {
      console.error('Code access failed:', err);
      setError(
        err.response?.data?.detail || 
        err.response?.data?.message || 
        'Code nicht gefunden oder ungültig.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleViewCard = () => {
    if (result && result.card) {
      navigate(`/card/${result.card.id}`);
    }
  };

  const handleClearResults = () => {
    setResult(null);
    setError('');
    setCode('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Zurück
          </Button>
          
          <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Key className="w-8 h-8 text-white" />
          </div>
          
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            Code eingeben
          </h1>
          <p className="text-gray-600">
            Geben Sie den Code einer Visitenkarte ein, um den Kontakt zu erhalten
          </p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center">
              <Search className="w-5 h-5 mr-2" />
              Visitenkarten-Code
            </CardTitle>
            <CardDescription>
              Codes sind eindeutige Bezeichnungen wie "WerbegiganCH" oder "MaxMustermann2024"
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {result && result.success && (
              <Alert className="mb-6 bg-green-50 border-green-200">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  <div className="font-medium mb-2">Visitenkarte gefunden!</div>
                  <div className="flex items-center space-x-3">
                    <img
                      src={result.card.profile_image || `https://ui-avatars.com/api/?name=${encodeURIComponent(result.card.name)}&background=22c55e&color=fff`}
                      alt={result.card.name}
                      className="w-10 h-10 rounded-full"
                    />
                    <div>
                      <p className="font-semibold">{result.card.name}</p>
                      {result.card.company && <p className="text-sm">{result.card.company}</p>}
                    </div>
                  </div>
                  <div className="mt-2 text-sm">
                    Code verwendet: <strong>{result.code_usage_count}</strong> Mal
                  </div>
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="code">Visitenkarten-Code</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    id="code"
                    type="text"
                    placeholder="z.B. WerbegiganCH oder MaxMustermann2024"
                    value={code}
                    onChange={(e) => {
                      setCode(e.target.value);
                      if (error) setError('');
                      if (result) setResult(null);
                    }}
                    className="pl-10 uppercase"
                    style={{ textTransform: 'uppercase' }}
                    disabled={loading}
                  />
                </div>
                <p className="text-xs text-gray-500">
                  Codes bestehen aus Buchstaben und Zahlen (3-50 Zeichen)
                </p>
              </div>

              <div className="space-y-3">
                <Button 
                  type="submit" 
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  disabled={loading || !code.trim()}
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Suche...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Code suchen
                    </>
                  )}
                </Button>

                {result && result.success && (
                  <div className="grid grid-cols-2 gap-3">
                    <Button 
                      variant="outline" 
                      onClick={handleViewCard}
                      className="w-full"
                    >
                      Visitenkarte anzeigen
                    </Button>
                    
                    <Button 
                      variant="outline" 
                      onClick={handleClearResults}
                      className="w-full"
                    >
                      Neuer Code
                    </Button>
                  </div>
                )}
              </div>
            </form>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h3 className="font-medium text-blue-900 mb-2">💡 Wie funktioniert es?</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Visitenkarten-Besitzer können eigene Codes erstellen</li>
                <li>• Codes sind einzigartig und leicht zu merken</li>
                <li>• Einfacher als QR-Codes bei Telefongesprächen</li>
                <li>• Automatischer Kontaktimport möglich</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CodeAccessPage;