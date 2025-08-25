// Mock data for digital business card app
export const mockUser = {
  id: "1",
  name: "Max Mustermann",
  company: "Tech Solutions GmbH",
  position: "Senior Developer",
  phone: "+49 123 456789",
  email: "max.mustermann@techsolutions.de",
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
    phone: "+49 987 654321",
    email: "sarah@designstudio-berlin.com",
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
          mockBusinessCards[index] = { ...mockBusinessCards[index], ...cardData };
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
        // Mock QR code URL
        resolve(`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://mydigitalcard.app/card/${cardId}`);
      }, 200);
    });
  },

  generateVCard: (cardData) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const vcard = `BEGIN:VCARD
VERSION:3.0
FN:${cardData.name}
ORG:${cardData.company}
TITLE:${cardData.position}
TEL:${cardData.phone}
EMAIL:${cardData.email}
URL:${cardData.website}
END:VCARD`;
        resolve(vcard);
      }, 200);
    });
  }
};