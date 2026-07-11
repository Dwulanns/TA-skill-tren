import React, { createContext, useContext, useState, useEffect } from "react";

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem("theme-mode");
    if (saved) {
      return saved === "dark";
    }
    // Default ke dark jika tidak ada preference
    return true;
  });

  useEffect(() => {
    localStorage.setItem("theme-mode", isDark ? "dark" : "light");
    const root = document.documentElement;

    // Only set data-theme attribute - CSS variables will handle the colors
    if (isDark) {
      root.setAttribute("data-theme", "dark");
    } else {
      root.setAttribute("data-theme", "light");
    }
  }, [isDark]);

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  const theme = {
    isDark,
    toggleTheme,
    colors: isDark ? darkColors : lightColors,
  };

  return (
    <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
};

// Dark Theme Colors - Modern & Professional with High Contrast
const darkColors = {
  bg: {
    primary: "#0a0e17", // Very dark navy (darkened for better contrast)
    secondary: "#141a26", // Dark blue-gray card (darkened)
    tertiary: "#1f2737", // Slightly lighter for hover
    hover: "#2d3748", // Hover state
  },
  text: {
    primary: "#f8fafc", // Nearly pure white (improved contrast)
    secondary: "#e2e8f0", // Very light gray (improved from #cbd5e0)
    tertiary: "#cbd5e0", // Medium light gray (improved from #a0aec0)
  },
  accent: {
    primary: "#60a5fa", // Bright blue (more visible)
    secondary: "#93c5fd", // Light blue (more visible)
    danger: "#ff6b6b", // Red (more vivid)
    success: "#34d399", // Green (more vivid)
    warning: "#fbbf24", // Amber (more vivid)
  },
  border: "#475569", // Slate border (slightly lighter)
  divider: "#334155", // Divider color (lighter)
};

// Light Theme Colors - Clean & Minimalist with High Contrast
const lightColors = {
  bg: {
    primary: "#f9fafb", // Very light gray
    secondary: "#ffffff", // White for cards
    tertiary: "#f3f4f6", // Light gray for hover
    hover: "#eff2f5", // Hover state
  },
  text: {
    primary: "#0f172a", // Almost black (full contrast)
    secondary: "#1e293b", // Dark gray (improved from #475569 for better contrast)
    tertiary: "#475569", // Medium gray (improved)
  },
  accent: {
    primary: "#1e40af", // Deep blue (darker for better visibility)
    secondary: "#3b82f6", // Medium blue
    danger: "#dc2626", // Deep red
    success: "#059669", // Deep green
    warning: "#d97706", // Deep amber
  },
  border: "#d1d5db", // Light gray border (darker)
  divider: "#e5e7eb", // Light divider (slightly darker)
};
