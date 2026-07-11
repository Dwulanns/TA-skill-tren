import React, { useState, useEffect } from "react";
import {
  Box,
  Grid,
  Heading,
  Text,
  VStack,
  HStack,
  Card,
  CardBody,
  CardHeader,
  Spinner,
  Badge,
  IconButton,
  Divider,
  Flex,
} from "@chakra-ui/react";
import { useNavigate } from "react-router-dom";
import { ArrowBackIcon } from "@chakra-ui/icons";
import { useTheme } from "../context/ThemeContext";
import {
  MdTrendingUp,
  MdStorage,
  MdAutoAwesome,
  MdDownload,
  MdBuild,
  MdCode,
  MdTableChart,
  MdInfo,
} from "react-icons/md";

const AdminDashboard = () => {
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/stats");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error loading stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const cardBg = isDark ? "gray.800" : "white";
  const borderColor = isDark ? "gray.700" : "gray.100";
  const cardShadow = isDark
    ? "0 2px 8px rgba(0,0,0,0.4)"
    : "0 2px 8px rgba(0,0,0,0.07)";
  const mutedText = isDark ? "gray.400" : "gray.500";
  const bodyText = isDark ? "gray.200" : "gray.700";

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minH="400px"
        bg={isDark ? "gray.900" : "gray.50"}
      >
        <VStack spacing={3}>
          <Spinner size="xl" color="blue.500" thickness="3px" speed="0.7s" />
          <Text fontSize="sm" color={mutedText}>Memuat data...</Text>
        </VStack>
      </Box>
    );
  }

  const statItems = [
    {
      label: "Total Jobs",
      value: (stats?.total_jobs || 0).toLocaleString("id-ID"),
      icon: MdDownload,
      accent: isDark ? "blue.400" : "blue.500",
      bg: isDark ? "blue.900" : "blue.50",
    },
    {
      label: "Unique Skills",
      value: (stats?.unique_skills || 0).toLocaleString("id-ID"),
      icon: MdAutoAwesome,
      accent: isDark ? "purple.400" : "purple.500",
      bg: isDark ? "purple.900" : "purple.50",
    },
    {
      label: "Processed Jobs",
      value: (stats?.processed_jobs || 0).toLocaleString("id-ID"),
      icon: MdTrendingUp,
      accent: isDark ? "green.400" : "green.500",
      bg: isDark ? "green.900" : "green.50",
    },
    {
      label: "Job-Skill Links",
      value: (stats?.total_skills || 0).toLocaleString("id-ID"),
      icon: MdStorage,
      accent: isDark ? "orange.400" : "orange.500",
      bg: isDark ? "orange.900" : "orange.50",
    },
  ];

  const menuCards = [
    {
      icon: MdDownload,
      title: "Web Scraping",
      description:
        "Ambil data lowongan pekerjaan terbaru dari LinkedIn berdasarkan keyword yang telah dikonfigurasi.",
      action: 'Buka menu "Web Scraping" untuk memulai',
      accent: isDark ? "blue.400" : "blue.500",
      bg: isDark ? "blue.900" : "blue.50",
    },
    {
      icon: MdCode,
      title: "Ekstrak Skill",
      description:
        "Analisis job description secara otomatis dengan AI untuk mengidentifikasi skill yang relevan.",
      action: 'Buka menu "Ekstrak Skill" untuk konfigurasi',
      accent: isDark ? "purple.400" : "purple.500",
      bg: isDark ? "purple.900" : "purple.50",
    },
    {
      icon: MdTableChart,
      title: "Olah Data",
      description:
        "Lihat, kelola, dan edit tabel keywords secara langsung dari antarmuka ini.",
      action: 'Buka menu "Management Keywords" untuk lihat keywords',
      accent: isDark ? "green.400" : "green.500",
      bg: isDark ? "green.900" : "green.50",
    },
    {
      icon: MdInfo,
      title: "Informasi System",
      description: (
        <VStack align="start" spacing={1}>
          <Text fontSize="sm" color={bodyText}>
            <Text as="span" fontWeight="600">Backend:</Text> http://localhost:8000
          </Text>
          <Text fontSize="sm" color={bodyText}>
            <Text as="span" fontWeight="600">Database:</Text> SQLite (skills_trend.db)
          </Text>
        </VStack>
      ),
      action: 'Gunakan menu "Olah Data" untuk troubleshooting',
      accent: isDark ? "orange.400" : "orange.500",
      bg: isDark ? "orange.900" : "orange.50",
    },
  ];

  return (
    <Box
      px={{ base: 4, md: 5, lg: 6 }}
      py={{ base: 4, md: 5 }}
      bg={isDark ? "gray.900" : "gray.50"}
      minH="100vh"
    >
      <VStack align="stretch" spacing={5} maxW="1200px" mx="auto">

        {/* Header */}
        <Flex justify="space-between" align="flex-start">
          <Box>
            <Heading
              fontSize={{ base: "20px", md: "24px" }}
              fontWeight="700"
              letterSpacing="-0.02em"
              color={isDark ? "white" : "gray.800"}
              mb={1}
            >
              Admin Dashboard
            </Heading>
            <Text fontSize="sm" color={mutedText}>
              Pantau database, jalankan scraping, dan kelola ekstraksi skill
            </Text>
          </Box>
          <IconButton
            icon={<ArrowBackIcon />}
            onClick={() => navigate("/dashboard")}
            title="Kembali ke Dashboard User"
            colorScheme="blue"
            variant="outline"
            size="sm"
            borderRadius="lg"
            mt={1}
          />
        </Flex>

        <Divider borderColor={borderColor} />

        {/* Stat Cards */}
        <Grid templateColumns={{ base: "repeat(2, 1fr)", md: "repeat(4, 1fr)" }} gap={3}>
          {statItems.map((item) => (
            <Card
              key={item.label}
              bg={cardBg}
              borderWidth="1px"
              borderColor={borderColor}
              boxShadow={cardShadow}
              borderRadius="xl"
              overflow="hidden"
            >
              <CardBody p={4}>
                <VStack align="start" spacing={3}>
                  <Box
                    p={2}
                    bg={item.bg}
                    borderRadius="lg"
                    display="inline-flex"
                    alignItems="center"
                    justifyContent="center"
                  >
                    <item.icon size={20} color={item.accent} style={{ color: item.accent }} />
                  </Box>
                  <Box>
                    <Text
                      fontSize="22px"
                      fontWeight="700"
                      letterSpacing="-0.02em"
                      color={isDark ? "white" : "gray.800"}
                      lineHeight="1"
                      mb={0.5}
                    >
                      {item.value}
                    </Text>
                    <Text fontSize="xs" color={mutedText} fontWeight="500">
                      {item.label}
                    </Text>
                  </Box>
                </VStack>
              </CardBody>
            </Card>
          ))}
        </Grid>

        {/* Database Overview */}
        <Card
          bg={cardBg}
          borderWidth="1px"
          borderColor={borderColor}
          boxShadow={cardShadow}
          borderRadius="xl"
        >
          <CardHeader pb={3} borderBottom="1px" borderColor={borderColor}>
            <HStack spacing={2}>
              <Box
                p={1.5}
                bg={isDark ? "gray.700" : "gray.100"}
                borderRadius="md"
                display="inline-flex"
              >
                <MdStorage size={16} color={isDark ? "#94a3b8" : "#64748b"} />
              </Box>
              <Heading size="sm" fontWeight="600" color={isDark ? "white" : "gray.800"}>
                Database Overview
              </Heading>
              <Badge
                colorScheme="green"
                borderRadius="full"
                px={2}
                fontSize="2xs"
                fontWeight="600"
              >
                Production
              </Badge>
            </HStack>
          </CardHeader>
          <CardBody pt={4}>
            <Grid templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }} gap={6}>
              {/* Skills by Type */}
              <VStack align="start" spacing={2}>
                <Text fontSize="xs" fontWeight="700" color={mutedText} textTransform="uppercase" letterSpacing="0.06em">
                  Skills by Type
                </Text>
                <VStack align="start" spacing={1.5} w="100%">
                  {stats?.skills_by_type
                    ? Object.entries(stats.skills_by_type).map(([type, count]) => (
                        <HStack key={type} justify="space-between" w="100%">
                          <Badge
                            colorScheme="blue"
                            borderRadius="md"
                            px={2}
                            fontSize="2xs"
                            fontWeight="600"
                          >
                            {type}
                          </Badge>
                          <Text fontSize="sm" fontWeight="700" color={isDark ? "white" : "gray.800"}>
                            {Number(count).toLocaleString("id-ID")}
                          </Text>
                        </HStack>
                      ))
                    : <Text fontSize="sm" color={mutedText}>Tidak ada data</Text>
                  }
                </VStack>
              </VStack>

              {/* Status */}
              <VStack align="start" spacing={2}>
                <Text fontSize="xs" fontWeight="700" color={mutedText} textTransform="uppercase" letterSpacing="0.06em">
                  Status
                </Text>
                <HStack spacing={2}>
                  <Box w={2} h={2} borderRadius="full" bg="green.400" />
                  <Text fontSize="sm" color={bodyText} fontWeight="500">Sistem berjalan normal</Text>
                </HStack>
                <Text fontSize="xs" color={mutedText}>
                  Last updated: {new Date().toLocaleDateString("id-ID", {
                    day: "numeric", month: "long", year: "numeric"
                  })}
                </Text>
              </VStack>

              {/* Quick Actions */}
              <VStack align="start" spacing={2}>
                <Text fontSize="xs" fontWeight="700" color={mutedText} textTransform="uppercase" letterSpacing="0.06em">
                  Menu Tersedia
                </Text>
                <VStack align="start" spacing={1}>
                  {[
                    { label: "Web Scraping", desc: "Ambil data lowongan" },
                    { label: "Ekstrak Skill", desc: "Analisis skill AI" },
                    { label: "Management Keywords", desc: "Kelola tabel data" },
                  ].map((m) => (
                    <HStack key={m.label} spacing={2} align="start">
                      <Box w={1} h={1} borderRadius="full" bg="blue.400" mt="6px" flexShrink={0} />
                      <Box>
                        <Text fontSize="xs" fontWeight="600" color={bodyText}>{m.label}</Text>
                        <Text fontSize="2xs" color={mutedText}>{m.desc}</Text>
                      </Box>
                    </HStack>
                  ))}
                </VStack>
              </VStack>
            </Grid>
          </CardBody>
        </Card>

        {/* Menu Cards */}
        <Box>
          <Text fontSize="xs" fontWeight="700" color={mutedText} textTransform="uppercase" letterSpacing="0.06em" mb={3}>
            Panduan Menu
          </Text>
          <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={3}>
            {menuCards.map((card) => (
              <Card
                key={card.title}
                bg={cardBg}
                borderWidth="1px"
                borderColor={borderColor}
                boxShadow={cardShadow}
                borderRadius="xl"
                transition="box-shadow 0.15s ease"
                _hover={{ boxShadow: isDark ? "0 4px 16px rgba(0,0,0,0.5)" : "0 4px 16px rgba(0,0,0,0.12)" }}
              >
                <CardBody p={4}>
                  <HStack spacing={3} align="flex-start">
                    <Box
                      p={2}
                      bg={card.bg}
                      borderRadius="lg"
                      display="inline-flex"
                      alignItems="center"
                      justifyContent="center"
                      flexShrink={0}
                      mt={0.5}
                    >
                      <card.icon size={18} color={card.accent} style={{ color: card.accent }} />
                    </Box>
                    <VStack align="start" spacing={1.5} flex={1}>
                      <Text fontSize="sm" fontWeight="700" color={isDark ? "white" : "gray.800"}>
                        {card.title}
                      </Text>
                      {typeof card.description === "string" ? (
                        <Text fontSize="sm" color={bodyText} lineHeight="1.5">
                          {card.description}
                        </Text>
                      ) : (
                        card.description
                      )}
                      <HStack spacing={1.5} mt={0.5}>
                        <Text fontSize="2xs" color="blue.400" fontWeight="500">
                          ➜ {card.action}
                        </Text>
                      </HStack>
                    </VStack>
                  </HStack>
                </CardBody>
              </Card>
            ))}
          </Grid>
        </Box>

      </VStack>
    </Box>
  );
};

export default AdminDashboard;