import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Progress } from '../components/ui/progress';
import { 
  ArrowLeft, 
  Upload, 
  Users, 
  Smartphone, 
  Cloud, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  Download,
  Sync,
  Settings,
  Trash2,
  Play,
  Pause,
  RefreshCw
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const ContactImportPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [activeTab, setActiveTab] = useState('sources'); // sources, import, unified
  const [contactSources, setContactSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [unifiedContacts, setUnifiedContacts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadContactSources();
    if (activeTab === 'unified') {
      loadUnifiedContacts();
    }
  }, [activeTab]);

  const loadContactSources = async () => {
    setLoading(true);
    try {
      const response = await api.get('/contacts/sources');
      setContactSources(response.data);
    } catch (error) {
      console.error('Failed to load contact sources:', error);
      toast({
        variant: "destructive",
        title: "Fehler",
        description: "Kontaktquellen konnten nicht geladen werden."
      });
    } finally {
      setLoading(false);
    }
  };

  const loadUnifiedContacts = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/contacts/unified?search=${encodeURIComponent(searchQuery)}&limit=100`);
      setUnifiedContacts(response.data);
    } catch (error) {
      console.error('Failed to load contacts:', error);
      toast({
        variant: "destructive",
        title: "Fehler",
        description: "Kontakte konnten nicht geladen werden."
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event, sourceType) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setImporting(true);

    try {
      for (const file of files) {
        const fileContent = await fileToBase64(file);
        
        const importRequest = {
          source_type: sourceType,
          display_name: `${sourceType.toUpperCase()} Import (${file.name})`,
          file_content: fileContent.split(',')[1], // Remove data URL prefix
          file_name: file.name
        };

        const response = await api.post('/contacts/import', importRequest);

        if (response.data.success) {
          toast({
            title: "Import erfolgreich!",
            description: `${response.data.contacts_imported} Kontakte aus ${file.name} importiert.`
          });
        } else {
          toast({
            variant: "destructive",
            title: "Import fehlgeschlagen",
            description: response.data.message
          });
        }
      }

      // Reload sources
      await loadContactSources();
      
    } catch (error) {
      console.error('File import failed:', error);
      toast({
        variant: "destructive",
        title: "Import fehlgeschlagen",
        description: error.response?.data?.detail || "Datei-Import ist fehlgeschlagen."
      });
    } finally {
      setImporting(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const handleContactPickerImport = async () => {
    if (!('contacts' in navigator)) {
      toast({
        variant: "destructive",
        title: "Nicht unterstützt",
        description: "Ihr Browser unterstützt die Contact Picker API nicht."
      });
      return;
    }

    try {
      setImporting(true);
      
      const contacts = await navigator.contacts.select(['name', 'email', 'tel'], { multiple: true });
      
      if (contacts.length === 0) {
        toast({
          title: "Keine Kontakte ausgewählt",
          description: "Sie haben keine Kontakte zum Import ausgewählt."
        });
        return;
      }

      const importRequest = {
        source_type: 'contact_picker',
        display_name: `Browser Kontakte (${contacts.length} Kontakte)`,
        contacts_data: contacts
      };

      const response = await api.post('/contacts/import', importRequest);

      if (response.data.success) {
        toast({
          title: "Import erfolgreich!",
          description: `${response.data.contacts_imported} Kontakte aus Ihrem Browser importiert.`
        });
        await loadContactSources();
      } else {
        toast({
          variant: "destructive", 
          title: "Import fehlgeschlagen",
          description: response.data.message
        });
      }

    } catch (error) {
      console.error('Contact picker import failed:', error);
      toast({
        variant: "destructive",
        title: "Import fehlgeschlagen", 
        description: "Browser-Kontakte konnten nicht importiert werden."
      });
    } finally {
      setImporting(false);
    }
  };

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const formatLastSync = (date) => {
    if (!date) return 'Nie';
    return new Date(date).toLocaleString('de-DE');
  };

  const getSourceIcon = (sourceType) => {
    switch (sourceType) {
      case 'google_contacts': return '📧';
      case 'apple_icloud': return '☁️';
      case 'contact_picker': return '🌐';
      case 'vcf_file': return '📁';
      case 'csv_file': return '📊';
      default: return '📱';
    }
  };

  const getSourceDisplayName = (sourceType) => {
    switch (sourceType) {
      case 'google_contacts': return 'Google Kontakte';
      case 'apple_icloud': return 'Apple iCloud';
      case 'contact_picker': return 'Browser Kontakte';
      case 'vcf_file': return 'VCF Datei';
      case 'csv_file': return 'CSV Datei';
      default: return sourceType;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'disabled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Zurück zum Dashboard
          </Button>
          
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
              Kontakt-Import & Synchronisation
            </h1>
            <p className="text-gray-600">
              Importieren Sie Ihre Kontakte aus verschiedenen Quellen für eine einheitliche Kommunikation
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-2 p-1 bg-gray-100 rounded-lg mb-8">
          <Button
            variant={activeTab === 'sources' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('sources')}
            className="flex-1"
          >
            <Cloud className="w-4 h-4 mr-2" />
            Kontaktquellen
          </Button>
          <Button
            variant={activeTab === 'import' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('import')}
            className="flex-1"
          >
            <Upload className="w-4 h-4 mr-2" />
            Import
          </Button>
          <Button
            variant={activeTab === 'unified' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('unified')}
            className="flex-1"
          >
            <Users className="w-4 h-4 mr-2" />
            Alle Kontakte
          </Button>
        </div>

        {/* Content */}
        {activeTab === 'sources' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Konfigurierte Kontaktquellen</CardTitle>
                <CardDescription>
                  Übersicht aller Ihrer Kontaktquellen und deren Synchronisationsstatus
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p>Lade Kontaktquellen...</p>
                  </div>
                ) : contactSources.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Cloud className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>Noch keine Kontaktquellen konfiguriert</p>
                    <p className="text-sm">Wechseln Sie zum Import-Tab, um Kontakte hinzuzufügen</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {contactSources.map((source) => (
                      <div key={source.id} className="border rounded-lg p-4 bg-white">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <span className="text-2xl">{getSourceIcon(source.source_type)}</span>
                            <div>
                              <h3 className="font-medium">{source.display_name}</h3>
                              <p className="text-sm text-gray-600">{getSourceDisplayName(source.source_type)}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Badge className={getStatusColor(source.sync_status)}>
                              {source.sync_status === 'active' ? 'Aktiv' : 
                               source.sync_status === 'paused' ? 'Pausiert' : 
                               source.sync_status === 'error' ? 'Fehler' : 'Deaktiviert'}
                            </Badge>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                          <div>
                            <span className="font-medium">Kontakte:</span>
                            <div>{source.total_contacts_imported}</div>
                          </div>
                          <div>
                            <span className="font-medium">Letzte Sync:</span>
                            <div>{formatLastSync(source.last_sync_at)}</div>
                          </div>
                          <div>
                            <span className="font-medium">Nächste Sync:</span>
                            <div>{formatLastSync(source.next_sync_at)}</div>
                          </div>
                          <div>
                            <span className="font-medium">Status:</span>
                            <div>{source.sync_enabled ? 'Synchronisation aktiv' : 'Synchronisation deaktiviert'}</div>
                          </div>
                        </div>
                        
                        {source.last_error_message && (
                          <Alert variant="destructive" className="mt-3">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>{source.last_error_message}</AlertDescription>
                          </Alert>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'import' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Contact Picker */}
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Smartphone className="w-5 h-5 mr-2 text-blue-600" />
                  Browser Kontakte
                </CardTitle>
                <CardDescription>
                  Importieren Sie Kontakte direkt aus Ihrem Browser (moderne Browser)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  onClick={handleContactPickerImport}
                  disabled={importing || !('contacts' in navigator)}
                  className="w-full"
                >
                  {importing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Importiere...
                    </>
                  ) : (
                    <>
                      <Smartphone className="w-4 h-4 mr-2" />
                      Kontakte auswählen
                    </>
                  )}
                </Button>
                {!('contacts' in navigator) && (
                  <p className="text-xs text-gray-500 mt-2">
                    Ihr Browser unterstützt diese Funktion nicht.
                  </p>
                )}
              </CardContent>
            </Card>

            {/* VCF File Import */}
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-green-600" />
                  VCF Dateien
                </CardTitle>
                <CardDescription>
                  Importieren Sie .vcf (vCard) Dateien von anderen Geräten oder Apps
                </CardDescription>
              </CardHeader>
              <CardContent>
                <input
                  type="file"
                  accept=".vcf"
                  multiple
                  onChange={(e) => handleFileUpload(e, 'vcf_file')}
                  className="hidden"
                  id="vcf-upload"
                />
                <Button 
                  onClick={() => document.getElementById('vcf-upload').click()}
                  disabled={importing}
                  className="w-full bg-green-600 hover:bg-green-700"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  VCF Dateien auswählen
                </Button>
              </CardContent>
            </Card>

            {/* CSV File Import */}
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-orange-600" />
                  CSV Dateien
                </CardTitle>
                <CardDescription>
                  Importieren Sie Kontakte aus Excel oder anderen CSV-Exporten
                </CardDescription>
              </CardHeader>
              <CardContent>
                <input
                  type="file"
                  accept=".csv"
                  multiple
                  onChange={(e) => handleFileUpload(e, 'csv_file')}
                  className="hidden"
                  id="csv-upload"
                />
                <Button 
                  onClick={() => document.getElementById('csv-upload').click()}
                  disabled={importing}
                  className="w-full bg-orange-600 hover:bg-orange-700"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  CSV Dateien auswählen
                </Button>
              </CardContent>
            </Card>

            {/* Google Contacts - Coming Soon */}
            <Card className="hover:shadow-lg transition-shadow opacity-75">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <span className="text-lg mr-2">📧</span>
                  Google Kontakte
                </CardTitle>
                <CardDescription>
                  Synchronisation mit Google Contacts (Coming Soon)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button disabled className="w-full">
                  <Cloud className="w-4 h-4 mr-2" />
                  Bald verfügbar
                </Button>
              </CardContent>
            </Card>

            {/* Apple iCloud - Coming Soon */}
            <Card className="hover:shadow-lg transition-shadow opacity-75">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <span className="text-lg mr-2">☁️</span>
                  Apple iCloud
                </CardTitle>
                <CardDescription>
                  Synchronisation mit iCloud Kontakten (Coming Soon)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button disabled className="w-full">
                  <Cloud className="w-4 h-4 mr-2" />
                  Bald verfügbar
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'unified' && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Alle Kontakte</CardTitle>
                  <CardDescription>
                    Vereinte Ansicht aller Ihrer Visitenkarten und importierten Kontakte
                  </CardDescription>
                </div>
                <Button onClick={loadUnifiedContacts} variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Aktualisieren
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Search */}
              <div className="mb-6">
                <Input
                  type="text"
                  placeholder="Kontakte durchsuchen..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && loadUnifiedContacts()}
                />
              </div>

              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p>Lade Kontakte...</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {unifiedContacts.map((contact) => (
                    <div key={`${contact.source_type}-${contact.id}`} className="flex items-center justify-between p-4 border rounded-lg bg-white hover:shadow-md transition-shadow">
                      <div className="flex items-center space-x-4">
                        <img
                          src={contact.profile_image || `https://ui-avatars.com/api/?name=${encodeURIComponent(contact.name)}&background=6366f1&color=fff`}
                          alt={contact.name}
                          className="w-10 h-10 rounded-full"
                        />
                        <div>
                          <h3 className="font-medium">{contact.name}</h3>
                          <div className="flex items-center space-x-2 text-sm text-gray-600">
                            {contact.company && <span>{contact.company}</span>}
                            {contact.position && <span>• {contact.position}</span>}
                          </div>
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <Badge variant="secondary" className="text-xs">
                              {contact.is_business_card ? 'Visitenkarte' : 'Importierter Kontakt'}
                            </Badge>
                            {contact.phones.length > 0 && (
                              <span>{contact.phones.length} Telefon{contact.phones.length !== 1 ? 'nummern' : 'nummer'}</span>
                            )}
                            {contact.emails.length > 0 && (
                              <span>{contact.emails.length} E-Mail{contact.emails.length !== 1 ? 's' : ''}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            if (contact.is_business_card) {
                              navigate(`/card/${contact.id}`);
                            } else {
                              // Handle imported contact view
                              toast({
                                title: "Kontakt-Details",
                                description: `${contact.name} aus ${contact.external_source}`
                              });
                            }
                          }}
                        >
                          <Users className="w-3 h-3 mr-1" />
                          Details
                        </Button>
                      </div>
                    </div>
                  ))}
                  
                  {unifiedContacts.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p>Keine Kontakte gefunden</p>
                      <p className="text-sm">
                        {searchQuery ? 'Versuchen Sie andere Suchbegriffe' : 'Importieren Sie Kontakte über den Import-Tab'}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ContactImportPage;