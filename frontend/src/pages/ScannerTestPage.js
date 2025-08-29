/**
 * Scanner Test Page
 * For testing the improved camera scanner functionality
 */
import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Camera, ArrowLeft, TestTube } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import CardScanner from '../components/CardScanner';

const ScannerTestPage = () => {
  const navigate = useNavigate();
  const [showScanner, setShowScanner] = useState(false);

  const handleCardCreated = (card) => {
    console.log('Card created:', card);
    setShowScanner(false);
    alert(`Visitenkarte erstellt: ${card.name || 'Unbekannt'}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
      <div className="container mx-auto max-w-4xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              onClick={() => navigate('/')}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Zurück</span>
            </Button>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Scanner Test
              </h1>
              <p className="text-gray-600">
                Testen Sie die verbesserte Kamera-Funktionalität für Visitenkarten-Scanner
              </p>
            </div>
          </div>
        </div>

        {!showScanner ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TestTube className="w-6 h-6 text-blue-600" />
                <span>Visitenkarten-Scanner Testen</span>
              </CardTitle>
              <CardDescription>
                Diese Seite testet die verbesserte Kamera-Funktionalität für Laptop-Kameras.
                Der neue Scanner verwendet direkten Kamera-Zugriff anstatt File Inputs.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-800 mb-2">Was wurde verbessert?</h3>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    <li>✅ Direkter Kamera-Zugriff mit getUserMedia()</li>
                    <li>✅ Live-Kamera-Vorschau vor dem Foto</li>
                    <li>✅ Mehrere Kamera-Auswahl (falls verfügbar)</li>
                    <li>✅ Bessere Fehlerbehandlung für Kamera-Berechtigungen</li>
                    <li>✅ Optimiert für Desktop/Laptop-Kameras</li>
                  </ul>
                </div>

                <Button
                  onClick={() => setShowScanner(true)}
                  className="w-full h-16 text-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                >
                  <Camera className="w-6 h-6 mr-3" />
                  Verbesserten Scanner testen
                </Button>

                <div className="text-sm text-gray-600 space-y-2">
                  <p><strong>Hinweis:</strong> Der Browser wird um Kamera-Berechtigung fragen.</p>
                  <p><strong>Empfehlung:</strong> Erlauben Sie den Zugriff für die beste Erfahrung.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          <CardScanner onCardCreated={handleCardCreated} />
        )}
      </div>
    </div>
  );
};

export default ScannerTestPage;