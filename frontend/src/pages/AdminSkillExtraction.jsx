import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Button,
  VStack,
  HStack,
  Heading,
  Text,
  Card,
  CardBody,
  CardHeader,
  Badge,
  useToast,
  Progress,
  Divider,
  FormControl,
  FormLabel,
  Select,
} from "@chakra-ui/react";
import { useTheme } from "../context/ThemeContext";

const PHASES = {
  IDLE: "idle",
  SCRAPING: "scraping",
  FETCHING_DESC: "fetching_desc",
  EXTRACTING: "extracting",
  DONE: "done",
};

function classifyLog(message) {
  if (/searching:/i.test(message) || /halaman \d+:/i.test(message)) {
    return { phase: PHASES.SCRAPING, subStatus: message };
  }
  if (
    /mengambil deskripsi/i.test(message) ||
    /\[ok\]\s*\[\d+\]/i.test(message) ||
    /tersimpan/i.test(message)
  ) {
    return { phase: PHASES.FETCHING_DESC, subStatus: message };
  }
  if (
    /ekstrak/i.test(message) ||
    /extract/i.test(message) ||
    /job_analysis/i.test(message) ||
    /batch \d+/i.test(message)
  ) {
    return { phase: PHASES.EXTRACTING, subStatus: message };
  }
  return { phase: null, subStatus: null };
}

