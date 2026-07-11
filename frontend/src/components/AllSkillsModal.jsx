import { useEffect, useState } from "react";
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Spinner,
  Center,
  Badge,
  Input,
  VStack,
  HStack,
  Text,
  Tooltip,
} from "@chakra-ui/react";
import axios from "axios";
import { useTheme } from "../context/ThemeContext";

import { API_ENDPOINTS, buildQueryString } from "../config/api";

const SKILL_TYPE_COLORS = {
  tech_stack: "blue",
  technical_skill: "purple",
  soft_skill: "orange",
};

export default function AllSkillsModal({
  isOpen,
  onClose,
  skillType,
  skillTypeId,
  filters,
}) {
  const { isDark } = useTheme();
  const [allSkills, setAllSkills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !skillTypeId) return;

    setLoading(true);
    setError(null);

    // Build query params
    const params = buildQueryString({
      skill_type_id: skillTypeId,
      keyword_id: filters?.keyword_id,
      location: filters?.location,
      employee_size: filters?.employee_size,
      month: filters?.month,
      year: filters?.year,
    });

    axios
      .get(`${API_ENDPOINTS.DASHBOARD.ALL_SKILLS_BY_TYPE}?${params}`)
      .then((res) => {
        console.log("All skills data:", res.data);
        setAllSkills(res.data || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching all skills:", err);
        setError(err.response?.data?.detail || err.message);
        setLoading(false);
      });
  }, [isOpen, skillTypeId, filters]);

  // Filter skills berdasarkan search term
  const filteredSkills = allSkills.filter((skill) =>
    skill.skill_name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const colorScheme = SKILL_TYPE_COLORS[skillType] || "blue";

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="2xl" isCentered>
      <ModalOverlay backdropFilter="blur(4px)" />
      <ModalContent
        maxH="90vh"
        bg={isDark ? "#1e293b" : "#ffffff"}
        color={isDark ? "#f8fafc" : "#0f172a"}
        display="flex"
        flexDirection="column"
      >
        <ModalHeader
          borderBottomWidth="1px"
          borderColor={isDark ? "#475569" : "#e2e8f0"}
          flexShrink={0}
        >
          <VStack align="start" spacing={2}>
            <Box display="flex" alignItems="center" gap={3}>
              <Text fontSize="xl" fontWeight="bold">
                Semua{" "}
                {skillType === "tech_stack"
                  ? "Tech Stack"
                  : skillType === "technical_skill"
                    ? "Technical Skill"
                    : "Soft Skill"}
              </Text>
              <Badge colorScheme={colorScheme} fontSize="sm">
                Total: {filteredSkills.length}
              </Badge>
            </Box>
            <Text fontSize="sm" color={isDark ? "#cbd5e1" : "#64748b"}>
              Total {allSkills.length} unique skills ditemukan
            </Text>
          </VStack>
        </ModalHeader>
        <ModalCloseButton
          color="#22c55e"
          bg="rgba(34, 197, 94, 0.08)"
          borderRadius="md"
          _hover={{
            bg: "rgba(34, 197, 94, 0.16)",
            color: "#16a34a",
          }}
          _focus={{
            boxShadow: "0 0 0 3px rgba(34, 197, 94, 0.2)",
          }}
          sx={{
            svg: {
              width: "18px",
              height: "18px",
              strokeWidth: 3,
            },
          }}
        />

        <ModalBody pb={0} flex={1} overflow="auto">
          <VStack spacing={4} align="stretch">
            {/* Search Box */}
            <Input
              placeholder="Cari skill..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="sm"
              bg={isDark ? "#334155" : "#f8fafc"}
              borderColor={isDark ? "#475569" : "#e2e8f0"}
              color={isDark ? "#f8fafc" : "#0f172a"}
              _placeholder={{ color: isDark ? "#94a3b8" : "#94a3b8" }}
              _focus={{
                borderColor: "#0284c7",
                boxShadow: `0 0 0 3px rgba(2, 132, 199, 0.1)`,
              }}
            />

            {/* Table or Loading/Error */}
            {loading ? (
              <Center h="300px">
                <Spinner size="lg" color={colorScheme} />
              </Center>
            ) : error ? (
              <Box
                p={4}
                bg={isDark ? "#7f1d1d" : "#fee2e2"}
                borderRadius="md"
                border="1px solid"
                borderColor={isDark ? "#dc2626" : "#fecaca"}
              >
                <Text color={isDark ? "#fca5a5" : "#dc2626"} fontWeight="bold">
                  Error: {error}
                </Text>
              </Box>
            ) : filteredSkills.length > 0 ? (
              <Box
                overflowY="auto"
                maxH="400px"
                borderRadius="md"
                border="1px solid"
                borderColor={isDark ? "#475569" : "#e2e8f0"}
              >
                <Table size="sm" variant="simple">
                  <Thead
                    position="sticky"
                    top={0}
                    bg={isDark ? "#334155" : "#f8fafc"}
                    zIndex={1}
                    borderBottomWidth="2px"
                    borderColor={isDark ? "#475569" : "#e2e8f0"}
                  >
                    <Tr>
                      <Th
                        w="80px"
                        color={isDark ? "#f8fafc" : "#0f172a"}
                        fontWeight="900"
                      >
                        Rank
                      </Th>
                      <Th
                        color={isDark ? "#f8fafc" : "#0f172a"}
                        fontWeight="900"
                      >
                        Skill Name
                      </Th>
                      <Th
                        w="100px"
                        isNumeric
                        color={isDark ? "#f8fafc" : "#0f172a"}
                        fontWeight="900"
                        title="Jumlah lowongan yang mengandung skill"
                      >
                        Lowongan
                      </Th>
                      <Th
                        w="100px"
                        isNumeric
                        color={isDark ? "#f8fafc" : "#0f172a"}
                        fontWeight="900"
                      >
                        %
                      </Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredSkills.map((skill, idx) => {
                      const isTop10 = skill.rank <= 10;
                      return (
                        <Tr
                          key={skill.rank}
                          bg={
                            isTop10
                              ? isDark
                                ? "rgba(34, 197, 94, 0.2)"
                                : "rgba(34, 197, 94, 0.1)"
                              : idx % 2 === 0
                                ? isDark
                                  ? "#1e293b"
                                  : "#f8fafc"
                                : isDark
                                  ? "#334155"
                                  : "#ffffff"
                          }
                          _hover={{ bg: isDark ? "#475569" : "#e0f2fe" }}
                          cursor="pointer"
                          borderBottomWidth="1px"
                          borderColor={isDark ? "#475569" : "#e2e8f0"}
                          borderLeftWidth={isTop10 ? "4px" : "0px"}
                          borderLeftColor={isTop10 ? "#22c55e" : "transparent"}
                        >
                          <Td
                            fontWeight="900"
                            color={isTop10 ? "#22c55e" : "#0284c7"}
                          >
                            #{skill.rank}
                          </Td>
                          <Td
                            fontWeight="700"
                            color={isDark ? "#f8fafc" : "#0f172a"}
                          >
                            {skill.skill_name}
                          </Td>
                          <Td
                            isNumeric
                            fontWeight="900"
                            color={isDark ? "#f8fafc" : "#0f172a"}
                          >
                            {skill.job_count}/{skill.total_jobs}
                          </Td>
                          <Td isNumeric>
                            <Tooltip
                              label={`${skill.skill_name} muncul di ${skill.job_count} dari ${skill.total_jobs} lowongan`}
                              placement="top"
                            >
                              <Box
                                fontSize="sm"
                                fontWeight="900"
                                color={
                                  isTop10
                                    ? "#22c55e"
                                    : isDark
                                      ? "#cbd5e1"
                                      : "#334155"
                                }
                                cursor="help"
                              >
                                {skill.percentage}%
                              </Box>
                            </Tooltip>
                          </Td>
                        </Tr>
                      );
                    })}
                  </Tbody>
                </Table>
              </Box>
            ) : (
              <Box
                p={8}
                textAlign="center"
                bg={isDark ? "#334155" : "#f8fafc"}
                borderRadius="md"
                border="1px solid"
                borderColor={isDark ? "#475569" : "#e2e8f0"}
              >
                <Text color={isDark ? "#cbd5e1" : "#64748b"} fontWeight="600">
                  {searchTerm
                    ? "Tidak ada skill yang cocok dengan pencarian"
                    : "Tidak ada data skill untuk filter ini"}
                </Text>
              </Box>
            )}
          </VStack>
        </ModalBody>

        {/* Stats Footer - ditempel di bawah */}
        {!loading && filteredSkills.length > 0 && (
          <Box
            p={4}
            bg={isDark ? "#334155" : "#f8fafc"}
            borderRadius="md"
            borderTop="1px solid"
            borderColor={isDark ? "#475569" : "#e2e8f0"}
            flexShrink={0}
          >
            <HStack justify="space-between">
              <Text
                color={isDark ? "#cbd5e1" : "#64748b"}
                fontWeight="600"
                fontSize="sm"
              >
                Menampilkan: {filteredSkills.length} dari {allSkills.length}{" "}
                skills
              </Text>
              <Text fontWeight="900" color="#0284c7" fontSize="sm">
                Total: {allSkills.length > 0 ? allSkills[0].total_jobs : 0}{" "}
                lowongan
              </Text>
            </HStack>
          </Box>
        )}
      </ModalContent>
    </Modal>
  );
}