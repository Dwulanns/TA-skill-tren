import {
  Box,
  VStack,
  Heading,
  Button,
  IconButton,
  Spacer,
  HStack,
  Text,
} from "@chakra-ui/react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { HamburgerIcon } from "@chakra-ui/icons";
import { useSidebar } from "../context/SidebarContext";
import { useState, useEffect } from "react";

/**
 * UNIFIED SIDEBAR COMPONENT
 *
 * Uses ONE state system for all pages (user & admin)
 * Structure is IDENTICAL - only content differs
 *
 * @param {string} headerTitle - Sidebar title
 * @param {string} headerSubtitle - Sidebar subtitle
 * @param {string} role - "user" or "admin" (for menu filtering)
 * @param {boolean} showFloatingButton - Show floating hamburger (user pages only)
 */
function Sidebar({
  headerTitle = "Skills",
  headerSubtitle = "Analytics",
  role = "user", // "user" or "admin"
  showFloatingButton = true,
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const { isOpen, setIsOpen } = useSidebar();
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false);

  // Check admin token
  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    setIsAdminLoggedIn(!!token);
  }, [location.pathname]);

  // SINGLE menu array - all menu items in one place
  const allMenuItems = [
    // Admin pages - protected
    {
      path: "/admin/dashboard",
      label: "Admin Dashboard",
      roles: ["admin"],
      requiresAuth: true,
    },
    // User & Admin pages
    { path: "/dashboard", label: "Tren Skills", roles: ["user", "admin"] },
    { path: "/detail", label: "Detail Analisis", roles: ["user", "admin"] },
    { path: "/skill-matcher", label: "Skill Matcher", roles: ["user", "admin"] },
    { path: "/skill-network", label: "Jaringan Skill", roles: ["user", "admin"] },

    {
      path: "/admin/scraping",
      label: "Scraping dan Ekstraksi Skill",
      roles: ["admin"],
      requiresAuth: true,
    },
    {
      path: "/admin/database",
      label: "Database",
      roles: ["admin"],
      requiresAuth: true,
    },
    {
      path: "/admin/keywords",
      label: "Manajemen Keyword",
      roles: ["admin"],
      requiresAuth: true,
    },
  ];

  // Filter menu items: only show items for current role + check auth if required
  const displayMenuItems = allMenuItems.filter((item) => {
    const hasRole = item.roles.includes(role);
    if (!hasRole) return false;

    // If item requires auth and user not logged in, hide it
    if (item.requiresAuth && !isAdminLoggedIn) return false;

    return true;
  });

  // Handle admin/login actions
  const handleAdminLink = (e) => {
    e.preventDefault();
    const token = localStorage.getItem("admin_token");
    if (!token) {
      navigate("/admin/login", { replace: true });
    } else {
      navigate("/admin/dashboard", { replace: true });
    }
  };

  const handleLogout = (e) => {
    e.preventDefault();
    localStorage.removeItem("admin_token");
    setIsAdminLoggedIn(false);
    navigate("/");
  };

  // Bottom menu items - changes based on role
  const bottomMenuItems =
    role === "admin"
      ? [{ label: "Logout", action: handleLogout }]
      : [{ label: "Admin", action: handleAdminLink }];

  // Simple inline icon set (keeps bundle light, no new deps)
  const icons = {
    "/admin/dashboard": (
      <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
    ),
    "/dashboard": (
      <path d="M3 17h2v-7H3v7zm5 0h2V7H8v10zm5 0h2v-4h-2v4zm5 0h2v-9h-2v9zM3 21h18v-1H3v1z" />
    ),
    "/detail": (
      <path d="M4 4h16v2H4V4zm0 5h16v2H4V9zm0 5h10v2H4v-2zm0 5h7v2H4v-2z" />
    ),
    "/skill-matcher": (
      <path d="M9 12l2 2 4-4M12 3l7 4v5c0 5-3 7.5-7 9-4-1.5-7-4-7-9V7l7-4z" />
    ),
    "/skill-network": (
      <path d="M18 8a3 3 0 100-6 3 3 0 000 6zm-6 8a3 3 0 100-6 3 3 0 000 6zm-6 6a3 3 0 100-6 3 3 0 000 6zm6-11l3.5-3m-7.5 10l4-3" />
    ),
    "/admin/scraping": (
      <path d="M12 3v12m0 0l-4-4m4 4l4-4M5 17v2a2 2 0 002 2h10a2 2 0 002-2v-2" />
    ),
    "/admin/database": (
      <path d="M12 3c4.4 0 8 1.1 8 2.5S16.4 8 12 8 4 6.9 4 5.5 7.6 3 12 3zm-8 5v4c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5V8m-16 4v4c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5v-4" />
    ),
    "/admin/keywords": (
      <path d="M3 7l8-4 8 4-8 4-8-4zm0 5l8 4 8-4M3 16l8 4 8-4" />
    ),
  };

  const MenuIcon = ({ path, isActive }) => (
    <Box
      as="svg"
      viewBox="0 0 24 24"
      w="17px"
      h="17px"
      fill="none"
      stroke={isActive ? "#ffffff" : "currentColor"}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      flexShrink={0}
      transition="stroke 0.2s ease"
    >
      {path}
    </Box>
  );

  return (
    <>
      {/* Overlay for mobile - Smooth fade */}
      {isOpen && (
        <Box
          position="fixed"
          top="0"
          left="0"
          w="100vw"
          h="100vh"
          bg="blackAlpha.600"
          backdropFilter="blur(2px)"
          zIndex="999"
          display={{ base: "block", md: "none" }}
          onClick={() => setIsOpen((prev) => !prev)}
          animation="fadeIn 0.3s ease"
        />
      )}

      {/* ===========================
          SIDEBAR STRUCTURE - UNIFIED & POLISHED
          LinkedIn-inspired blue theme, light & dark mode aware
          =========================== */}
      <Box
        position="fixed"
        left={isOpen ? "0" : "-232px"}
        top="0"
        w="232px"
        h="100vh"
        bg="var(--bg-secondary)"
        display="flex"
        flexDirection="column"
        boxShadow="6px 0 24px rgba(0, 0, 0, 0.12)"
        transition="left 0.32s cubic-bezier(0.4, 0, 0.2, 1)"
        zIndex="1001"
        overflowY="auto"
        overflowX="hidden"
        sx={{
          "&::-webkit-scrollbar": { width: "5px" },
          "&::-webkit-scrollbar-track": { bg: "transparent" },
          "&::-webkit-scrollbar-thumb": {
            bg: "var(--border-color)",
            borderRadius: "3px",
          },
          "&::-webkit-scrollbar-thumb:hover": { bg: "#0A66C2" },
        }}
      >
        {/* 1️⃣ HEADER — LinkedIn blue panel with dot-grid texture and glow */}
        <Box
          px={4}
          py={6}
          bg="linear-gradient(135deg, #0A66C2 0%, #004182 100%)"
          position="relative"
          overflow="hidden"
          flexShrink={0}
        >
          {/* Fine dot-grid texture for subtle depth */}
          <Box
            position="absolute"
            inset="0"
            bgImage="radial-gradient(circle, rgba(255,255,255,0.10) 1px, transparent 1px)"
            bgSize="14px 14px"
            opacity={0.5}
            pointerEvents="none"
          />
          {/* Glow accent — top right */}
          <Box
            position="absolute"
            top="-55px"
            right="-45px"
            w="150px"
            h="150px"
            borderRadius="full"
            bg="radial-gradient(circle, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0) 70%)"
            pointerEvents="none"
          />
          {/* Soft ring accent — bottom left */}
          <Box
            position="absolute"
            bottom="-50px"
            left="-30px"
            w="110px"
            h="110px"
            borderRadius="full"
            border="1px solid rgba(255,255,255,0.12)"
            pointerEvents="none"
          />

          <HStack spacing={3} align="center" position="relative">
            <Box
              w="42px"
              h="42px"
              borderRadius="11px"
              bg="rgba(255,255,255,0.16)"
              display="flex"
              alignItems="center"
              justifyContent="center"
              flexShrink={0}
            >
              <Text fontSize="md" fontWeight="800" color="white" lineHeight="1">
                {headerTitle.charAt(0).toUpperCase()}
              </Text>
            </Box>
            <Box flex={1} minW={0}>
              <Heading
                size="sm"
                color="white"
                fontWeight="700"
                lineHeight="1.3"
                letterSpacing="-0.2px"
                noOfLines={1}
              >
                {headerTitle}
              </Heading>
              <Text
                fontSize="sm"
                color="rgba(255,255,255,0.78)"
                lineHeight="1.4"
                mt={0.5}
                fontWeight="500"
                noOfLines={1}
              >
                {headerSubtitle}
              </Text>
            </Box>
            <IconButton
              icon={<HamburgerIcon />}
              onClick={() => setIsOpen((prev) => !prev)}
              bg="rgba(255,255,255,0.16)"
              color="white"
              size="sm"
              borderRadius="9px"
              _hover={{
                bg: "white",
                color: "#0A66C2",
              }}
              transition="all 0.2s ease"
              minW="32px"
              h="32px"
              flexShrink={0}
              aria-label="Toggle sidebar"
            />
          </HStack>
        </Box>

        {/* 2️⃣ MENU ITEMS — pill-style active state, iconography for scan-ability */}
        <VStack spacing={1} align="stretch" px={3} pt={4} mb={2} flex="none">
          <Text
            px={3}
            mb={1.5}
            fontSize="11px"
            fontWeight="700"
            letterSpacing="0.6px"
            color="var(--text-tertiary)"
            textTransform="uppercase"
            opacity={0.7}
          >
            Menu
          </Text>
          {displayMenuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Button
                key={item.path}
                as={Link}
                to={item.path}
                justifyContent="flex-start"
                variant="ghost"
                leftIcon={<MenuIcon path={icons[item.path]} isActive={isActive} />}
                color={isActive ? "#ffffff" : "var(--text-secondary)"}
                bg={isActive ? "#0A66C2" : "transparent"}
                _hover={{
                  bg: isActive ? "#0A66C2" : "var(--bg-tertiary)",
                  color: isActive ? "#ffffff" : "#0A66C2",
                }}
                _active={{ bg: isActive ? "#004182" : "rgba(10, 102, 194, 0.16)" }}
                borderRadius="20px"
                px={3.5}
                py={2.5}
                h="auto"
                minH="40px"
                fontWeight={isActive ? "700" : "500"}
                fontSize="sm"
                boxShadow={isActive ? "0 2px 8px rgba(10,102,194,0.45)" : "none"}
                transition="background 0.18s ease, color 0.18s ease"
                whiteSpace="normal"
                textAlign="left"
              >
                {item.label}
              </Button>
            );
          })}
        </VStack>

        {/* 3️⃣ SPACER - Same for all pages */}
        <Spacer />

        {/* 4️⃣ BOTTOM MENU — separated action zone */}
        <Box px={3} pt={3} mt={2}>
          <Box
            borderTop="1px solid var(--border-color)"
            pt={3}
            pb={2}
          >
            {bottomMenuItems.map((item) => {
              const isAdminButton = item.label === "Admin";
              const isLogoutButton = item.label === "Logout";
              const isOnAdminPath = location.pathname.startsWith("/admin");
              const isActive = isAdminButton && isOnAdminPath;

              return (
                <Button
                  key={item.label}
                  as="button"
                  onClick={item.action}
                  justifyContent="flex-start"
                  variant="ghost"
                  w="full"
                  leftIcon={
                    <Box
                      as="svg"
                      viewBox="0 0 24 24"
                      w="17px"
                      h="17px"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      flexShrink={0}
                    >
                      {isLogoutButton ? (
                        <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
                      ) : (
                        <path d="M12 15a4 4 0 100-8 4 4 0 000 8zM5.5 20a6.5 6.5 0 0113 0" />
                      )}
                    </Box>
                  }
                  color={isActive ? "#ffffff" : "var(--text-secondary)"}
                  bg={isActive ? "#0A66C2" : "transparent"}
                  _hover={{
                    bg: isLogoutButton ? "rgba(194, 49, 36, 0.12)" : "rgba(10, 102, 194, 0.12)",
                    color: isLogoutButton ? "#C23124" : "#0A66C2",
                  }}
                  _active={{
                    bg: isLogoutButton ? "rgba(194, 49, 36, 0.2)" : "rgba(10, 102, 194, 0.2)",
                  }}
                  borderRadius="20px"
                  px={3.5}
                  py={2.5}
                  fontWeight="600"
                  fontSize="sm"
                  transition="background 0.18s ease, color 0.18s ease"
                >
                  {item.label}
                </Button>
              );
            })}
          </Box>

          {/* 5️⃣ FOOTER INFO — compact brand footer */}
          <Box
            pt={1}
            pb={4}
            px={1}
            textAlign="center"
          >
            {role === "admin" && (
              <HStack
                justify="center"
                spacing={1.5}
                mb={2.5}
                px={2.5}
                py={1}
                mx="auto"
                w="fit-content"
                bg="rgba(10, 102, 194, 0.1)"
                borderRadius="full"
              >
                <Box w="6px" h="6px" borderRadius="full" bg="#0A66C2" />
                <Text
                  fontWeight="700"
                  color="#0A66C2"
                  fontSize="10px"
                  letterSpacing="0.5px"
                >
                  ADMIN MODE
                </Text>
              </HStack>
            )}
            <Text
              fontWeight="700"
              color="var(--text-secondary)"
              fontSize="xs"
              letterSpacing="0.4px"
            >
              SKILL TREND
            </Text>
            <Text fontSize="10px" fontWeight="500" letterSpacing="0.3px" mt={0.5} color="var(--text-tertiary)">
              D4 Teknik Informatika
            </Text>
          </Box>
        </Box>
      </Box>
    </>
  );
}

export { Sidebar as default };
export { Sidebar };