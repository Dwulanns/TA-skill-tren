import {
  Box,
  Heading,
  Text,
  Icon,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  HStack,
  Badge,
  Flex,
  Spinner,
  Button,
} from "@chakra-ui/react";
import { Filter, Terminal, Cpu, User2 } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

/**
 * Accordion list display of popular skills (Tech Stack, Technical, Soft Skill).
 * Allows users to choose one of the popular skills to trigger graph network analysis.
 */
export default function PopularSkillsAccordion({
  openCategories,
  setOpenCategories,
  techStackSkills,
  technicalSkills,
  softSkills,
  loadingCategorySkills,
  activeSkill,
  handleFetchCooccurrence,
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

  const skillCategories = [
    {
      label: "Tech Stack",
      icon: Terminal,
      accent: "blue",
      items: techStackSkills,
    },
    {
      label: "Technical Skill",
      icon: Cpu,
      accent: "cyan",
      items: technicalSkills,
    },
    {
      label: "Soft Skill",
      icon: User2,
      accent: "purple",
      items: softSkills,
    },
  ];

  return (
    <Box
      gridColumn={{ base: "span 1", lg: "span 4" }}
      bg={cardBg}
      borderWidth="1px"
      borderColor={cardBorder}
      borderRadius="xl"
      boxShadow={cardShadow}
      p={{ base: 4, md: 5 }}
      display="flex"
      flexDirection="column"
      minH={{ base: "auto", lg: "450px" }}
    >
      <Heading
        as="h2"
        size="xs"
        fontWeight="700"
        mb={1}
        color={textColor}
        display="flex"
        alignItems="center"
        gap={1.5}
      >
        <Icon as={Filter} boxSize="16px" color="blue.500" />
        Kompetensi Terpopuler
      </Heading>
      <Text fontSize="2xs" color={subTextColor} mb={3}>
        Klik kategori untuk membuka daftarnya, lalu pilih skill untuk melihat visualisasi jaringannya.
      </Text>

      <Accordion
        allowMultiple
        index={openCategories}
        onChange={(idx) => setOpenCategories(idx)}
        flex="1"
        overflowY="auto"
        maxH={{ base: "none", lg: "550px" }}
        pr={1}
      >
        {skillCategories.map((category) => (
          <AccordionItem key={category.label} border="none" mb={2}>
            <h2>
              <AccordionButton
                bg={isDark ? "gray.700" : "gray.100"}
                _hover={{ bg: isDark ? "gray.600" : "gray.200" }}
                borderRadius="md"
                px={3}
                py={2.5}
                transition="background 0.15s ease"
              >
                <HStack flex="1" textAlign="left" spacing={2}>
                  <Icon
                    as={category.icon}
                    boxSize="14px"
                    color={`${category.accent}.500`}
                  />
                  <Text fontWeight="700" fontSize="xs" color={textColor}>
                    {category.label}
                  </Text>
                  <Badge
                    colorScheme={category.accent}
                    variant="subtle"
                    fontSize="2xs"
                    borderRadius="full"
                  >
                    {category.items.length}
                  </Badge>
                </HStack>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={3} px={1} pt={2}>
              {loadingCategorySkills ? (
                <Flex justify="center" align="center" py={4}>
                  <Spinner size="xs" color={`${category.accent}.500`} />
                </Flex>
              ) : category.items.length === 0 ? (
                <Text
                  fontSize="xs"
                  color={subTextColor}
                  textAlign="center"
                  py={4}
                >
                  Tidak ada data skill untuk filter ini.
                </Text>
              ) : (
                <Flex wrap="wrap" gap={1.5}>
                  {category.items.map((item) => (
                    <Button
                      key={item.skill_name}
                      size="xs"
                      variant={
                        activeSkill === item.skill_name ? "solid" : "outline"
                      }
                      colorScheme={category.accent}
                      onClick={() => handleFetchCooccurrence(item.skill_name)}
                      fontWeight="600"
                      textTransform="none"
                      px={2.5}
                      py={3.5}
                      borderRadius="full"
                      transition="transform 0.1s ease"
                      _hover={{ transform: "translateY(-1px)" }}
                    >
                      {item.skill_name} ({item.percentage}%)
                    </Button>
                  ))}
                </Flex>
              )}
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>
    </Box>
  );
}
