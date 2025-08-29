/**
 * Improved Camera Scanner Component
 * FIXES: Direct laptop camera access for business card scanning
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { 
  Camera, 
  Square,
  RotateCcw, 
  Check, 
  X, 
  AlertCircle,
  Loader2,
  Settings,
  Zap,
  Eye,
  Sparkles
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const CameraScanner = ({ onCardScanned, onClose }) => {
  const { toast } = useToast();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  
  // States
  const [cameraActive, setCameraActive] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  
  // Initialize camera
  useEffect(() => {
    initializeCamera();
    return () => {
      stopCamera();
    };
  }, []);

  // Get camera devices
  const getCameraDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');
      setDevices(videoDevices);
      
      if (videoDevices.length > 0) {
        setSelectedDevice(videoDevices[0].deviceId);
      }
      
      return videoDevices;
    } catch (error) {
      console.error('Error getting camera devices:', error);
      return [];
    }
  };

  // Initialize camera
  const initializeCamera = async () => {
    try {
      setCameraError(null);
      
      // Check if camera is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Kamera wird von diesem Browser nicht unterstützt');
      }
      
      // Get available cameras
      await getCameraDevices();
      
      // Request camera permission
      const constraints = {
        video: {
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          facingMode: 'environment', // Prefer back camera
          deviceId: selectedDevice ? { exact: selectedDevice } : undefined
        },
        audio: false
      };
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      
      setCameraActive(true);
      
      toast({
        title: "Kamera aktiviert! 📹",
        description: "Positionieren Sie die Visitenkarte im Rahmen und drücken Sie den Auslöser.",
      });
      
    } catch (error) {
      console.error('Camera initialization failed:', error);
      
      let errorMessage = 'Kamera-Zugriff fehlgeschlagen';
      
      if (error.name === 'NotAllowedError') {
        errorMessage = 'Kamera-Berechtigung verweigert. Bitte erlauben Sie den Kamera-Zugriff in Ihrem Browser.';
      } else if (error.name === 'NotFoundError') {
        errorMessage = 'Keine Kamera gefunden. Bitte stellen Sie sicher, dass eine Kamera angeschlossen ist.';
      } else if (error.name === 'NotReadableError') {
        errorMessage = 'Kamera wird bereits von einer anderen Anwendung verwendet.';
      }
      
      setCameraError(errorMessage);
      
      toast({
        title: "Kamera-Fehler",
        description: errorMessage,
        variant: "destructive"
      });
    }
  };

  // Stop camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  }, []);

  // Switch camera
  const switchCamera = async (deviceId) => {
    stopCamera();
    setSelectedDevice(deviceId);
    
    setTimeout(() => {
      initializeCamera();
    }, 100);
  };

  // Capture photo
  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) {
      toast({
        title: "Fehler",
        description: "Kamera nicht bereit",
        variant: "destructive"
      });
      return;
    }
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    // Set canvas size to video size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw current video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to data URL
    const imageDataURL = canvas.toDataURL('image/jpeg', 0.95);
    setCapturedImage(imageDataURL);
    
    toast({
      title: "Foto aufgenommen! 📸",
      description: "Überprüfen Sie das Bild und scannen Sie es oder nehmen Sie ein neues auf.",
    });
  }, [toast]);

  // Retake photo
  const retakePhoto = useCallback(() => {
    setCapturedImage(null);
    setScanning(false);
  }, []);

  // Scan captured image
  const scanImage = async () => {
    if (!capturedImage) return;
    
    setScanning(true);
    
    try {
      // Convert data URL to base64
      const base64 = capturedImage.split(',')[1];
      
      // Send to OCR API
      const response = await api.post('/scanner/scan', {
        image_data: base64,
        scan_method: 'camera',
        device_info: {
          platform: navigator.platform,
          userAgent: navigator.userAgent.slice(0, 100),
          camera_device: selectedDevice
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
      setScanning(false);
    }
  };

  // Poll scan results and auto-convert to contact
  const pollScanResults = async (scanId, maxAttempts = 10) => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await api.get(`/scanner/scan/${scanId}`);
        const result = response.data;
        
        if (result.status === 'completed') {
          toast({
            title: "Scan abgeschlossen! ✨",
            description: `${result.scanned_card.extracted_fields.length} Felder erkannt - wird automatisch zur Kontaktliste hinzugefügt...`,
          });
          
          // Automatically convert to contact/business card
          await autoConvertToContact(result);
          
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
    
    setScanning(false);
  };

  // Auto-convert scan result to contact/business card
  const autoConvertToContact = async (scanResult) => {
    try {
      // Get name field for card name (safe access)
      const nameField = scanResult?.scanned_card?.extracted_fields?.find(
        field => field.field_type === 'name' || field.field_type === 'full_name'
      );
      
      const cardName = nameField?.value || 'Gescannte Visitenkarte';
      
      // Convert to business card automatically
      const convertResponse = await api.post(`/scanner/scan/${scanResult.scan_id}/convert`, {
        scan_id: scanResult.scan_id,
        card_name: cardName,
        auto_map_fields: true
      });
      
      if (convertResponse.data) {
        toast({
          title: "Automatisch zur Kontaktliste hinzugefügt! 🎉📇",
          description: `"${cardName}" wurde automatisch zu Ihren Kontakten hinzugefügt.`,
        });
        
        // Call parent callback with the created card
        if (onCardScanned) {
          onCardScanned(convertResponse.data);
        }
        
        // Stop camera and close scanner
        stopCamera();
        if (onClose) {
          onClose();
        }
        
      } else {
        // Fallback: show scan results for manual conversion
        if (onCardScanned) {
          onCardScanned(scanResult);
        }
        
        toast({
          title: "Scan erfolgreich - Manuelle Überprüfung erforderlich",
          description: "Bitte überprüfen Sie die erkannten Felder und bestätigen Sie die Erstellung.",
        });
      }
      
    } catch (error) {
      console.error('Auto-convert failed:', error);
      
      // Fallback: show scan results for manual conversion
      if (onCardScanned) {
        onCardScanned(scanResult);
      }
      
      toast({
        title: "Automatische Konvertierung fehlgeschlagen",
        description: "Scan erfolgreich - bitte prüfen Sie die Felder manuell.",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5" />
              <h2 className="text-xl font-bold">Kamera Scanner</h2>
            </div>
            <div className="flex items-center space-x-2">
              {devices.length > 1 && (
                <select
                  value={selectedDevice || ''}
                  onChange={(e) => switchCamera(e.target.value)}
                  className="px-3 py-1 rounded bg-white bg-opacity-20 text-white text-sm"
                >
                  {devices.map((device, index) => (
                    <option key={device.deviceId} value={device.deviceId} className="text-black">
                      {device.label || `Kamera ${index + 1}`}
                    </option>
                  ))}
                </select>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-white hover:bg-white hover:bg-opacity-20"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>

        <div className="p-6">
          {cameraError ? (
            // Camera Error
            <div className="text-center py-12">
              <AlertCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
              <h3 className="text-lg font-medium mb-2 text-red-700">Kamera-Fehler</h3>
              <p className="text-gray-600 mb-4">{cameraError}</p>
              <div className="space-x-4">
                <Button onClick={initializeCamera} className="bg-blue-600 hover:bg-blue-700">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Erneut versuchen
                </Button>
                <Button variant="outline" onClick={onClose}>
                  Schließen
                </Button>
              </div>
            </div>
          ) : scanning ? (
            // Scanning
            <div className="text-center py-12">
              <Loader2 className="w-16 h-16 mx-auto mb-4 animate-spin text-blue-600" />
              <h3 className="text-lg font-medium mb-2">Visitenkarte wird gescannt...</h3>
              <p className="text-gray-600 mb-4">KI analysiert das Bild und extrahiert die Informationen</p>
              <div className="w-64 mx-auto bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '75%'}}></div>
              </div>
            </div>
          ) : capturedImage ? (
            // Image Preview
            <div className="space-y-4">
              <div className="relative">
                <img 
                  src={capturedImage} 
                  alt="Aufgenommene Visitenkarte" 
                  className="w-full max-h-96 object-contain rounded-lg border"
                />
                <Badge className="absolute top-2 left-2 bg-green-600">
                  <Check className="w-3 h-3 mr-1" />
                  Aufgenommen
                </Badge>
              </div>
              
              <div className="flex space-x-4 justify-center">
                <Button
                  onClick={scanImage}
                  disabled={scanning}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  Visitenkarte scannen
                </Button>
                <Button
                  variant="outline"
                  onClick={retakePhoto}
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Neu aufnehmen
                </Button>
              </div>
            </div>
          ) : (
            // Camera View
            <div className="space-y-4">
              {cameraActive ? (
                <div className="relative">
                  <video
                    ref={videoRef}
                    className="w-full max-h-96 object-contain rounded-lg bg-gray-900"
                    autoPlay
                    playsInline
                    muted
                  />
                  
                  {/* Camera overlay with guidelines */}
                  <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute inset-4 border-2 border-white border-dashed rounded-lg opacity-50"></div>
                    <div className="absolute top-6 left-6 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
                      📄 Visitenkarte hier positionieren
                    </div>
                  </div>
                  
                  <Badge className="absolute top-2 right-2 bg-green-600">
                    <Eye className="w-3 h-3 mr-1" />
                    Live
                  </Badge>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Camera className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">Kamera wird aktiviert...</h3>
                  <p className="text-gray-600">Bitte erlauben Sie den Kamera-Zugriff in Ihrem Browser.</p>
                </div>
              )}
              
              {cameraActive && (
                <div className="flex justify-center">
                  <Button
                    onClick={capturePhoto}
                    size="lg"
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 px-8"
                  >
                    <Camera className="w-5 h-5 mr-2" />
                    Foto aufnehmen
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Hidden canvas for image capture */}
        <canvas ref={canvasRef} className="hidden" />
      </div>
    </div>
  );
};

export default CameraScanner;