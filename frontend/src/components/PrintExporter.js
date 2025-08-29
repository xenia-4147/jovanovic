/**
 * Print Export Component
 * Game-Changing Feature: Digital → Professional Print Ready
 */
import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  Printer, 
  Download, 
  FileImage, 
  FileText, 
  Settings,
  Palette,
  Loader2,
  Check,
  Eye,
  Sparkles,
  ZapIcon
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const FORMAT_INFO = {
  pdf: {
    icon: FileText,
    name: 'PDF',
    description: 'Für professionelle Druckereien',
    color: 'text-red-600',
    recommended: true
  },
  png: {
    icon: FileImage,
    name: 'PNG',
    description: 'Hochauflösende Bilddatei',
    color: 'text-blue-600'
  },
  svg: {
    icon: Settings,
    name: 'SVG',
    description: 'Vektor-Format (skalierbar)',
    color: 'text-purple-600'
  }
};

const QUALITY_INFO = {
  web: { name: 'Web (72 DPI)', description: 'Für digitale Verwendung' },
  print: { name: 'Druck (300 DPI)', description: 'Standard-Druckqualität', recommended: true },
  high_end: { name: 'Premium (600 DPI)', description: 'Hochwertige Druckereien' }
};

const SIZE_INFO = {
  'standard_eu': { name: 'EU Standard (85×55mm)', description: 'Europäischer Standard', recommended: true },
  'standard_us': { name: 'US Standard (89×51mm)', description: 'Amerikanischer Standard' },
  'square': { name: 'Quadratisch (70×70mm)', description: 'Instagram-Style' },
  'mini': { name: 'Kompakt (70×42mm)', description: 'Kleinformat' },
  'large': { name: 'Groß (105×65mm)', description: 'Premium-Format' }
};

