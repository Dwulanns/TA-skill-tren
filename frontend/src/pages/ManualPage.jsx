import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Card,
  CardBody,
  Divider,
  OrderedList,
  ListItem,
  SimpleGrid,
  Button,
  Flex,
} from "@chakra-ui/react";
import { useTheme } from "../context/ThemeContext";
import { useState } from "react";

const sections = [
  { id: "filters", label: "Filter Data" },
  { id: "charts", label: "Penjelasan Grafik" },
  { id: "tips", label: "Tips Membaca" },
  { id: "comparison", label: "Perbandingan" },
];

export default function ManualPage() {
  const { isDark } = useTheme();
  const [activeSection, setActiveSection] = useState("filters");

  const scrollToSection = (sectionId) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <Box bg={isDark ? "#0f172a" : "#ffffff"} minH="100vh" py={8}>
      <Container maxW="6xl">
        <Flex gap={{ base: 0, md: 8 }} direction={{ base: "column", md: "row" }}>
          <Box
            display={{ base: "none", md: "block" }}
            position="sticky"
            top="100px"
            minH="calc(100vh - 120px)"
            width="220px"
            flexShrink={0}
          >
            <Card
              bg={isDark ? "#1e293b" : "#f8fafc"}
              borderColor={isDark ? "#475569" : "#e2e8f0"}
              borderWidth="1px"
            >
              <CardBody>
                <Heading
                  size="sm"
                  color={isDark ? "#0284c7" : "#0284c7"}
                  mb={4}
                  fontWeight="700"
                  fontSize="sm"
                  textTransform="uppercase"
                  letterSpacing="0.5px"
                >
                  Daftar Isi
                </Heading>
                <VStack spacing={2} align="stretch">
                  {sections.map((section) => (
                    <Button
                      key={section.id}
                      onClick={() => scrollToSection(section.id)}
                      justifyContent="flex-start"
                      variant={activeSection === section.id ? "solid" : "ghost"}
                      bg={activeSection === section.id ? "#0284c7" : "transparent"}
                      color={activeSection === section.id ? "white" : isDark ? "#cbd5e1" : "#475569"}
                      _hover={{
                        bg: activeSection === section.id
                          ? "#0369a1"
                          : isDark
                            ? "rgba(2,132,199,0.12)"
                            : "rgba(2,132,199,0.08)",
                      }}
                      size="sm"
                    >
                      {section.label}
                    </Button>
                  ))}
                </VStack>
              </CardBody>
            </Card>
          </Box>

          <VStack spacing={8} align="stretch" flex={1}>
            <Box>
              <Heading
                size="2xl"
                color={isDark ? "#f8fafc" : "#0f172a"}
                mb={3}
                fontWeight="700"
                letterSpacing="-0.5px"
              >
                Panduan Dashboard Tren Skill
              </Heading>
              <Text
                color={isDark ? "#cbd5e1" : "#64748b"}
                fontSize="md"
                fontWeight="500"
                lineHeight="1.6"
              >
                Dashboard ini membantu Anda melihat tren skill yang paling banyak
                dicari berdasarkan data lowongan kerja LinkedIn. Gunakan filter
                dan grafik untuk memahami kebutuhan industri saat ini.
              </Text>
            </Box>

            <Box id="filters">
              <Heading
                size="lg"
                color={isDark ? "#0284c7" : "#0284c7"}
                mb={6}
                fontWeight="700"
                fontSize="2xl"
                pb={3}
                borderBottomWidth="2px"
                borderBottomColor={isDark ? "#0284c7" : "#0284c7"}
              >
                Filter Data
              </Heading>

              <VStack spacing={4} align="stretch">
                {[
                  {
                    title: "Nama Pekerjaan",
                    desc: "Pilih posisi pekerjaan yang ingin dianalisis, misalnya Data Analyst, Front-End Developer, atau UI/UX Designer.",
                  },
                  {
                    title: "Lokasi",
                    desc: "Pilih lokasi untuk melihat kebutuhan skill pada wilayah tertentu.",
                  },
                  {
                    title: "Bulan",
                    desc: "Pilih bulan untuk melihat data lowongan pada periode tertentu.",
                  },
                  {
                    title: "Tahun",
                    desc: "Pilih tahun untuk melihat perubahan tren skill dari waktu ke waktu.",
                  },
                ].map((filter, idx) => (
                  <Card
                    key={idx}
                    bg={isDark ? "#1e293b" : "#f8fafc"}
                    borderColor={isDark ? "#475569" : "#cbd5e0"}
                    borderWidth="2px"
                    borderLeft="4px solid #0284c7"
                    transition="all 0.3s ease"
                    _hover={{
                      borderColor: "#0284c7",
                      boxShadow: isDark
                        ? "0 8px 20px rgba(2, 132, 199, 0.15)"
                        : "0 8px 20px rgba(2, 132, 199, 0.12)",
                      transform: "translateY(-2px)",
                    }}
                  >
                    <CardBody>
                      <Heading size="sm" color={isDark ? "#0284c7" : "#0284c7"} mb={2} fontWeight="700">
                        {filter.title}
                      </Heading>
                      <Text color={isDark ? "#cbd5e1" : "#64748b"} fontWeight="500" fontSize="sm" lineHeight="1.6">
                        {filter.desc}
                      </Text>
                    </CardBody>
                  </Card>
                ))}
              </VStack>

              <Box
                mt={6}
                p={4}
                bg={isDark ? "rgba(2, 132, 199, 0.05)" : "rgba(2, 132, 199, 0.03)"}
                borderLeft="4px solid #0284c7"
                borderRadius="md"
              >
                <Text color={isDark ? "#e0f2fe" : "#0284c7"} fontWeight="600" fontSize="sm" lineHeight="1.6">
                  Anda dapat menggunakan beberapa filter sekaligus untuk
                  mendapatkan hasil yang lebih spesifik. Misalnya, pilih posisi
                  pekerjaan dan lokasi tertentu untuk melihat skill yang paling
                  banyak dibutuhkan pada area tersebut.
                </Text>
              </Box>
            </Box>

            <Box id="charts">
              <Heading
                size="lg"
                color={isDark ? "#0284c7" : "#0284c7"}
                mb={6}
                fontWeight="700"
                fontSize="2xl"
                pb={3}
                borderBottomWidth="2px"
                borderBottomColor={isDark ? "#0284c7" : "#0284c7"}
              >
                Penjelasan Grafik & Visualisasi
              </Heading>

              <VStack spacing={6} align="stretch">
                {[
                  {
                    title: "Tech Stack",
                    definition:
                      "Menampilkan teknologi, framework, atau tools yang paling sering disebut dalam lowongan kerja.",
                    points: [
                      "Semakin tinggi nilainya, semakin sering teknologi tersebut dibutuhkan.",
                      "Gunakan grafik tren untuk melihat perubahan kebutuhan teknologi dari waktu ke waktu.",
                      "Klik grafik untuk melihat detail data yang tersedia.",
                    ],
                  },
                  {
                    title: "Technical Skill",
                    definition:
                      "Menampilkan kemampuan teknis yang paling banyak dicari oleh perusahaan.",
                    points: [
                      "Skill dengan nilai tertinggi menunjukkan permintaan yang lebih besar.",
                      "Grafik membantu melihat skill yang sedang meningkat atau menurun kebutuhannya.",
                      "Gunakan informasi ini sebagai referensi untuk pengembangan kemampuan teknis.",
                    ],
                  },
                  {
                    title: "Soft Skill",
                    definition:
                      "Menampilkan kemampuan non-teknis yang sering dicari perusahaan, seperti komunikasi, kerja sama tim, dan kepemimpinan.",
                    points: [
                      "Semakin tinggi nilainya, semakin sering skill tersebut muncul dalam lowongan.",
                      "Grafik tren dapat menunjukkan perubahan kebutuhan soft skill dari waktu ke waktu.",
                      "Soft skill dapat melengkapi kemampuan teknis untuk meningkatkan daya saing kerja.",
                    ],
                  },
                ].map((chart, idx) => (
                  <Card
                    key={idx}
                    bg={isDark ? "#1e293b" : "#f8fafc"}
                    borderColor={isDark ? "#475569" : "#e2e8f0"}
                    borderWidth="1px"
                    transition="all 0.3s"
                    _hover={{
                      borderColor: "#0284c7",
                      boxShadow: isDark
                        ? "0 4px 12px rgba(2, 132, 199, 0.1)"
                        : "0 4px 12px rgba(2, 132, 199, 0.08)",
                    }}
                  >
                    <CardBody>
                      <Heading size="md" color={isDark ? "#f8fafc" : "#0f172a"} mb={3} fontWeight="700">
                        {chart.title}
                      </Heading>
                      <VStack spacing={4} align="start">
                        <Box>
                          <Text fontWeight="600" color={isDark ? "#0284c7" : "#0284c7"} fontSize="sm" mb={1}>
                            Apa yang Ditampilkan?
                          </Text>
                          <Text color={isDark ? "#cbd5e1" : "#64748b"} fontSize="sm" fontWeight="500" lineHeight="1.6">
                            {chart.definition}
                          </Text>
                        </Box>
                        <Box w="100%">
                          <Text fontWeight="600" color={isDark ? "#0284c7" : "#0284c7"} fontSize="sm" mb={2}>
                            Cara Membaca
                          </Text>
                          <VStack spacing={2} align="start">
                            {chart.points.map((point, pointIdx) => (
                              <HStack key={pointIdx} spacing={3} align="flex-start">
                                <Text color={isDark ? "#0284c7" : "#0284c7"} fontWeight="700" fontSize="xs" mt="2px"></Text>
                                <Text color={isDark ? "#cbd5e1" : "#64748b"} fontSize="sm" fontWeight="500" lineHeight="1.5">
                                  {point}
                                </Text>
                              </HStack>
                            ))}
                          </VStack>
                        </Box>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </VStack>
            </Box>

            <Box id="tips">
              <Heading
                size="lg"
                color={isDark ? "#0284c7" : "#0284c7"}
                mb={6}
                fontWeight="700"
                fontSize="2xl"
                pb={3}
                borderBottomWidth="2px"
                borderBottomColor={isDark ? "#0284c7" : "#0284c7"}
              >
                Tips Membaca Grafik
              </Heading>

              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                {[
                  {
                    title: "Perhatikan Filter yang Digunakan",
                    content:
                      "Hasil grafik akan berubah sesuai filter yang dipilih. Pastikan filter sudah sesuai dengan kebutuhan analisis.",
                  },
                  {
                    title: "Perhatikan Perubahan Tren",
                    content:
                      "Amati apakah suatu skill mengalami kenaikan atau penurunan dalam beberapa bulan terakhir.",
                  },
                  {
                    title: "Gunakan Data Sebagai Referensi",
                    content:
                      "Data dapat membantu memahami kebutuhan industri, namun tidak selalu mewakili seluruh lowongan kerja yang tersedia.",
                  },
                  {
                    title: "Baca Keterangan Grafik",
                    content:
                      "Beberapa periode mungkin tidak memiliki data hasil scraping. Perhatikan catatan yang tersedia pada grafik.",
                  },
                ].map((tip, idx) => (
                  <Card
                    key={idx}
                    bg={isDark ? "#1e293b" : "#f8fafc"}
                    borderColor={isDark ? "#475569" : "#e2e8f0"}
                    borderWidth="1px"
                    transition="all 0.3s"
                    _hover={{
                      borderColor: "#0284c7",
                      boxShadow: isDark
                        ? "0 4px 12px rgba(2, 132, 199, 0.1)"
                        : "0 4px 12px rgba(2, 132, 199, 0.08)",
                    }}
                  >
                    <CardBody>
                      <Heading size="sm" color={isDark ? "#0284c7" : "#0284c7"} mb={2} fontWeight="700">
                        {tip.title}
                      </Heading>
                      <Text fontSize="sm" color={isDark ? "#cbd5e1" : "#64748b"} fontWeight="500" lineHeight="1.6">
                        {tip.content}
                      </Text>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            </Box>

            <Box id="comparison">
              <Heading
                size="lg"
                color={isDark ? "#0284c7" : "#0284c7"}
                mb={6}
                fontWeight="700"
                fontSize="2xl"
                pb={3}
                borderBottomWidth="2px"
                borderBottomColor={isDark ? "#0284c7" : "#0284c7"}
              >
                Fitur Perbandingan Data
              </Heading>

              <Text mb={5} color={isDark ? "#cbd5e1" : "#64748b"}>
                Fitur perbandingan membantu melihat perubahan kebutuhan skill
                antara dua periode yang berbeda.
              </Text>

              <Card bg={isDark ? "#1e293b" : "#f8fafc"} borderColor={isDark ? "#475569" : "#e2e8f0"} borderWidth="1px">
                <CardBody>
                  <VStack spacing={6} align="start">
                    <Box>
                      <Heading size="sm" color={isDark ? "#0284c7" : "#0284c7"} mb={3} fontWeight="700">
                        Jenis Perbandingan
                      </Heading>
                      <VStack spacing={3} align="start">
                        <Box>
                          <Text fontWeight="700" color={isDark ? "#f8fafc" : "#0f172a"} fontSize="sm" mb={1}>
                            Perbandingan Tahun
                          </Text>
                          <Text color={isDark ? "#cbd5e1" : "#64748b"} fontSize="sm" fontWeight="500">
                            Bandingkan data dari dua tahun yang berbeda untuk
                            melihat tren jangka panjang dan perubahan preferensi
                            teknologi.
                          </Text>
                        </Box>
                        <Box>
                          <Text fontWeight="700" color={isDark ? "#f8fafc" : "#0f172a"} fontSize="sm" mb={1}>
                            Perbandingan Bulan
                          </Text>
                          <Text color={isDark ? "#cbd5e1" : "#64748b"} fontSize="sm" fontWeight="500">
                            Pilih bulan dan tahun untuk membandingkan tren
                            musiman. Misalnya: Februari 2025 vs Februari 2026.
                          </Text>
                        </Box>
                      </VStack>
                    </Box>

                    <Divider borderColor={isDark ? "#475569" : "#e2e8f0"} />

                    <Box>
                      <Heading size="sm" color={isDark ? "#0284c7" : "#0284c7"} mb={3} fontWeight="700">
                        Langkah-Langkah
                      </Heading>
                      <OrderedList
                        color={isDark ? "#cbd5e1" : "#64748b"}
                        spacing={2}
                        fontWeight="500"
                        fontSize="sm"
                      >
                        <ListItem>Masuk ke halaman Detail Analisis</ListItem>
                        <ListItem>Pilih jenis perbandingan (Tahun atau Bulan)</ListItem>
                        <ListItem>Tentukan periode pertama dan periode kedua</ListItem>
                        <ListItem>
                          Tambahkan filter tambahan jika diperlukan (Nama Pekerjaan,
                          Lokasi)
                        </ListItem>
                        <ListItem>Lihat hasil perbandingan di berbagai grafik</ListItem>
                      </OrderedList>
                    </Box>
                  </VStack>
                </CardBody>
              </Card>
            </Box>

            <Box
              p={4}
              bg={isDark ? "rgba(2, 132, 199, 0.05)" : "rgba(2, 132, 199, 0.03)"}
              borderRadius="md"
              borderLeftWidth="4px"
              borderLeftColor="#0284c7"
            >
              <Text
                color={isDark ? "#cbd5e1" : "#64748b"}
                fontWeight="500"
                fontSize="sm"
                lineHeight="1.6"
              >
                Gunakan dashboard untuk mengeksplorasi tren skill, teknologi,
                dan kebutuhan industri berdasarkan data lowongan kerja yang
                tersedia.
              </Text>
            </Box>
          </VStack>
        </Flex>
      </Container>
    </Box>
  );
}
