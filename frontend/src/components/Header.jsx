import {
  Box,
  HStack,
  IconButton,
  Heading,
  Link as ChakraLink,
  Button,
  Badge,
  Text,
} from "@chakra-ui/react";
import { Link as RouterLink, useLocation } from "react-router-dom";
import { HamburgerIcon } from "@chakra-ui/icons";
import { useSidebar } from "../context/SidebarContext";
import { useTheme } from "../context/ThemeContext";

/**
 * UNIFIED HEADER
 * Uses ONE state system (useSidebar) for all pages
 * No more separate admin sidebar context
 */
export default function Header({
  isLanding = false,
  showAdminBadge = false,
  zIndex = 100,
}) {
  const { setIsOpen } = useSidebar();
  const { isDark, toggleTheme } = useTheme();
  const location = useLocation();

  if (isLanding) {
    return (
      <Box
        as="nav"
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        px={{ base: "1rem", md: "1.5rem" }}
        py={{ base: "0.75rem", md: "0.875rem" }}
        bg={isDark ? "#0f172a" : "#ffffff"}
        borderBottom={isDark ? "2px solid #334155" : "2px solid #cbd5e0"}
        position="fixed"
        top={0}
        left={0}
        right={0}
        zIndex={1000}
        boxShadow="0 2px 8px rgba(0,0,0,0.1)"
        transition="all 0.3s ease"
      >
        {/* Logo */}
        <ChakraLink as={RouterLink} to="/" _hover={{ textDecoration: "none" }}>
          <Heading
            size="md"
            fontWeight="900"
            color="var(--accent-primary)"
            fontSize={{ base: "1.25rem", md: "1.5rem" }}
          >
            Skill Insight
          </Heading>
        </ChakraLink>

        {/* Menu Items */}
        <HStack
          spacing={8}
          alignItems="center"
          display={{ base: "none", md: "flex" }}
        >
          <ChakraLink
            as={RouterLink}
            to="/dashboard"
            fontWeight="700"
            fontSize={{ base: "sm", md: "md" }}
            color={isDark ? "#f1f5f9" : "#0f172a"}
            _hover={{
              color: "var(--accent-primary)",
              textDecoration: "none",
            }}
            transition="color 0.2s ease"
          >
            Dashboard
          </ChakraLink>

          <ChakraLink
            as={RouterLink}
            to="/manual"
            fontWeight="700"
            fontSize={{ base: "sm", md: "md" }}
            color={isDark ? "#f1f5f9" : "#0f172a"}
            _hover={{
              color: location.pathname === "/manual" ? "#ffffff" : "var(--accent-primary)",
              textDecoration: "none",
            }}
            transition="color 0.2s ease"
          >
            Panduan
          </ChakraLink>

          {/* Dark Mode Toggle */}
          <Button
            onClick={toggleTheme}
            bg={isDark ? "#1e293b" : "#f8fafc"}
            border={isDark ? "2px solid #475569" : "2px solid #cbd5e0"}
            color={isDark ? "#f1f5f9" : "#0f172a"}
            px={5}
            py={2.5}
            borderRadius="lg"
            cursor="pointer"
            fontSize="sm"
            fontWeight="700"
            _hover={{
              bg: isDark ? "#334155" : "#f1f5f9",
            }}
            transition="all 0.2s ease"
          >
            <HStack spacing={2}>
              <Box fontSize="lg">{isDark ? "☀️" : "🌙"}</Box>
              <Box fontWeight="600">{isDark ? "Light Mode" : "Dark Mode"}</Box>
            </HStack>
          </Button>
        </HStack>

        {/* Mobile Menu */}
        <HStack display={{ base: "flex", md: "none" }} spacing={2}>
          <Button
            onClick={toggleTheme}
            bg={isDark ? "#1e293b" : "#f8fafc"}
            border={isDark ? "1px solid #334155" : "1px solid #e2e8f0"}
            color={isDark ? "#f1f5f9" : "#0f172a"}
            px={3}
            py={2}
            borderRadius="lg"
            fontSize="sm"
            _hover={{
              bg: isDark ? "#334155" : "#f1f5f9",
            }}
            transition="all 0.2s ease"
          >
            <HStack spacing={1}>
              <Box fontSize="lg">{isDark ? "☀️" : "🌙"}</Box>
              <Box fontWeight="600">{isDark ? "Light" : "Dark"}</Box>
            </HStack>
          </Button>
        </HStack>
      </Box>
    );
  }

  // Dashboard Header
  return (
    <Box
      as="nav"
      display="flex"
      justifyContent="flex-start"
      alignItems="center"
      px={{ base: 2, md: 4 }}
      py={4}
      bg={isDark ? "#0f172a" : "#ffffff"}
      borderBottom={isDark ? "1px solid #1e293b" : "1px solid #e2e8f0"}
      position="fixed"
      top={0}
      left={0}
      right={0}
      zIndex="1000"
    >
      {/* Logo Section */}
      <HStack spacing={2}>
        <IconButton
          icon={<HamburgerIcon />}
          variant="ghost"
          onClick={() => setIsOpen((prev) => !prev)}
          color={isDark ? "#f1f5f9" : "#0f172a"}
          size={{ base: "md", md: "lg" }}
          display="flex"
        />
        <Box display="flex" flexDirection="column" gap={0}>
          <Heading
            size={{ base: "sm", md: "md" }}
            fontWeight="bold"
            color={isDark ? "#06b6d4" : "#0284c7"}
          >
            {showAdminBadge ? "Admin" : "Skill Insight"}
          </Heading>
          {showAdminBadge && (
            <Text fontSize="xs" color={isDark ? "#cbd5e1" : "#64748b"}>
              Dashboard
            </Text>
          )}
        </Box>
      </HStack>

      {/* Spacer */}
      <Box flex={1} />

      {/* Navigation Links */}
      <HStack spacing={6} display={{ base: "none", md: "flex" }} mr={6}>
        <ChakraLink
          as={RouterLink}
          to="/manual"
          _hover={{ textDecoration: "none" }}
        >
          <Button
            variant="ghost"
            fontWeight={location.pathname === "/manual" ? "900" : "600"}
            fontSize="sm"
            color={
              location.pathname === "/manual"
                ? "#0284c7"
                : isDark
                  ? "#cbd5e1"
                  : "#64748b"
            }
            _hover={{
              color: "#ffffff",
              bg: "#0284c7",
            }}
            transition="all 0.2s ease"
          >
            Panduan
          </Button>
        </ChakraLink>
      </HStack>

      {/* Back to Landing Button */}
      <ChakraLink
        as={RouterLink}
        to="/"
        _hover={{ textDecoration: "none" }}
        mr={4}
      >
        <Button
          bg={isDark ? "#1e293b" : "#f8fafc"}
          border={isDark ? "1px solid #334155" : "1px solid #e2e8f0"}
          color={isDark ? "#f1f5f9" : "#0f172a"}
          px={4}
          py={2}
          borderRadius="lg"
          fontSize="sm"
          _hover={{
            bg: isDark ? "#334155" : "#f1f5f9",
            borderColor: isDark ? "#0284c7" : "#0284c7",
          }}
          transition="all 0.2s ease"
        >
          <HStack spacing={2}>
            <Box fontSize="lg">←</Box>
            <Box fontWeight="600">Kembali</Box>
          </HStack>
        </Button>
      </ChakraLink>

      {/* Dark Mode Toggle */}
      <Button
        onClick={toggleTheme}
        bg={isDark ? "#1e293b" : "#f8fafc"}
        border={isDark ? "1px solid #334155" : "1px solid #e2e8f0"}
        color={isDark ? "#f1f5f9" : "#0f172a"}
        px={4}
        py={2}
        borderRadius="lg"
        fontSize="sm"
        _hover={{
          bg: isDark ? "#334155" : "#f1f5f9",
        }}
        transition="all 0.2s ease"
      >
        <HStack spacing={2}>
          <Box fontSize="lg">{isDark ? "☀️" : "🌙"}</Box>
          <Box fontWeight="600">{isDark ? "Light Mode" : "Dark Mode"}</Box>
        </HStack>
      </Button>
    </Box>
  );
}