const PrintExporter = ({ businessCard, onClose }) => {
  const { toast } = useToast();
  
  // States
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [printSettings, setPrintSettings] = useState({
    format: 'pdf',
    quality: 'print', 
    size: 'standard_eu',
    orientation: 'landscape',
    include_bleed: true,
    include_crop_marks: true,
    double_sided: false,
    quantity: 100
  });
  const [preview, setPreview] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [printJob, setPrintJob] = useState(null);
  
  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, []);
  
  // Load preview when template or settings change
  useEffect(() => {
    if (selectedTemplate && businessCard) {
      generatePreview();
    }
  }, [selectedTemplate, printSettings.size, printSettings.orientation]);
  
  // Load print templates
  const loadTemplates = async () => {
    try {
      const response = await api.get('/print/templates');
      setTemplates(response.data.templates);
      
      // Select first template by default
      if (response.data.templates.length > 0) {
        setSelectedTemplate(response.data.templates[0]);
      }
      
    } catch (error) {
      console.error('Failed to load templates:', error);
      toast({
        title: "Fehler beim Laden",
        description: "Druckvorlagen konnten nicht geladen werden.",
        variant: "destructive"
      });
    }
  };
  
  // Generate preview
  const generatePreview = async () => {
    if (!selectedTemplate) return;
    
    try {
      const response = await api.post('/print/preview', {
        business_card_id: businessCard.id,
        template_id: selectedTemplate.id,
        size: printSettings.size,
        orientation: printSettings.orientation
      });
      
      setPreview(response.data.preview_url);
      
    } catch (error) {
      console.error('Preview generation failed:', error);
    }
  };
  
  // Export for printing
  const exportForPrinting = async () => {
    if (!selectedTemplate) {
      toast({
        title: "Vorlage auswählen",
        description: "Bitte wählen Sie zuerst eine Druckvorlage aus.",
        variant: "destructive"
      });
      return;
    }
    
    setExporting(true);
    
    try {
      const response = await api.post('/print/export', {
        business_card_id: businessCard.id,
        template_id: selectedTemplate.id,
        format: printSettings.format,
        quality: printSettings.quality,
        size: printSettings.size,
        orientation: printSettings.orientation,
        custom_colors: {},
        include_bleed: printSettings.include_bleed,
        include_crop_marks: printSettings.include_crop_marks,
        double_sided: printSettings.double_sided,
        quantity: printSettings.quantity
      });
      
      if (response.data.success) {
        setPrintJob(response.data);
        
        // Poll for job completion
        pollJobStatus(response.data.job_id);
        
        toast({
          title: "Export gestartet! 🖨️",
          description: "Ihre druckfertigen Dateien werden erstellt.",
        });
      }
      
    } catch (error) {
      console.error('Export failed:', error);
      toast({
        title: "Export fehlgeschlagen",
        description: "Die Druckdateien konnten nicht erstellt werden.",
        variant: "destructive"
      });
      setExporting(false);
    }
  };
  
  // Quick print (PDF with default settings)
  const quickPrint = async () => {
    setExporting(true);
    
    try {
      const response = await api.post('/print/quick', {
        business_card_id: businessCard.id,
        format: 'pdf',
        size: 'standard_eu',
        quality: 'print'
      });
      
      if (response.data.success) {
        setPrintJob(response.data);
        pollJobStatus(response.data.job_id);
        
        toast({
          title: "Schnelldruck gestartet! ⚡",
          description: "PDF wird mit Standard-Einstellungen erstellt.",
        });
      }
      
    } catch (error) {
      console.error('Quick print failed:', error);
      toast({
        title: "Schnelldruck fehlgeschlagen",
        description: "Die PDF konnte nicht erstellt werden.",
        variant: "destructive"
      });
      setExporting(false);
    }
  };
  
  // Poll job status
  const pollJobStatus = async (jobId, maxAttempts = 30) => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
        
        const response = await api.get(`/print/jobs/${jobId}`);
        const jobStatus = response.data;
        
        setPrintJob(prev => ({...prev, ...jobStatus}));
        
        if (jobStatus.status === 'completed') {
          toast({
            title: "Druckdateien fertig! 🎉",
            description: "Ihre professionellen Druckdateien stehen zum Download bereit.",
          });
          setExporting(false);
          break;
        } else if (jobStatus.status === 'failed') {
          toast({
            title: "Druckexport fehlgeschlagen",
            description: jobStatus.error_message || "Ein Fehler ist aufgetreten.",
            variant: "destructive"
          });
          setExporting(false);
          break;
        }
        
      } catch (error) {
        console.error('Status polling error:', error);
        if (attempt === maxAttempts - 1) {
          setExporting(false);
        }
      }
    }
  };
  
  // Download file
  const downloadFile = (url, filename) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'business_card.pdf';
    link.click();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Printer className="w-5 h-5 mr-2 text-blue-600" />
            Professioneller Druckexport
          </CardTitle>
          <CardDescription>
            Exportieren Sie "{businessCard.name}" als druckfertige Datei für Druckereien
          </CardDescription>
        </CardHeader>
      </Card>
      
      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Button
          onClick={quickPrint}
          disabled={exporting}
          className="h-20 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
        >
          <div className="flex flex-col items-center">
            <ZapIcon className="w-6 h-6 mb-1" />
            <span>Schnelldruck (PDF)</span>
            <span className="text-xs opacity-90">Standard EU-Format, 300 DPI</span>
          </div>
        </Button>
        
        <Button
          onClick={() => document.getElementById('advanced-settings').scrollIntoView()}
          variant="outline"
          className="h-20 border-2 border-dashed"
        >
          <div className="flex flex-col items-center">
            <Settings className="w-6 h-6 mb-1" />
            <span>Erweiterte Einstellungen</span>
            <span className="text-xs text-gray-600">Vorlagen, Formate, Qualität</span>
          </div>
        </Button>
      </div>
      
      {/* Template Selection */}
      <Card id="advanced-settings">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Palette className="w-5 h-5 mr-2" />
            Druckvorlagen
          </CardTitle>
          <CardDescription>
            Wählen Sie ein professionelles Design für Ihre Visitenkarte
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {templates.map((template) => (
              <div
                key={template.id}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedTemplate?.id === template.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedTemplate(template)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">{template.name}</h3>
                  {template.is_premium && (
                    <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                      <Sparkles className="w-3 h-3 mr-1" />
                      Premium
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{template.category}</span>
                  {template.is_premium && template.price && (
                    <span className="text-xs text-yellow-700">€{template.price}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      {/* Print Settings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Settings Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Druck-Einstellungen</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Format Selection */}
            <div>
              <label className="text-sm font-medium mb-3 block">Dateiformat</label>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(FORMAT_INFO).map(([format, info]) => {
                  const Icon = info.icon;
                  return (
                    <Button
                      key={format}
                      variant={printSettings.format === format ? "default" : "outline"}
                      className="h-16 flex flex-col"
                      onClick={() => setPrintSettings({...printSettings, format})}
                    >
                      <Icon className={`w-5 h-5 mb-1 ${info.color}`} />
                      <span className="text-xs">{info.name}</span>
                      {info.recommended && (
                        <Badge variant="secondary" className="text-xs">Empfohlen</Badge>
                      )}
                    </Button>
                  );
                })}
              </div>
            </div>
            
            {/* Quality Selection */}
            <div>
              <label className="text-sm font-medium mb-3 block">Druckqualität</label>
              <div className="space-y-2">
                {Object.entries(QUALITY_INFO).map(([quality, info]) => (
                  <div
                    key={quality}
                    className={`p-3 border rounded-lg cursor-pointer ${
                      printSettings.quality === quality 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setPrintSettings({...printSettings, quality})}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{info.name}</span>
                      {info.recommended && (
                        <Badge variant="secondary">Empfohlen</Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{info.description}</p>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Size Selection */}
            <div>
              <label className="text-sm font-medium mb-3 block">Kartengröße</label>
              <select
                value={printSettings.size}
                onChange={(e) => setPrintSettings({...printSettings, size: e.target.value})}
                className="w-full p-2 border rounded-lg"
              >
                {Object.entries(SIZE_INFO).map(([size, info]) => (
                  <option key={size} value={size}>
                    {info.name} - {info.description}
                  </option>
                ))}
              </select>
            </div>
            
            {/* Print Options */}
            <div className="space-y-3">
              <label className="text-sm font-medium block">Druckoptionen</label>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="bleed"
                  checked={printSettings.include_bleed}
                  onChange={(e) => setPrintSettings({...printSettings, include_bleed: e.target.checked})}
                />
                <label htmlFor="bleed" className="text-sm">Anschnitt hinzufügen (empfohlen)</label>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="cropmarks"
                  checked={printSettings.include_crop_marks}
                  onChange={(e) => setPrintSettings({...printSettings, include_crop_marks: e.target.checked})}
                />
                <label htmlFor="cropmarks" className="text-sm">Schnittmarken hinzufügen</label>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="doublesided"
                  checked={printSettings.double_sided}
                  onChange={(e) => setPrintSettings({...printSettings, double_sided: e.target.checked})}
                />
                <label htmlFor="doublesided" className="text-sm">Doppelseitig (Rückseite)</label>
              </div>
            </div>
            
            {/* Quantity */}
            <div>
              <label className="text-sm font-medium mb-2 block">Auflage</label>
              <select
                value={printSettings.quantity}
                onChange={(e) => setPrintSettings({...printSettings, quantity: parseInt(e.target.value)})}
                className="w-full p-2 border rounded-lg"
              >
                <option value={100}>100 Stück</option>
                <option value={250}>250 Stück</option>
                <option value={500}>500 Stück</option>
                <option value={1000}>1.000 Stück</option>
              </select>
            </div>
          </CardContent>
        </Card>
        
        {/* Preview Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Eye className="w-5 h-5 mr-2" />
              Vorschau
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-100 rounded-lg p-4 min-h-64 flex items-center justify-center">
              {preview ? (
                <img 
                  src={preview} 
                  alt="Print Preview"
                  className="max-w-full max-h-64 rounded border shadow-sm"
                />
              ) : (
                <div className="text-center text-gray-500">
                  <Eye className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Vorschau wird geladen...</p>
                </div>
              )}
            </div>
            
            {selectedTemplate && (
              <div className="mt-4 text-sm text-gray-600">
                <p><strong>Vorlage:</strong> {selectedTemplate.name}</p>
                <p><strong>Format:</strong> {FORMAT_INFO[printSettings.format].name}</p>
                <p><strong>Qualität:</strong> {QUALITY_INFO[printSettings.quality].name}</p>
                <p><strong>Größe:</strong> {SIZE_INFO[printSettings.size].name}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Export Actions */}
      <Card>
        <CardContent className="pt-6">
          {!printJob && (
            <div className="flex space-x-4">
              <Button
                onClick={exportForPrinting}
                disabled={exporting || !selectedTemplate}
                className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                {exporting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Wird exportiert...
                  </>
                ) : (
                  <>
                    <Printer className="w-4 h-4 mr-2" />
                    Druckdateien erstellen
                  </>
                )}
              </Button>
              
              <Button variant="outline" onClick={onClose}>
                Schließen
              </Button>
            </div>
          )}
          
          {/* Job Progress */}
          {printJob && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">Druckauftrag #{printJob.job_id?.slice(-8)}</h3>
                <Badge 
                  variant={printJob.status === 'completed' ? 'default' : 'secondary'}
                  className={printJob.status === 'completed' ? 'bg-green-100 text-green-800' : ''}
                >
                  {printJob.status === 'pending' ? 'Wartend' :
                   printJob.status === 'processing' ? 'Verarbeitung' :
                   printJob.status === 'completed' ? 'Fertig' :
                   printJob.status === 'failed' ? 'Fehler' : printJob.status}
                </Badge>
              </div>
              
              <Progress value={printJob.progress_percentage || 0} className="w-full" />
              
              {printJob.status === 'completed' && printJob.download_url && (
                <div className="flex space-x-4">
                  <Button
                    onClick={() => downloadFile(printJob.download_url, `${businessCard.name}_print.pdf`)}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Druckdateien herunterladen
                  </Button>
                  
                  <Button variant="outline" onClick={() => setPrintJob(null)}>
                    Neuer Export
                  </Button>
                </div>
              )}
              
              {printJob.status === 'failed' && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800">
                    {printJob.error_message || 'Druckexport fehlgeschlagen'}
                  </p>
                  <Button 
                    variant="outline" 
                    className="mt-2"
                    onClick={() => setPrintJob(null)}
                  >
                    Erneut versuchen
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PrintExporter;