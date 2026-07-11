import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Button,
  VStack,
  HStack,
  SimpleGrid,
  Heading,
  Text,
  Card,
  CardBody,
  CardHeader,
  Checkbox,
  Progress,
  Badge,
  useToast,
  Spinner,
  Divider,
  Stack,
  Wrap,
  WrapItem,
  Grid,
  GridItem,
} from "@chakra-ui/react";
import { useTheme } from "../context/ThemeContext";
import { API_ENDPOINTS } from "../config/api";

const AdminScraping = () => {
  const { isDark } = useTheme();
  const [keywords, setKeywords] = useState([]);
  const [selectedKeywords, setSelectedKeywords] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentPhase, setCurrentPhase] = useState("idle");
  const [logs, setLogs] = useState([]);
  const [scrapeProgress, setScrapeProgress] = useState({ current: 0, total: 0 });
  const [fetchDescProgress, setFetchDescProgress] = useState({ current: 0, total: 0 });
  const [extractionProgress, setExtractionProgress] = useState({ current: 0, total: 0 });
  const [overview, setOverview] = useState({ items: [], summary: null });
  const [lastScrapedAt, setLastScrapedAt] = useState(null);
  const [lastExtractionAt, setLastExtractionAt] = useState(null);
  const logEndRef = useRef(null);
  const toast = useToast();

  // Ref to track phase inside streaming callback (avoids stale closure)
  const currentPhaseRef = useRef("idle");
  // Ref for the fetch-desc animation interval
  const fetchDescIntervalRef = useRef(null);

  const bgCard = "var(--bg-secondary)";
  const borderColor = "var(--border-color)";
  const bgLog = "var(--bg-tertiary)";
  const bgMain = "var(--bg-primary)";
  const textPrimary = "var(--text-primary)";
  const textSecondary = "var(--text-secondary)";
  const textTertiary = "var(--text-tertiary)";

  useEffect(() => {
    loadKeywords();
    loadOverview();
    loadLastRuns();
  }, []);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  // Keep ref in sync
  useEffect(() => {
    currentPhaseRef.current = currentPhase;
  }, [currentPhase]);

  const setPhase = (phase) => {
    currentPhaseRef.current = phase;
    setCurrentPhase(phase);
  };

  const loadKeywords = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/admin/keywords");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const keywordList = data.keywords || [];
      setKeywords(keywordList.map((k) => ({ id: k.id, keyword: k.keyword })));
    } catch (error) {
      console.error("Error loading keywords:", error);
      toast({ title: "Error", description: `Gagal load keywords: ${error.message}`, status: "error", duration: 3000 });
    }
  };

  const loadOverview = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.ADMIN.SCRAPING_OVERVIEW);
      if (!response.ok) return;
      const data = await response.json();
      setOverview({ items: data.items || [], summary: data.summary || null });
      try {
        const scrapedTimes = (data.items || [])
          .map((it) => it.last_scraped_at)
          .filter(Boolean)
          .map((s) => new Date(s));
        if (scrapedTimes.length > 0) {
          const maxDate = new Date(Math.max(...scrapedTimes.map((d) => d.getTime())));
          setLastScrapedAt(maxDate.toLocaleString("id-ID"));
        } else {
          setLastScrapedAt(null);
        }
      } catch (e) {
        console.error("Error computing last scraped time", e);
      }
    } catch (error) {
      console.error("Error loading scraping overview:", error);
    }
  };

  const loadLastRuns = async () => {
    try {
      const url = `${API_ENDPOINTS.JOB_ANALYSIS}?limit=1&offset=0`;
      const res = await fetch(url);
      if (!res.ok) return;
      const arr = await res.json();
      if (Array.isArray(arr) && arr.length > 0) {
        setLastExtractionAt(new Date(arr[0].extracted_at).toLocaleString("id-ID"));
      } else {
        setLastExtractionAt(null);
      }
    } catch (e) {
      console.error("Error loading last extraction:", e);
    }
  };

  const handleSelectAll = () => {
    if (selectedKeywords.length === keywords.length) {
      setSelectedKeywords([]);
    } else {
      setSelectedKeywords(keywords.map((k) => k.id));
    }
  };

  const handleKeywordToggle = (keywordId) => {
    setSelectedKeywords((prev) =>
      prev.includes(keywordId) ? prev.filter((id) => id !== keywordId) : [...prev, keywordId]
    );
  };

  const addLog = (message, type = "info") => {
    const timestamp = new Date().toLocaleTimeString("id-ID");
    const prefix = { info: "ℹ️", success: "✅", warning: "⚠️", error: "❌" }[type];
    const formattedMessages = message.split("\n").map((line) => {
      if (line.trim() === "") return "";
      return `[${timestamp}] ${prefix} ${line}`;
    });
    setLogs((prev) => [...prev, ...formattedMessages]);
  };

  // ── Start the fake-progress animation for "Mengambil Deskripsi" ──────────
  // Crawls from 0 → 85% slowly, stops when extracting phase begins
  const startFetchDescAnimation = () => {
    // Clear any existing interval
    if (fetchDescIntervalRef.current) clearInterval(fetchDescIntervalRef.current);

    setPhase("fetching_desc");
    setFetchDescProgress({ current: 0, total: 100 });

    let fakeVal = 0;
    fetchDescIntervalRef.current = setInterval(() => {
      // If phase has moved to extracting, snap to 100 and stop
      if (currentPhaseRef.current === "extracting" || currentPhaseRef.current === "idle") {
        setFetchDescProgress({ current: 100, total: 100 });
        clearInterval(fetchDescIntervalRef.current);
        fetchDescIntervalRef.current = null;
        return;
      }

      // Slow crawl: big jump early, then slow down near 85
      const step = fakeVal < 40 ? 8 : fakeVal < 70 ? 4 : fakeVal < 85 ? 1 : 0;
      fakeVal = Math.min(fakeVal + step, 85);
      setFetchDescProgress({ current: fakeVal, total: 100 });
    }, 600);
  };

  const stopFetchDescAnimation = () => {
    if (fetchDescIntervalRef.current) {
      clearInterval(fetchDescIntervalRef.current);
      fetchDescIntervalRef.current = null;
    }
    setFetchDescProgress({ current: 100, total: 100 });
  };

  const runStreamingRequest = async ({ url, body, onMessage }) => {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText.slice(0, 120)}`);
    }

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
          onMessage?.(data);
        } catch (e) {
          console.error("Failed to parse SSE data:", line, e);
        }
      }

      buffer = lines[lines.length - 1];
    }
  };

  const startScraping = async () => {
    if (selectedKeywords.length === 0) {
      toast({ title: "Warning", description: "Pilih minimal 1 keyword untuk discrape", status: "warning", duration: 3000 });
      return;
    }

    setIsRunning(true);
    setPhase("scraping");
    setScrapeProgress({ current: 0, total: 0 });
    setFetchDescProgress({ current: 0, total: 0 });
    setExtractionProgress({ current: 0, total: 0 });
    setLogs([]);
    addLog("Memulai scraping...", "info");

    // Track if fetch-desc animation has been started already
    let fetchDescStarted = false;

    try {
      const keywordNames = keywords
        .filter((k) => selectedKeywords.includes(k.id))
        .map((k) => k.keyword);
      addLog(`Target keywords: ${keywordNames.join(", ")}`, "info");
      addLog("Menghubungkan ke backend scraper...", "info");

      await runStreamingRequest({
        url: API_ENDPOINTS.ADMIN.SCRAPE,
        body: { keyword_ids: selectedKeywords },
        onMessage: (data) => {
          if (data.type === "log") {
            const msg = data.message || "";

            // ── Detect phase transitions from log text ──────────────────
            const isExtractionLog =
              /EKSTRAKSI SKILL/i.test(msg) ||
              /memulai ekstraksi/i.test(msg) ||
              /extracting batch/i.test(msg);

            const isFetchDescLog =
              /mengambil deskripsi/i.test(msg) ||
              /menyimpan \d+ lowongan/i.test(msg) ||
              /\[ok\]\s*\[\d+\]/i.test(msg);

            const isScrapingLog =
              /MEMULAI SCRAPING/i.test(msg) ||
              /searching:/i.test(msg);

            if (isExtractionLog && currentPhaseRef.current !== "extracting") {
              // Scraping & fetch-desc both done → snap fetch bar to 100
              stopFetchDescAnimation();
              setPhase("extracting");
            } else if (
              isFetchDescLog &&
              !fetchDescStarted &&
              currentPhaseRef.current !== "extracting"
            ) {
              fetchDescStarted = true;
              startFetchDescAnimation();
            } else if (
              isScrapingLog &&
              currentPhaseRef.current === "idle"
            ) {
              setPhase("scraping");
            }

            addLog(msg, "info");
          } else if (data.type === "progress") {
            const phase = data.phase || currentPhaseRef.current;

            if (phase === "fetching_desc") {
              // Backend actually sent fetch-desc progress → use it directly
              if (fetchDescIntervalRef.current) {
                clearInterval(fetchDescIntervalRef.current);
                fetchDescIntervalRef.current = null;
              }
              setPhase("fetching_desc");
              setFetchDescProgress({ current: data.current, total: data.total });
            } else if (phase === "extracting") {
              stopFetchDescAnimation();
              setPhase("extracting");
              setExtractionProgress({ current: data.current, total: data.total });
            } else {
              // Default: scraping progress
              const newProg = { current: data.current, total: data.total };
              setScrapeProgress(newProg);

              // When scraping hits 100%, kick off fetch-desc animation
              if (
                data.total > 0 &&
                data.current >= data.total &&
                !fetchDescStarted &&
                currentPhaseRef.current === "scraping"
              ) {
                fetchDescStarted = true;
                startFetchDescAnimation();
              }
            }
          } else if (data.type === "success") {
            addLog(data.message, "success");
          } else if (data.type === "error") {
            addLog(data.message, "error");
          }
        },
      });

      await loadOverview();
      toast({ title: "Success", description: "Scraping berhasil selesai", status: "success", duration: 3000 });
    } catch (error) {
      console.error("Scraping error:", error);
      addLog(`❌ Error: ${error.message}`, "error");
      toast({ title: "Error", description: `Scraping gagal: ${error.message}`, status: "error", duration: 3000 });
    } finally {
      // Clean up interval if still running
      if (fetchDescIntervalRef.current) {
        clearInterval(fetchDescIntervalRef.current);
        fetchDescIntervalRef.current = null;
      }
      setIsRunning(false);
      setPhase("idle");
    }
  };

  const startExtraction = async () => {
    setIsRunning(true);
    setPhase("extracting");
    setExtractionProgress({ current: 0, total: 0 });

    try {
      addLog("Melanjutkan ekstraksi skill...", "info");

      await runStreamingRequest({
        url: API_ENDPOINTS.ADMIN.EXTRACT_SKILLS,
        onMessage: (data) => {
          if (data.type === "log") {
            addLog(data.message, "info");
          } else if (data.type === "progress") {
            setExtractionProgress({ current: data.current, total: data.total });
          } else if (data.type === "success") {
            addLog(data.message, "success");
          } else if (data.type === "error") {
            addLog(data.message, "error");
          }
        },
      });

      await loadOverview();
      toast({ title: "Success", description: "Ekstraksi skill selesai", status: "success", duration: 3000 });
    } catch (error) {
      console.error("Extraction error:", error);
      addLog(`❌ Error: ${error.message}`, "error");
      toast({ title: "Error", description: `Ekstraksi gagal: ${error.message}`, status: "error", duration: 3000 });
    } finally {
      setIsRunning(false);
      setPhase("idle");
    }
  };

  const clearLogs = () => setLogs([]);

  const pctStr = (prog) =>
    prog.total > 0
      ? `${Math.round((prog.current / prog.total) * 100)}% (${prog.current}/${prog.total})`
      : "0%";

  const pctVal = (prog) =>
    prog.total > 0 ? (prog.current / prog.total) * 100 : 0;

  const StepBar = ({ label, progress, colorScheme, isActive, isDone }) => {
    const accentColor =
      colorScheme === "cyan" ? "cyan.500" :
        colorScheme === "blue" ? "blue.500" : "purple.500";
    const dotColor =
      colorScheme === "cyan" ? "cyan.400" :
        colorScheme === "blue" ? "blue.400" : "purple.400";

    return (
      <Box>
        <HStack justify="space-between" mb={1}>
          <HStack spacing={2}>
            {isDone ? (
              <Text fontSize="xs" lineHeight="1">✅</Text>
            ) : isActive ? (
              <Box
                w="8px"
                h="8px"
                borderRadius="full"
                bg={dotColor}
                flexShrink={0}
                sx={{
                  animation: "blink 1.2s ease-in-out infinite",
                  "@keyframes blink": {
                    "0%, 100%": { opacity: 1, transform: "scale(1)" },
                    "50%": { opacity: 0.2, transform: "scale(0.7)" },
                  },
                }}
              />
            ) : (
              <Box
                w="8px"
                h="8px"
                borderRadius="full"
                bg={isDark ? "gray.600" : "gray.300"}
                flexShrink={0}
              />
            )}
            <Text
              fontSize={{ base: "xs", sm: "sm" }}
              fontWeight="700"
              color={isDone ? "green.500" : isActive ? accentColor : textTertiary}
            >
              {label}
            </Text>
          </HStack>
          <Text
            fontSize="xs"
            color={isDone ? "green.500" : isActive ? textSecondary : textTertiary}
            fontWeight={isActive ? "600" : "400"}
          >
            {isDone && progress.total === 100
              ? "100%"
              : pctStr(progress)}
          </Text>
        </HStack>
        <Progress
          value={pctVal(progress)}
          size="sm"
          colorScheme={isDone ? "green" : colorScheme}
          borderRadius="full"
          bg={isDark ? "gray.700" : "gray.100"}
          transition="value 0.4s ease"
        />
      </Box>
    );
  };

  return (
    <Box p={{ base: "1rem", sm: "1.5rem", md: "2rem", lg: "2.5rem" }} bg={bgMain}>
      <VStack align="start" mb={{ base: 6, md: 8, lg: 10 }} spacing={{ base: 2, md: 3 }}>
        <Heading
          size={{ base: "sm", sm: "md", md: "lg", lg: "xl" }}
          color={isDark ? "#ffffff" : "#000000"}
          fontWeight="800"
        >
          Scraping dan Ekstraksi Skill
        </Heading>
        <Text
          color={textSecondary}
          fontSize={{ base: "xs", sm: "sm", md: "md" }}
        >
          Scrape data lowongan pekerjaan dari LinkedIn berdasarkan keyword,
          sekaligus ekstrak skill yang dibutuhkan untuk analisis tren skill
        </Text>
        <Divider borderColor="var(--border-color)" w="100%" thickness="2px" />
      </VStack>

      {/* Responsive: Stack on mobile, row on larger screens */}
      <Stack
        direction={{ base: "column", lg: "row" }}
        spacing={{ base: 4, md: 6 }}
        align="stretch"
      >
        {/* Left Column - Full width on mobile, 1/3 on large screens */}
        <Box flex={{ base: "1", lg: "1" }} minW={{ base: "unset", lg: "300px" }}>
          <Card bg={bgCard} borderColor="var(--border-color)" borderWidth="2px" mb={{ base: 4, md: 7 }} boxShadow="var(--shadow-md)">
            <CardHeader pb={{ base: 3, md: 5 }} borderBottom="2px" borderColor={borderColor}>
              <Heading size={{ base: "xs", md: "sm" }} color="var(--accent-primary)" fontWeight="700">
                ✓ Pilih Keywords
              </Heading>
            </CardHeader>
            <CardBody>
              {keywords.length === 0 ? (
                <VStack align="center" spacing={4} py={6}>
                  <Spinner color="var(--accent-primary)" size="lg" thickness="4px" />
                  <Text color={textSecondary} fontSize="sm">Loading keywords...</Text>
                </VStack>
              ) : (
                <>
                  {/* 🔥 PERBAIKAN: Grid layout untuk keyword checkboxes */}
                  <Grid
                    templateColumns={{
                      base: "1fr",
                      sm: "repeat(2, 1fr)",
                      md: "repeat(2, 1fr)",
                      lg: "repeat(1, 1fr)"
                    }}
                    gap={{ base: 2, md: 3 }}
                    mb={4}
                  >
                    {keywords.map((keyword) => (
                      <GridItem key={keyword.id}>
                        <Checkbox
                          isChecked={selectedKeywords.includes(keyword.id)}
                          onChange={() => handleKeywordToggle(keyword.id)}
                          size={{ base: "sm", md: "md" }}
                          colorScheme="cyan"
                          spacing="0.75rem"
                        >
                          <Text fontSize={{ base: "sm", md: "md" }} fontWeight="500">
                            {keyword.keyword}
                          </Text>
                        </Checkbox>
                      </GridItem>
                    ))}
                  </Grid>

                  <Divider my={4} borderColor="var(--divider-color)" thickness="1px" />

                  <VStack align="stretch" spacing={3}>
                    <HStack justify="space-between">
                      <Text fontSize={{ base: "xs", md: "sm" }} color={textTertiary} fontWeight="600">
                        ✓ Selected
                      </Text>
                      <Badge
                        colorScheme="cyan"
                        fontSize={{ base: "xs", md: "sm" }}
                        px={3}
                        py={1}
                        borderRadius="full"
                      >
                        {selectedKeywords.length} / {keywords.length}
                      </Badge>
                    </HStack>
                    <Button
                      size={{ base: "sm", md: "md" }}
                      variant="outline"
                      colorScheme="cyan"
                      onClick={handleSelectAll}
                      w="100%"
                      fontWeight="700"
                      borderWidth="2px"
                    >
                      {selectedKeywords.length === keywords.length ? "◯ Deselect All" : "○ Select All"}
                    </Button>
                  </VStack>

                  <Divider my={4} borderColor="var(--divider-color)" thickness="1px" />

                  <VStack align="stretch" spacing={3}>
                    <Button
                      colorScheme="cyan"
                      w="100%"
                      onClick={startScraping}
                      isLoading={isRunning}
                      disabled={isRunning || selectedKeywords.length === 0}
                      size={{ base: "md", lg: "lg" }}
                      fontWeight="800"
                      bg="var(--accent-primary)"
                      color="#ffffff"
                      _hover={{ bg: "var(--accent-secondary)", boxShadow: "var(--shadow-lg)" }}
                      _disabled={{ opacity: 0.5, cursor: "not-allowed" }}
                    >
                      Mulai Scraping & Ekstrak Skill
                    </Button>

                    <Button
                      variant="outline"
                      w="100%"
                      onClick={clearLogs}
                      disabled={isRunning || logs.length === 0}
                      size={{ base: "sm", md: "md" }}
                      fontWeight="700"
                      borderWidth="2px"
                      borderColor="var(--border-color)"
                      color={isDark ? "#ffffff" : "#000000"}
                      _hover={{ bg: isDark ? "gray.700" : "gray.100" }}
                    >
                      Clear Logs
                    </Button>
                  </VStack>
                </>
              )}
            </CardBody>
          </Card>

          {/* Info Setup Card - Responsive */}
          <Card
            bg={bgCard}
            borderColor="var(--border-color)"
            borderWidth="2px"
            borderLeft="5px"
            borderLeftColor="var(--accent-primary)"
            boxShadow="var(--shadow-md)"
          >
            <CardHeader pb={{ base: 2, md: 3 }}>
              <Heading size="xs" color="var(--accent-primary)" fontWeight="700">ℹ️ Info Setup</Heading>
            </CardHeader>
            <CardBody pt={2}>
              <VStack align="start" spacing={{ base: 1, md: 2 }} fontSize={{ base: "xxs", sm: "xs" }} color={textSecondary} fontWeight="500">
                <Text>• Backend: http://localhost:8000</Text>
                <Text>• Database: SQLite</Text>
                <Text>• Rate Limit: 2-5 detik per request</Text>
                <Text>• Max Pages: Unlimited (otomatis stop)</Text>
              </VStack>
            </CardBody>
          </Card>
        </Box>

        {/* Right Column - Full width on mobile, 2/3 on large screens */}
        <Box flex={{ base: "1", lg: "1.5" }} minW={{ base: "unset", lg: "400px" }}>
          <Card bg={bgCard} borderColor={borderColor} borderWidth="1px" mb={4} boxShadow="var(--shadow-md)">
            <CardHeader pb={{ base: 2, md: 3 }} borderBottom="1px" borderColor={borderColor}>
              <Heading size={{ base: "xs", md: "sm" }}>Ringkasan Scraping & Ekstraksi</Heading>
            </CardHeader>
            <CardBody>
              {/* Responsive stat cards: 1 col on mobile, 2 on tablet, 3 on desktop */}
              <SimpleGrid columns={{ base: 1, sm: 2, md: 3 }} spacing={{ base: 2, md: 3 }} mb={4}>
                <Box p={{ base: 2, md: 3 }} borderRadius="lg" bg={bgLog}>
                  <Text fontSize={{ base: "xxs", sm: "xs" }} color={textTertiary} mb={1}>Total Keyword</Text>
                  <Text fontSize={{ base: "lg", md: "xl" }} fontWeight="800">{overview.summary?.total_keywords || 0}</Text>
                </Box>
                <Box p={{ base: 2, md: 3 }} borderRadius="lg" bg={bgLog}>
                  <Text fontSize={{ base: "xxs", sm: "xs" }} color={textTertiary} mb={1}>Job Belum di Ekstraksi</Text>
                  <Text fontSize={{ base: "lg", md: "xl" }} fontWeight="800">{overview.summary?.total_pending || 0}</Text>
                </Box>
                <Box p={{ base: 2, md: 3 }} borderRadius="lg" bg={bgLog}>
                  <Text fontSize={{ base: "xxs", sm: "xs" }} color={textTertiary} mb={1}>Skill Completed</Text>
                  <Text fontSize={{ base: "lg", md: "xl" }} fontWeight="800">{overview.summary?.total_completed || 0}</Text>
                </Box>
              </SimpleGrid>

              {/* Responsive timestamp: stacked on mobile, row on larger */}
              <Stack
                direction={{ base: "column", sm: "row" }}
                justify="space-between"
                spacing={{ base: 1, md: 0 }}
                mb={4}
              >
                <Text fontSize={{ base: "xxs", sm: "xs", md: "sm" }} color={textSecondary}>
                  Terakhir Scraping:
                  <Text as="span" fontWeight="700" ml={2}>{lastScrapedAt || "-"}</Text>
                </Text>
                <Text fontSize={{ base: "xxs", sm: "xs", md: "sm" }} color={textSecondary}>
                  Terakhir Ekstraksi:
                  <Text as="span" fontWeight="700" ml={2}>{lastExtractionAt || "-"}</Text>
                </Text>
              </Stack>

              {/* 3-step progress - responsive spacing */}
              <VStack align="stretch" spacing={{ base: 3, md: 4 }}>
                <StepBar
                  label="Scraping Data"
                  progress={scrapeProgress}
                  colorScheme="cyan"
                  isActive={currentPhase === "scraping"}
                  isDone={
                    scrapeProgress.total > 0 &&
                    scrapeProgress.current >= scrapeProgress.total &&
                    currentPhase !== "scraping"
                  }
                />
                <StepBar
                  label="Mengambil Deskripsi"
                  progress={fetchDescProgress}
                  colorScheme="blue"
                  isActive={currentPhase === "fetching_desc"}
                  isDone={
                    fetchDescProgress.current >= fetchDescProgress.total &&
                    fetchDescProgress.total > 0 &&
                    (currentPhase === "extracting" || currentPhase === "idle")
                  }
                />
                <StepBar
                  label="Extracting Skills"
                  progress={extractionProgress}
                  colorScheme="purple"
                  isActive={currentPhase === "extracting"}
                  isDone={
                    extractionProgress.total > 0 &&
                    extractionProgress.current >= extractionProgress.total &&
                    currentPhase === "idle"
                  }
                />
              </VStack>
            </CardBody>
          </Card>

          {/* Logs Card - Responsive height */}
          <Card
            bg={bgCard}
            borderColor={borderColor}
            borderWidth="1px"
            h={{ base: "300px", sm: "350px", md: "400px", lg: "500px" }}
            display="flex"
            flexDirection="column"
          >
            <CardHeader pb={{ base: 2, md: 4 }} borderBottom="1px" borderColor={borderColor}>
              <HStack justify="space-between">
                <Heading size={{ base: "xs", md: "sm" }}>Process Logs</Heading>
                {isRunning && <Badge colorScheme="green" fontSize={{ base: "xs", md: "sm" }}>Running...</Badge>}
              </HStack>
            </CardHeader>

            <Box
              flex="1"
              bg={bgLog}
              overflowY="auto"
              p={{ base: 2, md: 4 }}
              fontFamily="'Courier New', monospace"
              fontSize={{ base: "xs", sm: "sm" }}
              color={textSecondary}
              whiteSpace="pre-wrap"
              wordBreak="break-word"
              lineHeight={{ base: "1.6", md: "1.8" }}
              sx={{
                "&::-webkit-scrollbar": { width: "6px" },
                "&::-webkit-scrollbar-track": { bg: bgCard },
                "&::-webkit-scrollbar-thumb": { bg: "var(--accent-primary)", borderRadius: "3px" },
              }}
            >
              {logs.length === 0 ? (
                <Text color={textTertiary} textAlign="center" py={8}>
                  Log akan muncul di sini...
                </Text>
              ) : (
                logs.map((log, idx) => (
                  <Box key={idx} mb={log.trim() === "" ? 2 : 0}>{log}</Box>
                ))
              )}
              <Box ref={logEndRef} />
            </Box>
          </Card>
        </Box>
      </Stack>
    </Box>
  );
};

export default AdminScraping;