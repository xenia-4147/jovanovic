/**
 * OCR Business Card Scanner Component
 * Game-Changing Feature: Paper → Digital Card Conversion
 * IMPROVED: Direct laptop camera access
 */
import React, { useState, useRef, useCallback } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  Camera, 
  Upload, 
  Scan, 
  Check, 
  X, 
  Edit,
  Loader2,
  AlertCircle,
  Eye,
  Download,
  Sparkles
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';
import CameraScanner from './CameraScanner';

const CONFIDENCE_LEVELS = {
  high: { color: 'bg-green-100 text-green-800 border-green-300', icon: Check },
  medium: { color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: AlertCircle },
  low: { color: 'bg-red-100 text-red-800 border-red-300', icon: X }
};

const CardScanner = ({ onCardCreated }) => {
  const { toast } = useToast();
  const fileInputRef = useRef(null);
  
  // States
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [converting, setConverting] = useState(false);
  const [editingField, setEditingField] = useState(null);
  const [showCameraScanner, setShowCameraScanner] = useState(false);
  
  // Open improved camera scanner
  const openCameraScanner = useCallback(() => {
    setShowCameraScanner(true);
  }, []);

  // Handle camera scan result
  const handleCameraScanResult = useCallback((scanResult) => {
    setScanResult(scanResult);
    setShowCameraScanner(false);
  }, []);

  // Close camera scanner
  const closeCameraScanner = useCallback(() => {
    setShowCameraScanner(false);
  }, []);
  
  // File upload
  const handleFileUpload = useCallback(async (event) => {
    const file = event.target.files[0];
    if (file) {
      await processImage(file, 'upload');
    }
  }, []);
  
  // Process image with OCR
  const processImage = async (file, method) => {
    if (!file.type.startsWith('image/')) {
      toast({
        title: "Ungültiger Dateityp",
        description: "Bitte wählen Sie eine Bilddatei aus.",
        variant: "destructive"
      });
      return;
    }
    
    setScanning(true);
    setScanResult(null);
    
    try {
      // Convert to base64
      const base64 = await fileToBase64(file);
      
      // Start OCR scan
      const response = await api.post('/scanner/scan', {
        image_data: base64,
        scan_method: method,
        device_info: {
          platform: navigator.platform,
          userAgent: navigator.userAgent.slice(0, 100)
        }
      });
      
      if (response.data.success) {
        // Poll for results
        await pollScanResults(response.data.scan_id);
      } else {
        throw new Error('Scan konnte nicht gestartet werden');
      }
      
    } catch (error) {
      console.error('Scan failed:', error);
      toast({
        title: "Scan fehlgeschlagen",
        description: "Die Visitenkarte konnte nicht gescannt werden. Bitte versuchen Sie es erneut.",
        variant: "destructive"
      });
    } finally {
      setScanning(false);
    }
  };
  
  // Poll scan results
  const pollScanResults = async (scanId, maxAttempts = 10) => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await api.get(`/scanner/scan/${scanId}`);
        const result = response.data;
        
        if (result.status === 'completed') {
          setScanResult(result);
          
          toast({
            title: "Scan abgeschlossen! ✨",
            description: `${result.scanned_card.extracted_fields.length} Felder erkannt`,
          });
          break;
        } else if (result.status === 'failed') {
          throw new Error('Scan fehlgeschlagen');
        }
        
        // Wait before next attempt
        if (attempt < maxAttempts - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
      } catch (error) {
        console.error('Polling error:', error);
        break;
      }
    }
  };
  
  // Convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };
  
  // Correct field
  const correctField = async (fieldType, newValue) => {
    try {
      await api.post(`/scanner/scan/${scanResult.scan_id}/correct`, {
        scan_id: scanResult.scan_id,
        field_type: fieldType,
        corrected_value: newValue
      });
      
      // Update local state
      const updatedFields = scanResult.scanned_card.extracted_fields.map(field => 
        field.field_type === fieldType 
          ? { ...field, value: newValue, manually_corrected: true, confidence_level: 'manual' }
          : field
      );
      
      setScanResult({
        ...scanResult,
        scanned_card: {
          ...scanResult.scanned_card,
          extracted_fields: updatedFields
        }
      });
      
      setEditingField(null);
      
      toast({
        title: "Korrektur gespeichert",
        description: "Das Feld wurde erfolgreich korrigiert.",
      });
      
    } catch (error) {
      toast({
        title: "Korrektur fehlgeschlagen",
        description: "Die Korrektur konnte nicht gespeichert werden.",
        variant: "destructive"
      });
    }
  };
  
  // Convert to digital card
  const convertToCard = async () => {
    if (!scanResult?.conversion_ready) return;
    
    setConverting(true);
    
    try {
      // Get name field for card name
      const nameField = scanResult.scanned_card.extracted_fields.find(
        field => field.field_type === 'name'
      );
      
      const cardName = nameField?.value || 'Gescannte Visitenkarte';
      
      const response = await api.post(`/scanner/scan/${scanResult.scan_id}/convert`, {
        scan_id: scanResult.scan_id,
        card_name: cardName,
        auto_map_fields: true
      });
      
      if (response.data) {
        toast({
          title: "Visitenkarte erstellt! 🎉",
          description: `"${cardName}" wurde erfolgreich zu Ihren Visitenkarten hinzugefügt.`,
        });
        
        // Call parent callback
        if (onCardCreated) {
          onCardCreated(response.data);
        }
        
        // Reset scanner
        setScanResult(null);
      }
      
    } catch (error) {
      console.error('Conversion failed:', error);
      toast({
        title: "Konvertierung fehlgeschlagen",
        description: "Die Visitenkarte konnte nicht erstellt werden.",
        variant: "destructive"
      });
    } finally {
      setConverting(false);
    }
  };
  
  // Render confidence badge
  const renderConfidenceBadge = (confidenceLevel) => {
    const config = CONFIDENCE_LEVELS[confidenceLevel] || CONFIDENCE_LEVELS.low;
    const Icon = config.icon;
    
    return (
      <Badge variant="outline" className={config.color}>
        <Icon className="w-3 h-3 mr-1" />
        {confidenceLevel === 'manual' ? 'Korrigiert' : confidenceLevel}
      </Badge>
    );
  };
  
  // Render extracted field
  const renderField = (field) => {
    const isEditing = editingField === field.field_type;
    
    return (
      <div key={field.field_type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm font-medium text-gray-700 capitalize">
              {field.field_type === 'name' ? 'Name' :
               field.field_type === 'email' ? 'E-Mail' :
               field.field_type === 'phone' ? 'Telefon' :
               field.field_type === 'company' ? 'Firma' :
               field.field_type === 'position' ? 'Position' :
               field.field_type === 'website' ? 'Website' : 
               field.field_type}
            </span>
            {renderConfidenceBadge(field.confidence_level)}
          </div>
          
          {isEditing ? (
            <div className="flex items-center space-x-2">
              <input
                type="text"
                defaultValue={field.value}
                className="flex-1 px-2 py-1 text-sm border rounded"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    correctField(field.field_type, e.target.value);
                  } else if (e.key === 'Escape') {
                    setEditingField(null);
                  }
                }}
                autoFocus
              />
              <Button
                size="sm" 
                variant="ghost"
                onClick={(e) => {
                  const input = e.target.closest('div').querySelector('input');
                  correctField(field.field_type, input.value);
                }}
              >
                <Check className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="ghost" 
                onClick={() => setEditingField(null)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-900">{field.value}</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setEditingField(field.field_type)}
              >
                <Edit className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Scanner Interface */}
      {!scanResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Sparkles className="w-5 h-5 mr-2 text-blue-600" />
              Visitenkarten Scanner
            </CardTitle>
            <CardDescription>
              Fotografieren oder laden Sie eine Papier-Visitenkarte hoch, um sie automatisch zu digitalisieren.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {scanning ? (
              <div className="text-center py-12">
                <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-600" />
                <h3 className="text-lg font-medium mb-2">Visitenkarte wird gescannt...</h3>
                <p className="text-gray-600 mb-4">KI analysiert das Bild und extrahiert die Informationen</p>
                <Progress value={75} className="w-64 mx-auto" />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Button
                  onClick={() => cameraInputRef.current?.click()}
                  className="h-32 flex flex-col space-y-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                >
                  <Camera className="w-8 h-8" />
                  <span>Mit Kamera fotografieren</span>
                  <span className="text-xs opacity-90">Empfohlen für beste Ergebnisse</span>
                </Button>
                
                <Button
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  className="h-32 flex flex-col space-y-2 border-2 border-dashed hover:border-blue-400"
                >
                  <Upload className="w-8 h-8" />
                  <span>Datei hochladen</span>
                  <span className="text-xs text-gray-600">JPG, PNG unterstützt</span>
                </Button>
              </div>
            )}
            
            {/* Hidden file inputs */}
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={handleCameraCapture}
            />
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileUpload}
            />
          </CardContent>
        </Card>
      )}
      
      {/* Scan Results */}
      {scanResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <Scan className="w-5 h-5 mr-2 text-green-600" />
                Scan-Ergebnisse
              </div>
              <Badge 
                variant="outline" 
                className="bg-green-100 text-green-800 border-green-300"
              >
                {Math.round(scanResult.scanned_card.overall_confidence)}% Genauigkeit
              </Badge>
            </CardTitle>
            <CardDescription>
              Überprüfen Sie die erkannten Informationen und korrigieren Sie sie bei Bedarf.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Extracted Fields */}
              {scanResult.scanned_card.extracted_fields.length > 0 ? (
                <div className="space-y-3">
                  {scanResult.scanned_card.extracted_fields.map(renderField)}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <AlertCircle className="w-12 h-12 mx-auto mb-2" />
                  <p>Keine Informationen erkannt. Bitte versuchen Sie es mit einem anderen Bild.</p>
                </div>
              )}
              
              {/* Action Buttons */}
              {scanResult.conversion_ready && (
                <div className="flex space-x-4 pt-4">
                  <Button
                    onClick={convertToCard}
                    disabled={converting}
                    className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
                  >
                    {converting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Wird erstellt...
                      </>
                    ) : (
                      <>
                        <Check className="w-4 h-4 mr-2" />
                        Digitale Visitenkarte erstellen
                      </>
                    )}
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={() => setScanResult(null)}
                  >
                    Neu scannen
                  </Button>
                </div>
              )}
              
              {!scanResult.conversion_ready && scanResult.scanned_card.extracted_fields.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 mr-2" />
                    <div>
                      <h4 className="font-medium text-yellow-800">Verbesserung empfohlen</h4>
                      <p className="text-sm text-yellow-700 mt-1">
                        Korrigieren Sie unsichere Felder oder scannen Sie ein klareres Bild für bessere Ergebnisse.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CardScanner;