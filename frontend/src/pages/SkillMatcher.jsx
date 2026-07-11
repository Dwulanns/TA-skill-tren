import { Box, Heading, Text, VStack, Divider, SimpleGrid } from "@chakra-ui/react";
import { useTheme } from "../context/ThemeContext";
import useSkillMatcherData from "../hooks/useSkillMatcherData";
import SkillMatcherFilters from "../components/SkillMatcher/SkillMatcherFilters";
import MatchingResultsPanel from "../components/SkillMatcher/MatchingResultsPanel";

/**
 * Skill Matcher Page - Refactored for clean code and separation of concerns.
 * Uses the custom hook `useSkillMatcherData` and delegates display to modular components.
 */
export default function SkillMatcher() {
  const { isDark } = useTheme();

  const {
    jobOptions,
    loadingOptions,
    targetJobTitle,
    setTargetJobTitle,
    employeeSize,
    setEmployeeSize,
    employeeSizeOptions,
    loadingEmployeeSizes,
    skillInput,
    setSkillInput,
    userSkills,
    dbSkills,
    dbSkillsType,
    loadingDbSkills,
    matchingResults,
    loadingMatch,
    suggestedSkills,
    setSuggestedSkills,
    showSuggestions,
    setShowSuggestions,
    skillTypeFilter,
    setSkillTypeFilter,
    showAllMissing,
    setShowAllMissing,
    handleAddSkill,
    handleRemoveSkill,
    handleKeyPress,
    fetchDbSkills,
    handleCalculateMatch,
    SKILL_TYPE_FILTERS,
  } = useSkillMatcherData();

  const pageBg = isDark ? "gray.900" : "gray.50";
  const textColor = isDark ? "white" : "gray.800";
  const subTextColor = isDark ? "gray.400" : "gray.600";

  return (
    <Box px={{ base: 4, md: 6 }} py={6} bg={pageBg} minH="100vh">
      <VStack align="stretch" spacing={6} maxW="1500px" mx="auto">
        {/* Header */}
        <Box>
          <Heading
            as="h1"
            size={{ base: "lg", md: "xl" }}
            fontWeight="800"
            letterSpacing="-0.02em"
            color={textColor}
            mb={2}
          >
            Skill Matcher & Skill Network
          </Heading>
          <Text
            fontSize={{ base: "sm", md: "md" }}
            color={subTextColor}
            maxW="4xl"
          >
            Hitung kesesuaian skill Anda terhadap target pekerjaan industri dan
            lihat peta hubungan skill.
          </Text>
          <Divider mt={3} borderColor={isDark ? "gray.700" : "gray.200"} />
        </Box>

        {/* Main Layout */}
        <SimpleGrid columns={{ base: 1, lg: 12 }} spacing={6}>
          {/* LEFT PANEL: FORM */}
          <SkillMatcherFilters
            targetJobTitle={targetJobTitle}
            setTargetJobTitle={setTargetJobTitle}
            jobOptions={jobOptions}
            loadingOptions={loadingOptions}
            employeeSize={employeeSize}
            setEmployeeSize={setEmployeeSize}
            employeeSizeOptions={employeeSizeOptions}
            loadingEmployeeSizes={loadingEmployeeSizes}
            skillInput={skillInput}
            setSkillInput={setSkillInput}
            suggestedSkills={suggestedSkills}
            setSuggestedSkills={setSuggestedSkills}
            showSuggestions={showSuggestions}
            setShowSuggestions={setShowSuggestions}
            handleAddSkill={handleAddSkill}
            handleRemoveSkill={handleRemoveSkill}
            handleKeyPress={handleKeyPress}
            dbSkillsType={dbSkillsType}
            fetchDbSkills={fetchDbSkills}
            loadingDbSkills={loadingDbSkills}
            dbSkills={dbSkills}
            userSkills={userSkills}
            skillTypeFilter={skillTypeFilter}
            setSkillTypeFilter={setSkillTypeFilter}
            handleCalculateMatch={handleCalculateMatch}
            loadingMatch={loadingMatch}
            SKILL_TYPE_FILTERS={SKILL_TYPE_FILTERS}
          />

          {/* RIGHT PANEL: RESULTS */}
          <MatchingResultsPanel
            targetJobTitle={targetJobTitle}
            matchingResults={matchingResults}
            skillTypeFilter={skillTypeFilter}
            showAllMissing={showAllMissing}
            setShowAllMissing={setShowAllMissing}
            SKILL_TYPE_FILTERS={SKILL_TYPE_FILTERS}
          />
        </SimpleGrid>
      </VStack>
    </Box>
  );
}
