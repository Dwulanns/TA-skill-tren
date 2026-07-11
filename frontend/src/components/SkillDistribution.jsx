/**
 * SkillDistribution Component
 * ============================
 * Menampilkan bar chart untuk distribusi skill bertipe TECHNICAL_SKILL
 *
 * DATA SOURCE: /api/dashboard/top-skills-by-type (dari database)
 * =====================================================================
 * ✅ Data diambil dari backend API endpoint
 * ✅ Backend query database: Skill, JobSkill, Job tables
 * ✅ Bukan hardcoded atau mock data
 * ✅ Real data dari LinkedIn scraper yang disimpan di database
 *
 * Data Flow:
 * 1. Component mount
 * 2. useEffect() trigger
 * 3. axios.get('/api/dashboard/top-skills-by-type?skill_type_id=2')
 * 4. Backend query database untuk skill tipe 'technical_skill'
 * 5. Database return [{skill_name, count}, ...]
 * 6. Chart render dengan real data
 *
 * Filter Query Parameters:
 * - skill_type_id: 2 (technical_skill)
 * - keyword_id: optional
 * - location: optional
 * - month: optional
 * - year: optional
 * - limit: 10 (top 10 skills)
 */
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
import { useTheme } from "../context/ThemeContext";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Legend);

import { API_ENDPOINTS, buildQueryString } from "../config/api";

export default function SkillDistribution({
  filters,
  onSkillClick,
  onExpandClick,
  activeFilterBadges = [],
}) {
  const { isDark } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    // Query parameters untuk filter data dari database
    // buildQueryString() filters out empty values untuk prevent 422 errors
    const params = buildQueryString({
      skill_type_id: 2, // 2 = technical_skill (dari SkillType table)
      keyword_id: filters?.keyword_id, // optional: Keyword table ID
      location: filters?.location, // optional: Job.location filter
      employee_size: filters?.employee_size, // optional: Job.employee_size filter
      month: filters?.month, // optional: extract(month from Job.posted_date)
      year: filters?.year, // optional: extract(year from Job.posted_date)
      limit: 10, // top 10 skills
    });

    const url = `${API_ENDPOINTS.DASHBOARD.TOP_SKILLS_BY_TYPE}?${params}`;
    console.log("SkillDistribution fetching:", url);

    axios
      .get(url, { timeout: 30000 })
      .then((res) => {
        console.log("SkillDistribution (Technical Skill) data:", res.data);
        const skillData = Array.isArray(res.data) ? res.data : [];
        setData(skillData.length > 0 ? skillData : []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("SkillDistribution error:", err);
        console.error("Error status:", err.response?.status);
        console.error("Error data:", err.response?.data);
        setError(
          err.response?.data?.detail || err.message || "Failed to load data",
        );
        setData([]);
        setLoading(false);
      });
  }, [filters?.keyword_id, filters?.location, filters?.employee_size, filters?.month, filters?.year]);

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
            <p>{error || "No data available"}</p>
          </Box>
        </Center>
      </Box>
    );
  }

  const chartData = {
    labels: data.slice(0, 10).map((d, i) => `${i + 1}. ${d.skill_name}`) || [],
    datasets: [
      {
        label: "Jumlah Lowongan",
        data: data.slice(0, 10).map((d) => d.count) || [],
        backgroundColor: isDark
          ? [
              "rgba(2, 132, 199, 0.8)",
              "rgba(6, 182, 212, 0.8)",
              "rgba(14, 165, 233, 0.8)",
              "rgba(34, 211, 232, 0.8)",
              "rgba(2, 132, 199, 0.6)",
              "rgba(6, 182, 212, 0.6)",
              "rgba(14, 165, 233, 0.6)",
              "rgba(34, 211, 232, 0.6)",
              "rgba(99, 178, 157, 0.7)",
              "rgba(79, 172, 254, 0.7)",
            ]
          : [
              "rgba(2, 132, 199, 0.9)",
              "rgba(3, 105, 161, 0.9)",
              "rgba(5, 150, 213, 0.85)",
              "rgba(6, 182, 212, 0.8)",
              "rgba(2, 132, 199, 0.7)",
              "rgba(3, 105, 161, 0.7)",
              "rgba(5, 150, 213, 0.65)",
              "rgba(6, 182, 212, 0.6)",
              "rgba(5, 150, 213, 0.75)",
              "rgba(2, 132, 199, 0.8)",
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

  const options = {
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
        titleFont: { size: 14, weight: "bold" },
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
            skillType: "technical_skill",
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
                    skillTypeId: 2,
                    skillType: "technical_skill",
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
                  Technical Skills Paling Dibutuhkan
                </Heading>
                <Text
                  fontSize="xs"
                  color="var(--text-tertiary)"
                  fontWeight="normal"
                  mt={1}
                >
                  10 Kemampuan teknis & expertise yang paling dicari industri
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
          <Bar data={chartData} options={options} />
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
