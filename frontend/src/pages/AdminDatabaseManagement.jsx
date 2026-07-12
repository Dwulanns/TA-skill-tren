import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
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
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  useToast,
  Spinner,
  Input,
  Select,
  InputGroup,
  InputLeftElement,
} from "@chakra-ui/react";
import { useTheme } from "../context/ThemeContext";
import { ChevronLeftIcon, ChevronRightIcon, SearchIcon } from "@chakra-ui/icons";
import { API_ENDPOINTS } from "../config/api";

// ===========================
// TableHeader — moved OUTSIDE the main component.
// This is the actual fix for the "search loses focus every keystroke" bug:
// when this was defined inside AdminDatabaseManagement, every re-render
// (which happens on every keystroke, since typing updates state) created
// a brand-new component function. React then unmounted the old <Input>
// DOM node and mounted a fresh one, which is why focus dropped after
// every single character. Defining it here means the function identity
// stays stable across renders, so the <Input> stays the same DOM node
// and focus is never lost.
// ===========================
const TableHeader = ({
  title,
  count,
  onSort,
  searchTerm,
  onSearchChange,
  filteredCount,
  sortConfig,
  onSortChange,
  searchInputRef,
  isDark,
  textPrimary,
  textTertiary,
  textSecondary,
  accentColor,
  borderColor,
}) => (
  <VStack align="stretch" mb={5} spacing={3}>
    <HStack justify="space-between" flexWrap="wrap" spacing={3}>
      <VStack align="start" spacing={0}>
        <Heading size="md" color={textPrimary} fontWeight="700">
          {title}
        </Heading>
        <Text fontSize="sm" color={textTertiary}>
          Total: <strong style={{ color: accentColor }}>{count}</strong> records
          {searchTerm && (
            <span style={{ marginLeft: "8px", color: accentColor }}>
              | Found: {filteredCount}
            </span>
          )}
        </Text>
      </VStack>
      <InputGroup maxW="280px">
        <InputLeftElement pointerEvents="none" height="36px">
          <SearchIcon color={textTertiary} fontSize="14px" />
        </InputLeftElement>
        <Input
          ref={searchInputRef}
          placeholder="Search..."
          value={searchTerm}
          onChange={onSearchChange}
          size="sm"
          height="36px"
          fontSize="14px"
          pl={9}
          bg={isDark ? "rgba(22, 27, 34, 0.8)" : "gray.50"}
          borderColor={borderColor}
          color={textPrimary}
          _hover={{ borderColor: accentColor }}
          _focus={{
            borderColor: accentColor,
            boxShadow: `0 0 0 3px ${isDark ? "rgba(88, 166, 255, 0.25)" : "rgba(66, 153, 225, 0.15)"}`,
          }}
          borderRadius="md"
        />
      </InputGroup>
    </HStack>
    {onSort && (
      <HStack spacing={2}>
        <Text fontSize="xs" fontWeight="600" color={textSecondary}>
          Sort by ID:
        </Text>
        <Button
          size="xs"
          variant={sortConfig.direction === "asc" ? "solid" : "outline"}
          colorScheme="blue"
          onClick={() => onSortChange({ column: "id", direction: "asc" })}
          fontSize="11px"
          height="28px"
        >
          ↑ Ascending
        </Button>
        <Button
          size="xs"
          variant={sortConfig.direction === "desc" ? "solid" : "outline"}
          colorScheme="blue"
          onClick={() => onSortChange({ column: "id", direction: "desc" })}
          fontSize="11px"
          height="28px"
        >
          ↓ Descending
        </Button>
      </HStack>
    )}
  </VStack>
);

