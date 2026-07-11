import {
  Box,
  Heading,
  VStack,
  Flex,
  Text,
  Badge,
  Icon,
  Tooltip,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Button,
} from "@chakra-ui/react";
import { Award, BarChart3, CheckCircle2, AlertCircle } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

/**
 * Result display panel for the Skill Matcher.
 * Shows compatibility score (radial indicator), details on matched/missing skills,
 * demand metrics from jobs analysis, and lets users toggle long skill listings.
 */
export default function MatchingResultsPanel({
  targetJobTitle,
  matchingResults,
  skillTypeFilter,
  showAllMissing,
  setShowAllMissing,
  SKILL_TYPE_FILTERS,
}) {
  const { isDark } = useTheme();

  // Style tokens
  const cardBg = isDark ? "gray.800" : "white";
  const cardBorder = isDark ? "gray.700" : "gray.100";
  const cardShadow = isDark
    ? "0 8px 25px rgba(0,0,0,0.5)"
    : "0 8px 25px rgba(0,0,0,0.05)";
  const textColor = isDark ? "white" : "gray.800";
  const subTextColor = isDark ? "gray.400" : "gray.600";

  const getScoreColor = (score) => {
    if (score >= 75) return "green";
    if (score >= 40) return "yellow";
    return "red";
  };

  const getScoreGlow = (score) => {
    if (score >= 75) return "0 0 15px rgba(16,185,129,0.4)";
    if (score >= 40) return "0 0 15px rgba(245,158,11,0.4)";
    return "0 0 15px rgba(239,68,68,0.4)";
  };

  const getFilterLabel = () =>
    SKILL_TYPE_FILTERS.find((f) => f.value === skillTypeFilter)?.label ||
    "Semua Skill";

  const hasResults = matchingResults !== null;

  return (
    <VStack align="stretch" spacing={6} gridColumn={{ lg: "span 7" }}>
      {hasResults ? (
        <Box
          bg={cardBg}
          borderWidth="1px"
          borderColor={cardBorder}
          borderRadius="xl"
          boxShadow={cardShadow}
          p={6}
          className="animate-scale-in"
        >
          <Heading
            as="h2"
            size="sm"
            fontWeight="700"
            mb={4}
            display="flex"
            alignItems="center"
          >
            <Icon as={Award} mr={2} color="green.500" />
            Hasil Analisis Kesesuaian
            <Badge ml={3} colorScheme="blue" fontSize="xs">
              {getFilterLabel()}
            </Badge>
          </Heading>

          {/* Score Circle */}
          <Flex
            direction="column"
            align="center"
            mb={6}
            py={4}
            bg={isDark ? "gray.900" : "gray.50"}
            borderRadius="xl"
          >
            <Box
              w="110px"
              h="110px"
              borderRadius="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
              bg={isDark ? "gray.800" : "white"}
              boxShadow={getScoreGlow(matchingResults.matchScore)}
              border="4px solid"
              borderColor={`${getScoreColor(matchingResults.matchScore)}.500`}
              mb={3}
            >
              <Text
                fontSize="2xl"
                fontWeight="900"
                color={`${getScoreColor(matchingResults.matchScore)}.500`}
              >
                {matchingResults.matchScore}%
              </Text>
            </Box>
            <Text fontWeight="800" fontSize="sm" color={textColor}>
              Kecocokan Kompetensi
            </Text>
            <Text fontSize="xs" color={subTextColor} mt={0.5}>
              Target: {targetJobTitle}
            </Text>
            <Text fontSize="2xs" color={subTextColor} mt={1}>
              Filter: {getFilterLabel()} •{" "}
              {matchingResults.matchedSkills.length} skill cocok dari{" "}
              {matchingResults.matchedSkills.length +
                matchingResults.missingSkills.length}{" "}
              skill yang dibutuhkan
              {matchingResults.totalJobsAnalyzed && (
                <> • Dari {matchingResults.totalJobsAnalyzed} lowongan</>
              )}
            </Text>
          </Flex>

          {/* Tab lists */}
          <Tabs variant="soft-rounded" colorScheme="blue" size="sm">
            <TabList mb={3}>
              <Tab
                fontWeight="700"
                fontSize="xs"
                color="green.500"
                _selected={{ bg: "green.500", color: "white" }}
              >
                <Icon as={CheckCircle2} size={12} mr={1} />
                Matched ({matchingResults.matchedSkills.length})
              </Tab>
              <Tab
                fontWeight="700"
                fontSize="xs"
                color="red.500"
                _selected={{ bg: "red.500", color: "white" }}
              >
                <Icon as={AlertCircle} size={12} mr={1} />
                Missing ({matchingResults.missingSkills.length})
              </Tab>
            </TabList>

            <TabPanels>
              {/* MATCHED SKILLS */}
              <TabPanel px={0} pb={0}>
                <Text fontSize="2xs" color={subTextColor} mb={2}>
                  Angka = % lowongan yang meminta skill ini.
                </Text>
                {matchingResults.matchedSkills.length === 0 ? (
                  <Text fontSize="xs" color={subTextColor}>
                    Tidak ada skill yang cocok.
                  </Text>
                ) : (
                  <Flex wrap="wrap" gap={1.5}>
                    {matchingResults.matchedSkills.map((skill, i) => {
                      const detail = matchingResults.matchedDetails?.[i];
                      return (
                        <Tooltip
                          key={skill}
                          label={
                            detail
                              ? `Diminta ${detail.demand} dari ${matchingResults.totalJobsAnalyzed} lowongan (${detail.demandPct}% pasar) · Kontribusi ke score: ${detail.contribution}%`
                              : skill
                          }
                          placement="top"
                          hasArrow
                        >
                          <Button
                            size="xs"
                            colorScheme="green"
                            variant="outline"
                            borderRadius="lg"
                            cursor="default"
                            rightIcon={
                              detail ? (
                                <Text fontSize="2xs" opacity={0.8}>
                                  {detail.demandPct}%
                                </Text>
                              ) : null
                            }
                            fontWeight="600"
                            textTransform="none"
                          >
                            {skill}
                          </Button>
                        </Tooltip>
                      );
                    })}
                  </Flex>
                )}
              </TabPanel>

              {/* MISSING SKILLS */}
              <TabPanel px={0} pb={0}>
                <Text fontSize="2xs" color={subTextColor} mb={2}>
                  Angka = % lowongan yang meminta skill ini.
                </Text>
                {matchingResults.missingSkills.length === 0 ? (
                  <Text fontSize="xs" color="green.500" fontWeight="600">
                    Selamat! Semua skill terpenuhi.
                  </Text>
                ) : (
                  <VStack align="stretch" spacing={3}>
                    <Flex wrap="wrap" gap={1.5}>
                      {(showAllMissing
                        ? matchingResults.missingSkills
                        : matchingResults.missingSkills.slice(0, 10)
                      ).map((skill) => {
                        const origIndex =
                          matchingResults.missingSkills.indexOf(skill);
                        const detail =
                          matchingResults.missingDetails?.[origIndex];
                        return (
                          <Tooltip
                            key={skill}
                            label={
                              detail
                                ? `Diminta ${detail.demand} dari ${matchingResults.totalJobsAnalyzed} lowongan (${detail.demandPct}% pasar) · Kontribusi ke score: ${detail.contribution}%`
                                : skill
                            }
                            placement="top"
                            hasArrow
                          >
                            <Button
                              size="xs"
                              colorScheme="red"
                              variant="outline"
                              borderRadius="lg"
                              cursor="default"
                              rightIcon={
                                detail ? (
                                  <Text fontSize="2xs" opacity={0.8}>
                                    {detail.demandPct}%
                                  </Text>
                                ) : null
                              }
                              fontWeight="600"
                              textTransform="none"
                            >
                              {skill}
                            </Button>
                          </Tooltip>
                        );
                      })}
                    </Flex>
                    {matchingResults.missingSkills.length > 10 && (
                      <Button
                        size="xs"
                        variant="ghost"
                        colorScheme="red"
                        onClick={() => setShowAllMissing(!showAllMissing)}
                        w="fit-content"
                        fontSize="2xs"
                        fontWeight="700"
                      >
                        {showAllMissing
                          ? "Tampilkan Lebih Sedikit"
                          : `Lihat Lebih Banyak (${
                              matchingResults.missingSkills.length - 10
                            } skill lagi)`}
                      </Button>
                    )}
                  </VStack>
                )}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Box>
      ) : (
        <Box
          bg={cardBg}
          borderWidth="1px"
          borderColor={cardBorder}
          borderRadius="xl"
          boxShadow={cardShadow}
          p={6}
          display="flex"
          alignItems="center"
          justifyContent="center"
          minH="200px"
        >
          <VStack spacing={3}>
            <Icon as={BarChart3} size={40} color="gray.500" />
            <Text fontSize="sm" color={subTextColor} textAlign="center">
              Belum ada analisis. Silakan pilih target pekerjaan dan tambahkan
              skill Anda, lalu klik "Hitung Kesesuaian".
            </Text>
          </VStack>
        </Box>
      )}
    </VStack>
  );
}
