import { useState, useEffect } from "react";
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Grid,
  Select,
  Radio,
  RadioGroup,
  Stack,
  useDisclosure,
  Divider,
} from "@chakra-ui/react";
import axios from "axios";
import { useTheme } from "../context/ThemeContext";
import AlternativeSkillComparison from "../components/AlternativeSkillComparison";
import SkillDetailModal from "../components/SkillDetailModal";

import { API_ENDPOINTS } from "../config/api";

const MONTHS = [
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

export default function DetailAnalisis() {
  const [compareMode, setCompareMode] = useState("year");
  const [year1, setYear1] = useState("2024");
  const [year2, setYear2] = useState("2023");
  const [month1, setMonth1] = useState("1");
  const [month2, setMonth2] = useState("2");
  const [jobTitle, setJobTitle] = useState("");
  const [location, setLocation] = useState("");
  const [employeeSize, setEmployeeSize] = useState("");
  const [filterOptions, setFilterOptions] = useState(null);
  const [employeeSizeOptions, setEmployeeSizeOptions] = useState([]);

  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedSkill, setSelectedSkill] = useState(null);

  const [techData1, setTechData1] = useState([]);
  const [techData2, setTechData2] = useState([]);
  const [techLoading1, setTechLoading1] = useState(false);
  const [techLoading2, setTechLoading2] = useState(false);

  const [techSkillData1, setTechSkillData1] = useState([]);
  const [techSkillData2, setTechSkillData2] = useState([]);
  const [techSkillLoading1, setTechSkillLoading1] = useState(false);
  const [techSkillLoading2, setTechSkillLoading2] = useState(false);

  const [softData1, setSoftData1] = useState([]);
  const [softData2, setSoftData2] = useState([]);
  const [softLoading1, setSoftLoading1] = useState(false);
  const [softLoading2, setSoftLoading2] = useState(false);

  useEffect(() => {
    axios
      .get(`${API_ENDPOINTS.FILTERS}`)
      .then((res) => setFilterOptions(res.data))
      .catch((err) => console.error("Error fetching filters:", err));

    axios
      .get(`${API_ENDPOINTS.EMPLOYEE_SIZES}`)
      .then((res) => {
        const data = Array.isArray(res.data) ? res.data : [];
        setEmployeeSizeOptions(data);
      })
      .catch((err) => {
        console.error("Error fetching employee sizes:", err);
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
      });
  }, []);

  const buildParams = (year, month, isMonthMode) => {
    const params = new URLSearchParams();

    if (isMonthMode) {
      if (month) params.append("month", month);
      if (year) params.append("year", year);
    } else {
      if (year) params.append("year", year);
    }

    if (jobTitle && jobTitle !== "") params.append("keyword_id", jobTitle);
    if (location && location !== "") params.append("location", location);
    if (employeeSize && employeeSize !== "") params.append("employee_size", employeeSize);
    params.append("limit", "10");

    return params;
  };

  useEffect(() => {
    const isMonthMode = compareMode === "month";
    const params1 = buildParams(year1, month1, isMonthMode);

    if (compareMode === "year" ? year1 : month1 || year1) {
      setTechLoading1(true);
      axios
        .get(
          `${API_ENDPOINTS.DASHBOARD.TOP_SKILLS_BY_TYPE}?skill_type_id=3&${params1}`,
        )
        .then((res) => {
          setTechData1(res.data || []);
          setTechLoading1(false);
        })
        .catch((err) => {
          console.error("Error fetching tech stack period 1:", err);
          setTechLoading1(false);
        });

      setTechSkillLoading1(true);
      axios
        .get(
          `${API_ENDPOINTS.DASHBOARD.TOP_SKILLS_BY_TYPE}?skill_type_id=2&${params1}`,
        )
        .then((res) => {
          setTechSkillData1(res.data || []);
          setTechSkillLoading1(false);
        })
        .catch((err) => {
          console.error("Error fetching technical skill period 1:", err);
          setTechSkillLoading1(false);
        });

      setSoftLoading1(true);
      axios
        .get(
          `${API_ENDPOINTS.DASHBOARD.TOP_SKILLS_BY_TYPE}?skill_type_id=1&${params1}`,
        )
        .then((res) => {
          setSoftData1(res.data || []);
          setSoftLoading1(false);
        })
        .catch((err) => {
          console.error("Error fetching soft skill period 1:", err);
          setSoftLoading1(false);
        });
    }
  }, [year1, month1, jobTitle, location, employeeSize, compareMode]);

  useEffect(() => {
    const isMonthMode = compareMode === "month";
    const params2 = buildParams(year2, month2, isMonthMode);

    if (compareMode === "year" ? year2 : month2 || year2) {
      setTechLoading2(true);
      axios
        .get(
          `${API_ENDPOINTS.DASHBOARD.TOP_SKILLS_BY_TYPE}?skill_type_id=3&${params2}`,
        )
        .then((res) => {
          setTechData2(res.data || []);
          setTechLoading2(false);
        })
        .catch((err) => {
          console.error("Error fetching tech stack period 2:", err);
          setTechLoading2(false);
        });

      setTechSkillLoading2(true);
      axios
        .get(
          `${API_ENDPOINTS.DASHBOARD.TOP_SKILLS_BY_TYPE}?skill_type_id=2&${params2}`,
        )
        .then((res) => {
          setTechSkillData2(res.data || []);
          setTechSkillLoading2(false);
        })
        .catch((err) => {
          console.error("Error fetching technical skill period 2:", err);
          setTechSkillLoading2(false);
        });

      setSoftLoading2(true);
      axios
        .get(
          `${API_ENDPOINTS.DASHBOARD.TOP_SKILLS_BY_TYPE}?skill_type_id=1&${params2}`,
        )
        .then((res) => {
          setSoftData2(res.data || []);
          setSoftLoading2(false);
        })
        .catch((err) => {
          console.error("Error fetching soft skill period 2:", err);
          setSoftLoading2(false);
        });
    }
  }, [year2, month2, jobTitle, location, employeeSize, compareMode]);

  const period1 =
    compareMode === "year" ? year1 : MONTHS[month1 - 1] || "Periode 1";
  const period2 =
    compareMode === "year" ? year2 : MONTHS[month2 - 1] || "Periode 2";

  const handleSkillClick = (skillData) => {
    setSelectedSkill(skillData);
    onOpen();
  };

  const { isDark } = useTheme();

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
        {/* Header */}
        <Box>
          <Heading
            as="h1"
            size={{ base: "md", md: "lg" }}
            fontWeight="800"
            letterSpacing="-0.02em"
            mb={0.5}
            fontSize={{ base: "28px", md: "36px" }}
          >
            Analisis Perbandingan Skill
          </Heading>
          <Text
            fontSize={{ base: "sm", md: "sm" }}
            color={isDark ? "gray.400" : "gray.600"}
            maxW="3xl"
            mb={1.5}
          >
            Bandingkan kebutuhan skill antar periode waktu untuk melihat tren
            permintaan di industri
          </Text>
          <Divider borderColor={isDark ? "gray.700" : "gray.200"} />
        </Box>

        {/* Filter Section - Diperbesar ukuran sedang */}
        <Box
          bg={isDark ? "gray.800" : "white"}
          p={4}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={isDark ? "gray.700" : "gray.100"}
          boxShadow={cardShadow}
        >
          <VStack align="stretch" spacing={3}>
            <Heading as="h2" size="sm" fontWeight="600" mb={0.5} fontSize="14px">
              Mode Perbandingan
            </Heading>
            <RadioGroup value={compareMode} onChange={setCompareMode}>
              <Stack direction="row" spacing={5}>
                <Radio value="year" colorScheme="blue" size="md">
                  <Text fontSize="14px" fontWeight="500">Antar Tahun</Text>
                </Radio>
                <Radio value="month" colorScheme="blue" size="md">
                  <Text fontSize="14px" fontWeight="500">Antar Bulan</Text>
                </Radio>
              </Stack>
            </RadioGroup>

            <Grid
              templateColumns={{
                base: "1fr",
                md: "repeat(2, 1fr)",
                lg: "repeat(3, 1fr)",
              }}
              gap={3}
              pt={1}
            >
              {compareMode === "year" ? (
                <>
                  <Select
                    value={year1}
                    onChange={(e) => setYear1(e.target.value)}
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
                    {filterOptions?.years?.map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </Select>
                  <Select
                    value={year2}
                    onChange={(e) => setYear2(e.target.value)}
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
                    {filterOptions?.years?.map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </Select>
                </>
              ) : (
                <>
                  <Select
                    value={year1}
                    onChange={(e) => setYear1(e.target.value)}
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
                    {filterOptions?.years?.map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </Select>
                  <Select
                    value={month1}
                    onChange={(e) => setMonth1(e.target.value)}
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
                    {MONTHS.map((m, idx) => (
                      <option key={idx + 1} value={idx + 1}>{m}</option>
                    ))}
                  </Select>
                  <Select
                    value={year2}
                    onChange={(e) => setYear2(e.target.value)}
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
                    {filterOptions?.years?.map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </Select>
                  <Select
                    value={month2}
                    onChange={(e) => setMonth2(e.target.value)}
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
                    {MONTHS.map((m, idx) => (
                      <option key={idx + 1} value={idx + 1}>{m}</option>
                    ))}
                  </Select>
                </>
              )}

              {/* Job Title Filter */}
              <Select
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
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
                <option value="">Semua Pekerjaan</option>
                {filterOptions?.keywords?.map((k) => (
                  <option key={k.id} value={k.id}>{k.keyword}</option>
                ))}
              </Select>

              {/* Location Filter */}
              <Select
                value={location}
                onChange={(e) => setLocation(e.target.value)}
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
                <option value="">Semua Lokasi</option>
                {filterOptions?.cities?.map((c) => (
                  <option key={c.city} value={c.city}>{c.city}</option>
                ))}
              </Select>

              {/* Employee Size Filter */}
              <Select
                value={employeeSize}
                onChange={(e) => setEmployeeSize(e.target.value)}
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
                <option value="">Semua Ukuran Perusahaan</option>
                {employeeSizeOptions.map((item) => (
                  <option key={item.size} value={item.size}>
                    {item.size} {item.count > 0 ? `(${item.count})` : ''}
                  </option>
                ))}
              </Select>
            </Grid>
          </VStack>
        </Box>

        {/* Tech Stack Section - Tetap seperti semula */}
        <Box
          bg={isDark ? "gray.800" : "white"}
          p={3}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={isDark ? "gray.700" : "gray.100"}
          boxShadow={cardShadow}
        >
          <Heading as="h2" size="sm" fontWeight="600" mb={0.5} fontSize="16px">
            Tech Stack
          </Heading>
          <Text fontSize="xs" color={isDark ? "gray.400" : "gray.500"} mb={2}>
            Teknologi dan tools yang paling diminati pada periode yang dibandingkan
          </Text>
          <AlternativeSkillComparison
            title="Tech Stack"
            skillData1={techData1}
            skillData2={techData2}
            period1={period1}
            period2={period2}
            loading1={techLoading1}
            loading2={techLoading2}
            skillType="tech_stack"
            onSkillClick={handleSkillClick}
            isCompact={false}
          />
        </Box>

        {/* Technical Skills Section - Tetap seperti semula */}
        <Box
          bg={isDark ? "gray.800" : "white"}
          p={3}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={isDark ? "gray.700" : "gray.100"}
          boxShadow={cardShadow}
        >
          <Heading as="h2" size="sm" fontWeight="600" mb={0.5} fontSize="16px">
            Technical Skills
          </Heading>
          <Text fontSize="xs" color={isDark ? "gray.400" : "gray.500"} mb={2}>
            Kemampuan teknis yang dicari industri pada periode yang dibandingkan
          </Text>
          <AlternativeSkillComparison
            title="Technical Skills"
            skillData1={techSkillData1}
            skillData2={techSkillData2}
            period1={period1}
            period2={period2}
            loading1={techSkillLoading1}
            loading2={techSkillLoading2}
            skillType="technical_skill"
            onSkillClick={handleSkillClick}
            isCompact={false}
          />
        </Box>

        {/* Soft Skills Section - Tetap seperti semula */}
        <Box
          bg={isDark ? "gray.800" : "white"}
          p={3}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={isDark ? "gray.700" : "gray.100"}
          boxShadow={cardShadow}
        >
          <Heading as="h2" size="sm" fontWeight="600" mb={0.5} fontSize="16px">
            Soft Skills
          </Heading>
          <Text fontSize="xs" color={isDark ? "gray.400" : "gray.500"} mb={2}>
            Kemampuan interpersonal yang penting untuk pengembangan karir profesional
          </Text>
          <AlternativeSkillComparison
            title="Soft Skills"
            skillData1={softData1}
            skillData2={softData2}
            period1={period1}
            period2={period2}
            loading1={softLoading1}
            loading2={softLoading2}
            skillType="soft_skill"
            onSkillClick={handleSkillClick}
            isCompact={false}
          />
        </Box>

        {/* Skill Detail Modal */}
        {selectedSkill && (
          <SkillDetailModal
            isOpen={isOpen}
            onClose={onClose}
            skillName={selectedSkill.skillName}
            skillType={selectedSkill.skillType}
            filters={{
              keyword_id: jobTitle,
              location: location,
              month: "",
              year: "",
              employee_size: employeeSize,
            }}
          />
        )}
      </VStack>
    </Box>
  );
}