// TableFooter — also moved outside for the same reason as TableHeader above.
const TableFooter = ({
  filteredCount,
  pagination,
  onPaginationChange,
  textPrimary,
  textSecondary,
  textTertiary,
  accentColor,
  borderColor,
  hoverBg,
  isDark,
}) => {
  const totalPages = Math.ceil(filteredCount / pagination.limit) || 1;
  const currentPage = Math.min(pagination.page, totalPages);

  return (
    <HStack
      justify="space-between"
      mt={6}
      pt={4}
      borderTop="1px"
      borderTopColor={borderColor}
      flexWrap="wrap"
      spacing={3}
    >
      <HStack spacing={2}>
        <Button
          size="sm"
          leftIcon={<ChevronLeftIcon />}
          onClick={() =>
            onPaginationChange({
              ...pagination,
              page: Math.max(1, currentPage - 1),
            })
          }
          isDisabled={currentPage === 1}
          fontSize="13px"
          height="34px"
          variant="outline"
          borderColor={borderColor}
          _hover={{ bg: hoverBg }}
        >
          Previous
        </Button>
        <Text fontSize="sm" color={textSecondary} fontWeight="500">
          Page <strong style={{ color: accentColor }}>{currentPage}</strong> of {totalPages}
        </Text>
        <Button
          size="sm"
          rightIcon={<ChevronRightIcon />}
          onClick={() =>
            onPaginationChange({
              ...pagination,
              page: Math.min(totalPages, currentPage + 1),
            })
          }
          isDisabled={currentPage === totalPages}
          fontSize="13px"
          height="34px"
          variant="outline"
          borderColor={borderColor}
          _hover={{ bg: hoverBg }}
        >
          Next
        </Button>
      </HStack>
      <HStack spacing={2}>
        <Text fontSize="xs" color={textTertiary}>
          {filteredCount > 0
            ? `${Math.min((currentPage - 1) * pagination.limit + 1, filteredCount)}-${Math.min(currentPage * pagination.limit, filteredCount)}`
            : "0"}{" "}
          of {filteredCount}
        </Text>
        <Select
          value={pagination.limit}
          onChange={(e) => {
            onPaginationChange({
              ...pagination,
              limit: parseInt(e.target.value),
              page: 1,
            });
          }}
          maxW="100px"
          size="sm"
          bg={isDark ? "rgba(22, 27, 34, 0.8)" : "gray.50"}
          borderColor={borderColor}
          color={textPrimary}
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </Select>
      </HStack>
    </HStack>
  );
};

