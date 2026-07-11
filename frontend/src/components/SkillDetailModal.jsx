import { useEffect, useState } from "react";
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Box,
  VStack,
  HStack,
  Grid,
  Text,
  Badge,
  Spinner,
  Center,
  Divider,
} from "@chakra-ui/react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import axios from "axios";
import { useTheme } from "../context/ThemeContext";
import TopCompaniesCard from "./TopCompaniesCard";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

import { API_ENDPOINTS, buildQueryString } from "../config/api";

const SKILL_TYPE_COLORS = {
  tech_stack: {
    badge: "blue",
    line: "rgba(10, 140, 255, 1)",
    bg: "rgba(10, 140, 255, 0.1)",
    label: "Tech Stack",
  },
  technical_skill: {
    badge: "purple",
    line: "rgba(26, 188, 156, 1)",
    bg: "rgba(26, 188, 156, 0.1)",
    label: "Technical Skill",
  },
  soft_skill: {
    badge: "orange",
    line: "rgba(251, 146, 60, 1)",
    bg: "rgba(251, 146, 60, 0.1)",
    label: "Soft Skill",
  },
};

// Helper function to determine trend
const getTrendInfo = (data) => {
  if (!data || data.length < 2) return null;
  const isIncreasing = data[data.length - 1].count > data[0].count;
  return {
    isIncreasing,
    label: isIncreasing ? "Meningkat" : "Menurun",
    icon: isIncreasing ? "📈" : "📉",
    change: Math.abs(data[data.length - 1].count - data[0].count),
    color: isIncreasing ? "#00897b" : "#d32f2f",
    bgColor: isIncreasing ? "#c8e6c9" : "#ffcccc",
    borderColor: isIncreasing ? "#c8e6c9" : "#ffcccc",
  };
};

