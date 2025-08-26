import React from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Plus, Trash2, Star, MapPin, Navigation } from 'lucide-react';

const AddressInput = ({ 
  items = [], 
  onChange, 
  title = "Adressen"
}) => {
  const addressLabels = ['Geschäftlich', 'Privat', 'Hauptsitz', 'Filiale', 'Homeoffice', 'Lieferadresse'];
  const countries = ['Deutschland', 'Österreich', 'Schweiz', 'Niederlande', 'Frankreich', 'Italien', 'Spanien', 'USA', 'Kanada'];

  const addAddress = () => {
    const newAddress = {
      id: Date.now().toString(),
      label: addressLabels[0],
      street: '',
      houseNumber: '',
      postalCode: '',
      city: '',
      state: '',
      country: 'Deutschland',
      isPrimary: items.length === 0
    };
    onChange([...items, newAddress]);
  };

  const updateAddress = (id, field, value) => {
    const updatedItems = items.map(item => {
      if (item.id === id) {
        let updatedItem = { ...item, [field]: value };
        
        // If setting as primary, unset others
        if (field === 'isPrimary' && value) {
          onChange(items.map(i => ({ ...i, isPrimary: i.id === id })));
          return updatedItem;
        }
        
        return updatedItem;
      }
      return item;
    });
    
    if (field !== 'isPrimary') {
      onChange(updatedItems);
    }
  };

  const removeAddress = (id) => {
    const filteredItems = items.filter(item => item.id !== id);
    // If we removed the primary item, make the first one primary
    if (filteredItems.length > 0 && !filteredItems.some(item => item.isPrimary)) {
      filteredItems[0].isPrimary = true;
    }
    onChange(filteredItems);
  };

  const getFullAddress = (address) => {
    const parts = [
      address.street && address.houseNumber ? `${address.street} ${address.houseNumber}` : address.street,
      address.postalCode && address.city ? `${address.postalCode} ${address.city}` : address.city,
      address.state,
      address.country
    ].filter(Boolean);
    
    return parts.join(', ');
  };

  const openInMaps = (address) => {
    const fullAddress = getFullAddress(address);
    if (fullAddress) {
      const encodedAddress = encodeURIComponent(fullAddress);
      // Open Google Maps with the address
      window.open(`https://www.google.com/maps/search/?api=1&query=${encodedAddress}`, '_blank');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label className="text-base font-medium">{title}</Label>
        <Button type="button" onClick={addAddress} size="sm" variant="outline">
          <Plus className="w-4 h-4 mr-2" />
          Hinzufügen
        </Button>
      </div>
      
      <div className="space-y-4">
        {items.map((address) => (
          <div key={address.id} className="p-4 border rounded-lg bg-gray-50 space-y-3">
            <div className="flex items-center justify-between">
              <Select 
                value={address.label} 
                onValueChange={(value) => updateAddress(address.id, 'label', value)}
              >
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {addressLabels.map(label => (
                    <SelectItem key={label} value={label}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <div className="flex items-center space-x-2">
                {address.isPrimary && (
                  <Badge className="bg-yellow-100 text-yellow-800 border-yellow-300">
                    <Star className="w-3 h-3 mr-1" />
                    Primär
                  </Badge>
                )}
                
                <Button
                  type="button"
                  size="sm"
                  variant={address.isPrimary ? "default" : "ghost"}
                  onClick={() => updateAddress(address.id, 'isPrimary', !address.isPrimary)}
                  className="h-8 w-8 p-0"
                >
                  <Star className={`w-4 h-4 ${address.isPrimary ? 'fill-current' : ''}`} />
                </Button>
                
                {items.length > 1 && (
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() => removeAddress(address.id)}
                    className="h-8 w-8 p-0 text-red-500 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div className="md:col-span-2">
                <Label htmlFor={`street-${address.id}`}>Straße</Label>
                <Input
                  id={`street-${address.id}`}
                  value={address.street}
                  onChange={(e) => updateAddress(address.id, 'street', e.target.value)}
                  placeholder="Musterstraße"
                />
              </div>
              
              <div>
                <Label htmlFor={`houseNumber-${address.id}`}>Hausnummer</Label>
                <Input
                  id={`houseNumber-${address.id}`}
                  value={address.houseNumber}
                  onChange={(e) => updateAddress(address.id, 'houseNumber', e.target.value)}
                  placeholder="123a"
                />
              </div>
              
              <div>
                <Label htmlFor={`postalCode-${address.id}`}>PLZ</Label>
                <Input
                  id={`postalCode-${address.id}`}
                  value={address.postalCode}
                  onChange={(e) => updateAddress(address.id, 'postalCode', e.target.value)}
                  placeholder="12345"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <Label htmlFor={`city-${address.id}`}>Stadt</Label>
                <Input
                  id={`city-${address.id}`}
                  value={address.city}
                  onChange={(e) => updateAddress(address.id, 'city', e.target.value)}
                  placeholder="Berlin"
                />
              </div>
              
              <div>
                <Label htmlFor={`state-${address.id}`}>Bundesland/Staat</Label>
                <Input
                  id={`state-${address.id}`}
                  value={address.state}
                  onChange={(e) => updateAddress(address.id, 'state', e.target.value)}
                  placeholder="Berlin"
                />
              </div>
              
              <div>
                <Label htmlFor={`country-${address.id}`}>Land</Label>
                <Select 
                  value={address.country} 
                  onValueChange={(value) => updateAddress(address.id, 'country', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {countries.map(country => (
                      <SelectItem key={country} value={country}>{country}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {/* Address Preview & Navigation */}
            {getFullAddress(address) && (
              <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-700">{getFullAddress(address)}</span>
                </div>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => openInMaps(address)}
                  className="h-8"
                >
                  <Navigation className="w-4 h-4 mr-1" />
                  Navigieren
                </Button>
              </div>
            )}
          </div>
        ))}
        
        {items.length === 0 && (
          <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-300 rounded-lg">
            <MapPin className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>Noch keine Adressen hinzugefügt</p>
            <Button type="button" onClick={addAddress} size="sm" variant="outline" className="mt-2">
              <Plus className="w-4 h-4 mr-2" />
              Erste Adresse hinzufügen
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AddressInput;