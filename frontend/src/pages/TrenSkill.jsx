import { useState, useEffect } from "react";
import {
  Box,
  Heading,
  Text,
  Select,
  Button,
  VStack,
  HStack,
  useDisclosure,
  Badge,
  Divider,
  useToast,
  SimpleGrid,
  Stack,
} from "@chakra-ui/react";
import axios from "axios";
import { API_ENDPOINTS, getErrorMessage } from "../config/api";
import { useTheme } from "../context/ThemeContext";
import MonthlyChart from "../components/MonthlyChart";
import SkillDistribution from "../components/SkillDistribution";
import SoftSkillList from "../components/SoftSkillList";
import TechStackTrendChart from "../components/TechStackTrendChart";
import TechnicalSkillsTrendChart from "../components/TechnicalSkillsTrendChart";
import SoftSkillsTrendChart from "../components/SoftSkillsTrendChart";
import SkillDetailModal from "../components/SkillDetailModal";
import AllSkillsModal from "../components/AllSkillsModal";

export default function TrenSkill() {
  const toast = useToast();
  const { isDark } = useTheme();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const {
    isOpen: isAllSkillsOpen,
    onOpen: onAllSkillsOpen,
    onClose: onAllSkillsClose,
  } = useDisclosure();
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [selectedExpand, setSelectedExpand] = useState(null);

  const [filters, setFilters] = useState({
    keyword_id: "",
    location: "",
    month: "",
    year: "",
    employee_size: "",
  });

  const [appliedFilters, setAppliedFilters] = useState({
    keyword_id: "",
    location: "",
    month: "",
    year: "",
    employee_size: "",
  });

  const [filterOptions, setFilterOptions] = useState(null);
  const [loadingFilters, setLoadingFilters] = useState(true);
  const [employeeSizeOptions, setEmployeeSizeOptions] = useState([]);
  const [loadingEmployeeSizes, setLoadingEmployeeSizes] = useState(false);

  const [jobAnalysisLocations, setJobAnalysisLocations] = useState([]);
  const [loadingLocations, setLoadingLocations] = useState(false);

  const cleanLocationName = (location) => {
    if (typeof location === "string") {
      return location.replace(/\s*\(\d+\)\s*$/, "").trim();
    }
    return location;
  };

  const formatDateTime = (isoString) => {
    if (!isoString) return "-";
    try {
      const date = new Date(isoString);
      const months = [
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
      const day = date.getDate();
      const month = months[date.getMonth()];
      const year = date.getFullYear();
      const hours = String(date.getHours()).padStart(2, "0");
      const minutes = String(date.getMinutes()).padStart(2, "0");
      return `${day} ${month} ${year}, ${hours}:${minutes} WIB`;
    } catch (e) {
      return isoString;
    }
  };

  const loadEmployeeSizes = async () => {
    try {
      setLoadingEmployeeSizes(true);
      const res = await axios.get(API_ENDPOINTS.EMPLOYEE_SIZES);
      const data = Array.isArray(res.data) ? res.data : [];
      setEmployeeSizeOptions(data);
    } catch (err) {
      console.error("Gagal memuat employee sizes:", err);
      setEmployeeSizeOptions([
        { size: "1-10", count: 0 },
        { size: "11-50", count: 0 },
        { size: "51-200", count: 0 },
        { size: "201-500", count: 0 },
        { size: "501-1000", count: 0 },
        { size: "1001-5000", count: 0 },
        { size: "5001-10000", count: 0 },
        { size: "10001+", count: 0 },
      ]);
    } finally {
      setLoadingEmployeeSizes(false);
    }
  };

  const loadLocationsFromJobAnalysis = async () => {
    try {
      setLoadingLocations(true);
      const res = await axios.get(API_ENDPOINTS.JOB_ANALYSIS_LOCATIONS);
      let locationsData = Array.isArray(res.data) ? res.data : [];

      locationsData = locationsData.map((loc) => {
        if (typeof loc === "string") {
          return cleanLocationName(loc);
        } else if (loc && typeof loc === "object") {
          if (loc.city) {
            return {
              ...loc,
              city: cleanLocationName(loc.city),
            };
          }
          const firstValue = Object.values(loc).find(
            (val) => typeof val === "string",
          );
          if (firstValue) {
            return {
              ...loc,
              ...Object.keys(loc).reduce((acc, key) => {
                if (typeof loc[key] === "string") {
                  acc[key] = cleanLocationName(loc[key]);
                }
                return acc;
              }, {}),
            };
          }
        }
        return loc;
      });

      setJobAnalysisLocations(locationsData);
    } catch (err) {
      console.error("Gagal memuat lokasi dari job_analysis:", err);
      if (filterOptions?.cities && Array.isArray(filterOptions.cities)) {
        const cleanCities = filterOptions.cities.map((city) =>
          typeof city === "string" ? cleanLocationName(city) : city,
        );
        setJobAnalysisLocations(cleanCities);
      } else {
        setJobAnalysisLocations([]);
      }
    } finally {
      setLoadingLocations(false);
    }
  };

  useEffect(() => {
    const loadFilters = async () => {
      try {
        setLoadingFilters(true);
        const res = await axios.get(API_ENDPOINTS.FILTERS);
        setFilterOptions(res.data);
        await Promise.all([
          loadLocationsFromJobAnalysis(),
          loadEmployeeSizes(),
        ]);
      } catch (err) {
        toast({
          title: "Gagal memuat filter",
          description: getErrorMessage(err),
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      } finally {
        setLoadingFilters(false);
      }
    };
    loadFilters();
  }, [toast]);

  const handleSkillClick = (skillData) => {
    setSelectedSkill(skillData);
    onOpen();
  };

  const handleExpandClick = (expandData) => {
    setSelectedExpand(expandData);
    onAllSkillsOpen();
  };

  const updateFilter = (field, value) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
  };

  const applyFilter = () => {
    setAppliedFilters({ ...filters });
  };

  const resetFilter = () => {
    setFilters({
      keyword_id: "",
      location: "",
      month: "",
      year: "",
      employee_size: "",
    });
    setAppliedFilters({
      keyword_id: "",
      location: "",
      month: "",
      year: "",
      employee_size: "",
    });
  };

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

  const selectedKeywordLabel =
    filterOptions?.keywords?.find(
      (k) => String(k.id) === String(appliedFilters.keyword_id),
    )?.keyword || null;

  const activeFilterBadges = [
    selectedKeywordLabel ? `Job: ${selectedKeywordLabel}` : null,
    appliedFilters.location ? `Lokasi: ${appliedFilters.location}` : null,
    appliedFilters.month
      ? `Bulan: ${monthLabels[Number(appliedFilters.month) - 1] || appliedFilters.month}`
      : null,
    appliedFilters.year ? `Tahun: ${appliedFilters.year}` : null,
    appliedFilters.employee_size
      ? `Ukuran: ${appliedFilters.employee_size}`
      : null,
  ].filter(Boolean);

  const displayLocations = (() => {
    if (
      Array.isArray(jobAnalysisLocations) &&
      jobAnalysisLocations.length > 0
    ) {
      return jobAnalysisLocations;
    }
    if (
      Array.isArray(filterOptions?.cities) &&
      filterOptions.cities.length > 0
    ) {
      return filterOptions.cities.map((city) =>
        typeof city === "string" ? cleanLocationName(city) : city,
      );
    }
    return [];
  })();

  const getLocationDisplayName = (loc) => {
    if (typeof loc === "string") {
      return cleanLocationName(loc);
    } else if (loc && typeof loc === "object") {
      if (loc.city) return cleanLocationName(loc.city);
      if (loc.name) return cleanLocationName(loc.name);
      if (loc.location) return cleanLocationName(loc.location);
      const stringValue = Object.values(loc).find(
        (val) => typeof val === "string",
      );
      return stringValue ? cleanLocationName(stringValue) : String(loc);
    }
    return String(loc);
  };

  const getLocationKey = (loc) => {
    if (typeof loc === "string") {
      return cleanLocationName(loc);
    } else if (loc && typeof loc === "object") {
      if (loc.city) return cleanLocationName(loc.city);
      if (loc.id) return `loc-${loc.id}`;
      if (loc.name) return cleanLocationName(loc.name);
      return `loc-${JSON.stringify(loc)}`;
    }
    return `loc-${String(loc)}`;
  };

  const getLocationValue = (loc) => {
    if (typeof loc === "string") {
      return cleanLocationName(loc);
    } else if (loc && typeof loc === "object") {
      if (loc.city) return cleanLocationName(loc.city);
      if (loc.name) return cleanLocationName(loc.name);
      if (loc.location) return cleanLocationName(loc.location);
      const stringValue = Object.values(loc).find(
        (val) => typeof val === "string",
      );
      return stringValue ? cleanLocationName(stringValue) : String(loc);
    }
    return String(loc);
  };

  const cardShadow = isDark
    ? "0 4px 12px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.2)"
    : "0 4px 12px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)";

  return (
    <Box
      px={{ base: 3, md: 4, lg: 5 }}
      py={{ base: 3, md: 4, lg: 5 }}
      w="100%"
      bg={isDark ? "gray.900" : "gray.100"}
      minH="100vh"
    >
      <VStack align="stretch" spacing={3} maxW="1200px" mx="auto">
        {/* Header - Lebih Compact */}
        <Box>
          <Heading
            as="h1"
            size={{ base: "md", md: "lg" }}
            fontWeight="800"
            letterSpacing="-0.02em"
            mb={0.5}
            fontSize={{ base: "28px", md: "36px" }}
          >
            Tren Kebutuhan Kompetensi Data & AI
          </Heading>
          <Text
            fontSize={{ base: "sm", md: "sm" }}
            color={isDark ? "gray.400" : "gray.600"}
            maxW="3xl"
            mb={2.5}
          >
            Analisis mendalam tentang skill dan teknologi yang dibutuhkan
            industri saat ini berdasarkan data lowongan pekerjaan terbaru
          </Text>
          {filterOptions?.last_extraction_at && (
            <Badge
              colorScheme="blue"
              variant="subtle"
              px={3}
              py={1.5}
              borderRadius="full"
              fontSize="xs"
              fontWeight="600"
              mb={3}
              display="inline-flex"
              alignItems="center"
              gap={1.5}
            >
              <Box w="6px" h="6px" borderRadius="full" bg="blue.500" />
              Terakhir Diperbarui :{" "}
              {formatDateTime(filterOptions.last_extraction_at)}
            </Badge>
          )}
          <Divider borderColor={isDark ? "gray.700" : "gray.200"} />
        </Box>

        {/* Filter Section - Diperbesar */}
        <Box
          bg={isDark ? "gray.800" : "white"}
          p={4}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={isDark ? "gray.700" : "gray.100"}
          boxShadow={cardShadow}
        >
          <Heading
            as="h2"
            size="sm"
            fontWeight="600"
            mb={3}
            color={isDark ? "gray.200" : "gray.700"}
            fontSize="14px"
          >
            Filter Data
          </Heading>

          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={3} mb={3}>
            {/* Job Title */}
            <Select
              key="filter-keyword"
              value={filters.keyword_id}
              onChange={(e) => updateFilter("keyword_id", e.target.value)}
              bg={isDark ? "gray.700" : "white"}
              borderColor={isDark ? "gray.600" : "gray.300"}
              borderWidth="2px"
              _hover={{ borderColor: isDark ? "blue.500" : "blue.500" }}
              _focus={{ borderColor: "blue.500", borderWidth: "2px" }}
              borderRadius="md"
              size="md"
              fontSize="14px"
              height="40px"
            >
              <option value="" disabled hidden>
                Pilih Job Title
              </option>
              {filterOptions?.keywords?.map((k) => (
                <option key={k.id} value={k.id}>
                  {k.keyword}
                </option>
              ))}
            </Select>

            {/* Lokasi */}
            <Select
              key="filter-location"
              value={filters.location}
              onChange={(e) => updateFilter("location", e.target.value)}
              bg={isDark ? "gray.700" : "white"}
              borderColor={isDark ? "gray.600" : "gray.300"}
              borderWidth="2px"
              _hover={{ borderColor: isDark ? "blue.500" : "blue.500" }}
              _focus={{ borderColor: "blue.500", borderWidth: "2px" }}
              borderRadius="md"
              size="md"
              fontSize="14px"
              height="40px"
            >
              <option value="" disabled hidden>
                {loadingLocations ? "Memuat lokasi..." : "Pilih Lokasi"}
              </option>
              {displayLocations.map((loc) => {
                const displayName = getLocationDisplayName(loc);
                const key = getLocationKey(loc);
                const value = getLocationValue(loc);
                return (
                  <option key={key} value={value}>
                    {displayName}
                  </option>
                );
              })}
            </Select>

            {/* UKURAN PERUSAHAAN */}
            <Select
              key="filter-employee-size"
              value={filters.employee_size}
              onChange={(e) => updateFilter("employee_size", e.target.value)}
              bg={isDark ? "gray.700" : "white"}
              borderColor={isDark ? "gray.600" : "gray.300"}
              borderWidth="2px"
              _hover={{ borderColor: isDark ? "blue.500" : "blue.500" }}
              _focus={{ borderColor: "blue.500", borderWidth: "2px" }}
              borderRadius="md"
              size="md"
              fontSize="14px"
              height="40px"
            >
              <option value="" disabled hidden>
                {loadingEmployeeSizes ? "Memuat ukuran..." : "Semua Ukuran"}
              </option>
              {Array.isArray(employeeSizeOptions) &&
              employeeSizeOptions.length > 0 ? (
                employeeSizeOptions.map((item) => (
                  <option key={item.size} value={item.size}>
                    {item.size} {item.count > 0 ? `(${item.count})` : ""}
                  </option>
                ))
              ) : (
                <>
                  <option value="1-10">1-10</option>
                  <option value="11-50">11-50</option>
                  <option value="51-200">51-200</option>
                  <option value="201-500">201-500</option>
                  <option value="501-1000">501-1000</option>
                  <option value="1001-5000">1001-5000</option>
                  <option value="5001-10000">5001-10000</option>
                  <option value="10001+">10001+</option>
                </>
              )}
            </Select>

            {/* Bulan */}
            <Select
              key="filter-month"
              value={filters.month}
              onChange={(e) => updateFilter("month", e.target.value)}
              bg={isDark ? "gray.700" : "white"}
              borderColor={isDark ? "gray.600" : "gray.300"}
              borderWidth="2px"
              _hover={{ borderColor: isDark ? "blue.500" : "blue.500" }}
              _focus={{ borderColor: "blue.500", borderWidth: "2px" }}
              borderRadius="md"
              size="md"
              fontSize="14px"
              height="40px"
            >
              <option value="" disabled hidden>
                Pilih Bulan
              </option>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((m) => (
                <option key={m} value={m}>
                  {monthLabels[m - 1]}
                </option>
              ))}
            </Select>

            {/* Tahun */}
            <Select
              key="filter-year"
              value={filters.year}
              onChange={(e) => updateFilter("year", e.target.value)}
              bg={isDark ? "gray.700" : "white"}
              borderColor={isDark ? "gray.600" : "gray.300"}
              borderWidth="2px"
              _hover={{ borderColor: isDark ? "blue.500" : "blue.500" }}
              _focus={{ borderColor: "blue.500", borderWidth: "2px" }}
              borderRadius="md"
              size="md"
              fontSize="14px"
              height="40px"
            >
              <option value="" disabled hidden>
                Pilih Tahun
              </option>
              {filterOptions?.years?.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </Select>
          </SimpleGrid>

          <HStack spacing={3}>
            <Button
              onClick={applyFilter}
              bg="blue.600"
              color="white"
              _hover={{ bg: "blue.700" }}
              _active={{ bg: "blue.800" }}
              border="2px solid"
              borderColor="blue.600"
              px={6}
              size="md"
              fontSize="14px"
              height="38px"
              borderRadius="md"
              fontWeight="600"
            >
              Terapkan Filter
            </Button>
            <Button
              onClick={resetFilter}
              variant="outline"
              border="2px solid"
              borderColor={isDark ? "gray.500" : "gray.400"}
              color={isDark ? "gray.200" : "gray.700"}
              _hover={{
                bg: isDark ? "gray.700" : "gray.100",
                borderColor: isDark ? "gray.400" : "gray.500",
              }}
              px={6}
              size="md"
              fontSize="14px"
              height="38px"
              borderRadius="md"
              fontWeight="600"
            >
              Reset
            </Button>
          </HStack>

          {activeFilterBadges.length > 0 && (
            <HStack spacing={2} mt={3} flexWrap="wrap">
              {activeFilterBadges.map((badge) => (
                <Badge
                  key={badge}
                  px={3}
                  py={1}
                  borderRadius="full"
                  bg={isDark ? "gray.700" : "gray.100"}
                  color={isDark ? "gray.300" : "gray.700"}
                  fontSize="xs"
                  fontWeight="500"
                >
                  {badge}
                </Badge>
              ))}
            </HStack>
          )}
        </Box>

        {/* Charts Section - Lebih Compact */}
        <Box>
          <Heading
            as="h2"
            size="sm"
            fontWeight="600"
            mb={1.5}
            letterSpacing="-0.01em"
            fontSize="16px"
          >
            Analisis Utama
          </Heading>
          <Divider mb={2} borderColor={isDark ? "gray.700" : "gray.200"} />
        </Box>

        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={3}>
          <Box
            bg={isDark ? "gray.800" : "white"}
            p={3}
            borderRadius="lg"
            borderWidth="1px"
            borderColor={isDark ? "gray.700" : "gray.100"}
            boxShadow={cardShadow}
          >
            <MonthlyChart
              filters={appliedFilters}
              onSkillClick={handleSkillClick}
              onExpandClick={handleExpandClick}
              activeFilterBadges={activeFilterBadges}
            />
          </Box>

          <Box
            bg={isDark ? "gray.800" : "white"}
            p={3}
            borderRadius="lg"
            borderWidth="1px"
            borderColor={isDark ? "gray.700" : "gray.100"}
            boxShadow={cardShadow}
          >
            <SkillDistribution
              skillTypeId={2}
              title="Technical Skills"
              description="Kemampuan teknis & expertise yang paling dicari industri"
              color="#22c55e"
              filters={appliedFilters}
              onSkillClick={handleSkillClick}
              onExpandClick={handleExpandClick}
              activeFilterBadges={activeFilterBadges}
            />
          </Box>
        </SimpleGrid>

        <Box
          bg={isDark ? "gray.800" : "white"}
          p={3}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={isDark ? "gray.700" : "gray.100"}
          boxShadow={cardShadow}
        >
          <SoftSkillList
            filters={appliedFilters}
            onSkillClick={handleSkillClick}
            onExpandClick={handleExpandClick}
            activeFilterBadges={activeFilterBadges}
          />
        </Box>

        <Box>
          <Heading
            as="h2"
            size="sm"
            fontWeight="600"
            mb={1.5}
            letterSpacing="-0.01em"
            fontSize="16px"
          >
            Grafik Tren Skill
          </Heading>
          <Divider mb={2} borderColor={isDark ? "gray.700" : "gray.200"} />
        </Box>

        <Stack spacing={3}>
          <Box
            bg={isDark ? "gray.800" : "white"}
            p={3}
            borderRadius="lg"
            borderWidth="1px"
            borderColor={isDark ? "gray.700" : "gray.100"}
            boxShadow={cardShadow}
          >
            <TechStackTrendChart
              filters={appliedFilters}
              activeFilterBadges={activeFilterBadges}
            />
          </Box>

          <Box
            bg={isDark ? "gray.800" : "white"}
            p={3}
            borderRadius="lg"
            borderWidth="1px"
            borderColor={isDark ? "gray.700" : "gray.100"}
            boxShadow={cardShadow}
          >
            <TechnicalSkillsTrendChart
              filters={appliedFilters}
              activeFilterBadges={activeFilterBadges}
            />
          </Box>

          <Box
            bg={isDark ? "gray.800" : "white"}
            p={3}
            borderRadius="lg"
            borderWidth="1px"
            borderColor={isDark ? "gray.700" : "gray.100"}
            boxShadow={cardShadow}
          >
            <SoftSkillsTrendChart
              filters={appliedFilters}
              activeFilterBadges={activeFilterBadges}
            />
          </Box>
        </Stack>

        {selectedSkill && (
          <SkillDetailModal
            isOpen={isOpen}
            onClose={onClose}
            skillName={selectedSkill.skillName}
            skillType={selectedSkill.skillType}
            filters={appliedFilters}
            employeeSizeOptions={employeeSizeOptions}
          />
        )}

        {selectedExpand && (
          <AllSkillsModal
            isOpen={isAllSkillsOpen}
            onClose={onAllSkillsClose}
            skillTypeId={selectedExpand.skillTypeId}
            skillType={selectedExpand.skillType}
            filters={appliedFilters}
          />
        )}
      </VStack>
    </Box>
  );
}
