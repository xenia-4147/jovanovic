import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Checkbox } from './ui/checkbox';
import { Plus, Trash2, Star, MessageSquare, Settings } from 'lucide-react';

const MultiContactInput = ({ 
  type = 'phone', 
  items = [], 
  onChange, 
  title,
  placeholder,
  labels = [] 
}) => {
  const defaultLabels = type === 'phone' 
    ? ['Geschäftlich', 'Mobil', 'WhatsApp', 'Privat', 'Festnetz']
    : ['Geschäftlich', 'Privat', 'Support', 'Info'];

  const availableLabels = labels.length > 0 ? labels : defaultLabels;

  const addItem = () => {
    const newItem = {
      id: Date.now(),
      label: availableLabels[0],
      [type === 'phone' ? 'number' : 'address']: '',
      isPrimary: items.length === 0,
      // Add default messaging apps for phone numbers
      ...(type === 'phone' && {
        messaging_apps: [
          { name: 'whatsapp', enabled: true },
          { name: 'sms', enabled: true }
        ]
      })
    };
    onChange([...items, newItem]);
  };

  const updateItem = (id, field, value) => {
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

  const removeItem = (id) => {
    const filteredItems = items.filter(item => item.id !== id);
    // If we removed the primary item, make the first one primary
    if (filteredItems.length > 0 && !filteredItems.some(item => item.isPrimary)) {
      filteredItems[0].isPrimary = true;
    }
    onChange(filteredItems);
  };

  const fieldName = type === 'phone' ? 'number' : 'address';
  const fieldType = type === 'phone' ? 'tel' : 'email';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label className="text-base font-medium">{title}</Label>
        <Button type="button" onClick={addItem} size="sm" variant="outline">
          <Plus className="w-4 h-4 mr-2" />
          Hinzufügen
        </Button>
      </div>
      
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="flex items-center space-x-3 p-3 border rounded-lg bg-gray-50">
            <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
              <Select 
                value={item.label} 
                onValueChange={(value) => updateItem(item.id, 'label', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableLabels.map(label => (
                    <SelectItem key={label} value={label}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <div className="md:col-span-2 relative">
                <Input
                  type={fieldType}
                  value={item[fieldName]}
                  onChange={(e) => updateItem(item.id, fieldName, e.target.value)}
                  placeholder={placeholder}
                  className="pr-12"
                />
                {item.isPrimary && (
                  <Badge 
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-yellow-100 text-yellow-800 border-yellow-300"
                    variant="secondary"
                  >
                    <Star className="w-3 h-3 mr-1" />
                    Primär
                  </Badge>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                type="button"
                size="sm"
                variant={item.isPrimary ? "default" : "ghost"}
                onClick={() => updateItem(item.id, 'isPrimary', !item.isPrimary)}
                className="h-8 w-8 p-0"
              >
                <Star className={`w-4 h-4 ${item.isPrimary ? 'fill-current' : ''}`} />
              </Button>
              
              {items.length > 1 && (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={() => removeItem(item.id)}
                  className="h-8 w-8 p-0 text-red-500 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        ))}
        
        {items.length === 0 && (
          <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-300 rounded-lg">
            <p>Noch keine {title.toLowerCase()} hinzugefügt</p>
            <Button type="button" onClick={addItem} size="sm" variant="outline" className="mt-2">
              <Plus className="w-4 h-4 mr-2" />
              Erste {title.toLowerCase().slice(0, -1)} hinzufügen
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MultiContactInput;