const AdminDatabaseManagement = () => {
  const { isDark } = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [allJobs, setAllJobs] = useState([]);
  const [allSkills, setAllSkills] = useState([]);
  const [allKeywords, setAllKeywords] = useState([]);
  const [allJobAnalysis, setAllJobAnalysis] = useState([]);
  const [allSkillTypes, setAllSkillTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [pagination, setPagination] = useState({ page: 1, limit: 20 });
  const [sortConfig, setSortConfig] = useState({
    column: "id",
    direction: "asc",
  });
  const toast = useToast();
  const searchInputRef = useRef(null);

  // Theme colors - Dark mode lebih terang
  const bgMain = isDark ? "#0d1117" : "#f0f4f8";
  const bgCard = isDark ? "rgba(22, 27, 34, 0.92)" : "rgba(255, 255, 255, 0.85)";
  const borderColor = isDark ? "rgba(88, 166, 255, 0.2)" : "rgba(66, 153, 225, 0.1)";
  const textPrimary = isDark ? "#f0f6fc" : "#2d3748";
  const textSecondary = isDark ? "#c9d1d9" : "#718096";
  const textTertiary = isDark ? "#8b949e" : "#a0aec0";
  const accentColor = isDark ? "#58a6ff" : "#4299e1";
  const hoverBg = isDark ? "rgba(88, 166, 255, 0.15)" : "rgba(66, 153, 225, 0.05)";

  // Warna solid seperti LinkedIn - Dark mode lebih terang
  const linkedinBlue = isDark ? "#1f6feb" : "#0a66c2";
  const tableHeaderBg = linkedinBlue;
  const tableHeaderText = "#ffffff";

  // Filter data menggunakan useMemo agar tidak re-render berlebihan
  const getFilteredData = useMemo(() => {
    let data = [];
    if (activeTab === 0) data = Array.isArray(allJobs) ? [...allJobs] : [];
    else if (activeTab === 1) data = Array.isArray(allKeywords) ? [...allKeywords] : [];
    else if (activeTab === 2) data = Array.isArray(allSkills) ? [...allSkills] : [];
    else if (activeTab === 3) data = Array.isArray(allJobAnalysis) ? [...allJobAnalysis] : [];
    else if (activeTab === 4) data = Array.isArray(allSkillTypes) ? [...allSkillTypes] : [];

    if (data.length === 0) return data;

    // Filter by search term
    if (searchTerm.trim() !== "") {
      const searchLower = searchTerm.toLowerCase().trim();
      data = data.filter((item) => {
        return Object.values(item).some((val) =>
          String(val).toLowerCase().includes(searchLower)
        );
      });
    }

    return data;
  }, [allJobs, allKeywords, allSkills, allJobAnalysis, allSkillTypes, searchTerm, activeTab]);

  // Apply sorting and pagination
  const paginatedData = useMemo(() => {
    let data = [...getFilteredData];

    if (data.length === 0) return [];

    // Apply sorting
    data.sort((a, b) => {
      let aVal = a[sortConfig.column];
      let bVal = b[sortConfig.column];

      if (typeof aVal === "string") {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (aVal < bVal) return sortConfig.direction === "asc" ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === "asc" ? 1 : -1;
      return 0;
    });

    // Apply pagination
    const start = (pagination.page - 1) * pagination.limit;
    const end = start + pagination.limit;
    return data.slice(start, end);
  }, [getFilteredData, pagination, sortConfig]);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 0) {
        const response = await fetch(`${API_ENDPOINTS.JOBS}?limit=500`);
        const data = await response.json();
        setAllJobs(Array.isArray(data) ? data : []);
      } else if (activeTab === 1) {
        const response = await fetch(API_ENDPOINTS.ADMIN.KEYWORDS);
        const data = await response.json();
        setAllKeywords(Array.isArray(data?.keywords) ? data.keywords : []);
      } else if (activeTab === 2) {
        const response = await fetch(`${API_ENDPOINTS.TOP_SKILLS}?limit=100`);
        const data = await response.json();
        setAllSkills(Array.isArray(data) ? data : []);
      } else if (activeTab === 3) {
        const response = await fetch(`${API_ENDPOINTS.JOB_ANALYSIS}?offset=0&limit=1000`);
        const data = await response.json();
        setAllJobAnalysis(Array.isArray(data) ? data : []);
      } else if (activeTab === 4) {
        const response = await fetch(API_ENDPOINTS.DASHBOARD.SKILLS_BY_TYPE);
        const data = await response.json();
        setAllSkillTypes(Array.isArray(data) ? data : []);
      }
      setPagination({ page: 1, limit: 20 });
      setSearchTerm("");
    } catch (error) {
      console.error("Error loading data:", error);
      toast({
        title: "Error",
        description: "Failed to load data",
        status: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  // Gunakan useCallback untuk handle search change
  const handleSearchChange = useCallback((e) => {
    const value = e.target.value;
    setSearchTerm(value);
    setPagination((prev) => ({ ...prev, page: 1 }));
  }, []);

  // NOTE: the old "re-focus on every searchTerm change" useEffect was removed.
  // It was a band-aid for the remount bug above, and was itself unreliable
  // (race condition between unmount/mount and the focus() call). With
  // TableHeader stabilized outside the component, the <Input> DOM node
  // never unmounts while typing, so focus is naturally preserved and this
  // effect is no longer needed.

  const formatDateTime = (value) => {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "-";
    return date.toLocaleString("id-ID", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Get current data berdasarkan activeTab
  const currentData = paginatedData;

  // Shared props bundle for TableHeader/TableFooter to avoid repeating the
  // same long prop list five times below.
  const headerThemeProps = {
    isDark,
    textPrimary,
    textTertiary,
    textSecondary,
    accentColor,
    borderColor,
  };
  const footerThemeProps = {
    textPrimary,
    textSecondary,
    textTertiary,
    accentColor,
    borderColor,
    hoverBg,
    isDark,
  };

  return (
    <Box p={8} bg={bgMain} minH="100vh">
      {/* Header - Bold Database */}
     <VStack align="start" mb={8} spacing={2}>
  <Heading 
    size="lg" 
    color={textPrimary} 
    fontWeight="900" 
    letterSpacing="tight"
    fontSize={{ base: "28px", md: "36px" }}
  >
    <span style={{ fontWeight: 800 }}>Database</span>
  </Heading>
  <Text 
    color={textSecondary} 
    fontSize={{ base: "14px", md: "16px" }} 
    fontWeight="500"
  >
    Kelola tabel: Jobs, Keywords, Skills, Job Analysis, dan Skill Types
  </Text>
</VStack>
      <Card
        bg={bgCard}
        borderColor={borderColor}
        borderWidth="1px"
        borderRadius="xl"
        boxShadow="0 8px 32px rgba(66, 153, 225, 0.06)"
        backdropFilter="blur(12px)"
      >
        <CardBody p={0}>
          <Tabs index={activeTab} onChange={setActiveTab} variant="enclosed">
            <TabList p={4} borderBottomColor={borderColor} flexWrap="wrap" gap={1}>
              <Tab
                fontSize="14px"
                fontWeight="600"
                color={textSecondary}
                _selected={{
                  color: isDark ? "#58a6ff" : "#2b6cb0",
                  bg: isDark ? "rgba(88, 166, 255, 0.15)" : "rgba(66, 153, 225, 0.1)",
                }}
                borderRadius="full"
                px={4}
                py={2}
                _hover={{ bg: hoverBg }}
              >
                Jobs ({getFilteredData.length > 0 && searchTerm ? getFilteredData.length : allJobs.length})
              </Tab>
              <Tab
                fontSize="14px"
                fontWeight="600"
                color={textSecondary}
                _selected={{
                  color: isDark ? "#58a6ff" : "#2b6cb0",
                  bg: isDark ? "rgba(88, 166, 255, 0.15)" : "rgba(66, 153, 225, 0.1)",
                }}
                borderRadius="full"
                px={4}
                py={2}
                _hover={{ bg: hoverBg }}
              >
                Keywords ({getFilteredData.length > 0 && searchTerm ? getFilteredData.length : allKeywords.length})
              </Tab>
              <Tab
                fontSize="14px"
                fontWeight="600"
                color={textSecondary}
                _selected={{
                  color: isDark ? "#58a6ff" : "#2b6cb0",
                  bg: isDark ? "rgba(88, 166, 255, 0.15)" : "rgba(66, 153, 225, 0.1)",
                }}
                borderRadius="full"
                px={4}
                py={2}
                _hover={{ bg: hoverBg }}
              >
                Skills ({getFilteredData.length > 0 && searchTerm ? getFilteredData.length : allSkills.length})
              </Tab>
              <Tab
                fontSize="14px"
                fontWeight="600"
                color={textSecondary}
                _selected={{
                  color: isDark ? "#58a6ff" : "#2b6cb0",
                  bg: isDark ? "rgba(88, 166, 255, 0.15)" : "rgba(66, 153, 225, 0.1)",
                }}
                borderRadius="full"
                px={4}
                py={2}
                _hover={{ bg: hoverBg }}
              >
                Job Analysis ({getFilteredData.length > 0 && searchTerm ? getFilteredData.length : allJobAnalysis.length})
              </Tab>
              <Tab
                fontSize="14px"
                fontWeight="600"
                color={textSecondary}
                _selected={{
                  color: isDark ? "#58a6ff" : "#2b6cb0",
                  bg: isDark ? "rgba(88, 166, 255, 0.15)" : "rgba(66, 153, 225, 0.1)",
                }}
                borderRadius="full"
                px={4}
                py={2}
                _hover={{ bg: hoverBg }}
              >
                Skill Types ({getFilteredData.length > 0 && searchTerm ? getFilteredData.length : allSkillTypes.length})
              </Tab>
            </TabList>

            <TabPanels>
              {/* Jobs Tab */}
              <TabPanel p={6}>
                {loading ? (
                  <Box display="flex" justifyContent="center" py={10}>
                    <Spinner size="xl" color="blue.500" thickness="3px" />
                  </Box>
                ) : (
                  <>
                    <TableHeader
                      title="Jobs"
                      count={allJobs.length}
                      onSort={true}
                      searchTerm={searchTerm}
                      onSearchChange={handleSearchChange}
                      filteredCount={getFilteredData.length}
                      sortConfig={sortConfig}
                      onSortChange={setSortConfig}
                      searchInputRef={searchInputRef}
                      {...headerThemeProps}
                    />
                    <Box overflowX="auto" mb={4} borderRadius="lg">
                      <Table size="sm" variant="simple">
                        <Thead bg={tableHeaderBg}>
                          <Tr>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>ID</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Title</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Company</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Location</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Keyword</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Created At</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Source</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {currentData.length > 0 ? (
                            currentData.map((job, idx) => (
                              <Tr
                                key={job.id}
                                bg={idx % 2 === 0 ? (isDark ? "rgba(88, 166, 255, 0.06)" : "rgba(66, 153, 225, 0.02)") : "transparent"}
                                _hover={{ bg: hoverBg }}
                                transition="all 0.15s"
                              >
                                <Td fontSize="13px" fontWeight="600" color={textPrimary} textAlign="center">{job.id}</Td>
                                <Td fontSize="13px" color={textPrimary}>
                                  <Text isTruncated maxW="200px" title={job.job_title || ""}>
                                    {job.job_title || "-"}
                                  </Text>
                                </Td>
                                <Td fontSize="13px" color={textPrimary}>
                                  <Text isTruncated maxW="150px" title={job.company || ""}>
                                    {job.company || "-"}
                                  </Text>
                                </Td>
                                <Td fontSize="13px" color={textPrimary} textAlign="center">{job.location || "-"}</Td>
                                <Td fontSize="13px" color={textPrimary} textAlign="center">
                                  <Badge colorScheme="purple" variant="subtle" fontSize="11px">
                                    {job.keyword || "-"}
                                  </Badge>
                                </Td>
                                <Td fontSize="13px" color={textSecondary} textAlign="center">{formatDateTime(job.created_at)}</Td>
                                <Td fontSize="13px" textAlign="center">
                                  <Badge bg={linkedinBlue} color="white" fontSize="11px" px={3} py={1} borderRadius="md">
                                    {job.source || "-"}
                                  </Badge>
                                </Td>
                              </Tr>
                            ))
                          ) : (
                            <Tr>
                              <Td colSpan={7} textAlign="center" py={6}>
                                <Text color={textSecondary} fontSize="14px">
                                  {searchTerm ? "No results found" : "No data available"}
                                </Text>
                              </Td>
                            </Tr>
                          )}
                        </Tbody>
                      </Table>
                    </Box>
                    <TableFooter
                      filteredCount={getFilteredData.length}
                      pagination={pagination}
                      onPaginationChange={setPagination}
                      {...footerThemeProps}
                    />
                  </>
                )}
              </TabPanel>

              {/* Keywords Tab */}
              <TabPanel p={6}>
                {loading ? (
                  <Box display="flex" justifyContent="center" py={10}>
                    <Spinner size="xl" color="blue.500" thickness="3px" />
                  </Box>
                ) : (
                  <>
                    <TableHeader
                      title="Keywords"
                      count={allKeywords.length}
                      onSort={true}
                      searchTerm={searchTerm}
                      onSearchChange={handleSearchChange}
                      filteredCount={getFilteredData.length}
                      sortConfig={sortConfig}
                      onSortChange={setSortConfig}
                      searchInputRef={searchInputRef}
                      {...headerThemeProps}
                    />
                    <Box overflowX="auto" mb={4} borderRadius="lg">
                      <Table size="sm" variant="simple">
                        <Thead bg={tableHeaderBg}>
                          <Tr>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>ID</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Keyword</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Status</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Created</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {currentData.length > 0 ? (
                            currentData.map((kw, idx) => (
                              <Tr
                                key={kw.id}
                                bg={idx % 2 === 0 ? (isDark ? "rgba(88, 166, 255, 0.06)" : "rgba(66, 153, 225, 0.02)") : "transparent"}
                                _hover={{ bg: hoverBg }}
                                transition="all 0.15s"
                              >
                                <Td fontSize="13px" fontWeight="600" color={textPrimary} textAlign="center">{kw.id}</Td>
                                <Td fontSize="13px" fontWeight="700" color={textPrimary} textAlign="center">{kw.keyword}</Td>
                                <Td textAlign="center"><Badge colorScheme="green" variant="subtle" fontSize="11px">Active</Badge></Td>
                                <Td fontSize="13px" color={textSecondary} textAlign="center">{new Date().toLocaleDateString("id-ID")}</Td>
                              </Tr>
                            ))
                          ) : (
                            <Tr>
                              <Td colSpan={4} textAlign="center" py={6}>
                                <Text color={textSecondary} fontSize="14px">
                                  {searchTerm ? "No results found" : "No data available"}
                                </Text>
                              </Td>
                            </Tr>
                          )}
                        </Tbody>
                      </Table>
                    </Box>
                    <TableFooter
                      filteredCount={getFilteredData.length}
                      pagination={pagination}
                      onPaginationChange={setPagination}
                      {...footerThemeProps}
                    />
                  </>
                )}
              </TabPanel>

              {/* Skills Tab */}
              <TabPanel p={6}>
                {loading ? (
                  <Box display="flex" justifyContent="center" py={10}>
                    <Spinner size="xl" color="blue.500" thickness="3px" />
                  </Box>
                ) : (
                  <>
                    <TableHeader
                      title="Skills"
                      count={allSkills.length}
                      onSort={true}
                      searchTerm={searchTerm}
                      onSearchChange={handleSearchChange}
                      filteredCount={getFilteredData.length}
                      sortConfig={sortConfig}
                      onSortChange={setSortConfig}
                      searchInputRef={searchInputRef}
                      {...headerThemeProps}
                    />
                    <Box overflowX="auto" mb={4} borderRadius="lg">
                      <Table size="sm" variant="simple">
                        <Thead bg={tableHeaderBg}>
                          <Tr>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>ID</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Skill Name</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Type</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Count</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Percentage</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {currentData.length > 0 ? (
                            currentData.map((skill, idx) => (
                              <Tr
                                key={skill.id}
                                bg={idx % 2 === 0 ? (isDark ? "rgba(88, 166, 255, 0.06)" : "rgba(66, 153, 225, 0.02)") : "transparent"}
                                _hover={{ bg: hoverBg }}
                                transition="all 0.15s"
                              >
                                <Td fontSize="13px" fontWeight="600" color={textPrimary} textAlign="center">{skill.id}</Td>
                                <Td fontSize="13px" fontWeight="600" color={textPrimary} textAlign="center">{skill.skill_name || "-"}</Td>
                                <Td textAlign="center">
                                  <Badge colorScheme="purple" variant="subtle" fontSize="11px">
                                    {(skill.skill_type || "").replace("_", " ")}
                                  </Badge>
                                </Td>
                                <Td fontSize="13px" fontWeight="700" color={textPrimary} textAlign="center">{skill.count || 0}</Td>
                                <Td fontSize="13px" color={textPrimary} textAlign="center">{(((skill.count || 0) / 100) * 100).toFixed(1)}%</Td>
                              </Tr>
                            ))
                          ) : (
                            <Tr>
                              <Td colSpan={5} textAlign="center" py={6}>
                                <Text color={textSecondary} fontSize="14px">
                                  {searchTerm ? "No results found" : "No data available"}
                                </Text>
                              </Td>
                            </Tr>
                          )}
                        </Tbody>
                      </Table>
                    </Box>
                    <TableFooter
                      filteredCount={getFilteredData.length}
                      pagination={pagination}
                      onPaginationChange={setPagination}
                      {...footerThemeProps}
                    />
                  </>
                )}
              </TabPanel>

              {/* Job Analysis Tab */}
              <TabPanel p={6}>
                {loading ? (
                  <Box display="flex" justifyContent="center" py={10}>
                    <Spinner size="xl" color="blue.500" thickness="3px" />
                  </Box>
                ) : (
                  <>
                    <TableHeader
                      title="Job Analysis"
                      count={allJobAnalysis.length}
                      onSort={true}
                      searchTerm={searchTerm}
                      onSearchChange={handleSearchChange}
                      filteredCount={getFilteredData.length}
                      sortConfig={sortConfig}
                      onSortChange={setSortConfig}
                      searchInputRef={searchInputRef}
                      {...headerThemeProps}
                    />
                    <Box overflowX="auto" mb={4} borderRadius="lg">
                      <Table size="sm" variant="simple">
                        <Thead bg={tableHeaderBg}>
                          <Tr>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>ID</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Job Title</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Soft Skills</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Tech Stack</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Extracted Date</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {currentData.length > 0 ? (
                            currentData.map((analysis, idx) => (
                              <Tr
                                key={analysis.id}
                                bg={idx % 2 === 0 ? (isDark ? "rgba(88, 166, 255, 0.06)" : "rgba(66, 153, 225, 0.02)") : "transparent"}
                                _hover={{ bg: hoverBg }}
                                transition="all 0.15s"
                              >
                                <Td fontSize="13px" fontWeight="600" color={textPrimary} textAlign="center">{analysis.id}</Td>
                                <Td fontSize="13px" color={textPrimary}>
                                  <Text isTruncated maxW="200px" title={analysis.job_title || ""}>
                                    {analysis.job_title || "-"}
                                  </Text>
                                </Td>
                                <Td fontSize="13px" color={textPrimary}>
                                  <Text isTruncated maxW="200px" title={analysis.soft_skill || ""}>
                                    {analysis.soft_skill || "-"}
                                  </Text>
                                </Td>
                                <Td fontSize="13px" color={textPrimary}>
                                  <Text isTruncated maxW="200px" title={analysis.tech_stack || ""}>
                                    {analysis.tech_stack || "-"}
                                  </Text>
                                </Td>
                                <Td fontSize="13px" color={textSecondary} textAlign="center">
                                  {analysis.extracted_at ? new Date(analysis.extracted_at).toLocaleDateString("id-ID") : "-"}
                                </Td>
                              </Tr>
                            ))
                          ) : (
                            <Tr>
                              <Td colSpan={5} textAlign="center" py={6}>
                                <Text color={textSecondary} fontSize="14px">
                                  {searchTerm ? "No results found" : "No data available"}
                                </Text>
                              </Td>
                            </Tr>
                          )}
                        </Tbody>
                      </Table>
                    </Box>
                    <TableFooter
                      filteredCount={getFilteredData.length}
                      pagination={pagination}
                      onPaginationChange={setPagination}
                      {...footerThemeProps}
                    />
                  </>
                )}
              </TabPanel>

              {/* Skill Types Tab */}
              <TabPanel p={6}>
                {loading ? (
                  <Box display="flex" justifyContent="center" py={10}>
                    <Spinner size="xl" color="blue.500" thickness="3px" />
                  </Box>
                ) : (
                  <>
                    <TableHeader
                      title="Skill Types"
                      count={allSkillTypes.length}
                      onSort={true}
                      searchTerm={searchTerm}
                      onSearchChange={handleSearchChange}
                      filteredCount={getFilteredData.length}
                      sortConfig={sortConfig}
                      onSortChange={setSortConfig}
                      searchInputRef={searchInputRef}
                      {...headerThemeProps}
                    />
                    <Box overflowX="auto" mb={4} borderRadius="lg">
                      <Table size="sm" variant="simple">
                        <Thead bg={tableHeaderBg}>
                          <Tr>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>ID</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Name</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Description</Th>
                            <Th color={tableHeaderText} fontSize="12px" fontWeight="700" letterSpacing="0.5px" textTransform="uppercase" py={3} textAlign="center" bg={tableHeaderBg}>Created</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {currentData.length > 0 ? (
                            currentData.map((st, idx) => (
                              <Tr
                                key={st.id}
                                bg={idx % 2 === 0 ? (isDark ? "rgba(88, 166, 255, 0.06)" : "rgba(66, 153, 225, 0.02)") : "transparent"}
                                _hover={{ bg: hoverBg }}
                                transition="all 0.15s"
                              >
                                <Td fontSize="13px" fontWeight="600" color={textPrimary} textAlign="center">{st.id}</Td>
                                <Td fontSize="13px" fontWeight="700" color={textPrimary} textAlign="center">{st.name}</Td>
                                <Td fontSize="13px" color={textPrimary}>
                                  <Text isTruncated maxW="300px" title={st.description}>
                                    {st.description || "-"}
                                  </Text>
                                </Td>
                                <Td fontSize="13px" color={textSecondary} textAlign="center">
                                  {st.created_at ? new Date(st.created_at).toLocaleDateString("id-ID") : "-"}
                                </Td>
                              </Tr>
                            ))
                          ) : (
                            <Tr>
                              <Td colSpan={4} textAlign="center" py={6}>
                                <Text color={textSecondary} fontSize="14px">
                                  {searchTerm ? "No results found" : "No data available"}
                                </Text>
                              </Td>
                            </Tr>
                          )}
                        </Tbody>
                      </Table>
                    </Box>
                    <TableFooter
                      filteredCount={getFilteredData.length}
                      pagination={pagination}
                      onPaginationChange={setPagination}
                      {...footerThemeProps}
                    />
                  </>
                )}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </CardBody>
      </Card>

      {/* Database Info */}
      <HStack spacing={6} mt={8} flexWrap="wrap">
        <Card
          bg={bgCard}
          borderColor={borderColor}
          borderWidth="1px"
          borderLeft="4px"
          borderLeftColor={accentColor}
          flex="1"
          minW="280px"
          borderRadius="lg"
          backdropFilter="blur(8px)"
        >
          <CardHeader pb={2}>
            <Heading size="sm" color={textPrimary} fontWeight="700">✅ Database Status</Heading>
          </CardHeader>
          <CardBody pt={0} fontSize="sm">
            <VStack align="start" spacing={1.5} color={textSecondary}>
              <HStack justify="space-between" w="100%">
                <Text fontWeight="500">Location:</Text>
                <Text color={textPrimary} fontWeight="600">/skills_trend.db</Text>
              </HStack>
              <HStack justify="space-between" w="100%">
                <Text fontWeight="500">Type:</Text>
                <Text color={textPrimary} fontWeight="600">SQLite</Text>
              </HStack>
              <HStack justify="space-between" w="100%">
                <Text fontWeight="500">Status:</Text>
                <Badge colorScheme="green" variant="solid" fontSize="11px">Connected</Badge>
              </HStack>
              <HStack justify="space-between" w="100%">
                <Text fontWeight="500">Size:</Text>
                <Text color={textPrimary} fontWeight="600">~2.5 MB</Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        <Card
          bg={bgCard}
          borderColor={borderColor}
          borderWidth="1px"
          borderLeft="4px"
          borderLeftColor="orange.400"
          flex="1"
          minW="280px"
          borderRadius="lg"
          backdropFilter="blur(8px)"
        >
          <CardHeader pb={2}>
            <Heading size="sm" color={textPrimary} fontWeight="700">⚠️ Catatan Penting</Heading>
          </CardHeader>
          <CardBody pt={0}>
            <VStack align="start" spacing={1.5}>
              <HStack>
                <Text color={accentColor}>•</Text>
                <Text fontSize="13px" color={textSecondary}>Data read-only di tampilan ini</Text>
              </HStack>
              <HStack>
                <Text color={accentColor}>•</Text>
                <Text fontSize="13px" color={textSecondary}>Edit data melalui API atau backend</Text>
              </HStack>
              <HStack>
                <Text color={accentColor}>•</Text>
                <Text fontSize="13px" color={textSecondary}>Backup database sebelum import data besar</Text>
              </HStack>
              <HStack>
                <Text color={accentColor}>•</Text>
                <Text fontSize="13px" color={textSecondary}>Refresh halaman untuk melihat data terbaru</Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </HStack>
    </Box>
  );
};

export default AdminDatabaseManagement;