import React from "react";
import ReactDOM from "react-dom/client";
import { ChakraProvider, extendTheme, useColorMode } from "@chakra-ui/react";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { ThemeProvider } from "./context/ThemeContext";
import { useTheme } from "./context/ThemeContext";
import "./index.css";

// Apply dark mode immediately on page load to prevent white flash
const savedTheme = localStorage.getItem("theme-mode") || "dark";
const root = document.documentElement;

// Only set data-theme attribute - let CSS variables handle colors
root.setAttribute("data-theme", savedTheme);

function ChakraColorModeSync() {
  const { isDark } = useTheme();
  const { colorMode, setColorMode } = useColorMode();

  React.useEffect(() => {
    const target = isDark ? "dark" : "light";
    if (colorMode !== target) setColorMode(target);
  }, [isDark, colorMode, setColorMode]);

  return null;
}

const theme = extendTheme({
  config: {
    initialColorMode: savedTheme,
    useSystemColorMode: false,
  },
  colors: {
    brand: {
      50: "#e3f2fd",
      100: "#bbdefb",
      500: "#2196f3",
      600: "#1e88e5",
      700: "#1976d2",
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ThemeProvider>
      <ChakraProvider theme={theme}>
        <ChakraColorModeSync />
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ChakraProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
