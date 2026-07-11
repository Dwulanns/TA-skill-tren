import {
  Box,
  Flex,
  VStack,
  Text,
  Heading,
  HStack,
  Button,
  IconButton,
  Icon,
} from "@chakra-ui/react";
import { GitMerge, X } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

/**
 * Details display panel for the selected node from the Skill Network force graph.
 * Displays node frequencies and provides a quick option to fetch network data centered on the selected skill.
 */
export default function NodeDetailsPanel({
  selectedNode,
  setSelectedNode,
  handleFetchCooccurrence,
}) {
  const { isDark } = useTheme();

  // Style tokens
  const cardBorder = isDark ? "gray.700" : "gray.100";
  const textColor = isDark ? "white" : "gray.800";
  const subTextColor = isDark ? "gray.400" : "gray.600";

  if (!selectedNode) return null;

  return (
    <Box
      mt={4}
      p={4}
      bg={isDark ? "gray.900" : "gray.50"}
      borderRadius="xl"
      borderWidth="1px"
      borderColor={cardBorder}
    >
      <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
        <VStack align="stretch" spacing={0.5}>
          <Text
            fontSize="2xs"
            fontWeight="700"
            color={subTextColor}
            textTransform="uppercase"
          >
            Kompetensi Terpilih
          </Text>
          <Heading as="h4" size="sm" color={textColor} fontWeight="800">
            {selectedNode.id}
          </Heading>
          <Text fontSize="xs" color={subTextColor}>
            Ditemukan sebanyak <b>{selectedNode.frequency} kali</b> dalam
            database lowongan kerja (dengan filter aktif).
          </Text>
        </VStack>
        <HStack spacing={2}>
          <Button
            size="sm"
            colorScheme="cyan"
            color="white"
            leftIcon={<Icon as={GitMerge} boxSize="14px" />}
            onClick={() => handleFetchCooccurrence(selectedNode.id)}
          >
            Jelajahi Jaringan
          </Button>
          <IconButton
            size="sm"
            icon={<X size={14} />}
            onClick={() => setSelectedNode(null)}
            variant="ghost"
            aria-label="Tutup Detail"
          />
        </HStack>
      </Flex>
    </Box>
  );
}
