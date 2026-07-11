import {
  Box,
  HStack,
  Text,
  Spinner,
  SimpleGrid,
  Select,
  Input,
  IconButton,
  Icon,
  List as ChakraList,
  ListItem,
} from "@chakra-ui/react";
import { SlidersHorizontal, Search, X, ChevronRight } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

/**
 * Filter panel for Skill Network Page.
 * Handles job title filters, employee size options, and search autocomplete overlay.
 */
export default function SkillNetworkFilters({
  keywordId,
  setKeywordId,
  employeeSize,
  setEmployeeSize,
  skillInput,
  setSkillInput,
  suggestedSkills,
  setSuggestedSkills,
  showSuggestions,
  setShowSuggestions,
  filterOptions,
  employeeSizeOptions,
  loadingFilters,
  handleFetchCooccurrence,
}) {
  const { isDark } = useTheme();

  // Style tokens
  const cardBg = isDark ? "gray.800" : "white";
  const cardBorder = isDark ? "gray.700" : "gray.100";
  const cardShadow = isDark
    ? "0 8px 25px rgba(0,0,0,0.5)"
    : "0 8px 25px rgba(0,0,0,0.05)";
  const subTextColor = isDark ? "gray.400" : "gray.600";
  const inputBg = isDark ? "gray.750" : "gray.50";

  return (
    <Box
      bg={cardBg}
      borderWidth="1px"
      borderColor={cardBorder}
      borderRadius="xl"
      boxShadow={cardShadow}
      p={{ base: 3, md: 4 }}
    >
      <HStack mb={2.5} spacing={1.5}>
        <Icon as={SlidersHorizontal} size={14} color="blue.500" />
        <Text
          fontSize="2xs"
          fontWeight="700"
          textTransform="uppercase"
          letterSpacing="0.04em"
          color={subTextColor}
        >
          Filter & Pencarian
        </Text>
        {loadingFilters && <Spinner size="xs" color="blue.500" />}
      </HStack>

      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={3}>
        {/* Job Title Select */}
        <Box>
          <Select
            value={keywordId}
            onChange={(e) => setKeywordId(e.target.value)}
            bg={inputBg}
            borderColor={isDark ? "gray.600" : "gray.300"}
            borderWidth="2px"
            borderRadius="md"
            h="44px"
            fontSize="sm"
            _hover={{ borderColor: "blue.400" }}
            _focus={{ borderColor: "blue.500", boxShadow: "none" }}
          >
            <option value="">Semua Lowongan Pekerjaan</option>
            {filterOptions?.keywords?.map((k) => (
              <option key={k.id} value={k.id}>
                {k.keyword}
              </option>
            ))}
          </Select>
        </Box>

        {/* Employee Size Select */}
        <Box>
          <Select
            value={employeeSize}
            onChange={(e) => setEmployeeSize(e.target.value)}
            bg={inputBg}
            borderColor={isDark ? "gray.600" : "gray.300"}
            borderWidth="2px"
            borderRadius="md"
            h="44px"
            fontSize="sm"
            _hover={{ borderColor: "blue.400" }}
            _focus={{ borderColor: "blue.500", boxShadow: "none" }}
          >
            <option value="">Semua Ukuran Perusahaan</option>
            {employeeSizeOptions.map((item) => (
              <option key={item.size} value={item.size}>
                {item.size}
              </option>
            ))}
          </Select>
        </Box>

        {/* Autocomplete Input Search */}
        <Box>
          <Box position="relative" zIndex={10}>
            <HStack
              bg={inputBg}
              borderColor={isDark ? "gray.600" : "gray.300"}
              borderWidth="2px"
              borderRadius="md"
              px={3}
              height="44px"
              _focusWithin={{ borderColor: "blue.500" }}
              _hover={{ borderColor: "blue.400" }}
            >
              <Icon as={Search} boxSize="16px" color="gray.400" flexShrink={0} />
              <Input
                variant="unstyled"
                placeholder="Ketik nama skill..."
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    if (suggestedSkills.length > 0) {
                      handleFetchCooccurrence(suggestedSkills[0]);
                    } else {
                      handleFetchCooccurrence(skillInput);
                    }
                  }
                }}
                fontSize="sm"
                h="100%"
                w="100%"
              />
              {skillInput && (
                <IconButton
                  size="xs"
                  icon={<X size={14} />}
                  onClick={() => {
                    setSkillInput("");
                    setSuggestedSkills([]);
                    setShowSuggestions(false);
                  }}
                  variant="ghost"
                  aria-label="Bersihkan input"
                  flexShrink={0}
                />
              )}
            </HStack>

            {/* Suggestions Overlay */}
            {showSuggestions && (
              <Box
                position="absolute"
                top="48px"
                left="0"
                right="0"
                bg={isDark ? "gray.800" : "white"}
                borderWidth="1px"
                borderColor={cardBorder}
                borderRadius="md"
                boxShadow="lg"
                maxH="220px"
                overflowY="auto"
                zIndex={99}
              >
                <ChakraList spacing={0}>
                  {suggestedSkills.map((skill, idx) => (
                    <ListItem
                      key={idx}
                      px={4}
                      py={2}
                      cursor="pointer"
                      fontSize="sm"
                      _hover={{
                        bg: isDark ? "blue.900" : "blue.50",
                        color: isDark ? "white" : "blue.600",
                      }}
                      onClick={() => handleFetchCooccurrence(skill)}
                    >
                      <HStack justify="space-between">
                        <Text fontWeight="600">{skill}</Text>
                        <Icon as={ChevronRight} boxSize="14px" color="gray.400" />
                      </HStack>
                    </ListItem>
                  ))}
                </ChakraList>
              </Box>
            )}
          </Box>
        </Box>
      </SimpleGrid>
    </Box>
  );
}
