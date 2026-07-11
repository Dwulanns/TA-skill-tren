import React, { useState } from "react";
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  IconButton,
  Divider,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate, useLocation } from "react-router-dom";
import { ArrowBackIcon } from "@chakra-ui/icons";
import {
  MdDashboard,
  MdAnalytics,
  MdCloudDownload,
  MdStorage,
  MdBuild,
} from "react-icons/md";
import { useTheme } from "../context/ThemeContext";

const AdminPanel = () => {
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const bgCard = "var(--bg-secondary)";
  const bgPanel = "var(--bg-primary)";
  const textColor = "var(--text-primary)";
  const textSecondary = "var(--text-secondary)";
  const borderColor = "var(--border-color)";
  const hoverBg = "var(--bg-hover)";
  const activeBg = "var(--bg-tertiary)";

  const menuItems = [
    { label: "Dashboard", icon: MdDashboard, path: "/admin/dashboard" },
    {
      label: "Detail Analisis",
      icon: MdAnalytics,
      path: "/admin/detail-analysis",
    },
    { label: "Web Scraping", icon: MdCloudDownload, path: "/admin/scraping" },
    { label: "Database", icon: MdStorage, path: "/admin/database" },
    { label: "Manajemen Keyword", icon: MdBuild, path: "/admin/keywords" },
  ];

  const isActive = (path) => location.pathname === path;

  const NavLink = ({ item }) => (
    <Button
      as={RouterLink}
      to={item.path}
      leftIcon={<item.icon size={20} />}
      w="100%"
      justifyContent="flex-start"
      bg={isActive(item.path) ? activeBg : "transparent"}
      color={isActive(item.path) ? "#0284c7" : textColor}
      _hover={{
        bg: isActive(item.path) ? activeBg : hoverBg,
        color: isActive(item.path) ? "#0284c7" : textColor,
      }}
      borderRadius="lg"
      fontWeight={500}
      mb={2}
      pr={4}
      pl={4}
      py={6}
      fontSize="md"
      border={isActive(item.path) ? "1px solid" : "1px solid transparent"}
      borderColor={isActive(item.path) ? "#0284c7" : "transparent"}
      transition="all 0.2s"
    >
      {item.label}
    </Button>
  );

  return (
    <Box bg={bgPanel} minH="100vh" p={8}>
      <VStack spacing={6} align="stretch" maxW="600px" mx="auto">
        {/* Header with Back Button */}
        <HStack justify="space-between" align="center">
          <VStack align="start" spacing={1} flex={1}>
            <Heading size="lg" color={textColor}>
              Admin Menu
            </Heading>
            <Text color={textSecondary} fontSize="sm">
              Kelola dashboard, data, dan proses ekstraksi
            </Text>
          </VStack>
          <IconButton
            icon={<ArrowBackIcon />}
            onClick={() => navigate("/dashboard")}
            title="Kembali ke Dashboard User"
            colorScheme="blue"
            variant="outline"
            size="md"
            borderRadius="lg"
          />
        </HStack>

        <Divider />

        {/* Menu Items */}
        <VStack align="stretch" spacing={1}>
          {menuItems.map((item) => (
            <NavLink key={item.path} item={item} />
          ))}
        </VStack>

        <Divider />

        {/* Logout Button */}
        <Button
          w="100%"
          colorScheme="red"
          variant="solid"
          size="lg"
          borderRadius="lg"
          fontWeight={600}
          py={6}
          onClick={() => {
            localStorage.removeItem("adminToken");
            navigate("/admin/login");
          }}
        >
          Logout
        </Button>
      </VStack>
    </Box>
  );
};

export default AdminPanel;