export default function SkillDetailModal({
  isOpen,
  onClose,
  skillName,
  skillType,
  filters, // ← filters dari parent (job title, lokasi, bulan, tahun, employee_size)
}) {
  const { isDark } = useTheme();
  const [trendData, setTrendData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !skillName) return;

    setLoading(true);
    setError(null);

    // Build query params dari SELURUH filters yang diterima dari parent
    const params = buildQueryString({
      keyword_id: filters?.keyword_id,
      location: filters?.location,
      month: filters?.month,
      year: filters?.year,
      employee_size: filters?.employee_size,
    });

    axios
      .get(
        `${API_ENDPOINTS.DASHBOARD.SKILL_TREND}/${encodeURIComponent(skillName)}?${params}`,
      )
      .then((res) => {
        setTrendData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching skill trend:", err);
        setError(err.response?.data?.detail || err.message);
        setLoading(false);
      });
  }, [
    isOpen,
    skillName,
    filters?.keyword_id,
    filters?.location,
    filters?.month,
    filters?.year,
    filters?.employee_size, // ← effect re-run setiap salah satu filter ini berubah
  ]);

  const colorScheme =
    SKILL_TYPE_COLORS[skillType] || SKILL_TYPE_COLORS.tech_stack;

  const chartData =
    trendData && trendData.data && trendData.data.length > 0
      ? {
          labels: trendData.data.map((d) => d.month),
          datasets: [
            {
              label: skillName,
              data: trendData.data.map((d) => d.count),
              borderColor: colorScheme.line,
              backgroundColor: colorScheme.bg,
              borderWidth: 3,
              fill: true,
              tension: 0.4,
              pointRadius: 6,
              pointBackgroundColor: colorScheme.line,
              pointBorderColor: "#ffffff",
              pointBorderWidth: 2,
              pointHoverRadius: 8,
            },
          ],
        }
      : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: "top",
        labels: {
          color: isDark ? "#cbd5e1" : "#333333",
          font: { size: 13 },
          padding: 15,
        },
      },
      tooltip: {
        backgroundColor: isDark
          ? "rgba(30, 41, 59, 0.95)"
          : "rgba(255, 255, 255, 0.95)",
        borderColor: isDark ? "#0284c7" : "#000000",
        borderWidth: 1,
        padding: 12,
        titleFont: { size: 13 },
        titleColor: isDark ? "#0284c7" : "#000000",
        bodyFont: { size: 12 },
        bodyColor: isDark ? "#cbd5e1" : "#000000",
        callbacks: {
          label: (ctx) => `Lowongan: ${ctx.parsed.y}`,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: isDark ? "#475569" : "#e5e5e5", drawBorder: false },
        ticks: { color: isDark ? "#cbd5e1" : "#000000", font: { size: 11 } },
        title: {
          display: true,
          text: "Jumlah Lowongan",
          color: isDark ? "#cbd5e1" : "#000000",
        },
      },
      x: {
        grid: { color: isDark ? "#475569" : "#e5e5e5", drawBorder: false },
        ticks: { color: isDark ? "#cbd5e1" : "#000000", font: { size: 11 } },
        title: {
          display: true,
          text: "Periode",
          color: isDark ? "#cbd5e1" : "#000000",
        },
      },
    },
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="2xl"
      isCentered
      scrollBehavior="inside"
    >
      <ModalOverlay backdropFilter="blur(6px)" />
      <ModalContent
        bg={isDark ? "#1e293b" : "#ffffff"}
        borderColor={isDark ? "#475569" : "#e0e0e0"}
        border="1px solid"
        borderRadius="xl"
        boxShadow={
          isDark
            ? "0 20px 40px rgba(0, 0, 0, 0.4)"
            : "0 20px 40px rgba(0, 0, 0, 0.15)"
        }
      >
        <ModalHeader
          borderBottomWidth="2px"
          borderColor={isDark ? "#0284c7" : "#e0e0e0"}
          pb={4}
          pt={5}
          bg={isDark ? "#0f172a" : "#f8f9fa"}
          borderTopRadius="xl"
        >
          <VStack align="start" spacing={2}>
            <HStack spacing={2} w="100%" justify="space-between">
              <Text
                fontSize="2xl"
                fontWeight="bold"
                color={isDark ? "#ffffff" : "#0f172a"}
              >
                {skillName}
              </Text>
              <Badge
                bg={colorScheme.line}
                color="#fff"
                fontSize="sm"
                px={3}
                py={1}
                borderRadius="md"
              >
                {colorScheme.label}
              </Badge>
            </HStack>

            <Box
              bg={isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.05)"}
              px={3}
              py={2}
              borderRadius="lg"
              w="100%"
            >
              <Text
                fontSize="sm"
                color={isDark ? "#cbd5e1" : "#475569"}
                fontWeight="500"
              >
                Periode: {trendData?.data?.[0]?.month || "N/A"} -{" "}
                {trendData?.data?.[trendData?.data?.length - 1]?.month || "N/A"}
                {filters?.employee_size && (
                  <Badge ml={2} colorScheme="blue" fontSize="xs">
                    Ukuran: {filters.employee_size}
                  </Badge>
                )}
              </Text>
            </Box>
          </VStack>
        </ModalHeader>
        <ModalCloseButton
          top="14px"
          right="14px"
          bg="rgba(0,0,0,0.1)"
          _hover={{ bg: "rgba(0,0,0,0.2)" }}
          borderRadius="full"
        />

        <ModalBody pb={4} pt={4} minH="400px">
          <VStack spacing={4} align="stretch" w="100%">
            {loading ? (
              <Center h="350px">
                <VStack spacing={2}>
                  <Spinner size="lg" color="#0284c7" thickness="4px" />
                  <Text fontSize="sm" color={isDark ? "#cbd5e1" : "#666"}>
                    Memuat data...
                  </Text>
                </VStack>
              </Center>
            ) : error ? (
              <Box
                p={4}
                bg={isDark ? "#7f1d1d" : "#ffebee"}
                borderRadius="lg"
                border="1px solid #ef5350"
              >
                <Text color={isDark ? "#fca5a5" : "#c62828"} fontWeight="bold">
                  Error: {error}
                </Text>
                <Text fontSize="12px" color={isDark ? "#fbcaca" : "#d32f2f"}>
                  Pastikan backend running di port 8000
                </Text>
              </Box>
            ) : chartData &&
              chartData.datasets &&
              chartData.datasets.length > 0 &&
              chartData.datasets[0].data &&
              chartData.datasets[0].data.length > 0 ? (
              <>
                {/* Chart */}
                <Box
                  h="320px"
                  bg={isDark ? "#334155" : "#fafbfc"}
                  p={4}
                  borderRadius="lg"
                  border="1px solid"
                  borderColor={isDark ? "#475569" : "#e0e0e0"}
                >
                  <Line data={chartData} options={chartOptions} />
                </Box>

                {/* Divider */}
                <Divider borderColor={isDark ? "#475569" : "#e0e0e0"} />

                {/* Top Companies Section */}
                <Box w="100%">
                  <Text
                    fontSize="sm"
                    fontWeight="bold"
                    mb={3}
                    color={isDark ? "#cbd5e1" : "#333333"}
                  >
                    Perusahaan Teratas yang Mencari Skill Ini
                  </Text>
                  <TopCompaniesCard
                    skillName={skillName}
                    filters={filters} // ← Kirim filters lengkap (keyword_id, location, month, year, employee_size)
                    isDark={isDark}
                  />
                </Box>

                {/* Divider */}
                <Divider borderColor={isDark ? "#475569" : "#e0e0e0"} />

                {/* Ringkasan Analisis */}
                <Box
                  bg={isDark ? "#334155" : "#f8f9fa"}
                  p={3}
                  borderRadius="lg"
                  border="1px solid"
                  borderColor={isDark ? "#475569" : "#e0e0e0"}
                >
                  <Text
                    fontSize="13px"
                    fontWeight="bold"
                    color={isDark ? "#0284c7" : "#0066cc"}
                    textTransform="uppercase"
                    letterSpacing="0.5px"
                    mb={2}
                  >
                    Ringkasan Analisis
                  </Text>

                  <VStack align="stretch" spacing={2}>
                    {/* Main Metrics - 2x2 Grid */}
                    <Grid templateColumns="repeat(2, 1fr)" gap={2}>
                      <Box
                        bg={isDark ? "#1e293b" : "#ffffff"}
                        p={2}
                        borderRadius="lg"
                        borderLeftWidth="3px"
                        borderLeftColor={isDark ? "#26dfc7" : "#00897b"}
                      >
                        <Text
                          fontSize="10px"
                          color={isDark ? "#cbd5e1" : "#666"}
                          fontWeight="600"
                        >
                          Total Periode
                        </Text>
                        <Text
                          fontSize="20px"
                          fontWeight="bold"
                          color={isDark ? "#26dfc7" : "#00897b"}
                        >
                          {trendData?.data?.length || 0}
                        </Text>
                        <Text
                          fontSize="9px"
                          color={isDark ? "#94a3b8" : "#999"}
                        >
                          bulan
                        </Text>
                      </Box>

                      <Box
                        bg={isDark ? "#1e293b" : "#ffffff"}
                        p={2}
                        borderRadius="lg"
                        borderLeftWidth="3px"
                        borderLeftColor={isDark ? "#26dfc7" : "#00897b"}
                      >
                        <Text
                          fontSize="10px"
                          color={isDark ? "#cbd5e1" : "#666"}
                          fontWeight="600"
                        >
                          Rata-rata Lowongan
                        </Text>
                        <Text
                          fontSize="20px"
                          fontWeight="bold"
                          color={isDark ? "#26dfc7" : "#00897b"}
                        >
                          {trendData?.data?.length > 0
                            ? (
                                trendData.data.reduce(
                                  (sum, d) => sum + d.count,
                                  0,
                                ) / trendData.data.length
                              ).toFixed(1)
                            : 0}
                        </Text>
                        <Text
                          fontSize="9px"
                          color={isDark ? "#94a3b8" : "#999"}
                        >
                          per bulan
                        </Text>
                      </Box>

                      <Box
                        bg={isDark ? "#1e293b" : "#ffffff"}
                        p={2}
                        borderRadius="lg"
                        borderLeftWidth="3px"
                        borderLeftColor={isDark ? "#26dfc7" : "#00897b"}
                      >
                        <Text
                          fontSize="10px"
                          color={isDark ? "#cbd5e1" : "#666"}
                          fontWeight="600"
                        >
                          Total Kemunculan
                        </Text>
                        <Text
                          fontSize="20px"
                          fontWeight="bold"
                          color={isDark ? "#26dfc7" : "#00897b"}
                        >
                          {trendData?.data?.reduce(
                            (sum, d) => sum + d.count,
                            0,
                          ) || 0}
                        </Text>
                        <Text
                          fontSize="9px"
                          color={isDark ? "#94a3b8" : "#999"}
                        >
                          lowongan
                        </Text>
                      </Box>

                      <Box
                        bg={isDark ? "#1e293b" : "#ffffff"}
                        p={2}
                        borderRadius="lg"
                        borderLeftWidth="3px"
                        borderLeftColor={isDark ? "#26dfc7" : "#00897b"}
                      >
                        <Text
                          fontSize="10px"
                          color={isDark ? "#cbd5e1" : "#666"}
                          fontWeight="600"
                        >
                          Nilai Tertinggi
                        </Text>
                        <Text
                          fontSize="20px"
                          fontWeight="bold"
                          color={isDark ? "#26dfc7" : "#00897b"}
                        >
                          {trendData?.data?.length > 0
                            ? Math.max(...trendData.data.map((d) => d.count))
                            : 0}
                        </Text>
                        <Text
                          fontSize="9px"
                          color={isDark ? "#94a3b8" : "#999"}
                        >
                          dalam satu bulan
                        </Text>
                      </Box>
                    </Grid>

                    {/* Trend Status */}
                    {trendData?.data?.length >= 2 &&
                      (() => {
                        const trend = getTrendInfo(trendData.data);
                        return trend ? (
                          <Box
                            bg={isDark ? "#1e293b" : "#ffffff"}
                            p={2}
                            borderRadius="lg"
                            borderLeftWidth="3px"
                            borderLeftColor={trend.color}
                          >
                            <HStack justify="space-between" align="center">
                              <VStack align="start" spacing={0}>
                                <Text
                                  fontSize="11px"
                                  color={isDark ? "#cbd5e1" : "#666"}
                                  fontWeight="600"
                                >
                                  Status Tren
                                </Text>
                                <Text
                                  fontSize="16px"
                                  fontWeight="bold"
                                  color={trend.color}
                                >
                                  {trend.label} {trend.icon}
                                </Text>
                              </VStack>
                              <VStack align="end" spacing={0}>
                                <Text
                                  fontSize="11px"
                                  color={isDark ? "#cbd5e1" : "#666"}
                                  fontWeight="600"
                                >
                                  Perubahan
                                </Text>
                                <Text
                                  fontSize="16px"
                                  fontWeight="bold"
                                  color={trend.color}
                                >
                                  +{trend.change}
                                </Text>
                              </VStack>
                            </HStack>
                          </Box>
                        ) : null;
                      })()}
                  </VStack>
                </Box>
              </>
            ) : (
              <Box
                p={6}
                textAlign="center"
                bg={isDark ? "#334155" : "#f5f7fa"}
                borderRadius="lg"
              >
                <Text color={isDark ? "#cbd5e1" : "#666"} fontSize="sm">
                  Tidak ada data trend untuk skill ini dengan filter yang
                  dipilih
                </Text>
              </Box>
            )}
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
}
