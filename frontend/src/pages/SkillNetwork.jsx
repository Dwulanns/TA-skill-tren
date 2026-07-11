import { Box, Heading, Text, VStack, Divider, SimpleGrid } from "@chakra-ui/react";
import { useTheme } from "../context/ThemeContext";
import useSkillNetworkData from "../hooks/useSkillNetworkData";
import SkillNetworkFilters from "../components/SkillNetwork/SkillNetworkFilters";
import PopularSkillsAccordion from "../components/SkillNetwork/PopularSkillsAccordion";
import NetworkGraphView from "../components/SkillNetwork/NetworkGraphView";
import NodeDetailsPanel from "../components/SkillNetwork/NodeDetailsPanel";

/**
 * Skill Network Page - Refactored for clean code and separation of concerns.
 * Uses the custom hook `useSkillNetworkData` and delegates display to modular components.
 */
export default function SkillNetwork() {
  const { isDark } = useTheme();

  const {
    skillInput,
    setSkillInput,
    suggestedSkills,
    setSuggestedSkills,
    showSuggestions,
    setShowSuggestions,
    keywordId,
    setKeywordId,
    employeeSize,
    setEmployeeSize,
    filterOptions,
    employeeSizeOptions,
    loadingFilters,
    techStackSkills,
    technicalSkills,
    softSkills,
    loadingCategorySkills,
    openCategories,
    setOpenCategories,
    activeSkill,
    graphData,
    loadingGraph,
    selectedNode,
    setSelectedNode,
    fgRef,
    handleFetchCooccurrence,
    handleZoomIn,
    handleZoomOut,
    handleResetZoom,
    neighbors,
  } = useSkillNetworkData();

  return (
    <Box
      px={{ base: 3, md: 4, lg: 5 }}
      py={{ base: 3, md: 4, lg: 5 }}
      w="100%"
      bg={isDark ? "gray.900" : "gray.100"}
      minH="100vh"
    >
      <VStack align="stretch" spacing={4} maxW="1200px" mx="auto">
        {/* Header */}
        <Box>
          <Heading
            as="h1"
            size={{ base: "md", md: "lg" }}
            fontWeight="800"
            letterSpacing="-0.02em"
            mb={0.5}
            fontSize={{ base: "24px", md: "36px" }}
          >
            Skill Co-occurrence Network
          </Heading>
          <Text
            fontSize={{ base: "xs", md: "sm" }}
            color={isDark ? "gray.400" : "gray.600"}
            maxW="3xl"
            mb={1.5}
          >
            Analisis hubungan antar kompetensi yang sering muncul bersama dalam lowongan kerja. Gunakan filter untuk melihat relasi spesifik per pekerjaan dan ukuran perusahaan.
          </Text>
          <Divider borderColor={isDark ? "gray.700" : "gray.200"} />
        </Box>

        {/* Filters */}
        <SkillNetworkFilters
          keywordId={keywordId}
          setKeywordId={setKeywordId}
          employeeSize={employeeSize}
          setEmployeeSize={setEmployeeSize}
          skillInput={skillInput}
          setSkillInput={setSkillInput}
          suggestedSkills={suggestedSkills}
          setSuggestedSkills={setSuggestedSkills}
          showSuggestions={showSuggestions}
          setShowSuggestions={setShowSuggestions}
          filterOptions={filterOptions}
          employeeSizeOptions={employeeSizeOptions}
          loadingFilters={loadingFilters}
          handleFetchCooccurrence={handleFetchCooccurrence}
        />

        {/* Dashboard Grid layout */}
        <SimpleGrid columns={{ base: 1, lg: 12 }} spacing={4} alignItems="stretch">
          {/* LEFT: Categorized Skills Lists (4 Cols) */}
          <PopularSkillsAccordion
            openCategories={openCategories}
            setOpenCategories={setOpenCategories}
            techStackSkills={techStackSkills}
            technicalSkills={technicalSkills}
            softSkills={softSkills}
            loadingCategorySkills={loadingCategorySkills}
            activeSkill={activeSkill}
            handleFetchCooccurrence={handleFetchCooccurrence}
          />

          {/* RIGHT: Visualizer Canvas (8 Cols) */}
          <Box gridColumn={{ base: "span 1", lg: "span 8" }}>
            <NetworkGraphView
              activeSkill={activeSkill}
              graphData={graphData}
              loadingGraph={loadingGraph}
              selectedNode={selectedNode}
              setSelectedNode={setSelectedNode}
              neighbors={neighbors}
              fgRef={fgRef}
              handleZoomIn={handleZoomIn}
              handleZoomOut={handleZoomOut}
              handleResetZoom={handleResetZoom}
              handleFetchCooccurrence={handleFetchCooccurrence}
            />

            {/* Selected Node Details Panel */}
            <NodeDetailsPanel
              selectedNode={selectedNode}
              setSelectedNode={setSelectedNode}
              handleFetchCooccurrence={handleFetchCooccurrence}
            />
          </Box>
        </SimpleGrid>
      </VStack>
    </Box>
  );
}