import { useEffect, useState } from "react";
import {
  Box,
  Heading,
  Spinner,
  Center,
  Text,
  HStack,
  Badge,
  Grid,
  Switch,
  FormControl,
  FormLabel,
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
import { API_ENDPOINTS, buildQueryString } from "../config/api";

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

const TECH_STACK_COLORS = [
  "#FF1744", // Bright Red
  "#00E5FF", // Bright Cyan
  "#FFD600", // Bright Yellow
  "#00E676", // Bright Green
  "#D500F9", // Bright Purple
  "#FF6D00", // Bright Orange
  "#00BCD4", // Teal
];

const monthLabels = [
  "Januari",
  "Februari",
  "Maret",
  "April",
  "Mei",
  "Juni",
  "Juli",
  "Agustus",
  "September",
  "Oktober",
  "November",
  "Desember",
];

export default function TechStackTrendChart({
  filters,
  activeFilterBadges: incomingFilterBadges,
}) {
  const { isDark } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analysisData, setAnalysisData] = useState(null);
  // true = garis tersambung, false = garis putus saat data kosong
  const [showContinuous, setShowContinuous] = useState(true);

  // Fallback filter badges
  const fallbackFilterBadges = [
    filters?.keyword_label ? `Job: ${filters.keyword_label}` : null,
    filters?.location ? `Lokasi: ${filters.location}` : null,
    filters?.month
      ? `Bulan: ${monthLabels[Number(filters.month) - 1] || filters.month}`
      : null,
    filters?.year ? `Tahun: ${filters.year}` : null,
  ].filter(Boolean);

  const activeFilterBadges = Array.isArray(incomingFilterBadges)
    ? incomingFilterBadges
    : fallbackFilterBadges;

  useEffect(() => {
    setLoading(true);

    const params = buildQueryString({
      keyword_id: filters?.keyword_id,
      location: filters?.location,
      employee_size: filters?.employee_size,
      month: filters?.month,
      year: filters?.year,
      skill_type_id: 3, // 3 = tech_stack
      limit: 20,
    });

    const totalJobsParams = buildQueryString({
      skill_type_id: 3, // Tech stack skill type
      keyword_id: filters?.keyword_id,
      location: filters?.location,
      employee_size: filters?.employee_size,
      month: filters?.month,
      year: filters?.year,
      limit: 5,
    });

    Promise.all([
      axios.get(`${API_ENDPOINTS.DASHBOARD.TREND_BY_MONTH}?${params}`),
      axios.get(
        `${API_ENDPOINTS.DASHBOARD.TOP_SKILLS_BY_TYPE}?${totalJobsParams}`,
      ),
    ])
      .then(([trendRes, totalJobsRes]) => {
        const topSkills = totalJobsRes?.data || [];
        const totalJobs = topSkills?.[0]?.total_jobs || 0;
        const monthlyData = trendRes.data || [];

        if (monthlyData.length === 0) {
          setLoading(false);
          return;
        }

        // Build trend map
        const skillTrendMap = {};

        monthlyData.forEach((monthItem) => {
          if (monthItem.skills && Array.isArray(monthItem.skills)) {
            monthItem.skills
              .filter((skill) => skill.skill_type === "tech_stack")
              .forEach((skill) => {
                if (!skillTrendMap[skill.skill_name]) {
                  skillTrendMap[skill.skill_name] = [];
                }

                skillTrendMap[skill.skill_name].push({
                  month: monthItem.month,
                  count: skill.count,
                });
              });
          }
        });

        // Generate month labels
        const selectedYear = filters?.year ? Number(filters.year) : null;

        let last12Months = [];

        if (selectedYear) {
          const currentYear = new Date().getFullYear();
          const currentMonth = new Date().getMonth() + 1;

          const maxMonth = selectedYear >= currentYear ? currentMonth : 12;

          for (let month = 1; month <= maxMonth; month++) {
            last12Months.push(
              `${selectedYear}-${String(month).padStart(2, "0")}`,
            );
          }
        } else {
          const allMonths = monthlyData.map((m) => m.month).sort();

          if (allMonths.length > 0) {
            const lastMonth = allMonths[allMonths.length - 1];
            const [lastYear, lastMonthNum] = lastMonth.split("-").map(Number);

            for (let i = 11; i >= 0; i--) {
              let year = lastYear;
              let month = lastMonthNum - i;

              while (month <= 0) {
                month += 12;
                year -= 1;
              }

              while (month > 12) {
                month -= 12;
                year += 1;
              }

              last12Months.push(`${year}-${String(month).padStart(2, "0")}`);
            }
          } else {
            const now = new Date();

            for (let i = 11; i >= 0; i--) {
              const d = new Date(now.getFullYear(), now.getMonth() - i, 1);

              const year = d.getFullYear();
              const month = String(d.getMonth() + 1).padStart(2, "0");

              last12Months.push(`${year}-${month}`);
            }
          }
        }

        const orderedTopSkills = topSkills.slice(0, 5);

        const skillsData = orderedTopSkills
          .map((skill, idx) => {
            const skillName = skill.skill_name;
            const data = skillTrendMap[skillName] || [];

            const color = TECH_STACK_COLORS[idx % TECH_STACK_COLORS.length];

            const processedData = last12Months.map((month) => {
              const found = data.find((d) => d.month === month);

              const val = found && found.count > 0 ? found.count : null;

              return showContinuous ? (val === null ? 0 : val) : val;
            });

            const hasPositive = processedData.some((v) => v > 0);

            if (!hasPositive && !showContinuous) {
              return null;
            }

            return {
              label: skillName,
              data: processedData,
              borderColor: color,
              backgroundColor: "transparent",
              borderWidth: 1.5,
              borderDash: [],
              tension: 0.4,
              fill: false,
              pointRadius: 3,
              pointHoverRadius: 6,
              pointBackgroundColor: color,
              pointBorderColor: "#fff",
              pointBorderWidth: 1.5,
              spanGaps: showContinuous,
              connectNulls: showContinuous,
            };
          })
          .filter(Boolean);

        if (skillsData.length === 0) {
          setData(null);
          setAnalysisData(null);
          setLoading(false);
          return;
        }

        const chartLabels = last12Months.map((m) => {
          const [year, month] = m.split("-");
          const monthNames = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
          ];

          return `${monthNames[parseInt(month) - 1]} ${year}`;
        });

        setData({
          labels: chartLabels,
          datasets: skillsData,
        });

        setAnalysisData({
          topSkill: skillsData[0]?.label || "N/A",
          totalJobs,
        });

        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [
    filters?.keyword_id,
    filters?.location,
    filters?.employee_size,
    filters?.month,
    filters?.year,
    showContinuous, // ✅ FIX: Tambahkan showContinuous ke dependency array
  ]);

  if (loading) {
    return (
      <Box
        bg="var(--bg-secondary)"
        p={6}
        borderRadius="xl"
        borderColor="var(--border-color)"
        border="1px solid"
      >
        <Center h="400px">
          <Spinner size="xl" color="var(--accent-primary)" />
        </Center>
      </Box>
    );
  }

  if (!data || !data.datasets.length) {
    return (
      <Box
        bg="var(--bg-secondary)"
        p={6}
        borderRadius="xl"
        borderColor="var(--border-color)"
        border="1px solid"
      >
        <Center h="400px">
          <Text color="var(--text-secondary)">
            Tidak ada data untuk ditampilkan
          </Text>
        </Center>
      </Box>
    );
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,

    interaction: {
      mode: "nearest",
      intersect: true,
    },

    plugins: {
      legend: {
        position: "top",
        align: "start",

        labels: {
          usePointStyle: true,
          boxWidth: 8,
          padding: 15,
          font: {
            size: 12,
            weight: "bold",
          },
          color: isDark ? "#f8fafc" : "#0f172a",
        },
      },

      tooltip: {
        mode: "nearest",
        intersect: true,
        displayColors: true,

        backgroundColor: isDark
          ? "rgba(52, 73, 94, 0.95)"
          : "rgba(226, 232, 240, 0.95)",

        padding: 12,

        titleFont: {
          size: 14,
          weight: "bold",
        },

        titleColor: isDark ? "#ffffff" : "#000000",

        bodyFont: {
          size: 13,
        },

        bodyColor: isDark ? "#ffffff" : "#000000",

        borderColor: "var(--accent-primary)",
        borderWidth: 2,

        callbacks: {
          label: (context) => {
            const value = context.parsed.y;

            return value !== null
              ? `${context.dataset.label}: ${value}`
              : `${context.dataset.label}: No Data`;
          },
        },
      },
    },

    scales: {
      y: {
        beginAtZero: true,

        grid: {
          color: isDark ? "#475569" : "#e5e7eb",
        },

        ticks: {
          font: { size: 11 },
          color: isDark ? "#cbd5e1" : "#1e293b",
        },
      },

      x: {
        grid: {
          display: false,
        },

        ticks: {
          font: { size: 11 },
          color: isDark ? "#cbd5e1" : "#1e293b",
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
      boxShadow="var(--shadow-sm)"
    >
      <Heading size="md" color="var(--text-primary)" mb={2} fontWeight="bold">
        Tech Stack Trends
      </Heading>

      <Text fontSize="sm" color="var(--text-secondary)" mb={2}>
        Tools, bahasa pemrograman, dan database yang paling dicari
      </Text>

      {/* Disclaimer Box */}
      <Box
        bg={isDark ? "rgba(2, 132, 199, 0.08)" : "rgba(2, 132, 199, 0.05)"}
        p={2.5}
        borderRadius="md"
        border="1px solid var(--border-color)"
        mb={4}
      >
        <Text
          fontSize="11px"
          color={isDark ? "#cbd5e1" : "#666666"}
          lineHeight="1.4"
        >
          ℹ️ <strong>Catatan:</strong> Grafik menampilkan jumlah kemunculan
          skill berdasarkan data lowongan yang berhasil di-scrape. Nilai kosong
          pada periode tertentu tidak selalu menunjukkan tidak adanya kebutuhan
          industri, tetapi dapat terjadi karena tidak ada data lowongan yang
          berhasil diperoleh pada periode tersebut.
        </Text>
      </Box>

      {/* Filter Badges */}
      <HStack spacing={2} mb={4} flexWrap="wrap">
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
            fontSize="0.72rem"
            fontWeight={item === "Filter: Semua Data" ? "600" : "700"}
          >
            {item}
          </Badge>
        ))}
      </HStack>

      {/* Toggle Switch */}
      <HStack spacing={4} mb={1} alignItems="center">
        <FormControl display="flex" alignItems="center" width="auto">
          <FormLabel mb="0" fontSize="sm" mr={3}>
            Tampilkan data kosong sebagai 0
          </FormLabel>

          <Switch
            isChecked={showContinuous}
            onChange={(e) => setShowContinuous(e.target.checked)}
            colorScheme="teal"
          />
        </FormControl>
      </HStack>

      <Text fontSize="xs" color="var(--text-secondary)" mb={4}>
        Aktif: data kosong ditampilkan sebagai 0. Nonaktif: data kosong tetap
        menjadi jeda pada garis.
      </Text>

      {/* Chart */}
      <Box h="450px" mb={4}>
        <Line data={data} options={options} />
      </Box>

      {/* Analysis Boxes */}
      {analysisData && (
        <Grid
          templateColumns={{
            base: "1fr",
            md: "repeat(2, 1fr)",
            lg: "repeat(4, 1fr)",
          }}
          gap={3}
          mb={3}
        >
          <Box
            bg="var(--bg-tertiary)"
            p={3}
            borderRadius="lg"
            border="1px solid var(--border-color)"
          >
            <Text
              fontSize="xs"
              color="var(--text-secondary)"
              textTransform="uppercase"
              fontWeight="bold"
              mb={1}
            >
              Top Skill
            </Text>

            <HStack>
              <Text
                fontSize="md"
                fontWeight="bold"
                color="var(--accent-primary)"
              >
                {analysisData.topSkill}
              </Text>
            </HStack>
          </Box>

          <Box
            bg="var(--bg-tertiary)"
            p={3}
            borderRadius="lg"
            border="1px solid var(--border-color)"
          >
            <Text
              fontSize="xs"
              color="var(--text-secondary)"
              textTransform="uppercase"
              fontWeight="bold"
              mb={1}
            >
              Total Lowongan
            </Text>

            <Text
              fontSize="md"
              fontWeight="bold"
              color="var(--accent-secondary)"
            >
              {analysisData.totalJobs} Lowongan
            </Text>
          </Box>
        </Grid>
      )}
    </Box>
  );
}