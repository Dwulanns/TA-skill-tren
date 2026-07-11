import { useEffect, useState, useRef } from "react";
import {
  Box,
  VStack,
  HStack,
  Grid,
  Text,
  Spinner,
  Center,
  Button,
} from "@chakra-ui/react";
import { Bar } from "react-chartjs-2";
import { useTheme } from "../context/ThemeContext";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
);

const COLORS = {
  TETAP: "rgba(2, 132, 199, 0.8)",
  NEW: "rgba(34, 197, 94, 0.8)",
  OUT: "rgba(239, 68, 68, 0.8)",
};

const BORDER_COLORS = {
  TETAP: "rgba(2, 132, 199, 1)",
  NEW: "rgba(34, 197, 94, 1)",
  OUT: "rgba(239, 68, 68, 1)",
};

export default function AlternativeSkillComparison({
  title,
  icon,
  skillData1,
  skillData2,
  period1,
  period2,
  loading1,
  loading2,
  skillType,
  onSkillClick,
  isCompact = false,
}) {
  const { isDark } = useTheme();
  const [chartData1, setChartData1] = useState(null);
  const [chartData2, setChartData2] = useState(null);
  const [statusMap1, setStatusMap1] = useState({});
  const [statusMap2, setStatusMap2] = useState({});
  const [viewMode, setViewMode] = useState("both"); // "both", "period1", "period2"
  const chartRef1 = useRef(null);
  const chartRef2 = useRef(null);

  useEffect(() => {
    if (!skillData1 || !skillData2) return;

    const map1 = {};
    const map2 = {};

    skillData1.forEach((skill) => {
      const foundInPeriod2 = skillData2.find(
        (s) => s.skill_name.toLowerCase() === skill.skill_name.toLowerCase(),
      );
      map1[skill.skill_name] = foundInPeriod2 ? "TETAP" : "OUT";
    });

    skillData2.forEach((skill) => {
      const foundInPeriod1 = skillData1.find(
        (s) => s.skill_name.toLowerCase() === skill.skill_name.toLowerCase(),
      );
      map2[skill.skill_name] = foundInPeriod1 ? "TETAP" : "NEW";
    });

    setStatusMap1(map1);
    setStatusMap2(map2);

    const top10Period1 = skillData1.slice(0, 10);
    const top10Period2 = skillData2.slice(0, 10);

    const labels1 = top10Period1.map((s) => s.skill_name);
    const data1 = top10Period1.map((s) => s.count);

    const labels2 = top10Period2.map((s) => s.skill_name);
    const data2 = top10Period2.map((s) => s.count);

    // Vertical Bar Chart Data
    setChartData1({
      labels: labels1,
      datasets: [
        {
          label: period1,
          data: data1,
          backgroundColor: data1.map((_, idx) => COLORS[map1[labels1[idx]]]),
          borderColor: data1.map((_, idx) => BORDER_COLORS[map1[labels1[idx]]]),
          borderWidth: 2,
        },
      ],
    });

    setChartData2({
      labels: labels2,
      datasets: [
        {
          label: period2,
          data: data2,
          backgroundColor: data2.map((_, idx) => COLORS[map2[labels2[idx]]]),
          borderColor: data2.map((_, idx) => BORDER_COLORS[map2[labels2[idx]]]),
          borderWidth: 2,
        },
      ],
    });
  }, [skillData1, skillData2]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    onClick: undefined,
    plugins: {
      legend: {
        labels: {
          color: isDark ? "#f8fafc" : "#0f172a",
          font: { size: 13, weight: "bold" },
          padding: 20,
          boxWidth: 18,
          boxHeight: 18,
        },
        position: "top",
      },
      tooltip: {
        backgroundColor: isDark
          ? "rgba(15, 23, 42, 0.95)"
          : "rgba(226, 232, 240, 0.95)",
        borderColor: "#0284c7",
        borderWidth: 2,
        padding: 12,
        titleFont: { size: 13, weight: "bold" },
        titleColor: "#0284c7",
        bodyFont: { size: 12 },
        bodyColor: isDark ? "#e0f2fe" : "#1e293b",
        callbacks: {
          label: (ctx) => `${ctx.parsed.y} lowongan`,
          afterLabel: (ctx) => {
            const skillName = ctx.label;
            const status =
              ctx.datasetIndex === 0
                ? statusMap1[skillName]
                : statusMap2[skillName];
            return `Status: ${status}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { color: isDark ? "#475569" : "#cbd5e0", drawBorder: false },
        ticks: { color: isDark ? "#cbd5e1" : "#64748b", font: { size: 11 } },
      },
      y: {
        grid: { color: isDark ? "#475569" : "#cbd5e0", drawBorder: false },
        ticks: { color: isDark ? "#cbd5e1" : "#64748b" },
        beginAtZero: true,
      },
    },
  };

  const chartOptions1 = {
    ...chartOptions,
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const barIndex = elements[0].index;
        if (chartData1?.labels?.[barIndex]) {
          onSkillClick?.({
            skillName: chartData1.labels[barIndex],
            skillType,
          });
        }
      }
    },
  };

  const chartOptions2 = {
    ...chartOptions,
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const barIndex = elements[0].index;
        if (chartData2?.labels?.[barIndex]) {
          onSkillClick?.({
            skillName: chartData2.labels[barIndex],
            skillType,
          });
        }
      }
    },
  };

  const horizontalChartOptions = {
    ...chartOptions,
    indexAxis: "y",
  };

  if (loading1 || loading2) {
    return (
      <Box
        bg={isDark ? "#1e293b" : "#ffffff"}
        p={isCompact ? 3 : 6}
        borderRadius="xl"
        border={isDark ? "1px solid #475569" : "1px solid #cbd5e0"}
        minH={isCompact ? "300px" : "500px"}
      >
        <Center h="100%">
          <Spinner size="lg" color="#0284c7" thickness="3px" />
        </Center>
      </Box>
    );
  }

  if (!chartData1 || !chartData2) {
    return (
      <Box
        bg={isDark ? "#1e293b" : "#ffffff"}
        p={isCompact ? 3 : 6}
        borderRadius="xl"
        border={isDark ? "1px solid #475569" : "1px solid #cbd5e0"}
        minH={isCompact ? "300px" : "500px"}
      />
    );
  }

  return (
    <Box
      bg={isDark ? "#1e293b" : "#ffffff"}
      p={isCompact ? 3 : 6}
      borderRadius="xl"
      border={isDark ? "1px solid #475569" : "1px solid #cbd5e0"}
    >
      <VStack align="stretch" spacing={isCompact ? 2 : 4}>
        {/* Toggle Buttons for View Mode */}
        <HStack spacing={2}>
          <Button
            size="sm"
            variant={viewMode === "period1" ? "solid" : "outline"}
            colorScheme="blue"
            onClick={() => setViewMode("period1")}
          >
            {period1}
          </Button>
          <Button
            size="sm"
            variant={viewMode === "period2" ? "solid" : "outline"}
            colorScheme="green"
            onClick={() => setViewMode("period2")}
          >
            {period2}
          </Button>
          <Button
            size="sm"
            variant={viewMode === "both" ? "solid" : "outline"}
            colorScheme="gray"
            onClick={() => setViewMode("both")}
          >
            Perbandingan
          </Button>
        </HStack>

        {/* Charts Display Based on View Mode */}
        <Grid
          templateColumns={
            viewMode === "both"
              ? { base: "1fr", md: "repeat(2, 1fr)" }
              : "1fr"
          }
          gap={isCompact ? 2 : 4}
        >
          {/* Period 1 - Show when viewMode is "period1" or "both" */}
          {(viewMode === "period1" || viewMode === "both") && (
            <Box>
              <Text
                fontSize={isCompact ? "xs" : "sm"}
                fontWeight="900"
                color="#0284c7"
                mb={isCompact ? 1 : 2}
              >
                {period1}
              </Text>
              {loading1 ? (
                <Center h="300px">
                  <Spinner size="lg" color="#0284c7" />
                </Center>
              ) : chartData1 ? (
                <Box
                  h={isCompact ? "250px" : "320px"}
                  cursor="pointer"
                  _hover={{ opacity: 0.9 }}
                >
                  <Bar
                    ref={chartRef1}
                    data={chartData1}
                    options={chartOptions1}
                  />
                </Box>
              ) : null}
            </Box>
          )}

          {/* Period 2 - Show when viewMode is "period2" or "both" */}
          {(viewMode === "period2" || viewMode === "both") && (
            <Box>
              <Text
                fontSize={isCompact ? "xs" : "sm"}
                fontWeight="900"
                color="#22c55e"
                mb={isCompact ? 1 : 2}
              >
                {period2}
              </Text>
              {loading2 ? (
                <Center h="300px">
                  <Spinner size="lg" color="#22c55e" />
                </Center>
              ) : chartData2 ? (
                <Box
                  h={isCompact ? "250px" : "320px"}
                  cursor="pointer"
                  _hover={{ opacity: 0.9 }}
                >
                  <Bar
                    ref={chartRef2}
                    data={chartData2}
                    options={chartOptions2}
                  />
                </Box>
              ) : null}
            </Box>
          )}
        </Grid>

        {/* Legend */}
        <Box
          bg={isDark ? "#334155" : "#e0f2fe"}
          p={isCompact ? 2 : 3}
          borderRadius="lg"
          border={isDark ? "1px solid #475569" : "1px solid #cbd5e0"}
        >
          <Text fontSize="xs" color="var(--text-tertiary)" lineHeight="1.6">
            <strong style={{ color: "var(--accent-primary)" }}>Tips:</strong>{" "}
            Klik pada salah satu skill di chart untuk melihat detail analisis.
          </Text>
        </Box>
      </VStack>
    </Box>
  );
}
