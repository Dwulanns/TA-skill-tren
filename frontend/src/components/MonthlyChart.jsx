import { useEffect, useState } from "react";
import {
  Box,
  Heading,
  Spinner,
  Center,
  Text,
  Tooltip,
  VStack,
  HStack,
  Badge,
  useToast,
} from "@chakra-ui/react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Legend,
} from "chart.js";
import axios from "axios";
import {
  API_ENDPOINTS,
  buildQueryString,
  getErrorMessage,
} from "../config/api";
import { useTheme } from "../context/ThemeContext";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Legend);

const SKILL_TYPE_ID = {
  TECH_STACK: "3",
};

/**
 * MonthlyChart Component
 * Displays top technical skills across jobs in a horizontal bar chart
 *
 * @param {Object} props
 * @param {Object} props.filters - Applied filter criteria (keyword_id, location, month, year)
 * @param {Function} props.onSkillClick - Callback when skill is clicked for detail view
 * @param {Function} props.onExpandClick - Callback when expand button is clicked
 */
export default function MonthlyChart({
  filters,
  onSkillClick,
  onExpandClick,
  activeFilterBadges = [],
}) {
  const toast = useToast();
  const { isDark } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetch chart data when filters change
   */
  useEffect(() => {
    const fetchChartData = async () => {
      try {
        setLoading(true);
        setError(null);

        const params = {
          skill_type_id: SKILL_TYPE_ID.TECH_STACK,
          limit: "10",
          keyword_id: filters?.keyword_id,
          location: filters?.location,
          employee_size: filters?.employee_size,
          month: filters?.month,
          year: filters?.year,
        };

        const queryString = buildQueryString(params);
        const url = `${API_ENDPOINTS.DASHBOARD.TOP_SKILLS_BY_TYPE}?${queryString}`;

        const response = await axios.get(url);
        setData(response.data || []);
      } catch (err) {
        const errorMsg = getErrorMessage(err);
        setError(errorMsg);
        toast({
          title: "Error loading skills chart",
          description: errorMsg,
          status: "error",
          duration: 4000,
          isClosable: true,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();
  }, [
    filters?.keyword_id,
    filters?.location,
    filters?.employee_size,
    filters?.month,
    filters?.year,
    toast,
  ]);

  // Loading state
  if (loading) {
    return (
      <Box
        bg="var(--bg-secondary)"
        p={6}
        borderRadius="xl"
        border="1px solid var(--border-color)"
        h="400px"
      >
        <Center h="100%">
          <Spinner size="xl" color="var(--accent-primary)" />
        </Center>
      </Box>
    );
  }

  // Error or empty data state
  if (error || !data || data.length === 0) {
    return (
      <Box
        bg="var(--bg-secondary)"
        p={6}
        borderRadius="xl"
        border="1px solid var(--border-color)"
        h="400px"
      >
        <Center h="100%">
          <Box textAlign="center" color="var(--text-tertiary)">
            <p>{error || "No data available for selected filters"}</p>
          </Box>
        </Center>
      </Box>
    );
  }

  /**
   * Prepare chart data from API response
   */
  const chartData = {
    labels: data.slice(0, 10).map((d, i) => `${i + 1}. ${d.skill_name}`) || [],
    datasets: [
      {
        label: "Jumlah Lowongan",
        data: data.slice(0, 10).map((d) => d.count) || [],
        backgroundColor: [
          isDark ? "rgba(2, 132, 199, 0.8)" : "rgba(2, 132, 199, 0.8)",
          isDark ? "rgba(6, 182, 212, 0.7)" : "rgba(3, 105, 161, 0.8)",
          isDark ? "rgba(14, 165, 233, 0.6)" : "rgba(2, 132, 199, 0.75)",
          isDark ? "rgba(34, 211, 238, 0.5)" : "rgba(3, 105, 161, 0.7)",
          isDark ? "rgba(2, 132, 199, 0.9)" : "rgba(59, 130, 246, 0.8)",
          isDark ? "rgba(6, 182, 212, 0.8)" : "rgba(2, 132, 199, 0.7)",
          isDark ? "rgba(14, 165, 233, 0.7)" : "rgba(3, 105, 161, 0.75)",
          isDark ? "rgba(2, 132, 199, 0.75)" : "rgba(59, 130, 246, 0.75)",
          isDark ? "rgba(6, 182, 212, 0.75)" : "rgba(2, 132, 199, 0.8)",
          isDark ? "rgba(14, 165, 233, 0.8)" : "rgba(3, 105, 161, 0.65)",
        ],
        borderColor: "var(--bg-secondary)",
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
        hoverBackgroundColor: isDark
          ? "rgba(6, 182, 212, 1)"
          : "rgba(3, 105, 161, 1)",
      },
    ],
  };

  /**
   * Chart configuration options
   */
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: "y",
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: isDark
          ? "rgba(52, 73, 94, 0.95)"
          : "rgba(226, 232, 240, 0.95)",
        padding: 12,
        titleFont: {
          size: 14,
          weight: "bold",
        },
        titleColor: isDark ? "#f8fafc" : "#0f172a",
        bodyFont: { size: 13 },
        bodyColor: isDark ? "#f8fafc" : "#0f172a",
        borderColor: "#0284c7",
        borderWidth: 2,
        callbacks: {
          label: (ctx) => `${ctx.parsed.x} lowongan`,
        },
      },
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const clickedIndex = elements[0].index;
        const skillName = data[clickedIndex]?.skill_name;
        if (skillName && onSkillClick) {
          onSkillClick({
            skillName,
            skillType: "tech_stack",
          });
        }
      }
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: { color: isDark ? "#475569" : "#e2e8f0", drawBorder: false },
        ticks: {
          font: { size: 11, color: isDark ? "#cbd5e1" : "#000000" },
          color: isDark ? "#cbd5e1" : "#000000",
        },
      },
      y: {
        grid: { display: false, drawBorder: false },
        ticks: {
          font: { size: 11, color: isDark ? "#cbd5e1" : "#000000" },
          color: isDark ? "#cbd5e1" : "#000000",
        },
      },
    },
  };

  return (
    <Box
      bg="var(--bg-secondary)"
      p={6}
      borderRadius="xl"
      border="1px solid var(--border-color)"
      cursor="pointer"
      _hover={{
        borderColor: "var(--accent-primary)",
        boxShadow: isDark
          ? "0 0 20px rgba(2, 132, 199, 0.3)"
          : "0 0 20px rgba(2, 132, 199, 0.15)",
      }}
      transition="all 0.3s"
    >
      <VStack align="stretch" spacing={4}>
        <Box position="relative">
          <Tooltip
            label="Klik skill untuk lihat trend detail. Klik judul untuk lihat semua skill."
            placement="bottom-start"
            hasArrow
            bg={isDark ? "#334155" : "#f8fafc"}
            color={isDark ? "#f8fafc" : "#0f172a"}
            borderColor={isDark ? "#0284c7" : "#0284c7"}
            border="1px solid"
            fontWeight="600"
          >
            <Box
              onClick={(e) => {
                e.stopPropagation();
                if (onExpandClick) {
                  onExpandClick({
                    skillTypeId: 3,
                    skillType: "tech_stack",
                  });
                }
              }}
              display="flex"
              justifyContent="space-between"
              alignItems="flex-start"
            >
              <Box>
                <Heading
                  size="md"
                  color="var(--accent-primary)"
                  fontWeight="bold"
                  cursor="pointer"
                  _hover={{ color: isDark ? "#06b6d4" : "#0369a1" }}
                  transition="color 0.2s"
                >
                  Tech Stack Paling Dibutuhkan
                </Heading>
                <Text
                  fontSize="xs"
                  color="var(--text-tertiary)"
                  fontWeight="normal"
                  mt={1}
                >
                  10 Teknologi & Tools yang paling sering diminta
                </Text>
                <HStack spacing={2} mt={2} flexWrap="wrap">
                  {(activeFilterBadges.length > 0
                    ? activeFilterBadges
                    : ["Filter: Semua Data"]
                  ).map((item) => (
                    <Badge
                      key={item}
                      px={2.5}
                      py={1}
                      borderRadius="full"
                      bg="var(--bg-tertiary)"
                      color={
                        item === "Filter: Semua Data"
                          ? "var(--text-secondary)"
                          : "var(--accent-primary)"
                      }
                      border={
                        item === "Filter: Semua Data"
                          ? "1px dashed var(--border-color)"
                          : "1px solid var(--border-color)"
                      }
                      fontSize="0.68rem"
                      fontWeight={item === "Filter: Semua Data" ? "600" : "700"}
                    >
                      {item}
                    </Badge>
                  ))}
                </HStack>
              </Box>
              <Box
                bg="var(--accent-primary)"
                color="white"
                px={2}
                py={1}
                borderRadius="md"
                fontSize="xs"
                fontWeight="bold"
                textAlign="center"
                whiteSpace="nowrap"
                ml={2}
                _hover={{ bg: isDark ? "#06b6d4" : "#0369a1" }}
              >
                Detail
              </Box>
            </Box>
          </Tooltip>
        </Box>
        <Box h="350px">
          <Bar data={chartData} options={chartOptions} />
        </Box>

        <Box
          bg="var(--bg-tertiary)"
          p={3}
          borderRadius="lg"
          border="1px solid var(--border-color)"
        >
          <Text fontSize="xs" color="var(--text-tertiary)" lineHeight="1.6">
            <strong style={{ color: "var(--accent-primary)" }}>Tips:</strong>{" "}
            Klik pada salah satu skill di chart untuk melihat detail analisis,
            atau klik judul untuk melihat seluruh skill di kategori ini.
          </Text>
        </Box>
      </VStack>
    </Box>
  );
}