const AdminSkillExtraction = () => {
  const { isDark } = useTheme();
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);

  const [scrapingPct, setScrapingPct] = useState(0);
  const [fetchingPct, setFetchingPct] = useState(0);
  const [extractingPct, setExtractingPct] = useState(0);

  const [scrapingStatus, setScrapingStatus] = useState("");
  const [fetchingStatus, setFetchingStatus] = useState("");
  const [extractingStatus, setExtractingStatus] = useState("");

  const [activePhase, setActivePhase] = useState(PHASES.IDLE);
  const [stats, setStats] = useState(null);
  const [batchSize, setBatchSize] = useState(50);
  const logEndRef = useRef(null);
  const toast = useToast();

  const selectedModel = "groq";
  const bgCard = "var(--bg-secondary)";
  const borderColor = "var(--border-color)";
  const bgLog = "var(--bg-tertiary)";
  const bgMain = "var(--bg-primary)";
  const textPrimary = "var(--text-primary)";
  const textSecondary = "var(--text-secondary)";
  const textTertiary = "var(--text-tertiary)";

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const loadStats = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/stats");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  };

  const addLog = (message, type = "info") => {
    const timestamp = new Date().toLocaleTimeString("id-ID");
    const prefix = { info: "ℹ️", success: "✅", warning: "⚠️", error: "❌" }[
      type
    ];
    setLogs((prev) => [...prev, `[${timestamp}] ${prefix} ${message}`]);
  };

  const applyProgressEvent = (data) => {
    const pct =
      data.total > 0 ? Math.round((data.current / data.total) * 100) : 0;
    if (data.phase === "scraping") {
      setScrapingPct(pct);
      setActivePhase(PHASES.SCRAPING);
    } else if (data.phase === "fetching_desc") {
      setScrapingPct(100);
      setFetchingPct(pct);
      setActivePhase(PHASES.FETCHING_DESC);
    } else if (data.phase === "extracting") {
      setScrapingPct(100);
      setFetchingPct(100);
      setExtractingPct(pct);
      setActivePhase(PHASES.EXTRACTING);
    } else {
      setExtractingPct(pct);
    }
  };

  const applyLogClassification = (message) => {
    const { phase, subStatus } = classifyLog(message);
    if (!phase) return;
    if (phase === PHASES.SCRAPING) {
      setActivePhase(PHASES.SCRAPING);
      setScrapingStatus(subStatus);
      setScrapingPct((p) => (p < 90 ? p + 5 : p));
    } else if (phase === PHASES.FETCHING_DESC) {
      setScrapingPct(100);
      setActivePhase(PHASES.FETCHING_DESC);
      setFetchingStatus(subStatus);
      setFetchingPct((p) => (p < 90 ? p + 10 : p));
    } else if (phase === PHASES.EXTRACTING) {
      setScrapingPct(100);
      setFetchingPct(100);
      setActivePhase(PHASES.EXTRACTING);
      setExtractingStatus(subStatus);
    }
  };

  const startExtraction = async () => {
    setIsRunning(true);
    setLogs([]);
    setScrapingPct(0);
    setFetchingPct(0);
    setExtractingPct(0);
    setScrapingStatus("");
    setFetchingStatus("");
    setExtractingStatus("");
    setActivePhase(PHASES.SCRAPING);

    addLog("Memulai ekstraksi skill...", "info");

    try {
      addLog(`AI Model: ${selectedModel}`, "info");
      addLog(`Batch Size: ${batchSize}`, "info");
      addLog(`Total Jobs: ${stats?.total_jobs || 0} untuk diproses`, "info");
      addLog("Menghubungkan ke backend AI extractor...", "info");

      const response = await fetch(
        "http://localhost:8000/api/admin/extract-skills",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ batch_size: batchSize, model: selectedModel }),
        },
      );

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i];
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "log") {
              addLog(data.message, "info");
              applyLogClassification(data.message);
            } else if (data.type === "progress") {
              applyProgressEvent(data);
            } else if (data.type === "success") {
              addLog(data.message, "success");
              applyLogClassification(data.message);
            } else if (data.type === "error") {
              addLog(data.message, "error");
            }
          } catch (e) {
            console.error("Failed to parse SSE data:", e);
          }
        }
        buffer = lines[lines.length - 1];
      }

      setScrapingPct(100);
      setFetchingPct(100);
      setExtractingPct(100);
      setActivePhase(PHASES.DONE);

      toast({
        title: "Success",
        description: "Skill extraction berhasil selesai",
        status: "success",
        duration: 3000,
      });
    } catch (error) {
      console.error("Extraction error:", error);
      addLog(`Error: ${error.message}`, "error");
      toast({
        title: "Error",
        description: "Skill extraction gagal",
        status: "error",
        duration: 3000,
      });
    } finally {
      setIsRunning(false);
    }
  };

  const clearLogs = () => setLogs([]);

  const StepProgress = ({ label, pct, subStatus, isActive, isDone }) => {
    const activeBg = isDark
      ? "rgba(139, 92, 246, 0.06)"
      : "rgba(139, 92, 246, 0.04)";
    const doneBg = isDark
      ? "rgba(34, 197, 94, 0.06)"
      : "rgba(34, 197, 94, 0.04)";

    return (
      <Box
        px={5}
        py={4}
        borderRadius="xl"
        border="1px solid"
        borderColor={
          isDone ? "green.200" : isActive ? "purple.200" : borderColor
        }
        bg={isDone ? doneBg : isActive ? activeBg : bgCard}
        transition="all 0.3s ease"
        w="100%"
      >
        <HStack justify="space-between" mb={2}>
          <HStack spacing={2}>
            {isDone ? (
              <Text fontSize="sm">✅</Text>
            ) : isActive ? (
              <Box
                w="8px"
                h="8px"
                borderRadius="full"
                bg="purple.400"
                sx={{
                  animation: "pulse 1.5s infinite",
                  "@keyframes pulse": {
                    "0%, 100%": { opacity: 1 },
                    "50%": { opacity: 0.3 },
                  },
                }}
              />
            ) : (
              <Box
                w="8px"
                h="8px"
                borderRadius="full"
                bg={isDark ? "gray.600" : "gray.300"}
              />
            )}
            <Text
              fontWeight="700"
              fontSize="sm"
              color={
                isDone ? "green.500" : isActive ? "purple.500" : textTertiary
              }
            >
              {label}
            </Text>
          </HStack>
          <Text
            fontWeight="600"
            fontSize="sm"
            color={
              isDone ? "green.500" : isActive ? "purple.500" : textTertiary
            }
          >
            {pct}%
          </Text>
        </HStack>

        <Progress
          value={pct}
          size="xs"
          borderRadius="full"
          colorScheme={isDone ? "green" : isActive ? "purple" : "gray"}
          bg={isDark ? "gray.700" : "gray.100"}
          transition="all 0.5s ease"
        />

        {subStatus && (isActive || isDone) && (
          <Text
            mt={2}
            fontSize="xs"
            color={textTertiary}
            noOfLines={1}
            title={subStatus}
            fontFamily="monospace"
          >
            {subStatus}
          </Text>
        )}
      </Box>
    );
  };

  return (
    <Box p={8} bg={bgMain}>
      <VStack align="start" mb={8} spacing={2}>
        <Heading size="lg" color={textPrimary}>
          Ekstrak Skill dari Job Description
        </Heading>
        <Text color={textSecondary}>
          Gunakan AI untuk menganalisis job description dan ekstrak skill yang
          relevan
        </Text>
      </VStack>

      <HStack spacing={8} align="start">
        {/* Left Column */}
        <Box flex="1" minW="300px">
          <Card bg={bgCard} borderColor={borderColor} borderWidth="1px" mb={6}>
            <CardHeader pb={4} borderBottom="1px" borderColor={borderColor}>
              <Heading size="sm" color={textPrimary}>
                Konfigurasi Ekstraksi
              </Heading>
            </CardHeader>
            <CardBody spacing={6}>
              <FormControl>
                <FormLabel fontSize="sm" fontWeight="bold">
                  Batch Size: {batchSize}
                </FormLabel>
                <Select
                  value={batchSize}
                  onChange={(e) => setBatchSize(parseInt(e.target.value))}
                  disabled={isRunning}
                  size="sm"
                >
                  <option value={25}>25 (Cepat, kurang akurat)</option>
                  <option value={50}>50 (Balanced)</option>
                  <option value={100}>100 (Lambat, lebih akurat)</option>
                </Select>
              </FormControl>

              <Divider />

              {stats && (
                <VStack align="start" spacing={2} fontSize="sm">
                  <HStack justify="space-between" w="100%">
                    <Text color={textTertiary}>Jobs to Process:</Text>
                    <Badge colorScheme="purple">
                      {stats.processed_jobs || 0}
                    </Badge>
                  </HStack>
                  <HStack justify="space-between" w="100%">
                    <Text color={textTertiary}>Estimated Time:</Text>
                    <Text fontWeight="bold" color={textPrimary}>
                      ~{Math.ceil((stats.processed_jobs || 0) / batchSize)}{" "}
                      menit
                    </Text>
                  </HStack>
                </VStack>
              )}

              <Divider />

              {/* 3-Step Progress */}
              <VStack spacing={3} w="100%">
                <StepProgress
                  label="Scraping Data"
                  pct={scrapingPct}
                  subStatus={scrapingStatus}
                  isActive={activePhase === PHASES.SCRAPING}
                  isDone={
                    scrapingPct === 100 &&
                    activePhase !== PHASES.SCRAPING &&
                    activePhase !== PHASES.IDLE
                  }
                />
                <StepProgress
                  label="Mengambil Deskripsi"
                  pct={fetchingPct}
                  subStatus={fetchingStatus}
                  isActive={activePhase === PHASES.FETCHING_DESC}
                  isDone={
                    fetchingPct === 100 &&
                    (activePhase === PHASES.EXTRACTING ||
                      activePhase === PHASES.DONE)
                  }
                />
                <StepProgress
                  label="Ekstraksi Skill"
                  pct={extractingPct}
                  subStatus={extractingStatus}
                  isActive={activePhase === PHASES.EXTRACTING}
                  isDone={activePhase === PHASES.DONE}
                />
              </VStack>

              <Divider />

              <Button
                colorScheme="purple"
                w="100%"
                onClick={startExtraction}
                isLoading={isRunning}
                disabled={isRunning}
                mb={2}
              >
                Mulai Ekstraksi
              </Button>

              <Button
                variant="outline"
                w="100%"
                onClick={clearLogs}
                disabled={isRunning || logs.length === 0}
              >
                Clear Logs
              </Button>
            </CardBody>
          </Card>

          <Card
            bg={bgCard}
            borderColor={borderColor}
            borderWidth="1px"
            borderLeft="4px"
            borderLeftColor="var(--accent-primary)"
          >
            <CardHeader pb={2}>
              <Heading size="xs">💡 Cara Kerja</Heading>
            </CardHeader>
            <CardBody pt={2}>
              <VStack align="start" spacing={2} fontSize="xs">
                <Text>
                  <strong>1.</strong> Scraping lowongan dari LinkedIn
                </Text>
                <Text>
                  <strong>2.</strong> Mengambil deskripsi tiap lowongan
                </Text>
                <Text>
                  <strong>3.</strong> Kirim ke AI untuk ekstrak skill
                </Text>
                <Text>
                  <strong>4.</strong> Simpan hasil ke tabel job_analysis
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </Box>

        {/* Right Column - Logs */}
        <Box flex="1.5" minW="400px">
          <Card
            bg={bgCard}
            borderColor={borderColor}
            borderWidth="1px"
            h="500px"
            display="flex"
            flexDirection="column"
          >
            <CardHeader pb={4} borderBottom="1px" borderColor={borderColor}>
              <HStack justify="space-between">
                <Heading size="sm" color={textPrimary}>
                  Extraction Logs
                </Heading>
                {isRunning && (
                  <Badge colorScheme="green" animate="pulse">
                    Processing...
                  </Badge>
                )}
              </HStack>
            </CardHeader>

            <Box
              flex="1"
              bg={bgLog}
              overflowY="auto"
              p={4}
              fontFamily="monospace"
              fontSize="xs"
              color={textSecondary}
              whiteSpace="pre-wrap"
              wordBreak="break-word"
              sx={{
                "&::-webkit-scrollbar": { width: "6px" },
                "&::-webkit-scrollbar-track": { bg: bgCard },
                "&::-webkit-scrollbar-thumb": {
                  bg: "#475569",
                  borderRadius: "3px",
                },
              }}
            >
              {logs.length === 0 ? (
                <Text color={textTertiary} textAlign="center" py={8}>
                  Log ekstraksi akan muncul di sini...
                </Text>
              ) : (
                logs.map((log, idx) => (
                  <Box key={idx} mb={1}>
                    {log}
                  </Box>
                ))
              )}
              <Box ref={logEndRef} />
            </Box>
          </Card>
        </Box>
      </HStack>
    </Box>
  );
};

export default AdminSkillExtraction;
