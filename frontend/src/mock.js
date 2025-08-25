// Enhanced mock data for digital business card app
export const mockUser = {
  id: "1",
  name: "Max Mustermann",
  company: "Tech Solutions GmbH",
  position: "Senior Developer",
  description: "Spezialisiert auf moderne Webanwendungen und Cloud-Lösungen. Über 8 Jahre Erfahrung in Full-Stack-Entwicklung mit React, Node.js und AWS.",
  phones: [
    { id: 1, label: "Geschäftlich", number: "+49 123 456789", isPrimary: true },
    { id: 2, label: "Mobil", number: "+49 172 987654", isPrimary: false },
    { id: 3, label: "WhatsApp", number: "+49 172 987654", isPrimary: false }
  ],
  emails: [
    { id: 1, label: "Geschäftlich", address: "max.mustermann@techsolutions.de", isPrimary: true },
    { id: 2, label: "Privat", address: "max@example.com", isPrimary: false }
  ],
  website: "https://techsolutions.de",
  profileImage: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face",
  logo: "https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=200&h=200&fit=crop",
  socialMedia: {
    instagram: "max_tech",
    linkedin: "max-mustermann-dev",
    twitter: "max_dev_solutions",
    tiktok: "maxtech_tips",
    telegram: "max_tech_support"
  },
  isPublic: true,
  backgroundColor: "#ffffff",
  textColor: "#1f2937",
  accentColor: "#3b82f6",
  embedBackgroundColor: "#f8fafc", // For website embedding
  allowEmbedding: true,
  autoUpdateEnabled: true,
  lastUpdated: "2025-01-15T14:30:00Z",
  createdAt: "2025-01-15T10:30:00Z"
};

export const mockBusinessCards = [
  {
    id: "1",
    ...mockUser
  },
  {
    id: "2",
    name: "Sarah Weber",
    company: "Design Studio Berlin",
    position: "Creative Director",
    description: "Kreative Lösungen für Markenidentität und digitales Design. Führe ein Team von 12 Designern und arbeite mit internationalen Kunden.",
    phones: [
      { id: 1, label: "Büro", number: "+49 987 654321", isPrimary: true },
      { id: 2, label: "Mobil", number: "+49 175 123456", isPrimary: false }
    ],
    emails: [
      { id: 1, label: "Geschäftlich", address: "sarah@designstudio-berlin.com", isPrimary: true }
    ],
    website: "https://designstudio-berlin.com",
    profileImage: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop&crop=face",
    logo: "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=200&h=200&fit=crop",
    socialMedia: {
      instagram: "sarahdesigns_berlin",
      linkedin: "sarah-weber-creative",
      twitter: "sarah_creates",
      tiktok: "designwithsarah",
      telegram: "sarah_design_tips"
    },
    isPublic: false,
    backgroundColor: "#fef7ff",
    textColor: "#374151",
    accentColor: "#ec4899",
    embedBackgroundColor: "#fdf2f8",
    allowEmbedding: true,
    autoUpdateEnabled: true,
    lastUpdated: "2025-01-14T16:45:00Z",
    createdAt: "2025-01-14T14:20:00Z"
  }
];

// Mock functions
export const mockApi = {
  createBusinessCard: (cardData) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const newCard = {
          id: Date.now().toString(),
          ...cardData,
          lastUpdated: new Date().toISOString(),
          createdAt: new Date().toISOString()
        };
        mockBusinessCards.push(newCard);
        resolve(newCard);
      }, 500);
    });
  },

  updateBusinessCard: (id, cardData) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const index = mockBusinessCards.findIndex(card => card.id === id);
        if (index !== -1) {
          mockBusinessCards[index] = { 
            ...mockBusinessCards[index], 
            ...cardData, 
            lastUpdated: new Date().toISOString() 
          };
          // Mock notification for auto-updates
          if (mockBusinessCards[index].autoUpdateEnabled) {
            console.log('📱 Auto-Update Benachrichtigung: Kontaktdaten wurden aktualisiert und an alle Empfänger gesendet.');
          }
          resolve(mockBusinessCards[index]);
        }
        resolve(null);
      }, 500);
    });
  },

  getBusinessCard: (id) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const card = mockBusinessCards.find(card => card.id === id);
        resolve(card || null);
      }, 300);
    });
  },

  generateQRCode: (cardId) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://mydigitalcard.app/card/${cardId}`);
      }, 200);
    });
  },

  generateVCard: (cardData) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        let vcard = `BEGIN:VCARD
VERSION:3.0
FN:${cardData.name}
ORG:${cardData.company}
TITLE:${cardData.position}`;

        // Add multiple phone numbers
        if (cardData.phones) {
          cardData.phones.forEach(phone => {
            vcard += `\nTEL;TYPE=${phone.label}:${phone.number}`;
          });
        }

        // Add multiple email addresses  
        if (cardData.emails) {
          cardData.emails.forEach(email => {
            vcard += `\nEMAIL;TYPE=${email.label}:${email.address}`;
          });
        }

        if (cardData.website) {
          vcard += `\nURL:${cardData.website}`;
        }

        if (cardData.description) {
          vcard += `\nNOTE:${cardData.description}`;
        }

        vcard += '\nEND:VCARD';
        resolve(vcard);
      }, 200);
    });
  },

  generateEmbedCode: (cardId, options = {}) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const embedCode = `<iframe 
  src="https://mydigitalcard.app/embed/${cardId}" 
  width="${options.width || '320'}" 
  height="${options.height || '400'}"
  style="border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"
  frameborder="0">
</iframe>`;
        resolve(embedCode);
      }, 200);
    });
  },

  trackCardUpdate: (cardId) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        // Mock update tracking
        resolve({
          updatesSent: 47,
          deliveryRate: 94.5,
          lastUpdate: new Date().toISOString()
        });
      }, 300);
    });
  }
};