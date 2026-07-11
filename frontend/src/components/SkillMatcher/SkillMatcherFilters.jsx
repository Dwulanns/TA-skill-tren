import {
  Box,
  Heading,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Select,
  Input,
  Button,
  Text,
  Badge,
  Icon,
  Tooltip,
  Flex,
} from "@chakra-ui/react";
import { Briefcase, Plus, Database, Filter, X } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

/**
 * Filter and input form panel for the Skill Matcher page.
 * Includes job selection, employee size filters, user skill additions, autocomplete suggestions,
 * and database-backed reference skill templates.
 */
export default function SkillMatcherFilters({
  targetJobTitle,
  setTargetJobTitle,
  jobOptions,
  loadingOptions,
  employeeSize,
  setEmployeeSize,
  employeeSizeOptions,
  loadingEmployeeSizes,
  skillInput,
  setSkillInput,
  suggestedSkills,
  showSuggestions,
  setShowSuggestions,
  handleAddSkill,
  handleRemoveSkill,
  handleKeyPress,
  dbSkillsType,
  fetchDbSkills,
  loadingDbSkills,
  dbSkills,
  userSkills,
  skillTypeFilter,
  setSkillTypeFilter,
  handleCalculateMatch,
  loadingMatch,
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

  const getFilterLabel = () =>
    SKILL_TYPE_FILTERS.find((f) => f.value === skillTypeFilter)?.label ||
    "Semua Skill";

  return (
    <VStack align="stretch" spacing={6} gridColumn={{ lg: "span 5" }}>
      <Box
        bg={cardBg}
        borderWidth="1px"
        borderColor={cardBorder}
        borderRadius="xl"
        boxShadow={cardShadow}
        p={6}
      >
        <Heading
          as="h2"
          size="sm"
          fontWeight="700"
          mb={4}
          display="flex"
          alignItems="center"
        >
          <Icon as={Briefcase} mr={2} color="blue.500" />
          Target Pekerjaan & Skill Anda
        </Heading>

        <VStack spacing={4} align="stretch">
          {/* Target Job */}
          <FormControl isRequired>
            <FormLabel fontWeight="600" fontSize="sm">
              Pilih Target Pekerjaan
            </FormLabel>
            <Select
              placeholder="Pilih Pekerjaan"
              value={targetJobTitle}
              onChange={(e) => setTargetJobTitle(e.target.value)}
              bg={isDark ? "gray.700" : "white"}
              borderColor={isDark ? "gray.600" : "gray.300"}
              borderRadius="lg"
              size="md"
              isLoading={loadingOptions}
            >
              {jobOptions.map((job) => (
                <option key={job.id} value={job.keyword}>
                  {job.keyword}
                </option>
              ))}
            </Select>
          </FormControl>

          {/* Company Size Filter */}
          <FormControl>
            <FormLabel fontWeight="600" fontSize="sm">
              Pilih Ukuran Perusahaan (Company Size)
            </FormLabel>
            <Select
              placeholder="Semua Ukuran"
              value={employeeSize}
              onChange={(e) => setEmployeeSize(e.target.value)}
              bg={isDark ? "gray.700" : "white"}
              borderColor={isDark ? "gray.600" : "gray.300"}
              borderRadius="lg"
              size="md"
              isLoading={loadingEmployeeSizes}
            >
              {employeeSizeOptions.map((opt) => (
                <option key={opt.size} value={opt.size}>
                  {opt.size}
                </option>
              ))}
            </Select>
          </FormControl>

          {/* Skill Input */}
          <FormControl>
            <FormLabel fontWeight="600" fontSize="sm">
              Ketik Skill Anda (lalu tekan Enter)
            </FormLabel>
            <Box position="relative">
              <HStack>
                <Input
                  placeholder="Contoh: SQL, Python, Tableau..."
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  onFocus={() =>
                    skillInput.length >= 2 && setShowSuggestions(true)
                  }
                  onBlur={() =>
                    setTimeout(() => setShowSuggestions(false), 200)
                  }
                  bg={isDark ? "gray.700" : "white"}
                  borderColor={isDark ? "gray.600" : "gray.300"}
                  borderRadius="lg"
                />
                <Button
                  onClick={() => {
                    if (suggestedSkills.length > 0) {
                      handleAddSkill(suggestedSkills[0].value);
                    } else {
                      handleAddSkill(skillInput);
                    }
                  }}
                  colorScheme="blue"
                  borderRadius="lg"
                  px={5}
                  leftIcon={<Plus size={16} />}
                >
                  Tambah
                </Button>
              </HStack>

              {showSuggestions && suggestedSkills.length > 0 && (
                <Box
                  position="absolute"
                  top="100%"
                  left="0"
                  right="0"
                  mt={1}
                  bg={isDark ? "gray.700" : "white"}
                  borderRadius="lg"
                  borderWidth="1px"
                  borderColor={isDark ? "gray.600" : "gray.200"}
                  boxShadow="lg"
                  zIndex={10}
                  maxH="200px"
                  overflowY="auto"
                >
                  {suggestedSkills.map((skill) => (
                    <Box
                      key={skill.value}
                      px={4}
                      py={2}
                      cursor="pointer"
                      _hover={{
                        bg: isDark ? "gray.600" : "gray.100",
                      }}
                      onClick={() => handleAddSkill(skill.value)}
                    >
                      <Flex justify="space-between" align="center">
                        <Text fontSize="sm" color={textColor}>
                          {skill.display}
                        </Text>
                        <Badge colorScheme="blue" fontSize="xs">
                          {skill.category}
                        </Badge>
                      </Flex>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          </FormControl>

          {/* Database Reference Skills */}
          <Box>
            <FormLabel
              fontWeight="600"
              fontSize="xs"
              color={subTextColor}
              mb={2}
            >
              <Icon as={Database} size={12} mr={1} />
              Lihat Contoh Skill yang Cocok dengan Pekerjaan
            </FormLabel>
            <HStack spacing={2} mb={3}>
              <Button
                size="xs"
                colorScheme="cyan"
                variant={dbSkillsType === 3 ? "solid" : "outline"}
                onClick={() => fetchDbSkills(3)}
                fontWeight="600"
              >
                Tech Stack
              </Button>
              <Button
                size="xs"
                colorScheme="purple"
                variant={dbSkillsType === 2 ? "solid" : "outline"}
                onClick={() => fetchDbSkills(2)}
                fontWeight="600"
              >
                Technical
              </Button>
              <Button
                size="xs"
                colorScheme="teal"
                variant={dbSkillsType === 1 ? "solid" : "outline"}
                onClick={() => fetchDbSkills(1)}
                fontWeight="600"
              >
                Soft Skill
              </Button>
            </HStack>

            {loadingDbSkills ? (
              <Flex align="center" py={2}>
                <Spinner size="xs" color="blue.500" mr={2} />
                <Text fontSize="xs" color={subTextColor}>
                  Memuat data...
                </Text>
              </Flex>
            ) : dbSkills.length > 0 ? (
              <Box
                p={3}
                bg={isDark ? "gray.900" : "gray.50"}
                borderRadius="lg"
                borderWidth="1px"
                borderColor={cardBorder}
                maxH="130px"
                overflowY="auto"
                mb={2}
              >
                <Flex wrap="wrap" gap={1.5}>
                  {dbSkills.map((skill) => (
                    <Tooltip
                      key={skill.skill_name}
                      label={`Tambahkan "${skill.skill_name}" (Demand: ${
                        skill.percentage !== undefined
                          ? `${skill.percentage}%`
                          : `${skill.count || skill.job_count} muncul`
                      })`}
                      placement="top"
                    >
                      <Button
                        size="xs"
                        variant="solid"
                        bg={isDark ? "gray.800" : "white"}
                        color={textColor}
                        borderWidth="1px"
                        borderColor={cardBorder}
                        borderRadius="md"
                        onClick={() => handleAddSkill(skill.skill_name)}
                        _hover={{
                          bg: "blue.500",
                          color: "white",
                          borderColor: "blue.500",
                        }}
                      >
                        +{skill.skill_name} (
                        {skill.percentage !== undefined
                          ? `${skill.percentage}%`
                          : `${skill.count || skill.job_count}`}
                        )
                      </Button>
                    </Tooltip>
                  ))}
                </Flex>
              </Box>
            ) : (
              dbSkillsType !== null && (
                <Text fontSize="xs" color="gray.500" fontStyle="italic">
                  Tidak ada data skill untuk kategori ini.
                </Text>
              )
            )}
          </Box>

          {/* Skill Type Filter */}
          <FormControl>
            <FormLabel
              fontWeight="600"
              fontSize="sm"
              display="flex"
              alignItems="center"
            >
              <Icon as={Filter} size={14} mr={1} />
              Tipe Skill yang Dibandingkan
            </FormLabel>
            <Select
              value={skillTypeFilter}
              onChange={(e) => setSkillTypeFilter(e.target.value)}
              bg={isDark ? "gray.700" : "white"}
              borderColor={isDark ? "gray.600" : "gray.300"}
              borderRadius="lg"
              size="md"
            >
              {SKILL_TYPE_FILTERS.map((filter) => (
                <option key={filter.value} value={filter.value}>
                  {filter.label}
                </option>
              ))}
            </Select>
            <Text fontSize="xs" color={subTextColor} mt={1}>
              Hanya skill bertipe ini yang akan dibandingkan dengan database.{" "}
              {skillTypeFilter !== "all" && (
                <Text as="span" color="blue.500" fontWeight="600">
                  Aktif: <b>{getFilterLabel()}</b>
                </Text>
              )}
            </Text>
          </FormControl>

          {/* Selected Skills list */}
          <Box
            minH="60px"
            p={3}
            bg={isDark ? "gray.900" : "gray.50"}
            borderRadius="lg"
            borderStyle="dashed"
            borderWidth="1.5px"
            borderColor={isDark ? "gray.600" : "gray.300"}
          >
            <FormLabel
              fontWeight="700"
              fontSize="xs"
              color={subTextColor}
              mb={2}
            >
              Skill Anda ({userSkills.length}):
            </FormLabel>
            {userSkills.length === 0 ? (
              <Text fontSize="xs" color="gray.500" fontStyle="italic">
                Belum ada skill yang ditambahkan.
              </Text>
            ) : (
              <Flex wrap="wrap" gap={1.5}>
                {userSkills.map((skill, index) => (
                  <Badge
                    key={`${skill}-${index}`}
                    px={2.5}
                    py={1}
                    borderRadius="full"
                    bg="blue.500"
                    color="white"
                    display="flex"
                    alignItems="center"
                    fontSize="xs"
                    textTransform="none"
                  >
                    {skill}
                    <Icon
                      as={X}
                      ml={1.5}
                      cursor="pointer"
                      size={10}
                      onClick={() => handleRemoveSkill(index)}
                      _hover={{ transform: "scale(1.2)" }}
                    />
                  </Badge>
                ))}
              </Flex>
            )}
          </Box>

          <Button
            colorScheme="blue"
            size="md"
            onClick={handleCalculateMatch}
            isLoading={loadingMatch}
            loadingText="Menganalisis..."
            borderRadius="lg"
            w="100%"
            fontWeight="bold"
            boxShadow="md"
            isDisabled={userSkills.length === 0}
          >
            Hitung Kesesuaian ({getFilterLabel()})
          </Button>
        </VStack>
      </Box>
    </VStack>
  );
}
