import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Grid,
  Flex,
  keyframes,
  IconButton,
  Link as ChakraLink,
  Icon,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { ChevronUpIcon, ChevronDownIcon } from "@chakra-ui/icons";
import { FaLinkedin } from "react-icons/fa";
import Header from "../components/Header";
import { useTheme } from "../context/ThemeContext";

// Animation for cards
const slideUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const fadeIn = keyframes`
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
`;

export default function LandingPage() {
  const { isDark } = useTheme();
  const [showScroll, setShowScroll] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setShowScroll(window.scrollY > 300);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const scrollToBottom = () => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: "smooth",
    });
  };

  return (
    <Box
      minH="100vh"
      bg={isDark ? "#0f172a" : "#f8fafc"}
      color={isDark ? "#f1f5f9" : "#0f172a"}
      pt={{ base: "80px", md: "90px" }}
    >
      {/* Header */}
      <Header isLanding={true} />

      {/* Hero Section */}
      <Box
        as="section"
        px={{ base: 4, md: 8 }}
        py={{ base: 20, md: 24 }}
        background={
          isDark
            ? "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
            : "linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%)"
        }
        position="relative"
        overflow="hidden"
        _before={{
          content: '""',
          position: "absolute",
          top: "-40%",
          right: "-20%",
          width: "500px",
          height: "500px",
          borderRadius: "50%",
          bg: isDark ? "rgba(6, 182, 212, 0.05)" : "rgba(2, 132, 199, 0.08)",
          filter: "blur(100px)",
          zIndex: 0,
        }}
        _after={{
          content: '""',
          position: "absolute",
          bottom: "-30%",
          left: "-10%",
          width: "400px",
          height: "400px",
          borderRadius: "50%",
          bg: isDark ? "rgba(14, 165, 233, 0.05)" : "rgba(59, 130, 246, 0.08)",
          filter: "blur(100px)",
          zIndex: 0,
        }}
        borderBottom={isDark ? "1px solid #1e293b" : "1px solid #cbd5e0"}
      >
        <Container maxW="6xl" px={0} position="relative" zIndex={1}>
          <Grid
            templateColumns={{ base: "1fr", md: "1fr 1fr" }}
            gap={{ base: 12, md: 16 }}
            alignItems="center"
          >
            {/* Left: Text Content */}
            <VStack
              spacing={8}
              align="start"
              animation={`${slideUp} 0.8s ease-out`}
            >
              <VStack spacing={4} align="start" w="100%">
                <Heading
                  as="h1"
                  size="2xl"
                  fontWeight="bold"
                  lineHeight="1.3"
                  letterSpacing="-0.5px"
                >
                  Analisis Tren Skill
                </Heading>
                <Heading
                  as="h2"
                  size="2xl"
                  fontWeight="bold"
                  lineHeight="1.3"
                  letterSpacing="-0.5px"
                  color={isDark ? "#06b6d4" : "#0284c7"}
                >
                  dari Lowongan Pekerjaan
                </Heading>
              </VStack>

              <Text
                fontSize="md"
                lineHeight="1.7"
                color={isDark ? "#e0f2fe" : "#1e293b"}
                maxW="sm"
              >
                Platform analisis data untuk memahami kebutuhan skill industri
                teknologi berdasarkan lowongan kerja dari LinkedIn.
              </Text>

              <HStack spacing={4} w="100%" pt={4}>
                <Button
                  as={RouterLink}
                  to="/dashboard"
                  bg={isDark ? "#0284c7" : "#0284c7"}
                  color="white"
                  px={8}
                  py={6}
                  fontSize="md"
                  fontWeight="600"
                  borderRadius="lg"
                  _hover={{
                    bg: isDark ? "#0369a1" : "#0369a1",
                    color: "#ffffff",
                    transform: "translateY(-2px)",
                    boxShadow: `0 8px 16px ${isDark ? "rgba(2, 132, 199, 0.2)" : "rgba(2, 132, 199, 0.15)"}`,
                  }}
                  transition="all 0.2s ease"
                >
                  Buka Dashboard
                </Button>

                <Button
                  as={RouterLink}
                  to="/manual"
                  bg="transparent"
                  color={isDark ? "#0284c7" : "#0284c7"}
                  border={`1.5px solid ${isDark ? "#0284c7" : "#0284c7"}`}
                  px={8}
                  py={6}
                  fontSize="md"
                  fontWeight="600"
                  borderRadius="lg"
                  _hover={{
                    bg: isDark
                      ? "rgba(2, 132, 199, 0.1)"
                      : "rgba(2, 132, 199, 0.05)",
                    transform: "translateY(-2px)",
                  }}
                  transition="all 0.2s ease"
                >
                  Pelajari Lebih Lanjut
                </Button>
              </HStack>
            </VStack>

            {/* Right: Visual Card */}
            <Flex
              justify="center"
              align="center"
              display={{ base: "none", md: "flex" }}
              animation={`${slideUp} 1s ease-out 0.2s both`}
            >
              <Box
                bg={isDark ? "#1e293b" : "#ffffff"}
                borderRadius="xl"
                p={{ base: 6, md: 8 }}
                border={isDark ? "1px solid #334155" : "1px solid #cbd5e0"}
                w="100%"
                transition="all 0.3s ease"
                boxShadow={
                  isDark
                    ? "0 4px 6px rgba(0,0,0,0.1)"
                    : "0 2px 12px rgba(2, 132, 199, 0.1)"
                }
                _hover={{
                  borderColor: isDark ? "#0284c7" : "#0284c7",
                  boxShadow: isDark
                    ? "0 12px 24px rgba(2, 132, 199, 0.1)"
                    : "0 12px 24px rgba(2, 132, 199, 0.15)",
                  transform: "translateY(-4px)",
                }}
              >
                <VStack spacing={6} align="stretch">
                  <Text
                    fontSize="sm"
                    fontWeight="600"
                    color={isDark ? "#cffafe" : "#374151"}
                  >
                    Preview Visualisasi
                  </Text>

                  {/* Mini Chart */}
                  <Box
                    h="160px"
                    bg={isDark ? "#0f172a" : "#f0f9ff"}
                    borderRadius="lg"
                    display="flex"
                    alignItems="flex-end"
                    justifyContent="space-around"
                    p={4}
                    gap={3}
                  >
                    {[42, 58, 46, 72, 80, 65, 88, 76, 82, 70, 65, 75].map(
                      (height, idx) => (
                        <Box
                          key={idx}
                          bg={isDark ? "#0284c7" : "#0284c7"}
                          height={`${height}%`}
                          flex={1}
                          borderRadius="md"
                          opacity={0.8}
                          transition="all 0.3s ease"
                          cursor="pointer"
                          _hover={{
                            opacity: 1,
                            height: `${Math.min(height + 12, 100)}%`,
                          }}
                        />
                      ),
                    )}
                  </Box>

                  {/* Stats Row */}
                  <Grid templateColumns="repeat(3, 1fr)" gap={4} pt={2}>
                    <VStack spacing={1}>
                      <Text
                        fontSize="sm"
                        fontWeight="700"
                        color={isDark ? "#f8fafc" : "#0f172a"}
                      >
                        10K+
                      </Text>
                      <Text
                        fontSize="xs"
                        color={isDark ? "#cffafe" : "#374151"}
                      >
                        Lowongan
                      </Text>
                    </VStack>
                    <VStack spacing={1}>
                      <Text
                        fontSize="sm"
                        fontWeight="700"
                        color={isDark ? "#f8fafc" : "#0f172a"}
                      >
                        500+
                      </Text>
                      <Text
                        fontSize="xs"
                        color={isDark ? "#cffafe" : "#374151"}
                      >
                        Skills
                      </Text>
                    </VStack>
                    <VStack spacing={1}>
                      <Text
                        fontSize="sm"
                        fontWeight="700"
                        color={isDark ? "#f8fafc" : "#0f172a"}
                      >
                        LinkedIn
                      </Text>
                      <Text
                        fontSize="xs"
                        color={isDark ? "#cffafe" : "#374151"}
                      >
                        Source
                      </Text>
                    </VStack>
                  </Grid>
                </VStack>
              </Box>
            </Flex>
          </Grid>
        </Container>
      </Box>

      {/* About Section */}
      <Box
        as="section"
        px={{ base: 4, md: 8 }}
        py={{ base: 16, md: 20 }}
        background={
          isDark
            ? "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)"
            : "linear-gradient(180deg, #f8fafc 0%, #e0f2fe 100%)"
        }
        position="relative"
        borderBottom={isDark ? "1px solid #1e293b" : "1px solid #cbd5e0"}
      >
        <Container maxW="6xl" px={0}>
          <VStack spacing={12} align="stretch">
            {/* Section Header */}
            <VStack spacing={3} align="start">
              <Heading
                size="xl"
                fontWeight="bold"
                color={isDark ? "#f8fafc" : "#0f172a"}
              >
                Tentang Data Kami
              </Heading>
              <Text color={isDark ? "#e0f2fe" : "#1e293b"} fontSize="md">
                Sumber dan jenis data yang kami analisis untuk memberikan
                insight industri
              </Text>
            </VStack>

            {/* Data Cards Grid */}
            <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={8}>
              {/* Card 1: Sumber Data */}
              <Box
                bg={isDark ? "#1e293b" : "#ffffff"}
                border={isDark ? "1px solid #334155" : "1px solid #cbd5e0"}
                borderRadius="xl"
                p={8}
                transition="all 0.3s ease"
                animation={`${slideUp} 0.8s ease-out`}
                boxShadow={
                  isDark
                    ? "0 4px 6px rgba(0,0,0,0.1)"
                    : "0 2px 8px rgba(2, 132, 199, 0.08)"
                }
                _hover={{
                  borderColor: isDark ? "#0284c7" : "#0284c7",
                  boxShadow: isDark
                    ? "0 12px 24px rgba(2, 132, 199, 0.1)"
                    : "0 12px 24px rgba(2, 132, 199, 0.12)",
                  transform: "translateY(-4px)",
                }}
                position="relative"
                overflow="hidden"
                _before={{
                  content: '""',
                  position: "absolute",
                  top: "-100px",
                  right: "-100px",
                  width: "200px",
                  height: "200px",
                  borderRadius: "50%",
                  bg: isDark
                    ? "rgba(2, 132, 199, 0.08)"
                    : "rgba(2, 132, 199, 0.05)",
                  filter: "blur(80px)",
                  zIndex: 0,
                }}
              >
                <Box position="relative" zIndex={1}>
                  <VStack spacing={6} align="start" h="100%">
                    <Heading
                      size="md"
                      fontWeight="bold"
                      color={isDark ? "#f8fafc" : "#0f172a"}
                    >
                      Sumber Data
                    </Heading>

                    <VStack spacing={4} align="start" flex={1}>
                      <VStack spacing={2} align="start">
                        <ChakraLink
                          href="https://www.linkedin.com/jobs/"
                          isExternal
                          role="group"
                          display="inline-flex"
                          w="fit-content"
                          _hover={{ textDecoration: "none" }}
                          _focusVisible={{
                            outline: "none",
                            boxShadow: isDark
                              ? "0 0 0 3px rgba(2, 132, 199, 0.35)"
                              : "0 0 0 3px rgba(2, 132, 199, 0.25)",
                            borderRadius: "lg",
                          }}
                          aria-label="Buka LinkedIn Jobs"
                        >
                          <HStack
                            spacing={3}
                            align="center"
                            px={3}
                            py={2}
                            borderRadius="lg"
                            bg={
                              isDark
                                ? "rgba(2, 132, 199, 0.12)"
                                : "rgba(2, 132, 199, 0.06)"
                            }
                            border={
                              isDark ? "1px solid #334155" : "1px solid #cbd5e0"
                            }
                            transition="all 0.2s ease"
                            _groupHover={{
                              transform: "translateY(-1px)",
                              borderColor: "#0284c7",
                              bg: isDark
                                ? "rgba(2, 132, 199, 0.18)"
                                : "rgba(2, 132, 199, 0.1)",
                            }}
                          >
                            <Icon as={FaLinkedin} boxSize={7} color="#0284c7" />
                            <VStack spacing={0} align="start">
                              <Text
                                as="span"
                                fontSize="sm"
                                fontWeight="700"
                                color={isDark ? "#f8fafc" : "#0f172a"}
                                lineHeight="1.2"
                              >
                                LinkedIn Jobs
                              </Text>
                              <Text
                                as="span"
                                fontSize="xs"
                                color={isDark ? "#cffafe" : "#374151"}
                                lineHeight="1.2"
                              >
                                Klik untuk membuka
                              </Text>
                            </VStack>
                          </HStack>
                        </ChakraLink>
                        <Text
                          fontSize="sm"
                          color={isDark ? "#e0f2fe" : "#1e293b"}
                          lineHeight="1.6"
                        >
                          Data dikumpulkan melalui <strong>web scraping</strong>{" "}
                          dari platform LinkedIn, menganalisis jutaan lowongan
                          kerja.
                        </Text>
                      </VStack>

                      <Box pt={4} w="100%">
                        <VStack spacing={3} align="start" w="100%">
                          <Box
                            w="100%"
                            h="px"
                            bg={isDark ? "#334155" : "#cbd5e0"}
                          />
                          <HStack spacing={2} w="100%">
                            <Box w={2} h={2} bg="#0284c7" borderRadius="full" />
                            <Text
                              fontSize="xs"
                              color={isDark ? "#cffafe" : "#374151"}
                            >
                              Data diambil dari LinkedIn
                            </Text>
                          </HStack>
                          <HStack spacing={2} w="100%">
                            <Box w={2} h={2} bg="#0284c7" borderRadius="full" />
                            <Text
                              fontSize="xs"
                              color={isDark ? "#cffafe" : "#374151"}
                            >
                              Update berkala setiap bulan
                            </Text>
                          </HStack>
                        </VStack>
                      </Box>
                    </VStack>
                  </VStack>
                </Box>
              </Box>

              {/* Card 2: Jenis Data */}
              <Box
                bg={isDark ? "#1e293b" : "#ffffff"}
                border={isDark ? "1px solid #334155" : "1px solid #cbd5e0"}
                borderRadius="xl"
                p={8}
                transition="all 0.3s ease"
                animation={`${slideUp} 0.8s ease-out 0.1s both`}
                boxShadow={
                  isDark
                    ? "0 4px 6px rgba(0,0,0,0.1)"
                    : "0 2px 8px rgba(2, 132, 199, 0.08)"
                }
                _hover={{
                  borderColor: isDark ? "#0284c7" : "#0284c7",
                  boxShadow: isDark
                    ? "0 12px 24px rgba(2, 132, 199, 0.1)"
                    : "0 12px 24px rgba(2, 132, 199, 0.12)",
                  transform: "translateY(-4px)",
                }}
                position="relative"
                overflow="hidden"
                _before={{
                  content: '""',
                  position: "absolute",
                  top: "-100px",
                  right: "-100px",
                  width: "200px",
                  height: "200px",
                  borderRadius: "50%",
                  bg: isDark
                    ? "rgba(14, 165, 233, 0.08)"
                    : "rgba(59, 130, 246, 0.05)",
                  filter: "blur(80px)",
                  zIndex: 0,
                }}
              >
                <Box position="relative" zIndex={1}>
                  <VStack spacing={6} align="start" h="100%">
                    <Heading
                      size="md"
                      fontWeight="bold"
                      color={isDark ? "#f8fafc" : "#0f172a"}
                    >
                      Jenis Data Dianalisis
                    </Heading>

                    <VStack spacing={4} align="start" flex={1} w="100%">
                      {[
                        ["Job Title", "Posisi pekerjaan yang tersedia"],
                        ["Lokasi", "Area/kota penempatan kerja"],
                        ["Skill", "Kompetensi yang dibutuhkan"],
                        ["Perusahaan", "Perusahaan yang merekrut"],
                      ].map((item, idx) => (
                        <Box
                          key={idx}
                          w="100%"
                          pb={4}
                          borderBottom={
                            idx < 3
                              ? isDark
                                ? "1px solid #334155"
                                : "1px solid #cbd5e0"
                              : "none"
                          }
                        >
                          <Text
                            fontSize="sm"
                            fontWeight="600"
                            color={isDark ? "#f8fafc" : "#0f172a"}
                            mb={1}
                          >
                            {item[0]}
                          </Text>
                          <Text
                            fontSize="sm"
                            color={isDark ? "#e0f2fe" : "#1e293b"}
                          >
                            {item[1]}
                          </Text>
                        </Box>
                      ))}
                    </VStack>
                  </VStack>
                </Box>
              </Box>
            </Grid>
          </VStack>
        </Container>
      </Box>

      {/* Features Section */}
      <Box
        as="section"
        px={{ base: 4, md: 8 }}
        py={{ base: 16, md: 20 }}
        background={
          isDark
            ? "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)"
            : "linear-gradient(180deg, #e0f2fe 0%, #f0f9ff 100%)"
        }
        position="relative"
        borderBottom={isDark ? "1px solid #1e293b" : "1px solid #cbd5e0"}
      >
        <Container maxW="6xl" px={0}>
          <VStack spacing={12} align="stretch">
            {/* Section Header */}
            <VStack spacing={3} align="start">
              <Heading
                size="xl"
                fontWeight="bold"
                color={isDark ? "#f8fafc" : "#0f172a"}
              >
                Fitur Utama
              </Heading>
              <Text color={isDark ? "#e0f2fe" : "#1e293b"} fontSize="md">
                Analisis mendalam dengan visualisasi interaktif untuk memahami
                tren skill
              </Text>
            </VStack>

            {/* Features Grid */}
            <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={8}>
              {[
                [
                  "Visualisasi Tren",
                  "Grafik interaktif untuk melihat perubahan kebutuhan skill dari waktu ke waktu",
                ],
                [
                  "Filter Data",
                  "Filter berdasarkan skill, lokasi, dan waktu untuk analisis lebih mendalam",
                ],
                [
                  "Perbandingan Skill",
                  "Bandingkan berbagai skill dalam kategori yang sama",
                ],
                [
                  "Statistik Komprehensif",
                  "Data lengkap dari lowongan pekerjaan LinkedIn",
                ],
              ].map((feature, idx) => (
                <Box
                  key={idx}
                  bg={isDark ? "#0f172a" : "#ffffff"}
                  border={isDark ? "1px solid #334155" : "1px solid #cbd5e0"}
                  borderRadius="xl"
                  p={6}
                  transition="all 0.3s ease"
                  animation={`${slideUp} 0.8s ease-out ${idx * 0.1}s both`}
                  boxShadow={
                    isDark
                      ? "0 2px 4px rgba(0,0,0,0.1)"
                      : "0 2px 8px rgba(2, 132, 199, 0.08)"
                  }
                  _hover={{
                    borderColor: isDark ? "#0284c7" : "#0284c7",
                    transform: "translateY(-4px)",
                    boxShadow: isDark
                      ? "0 12px 24px rgba(2, 132, 199, 0.1)"
                      : "0 12px 24px rgba(2, 132, 199, 0.12)",
                  }}
                >
                  <VStack spacing={3} align="start" h="100%">
                    <Heading
                      size="sm"
                      fontWeight="bold"
                      color={isDark ? "#f8fafc" : "#0f172a"}
                    >
                      {feature[0]}
                    </Heading>
                    <Text
                      fontSize="sm"
                      color={isDark ? "#e0f2fe" : "#1e293b"}
                      lineHeight="1.6"
                    >
                      {feature[1]}
                    </Text>
                  </VStack>
                </Box>
              ))}
            </Grid>
          </VStack>
        </Container>
      </Box>

      {/* Footer */}
      <Box
        as="footer"
        px={{ base: 4, md: 8 }}
        py={8}
        background={
          isDark
            ? "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)"
            : "linear-gradient(180deg, #e0f2fe 0%, #f0f9ff 100%)"
        }
        borderTop={isDark ? "1px solid #1e293b" : "1px solid #cbd5e0"}
      >
        <Container maxW="6xl" px={0}>
          <VStack spacing={4} align="center">
            <Text
              fontWeight="600"
              fontSize="sm"
              color={isDark ? "#f8fafc" : "#0f172a"}
            >
              TA Skill Trend Analytics
            </Text>
            <Text fontSize="xs" color={isDark ? "#e0f2fe" : "#1e293b"}>
              Analisis tren kebutuhan skill berdasarkan lowongan pekerjaan dari
              LinkedIn
            </Text>
            <Text fontSize="xs" color={isDark ? "#cffafe" : "#374151"}>
              Tugas Akhir D4 Teknik Informatika © 2024
            </Text>
          </VStack>
        </Container>
      </Box>

      {/* Scroll Up/Down Buttons */}
      {showScroll && (
        <VStack
          position="fixed"
          bottom="2rem"
          right="2rem"
          spacing={2}
          zIndex={500}
        >
          <IconButton
            icon={<ChevronUpIcon w={5} h={5} />}
            onClick={scrollToTop}
            bg={isDark ? "#0284c7" : "#0284c7"}
            color="white"
            borderRadius="full"
            size="sm"
            _hover={{
              bg: isDark ? "#0369a1" : "#0369a1",
              transform: "scale(1.1)",
            }}
            transition="all 0.2s ease"
            title="Scroll to top"
          />
          <IconButton
            icon={<ChevronDownIcon w={5} h={5} />}
            onClick={scrollToBottom}
            bg={isDark ? "#0284c7" : "#0284c7"}
            color="white"
            borderRadius="full"
            size="sm"
            _hover={{
              bg: isDark ? "#0369a1" : "#0369a1",
              transform: "scale(1.1)",
            }}
            transition="all 0.2s ease"
            title="Scroll to bottom"
          />
        </VStack>
      )}
    </Box>
  );
}
