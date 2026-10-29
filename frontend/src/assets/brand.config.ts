/**
 * SSK Collections Brand Asset Configuration
 * Centralized configuration for logo, typography, colors, and identity.
 * Replace `customLogoImage` with your uploaded PNG/JPEG path to override SVG without touching components.
 */
export const BRAND_CONFIG = {
  name: "Sree Sai Krishna Collections",
  shortName: "SSK",
  tagline: "Exclusive Women's Jewellery & Fashion Accessories",
  foundedYear: 2024,
  // If user provides a static image path (e.g. '/custom-ssk-logo.png'), it will be rendered instead of the SVG
  customLogoImage: null as string | null,
  
  colors: {
    primaryNavy: "#123F7A",
    deepNavy: "#082B55",
    royalBlue: "#1769AA",
    lightBlue: "#EAF3FC",
    backgroundWhite: "#FFFFFF",
    gridBackground: "#F7F9FC",
    premiumGold: "#C89A43",
    goldLight: "#E5B963",
    goldDark: "#A37728",
    darkText: "#1D2939",
    secondaryText: "#667085",
    borders: "#E4EAF2",
    success: "#15803D",
    warning: "#B7791F",
    error: "#DC2626"
  },
  
  contact: {
    phone: "+91 98480 22338",
    whatsapp: "+91 98480 22338",
    email: "support@sreesaikrishnacollections.com",
    address: "Shop #12, Sri Krishna Temple Street, Near Clock Tower, Secunderabad, Telangana - 500003, India"
  },
  
  social: {
    instagram: "https://instagram.com/sreesaikrishnacollections",
    facebook: "https://facebook.com/sreesaikrishnacollections",
    youtube: "https://youtube.com/@sreesaikrishnacollections"
  }
};
