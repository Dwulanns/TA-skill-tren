import { useEffect, useState } from "react";
import {
  Box,
  VStack,
  HStack,
  Text,
  Spinner,
  Center,
  Link as ChakraLink,
} from "@chakra-ui/react";
import axios from "axios";
import { useTheme } from "../context/ThemeContext";
import { API_ENDPOINTS, buildQueryString } from "../config/api";

const CompanyRow = ({ rank, company, jobCount, percentage, companyLinkedinUrl, isDark }) => {
  // ✅ Pakai URL dari database, fallback ke search jika tidak ada
  const url = companyLinkedinUrl || `https://www.linkedin.com/search/results/companies/?keywords=${encodeURIComponent(company)}`;

  const rankColors = {
    1: { bg: "rgba(2, 132, 199, 0.1)", text: "#0284c7", border: "#0284c7" },
    2: { bg: "rgba(2, 132, 199, 0.08)", text: "#0284c7", border: "#06b6d4" },
    3: { bg: "rgba(2, 132, 199, 0.06)", text: "#0284c7", border: "#22d3ee" },
  };

  const colors = rankColors[rank] || rankColors[3];

  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="space-between"
      p={1.5}
      mb={1.5}
      bg={isDark ? "rgba(2, 132, 199, 0.08)" : colors.bg}
      borderRadius="md"
      borderLeft="3px solid"
      borderLeftColor={colors.border}
      fontSize="13px"
      _hover={{
        bg: isDark ? "rgba(2, 132, 199, 0.15)" : "rgba(2, 132, 199, 0.15)",
      }}
    >
      <HStack spacing={2} flex={1} minW={0}>
        <Text fontWeight="bold" color={colors.text} minW="24px">
          #{rank}
        </Text>
        <ChakraLink
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          fontWeight="600"
          color={colors.text}
          textDecoration="none"
          _hover={{
            textDecoration: "underline",
            opacity: 0.8,
          }}
          noOfLines={1}
        >
          {company} 🔗
        </ChakraLink>
      </HStack>

      <HStack spacing={2} justify="flex-end" minW="fit-content" ml={2}>
        <Text fontSize="12px" color={isDark ? "#94a3b8" : "#666666"}>
          {jobCount} lowongan
        </Text>
        <Text fontWeight="bold" color={colors.text} minW="35px" textAlign="right">
          {percentage}%
        </Text>
      </HStack>
    </Box>
  );
};

export default function TopCompaniesCard({
  skillName,
  filters,
  isDark = false,
}) {
  const { isDark: themeIsDark } = useTheme();
  const [companies, setCompanies] = useState([]);
  const [totalJobs, setTotalJobs] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const currentIsDark = isDark !== undefined ? isDark : themeIsDark;

  useEffect(() => {
    if (!skillName) {
      setCompanies([]);
      setTotalJobs(0);
      return;
    }

    setLoading(true);
    setError(null);

    const params = buildQueryString({
      keyword_id: filters?.keyword_id,
      location: filters?.location,
      month: filters?.month,
      year: filters?.year,
      employee_size: filters?.employee_size, // ✅ FIX: sebelumnya tidak dikirim ke backend
      limit: 5,
    });

    const endpoint = `${API_ENDPOINTS.DASHBOARD.TOP_COMPANIES_BY_SKILL}/${encodeURIComponent(skillName)}?${params}`;

    axios
      .get(endpoint)
      .then((res) => {
        const data = res.data;
        console.log("Companies from API:", data.companies);
        
        // ✅ PASTIKAN data companies memiliki field yang benar
        const formattedCompanies = (data.companies || []).map((item) => ({
          rank: item.rank,
          company_name: item.company_name || item.company,  // ← flexible
          company_linkedin_url: item.company_linkedin_url,
          job_count: item.job_count,
          percentage: item.percentage,
        }));
        
        setCompanies(formattedCompanies);
        setTotalJobs(data.total_jobs_with_skill || 0);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching top companies:", err);
        setError(
          err.response?.data?.detail ||
            err.message ||
            "Failed to load companies",
        );
        setLoading(false);
      });
  }, [
    skillName,
    filters?.keyword_id,
    filters?.location,
    filters?.month,
    filters?.year,
    filters?.employee_size, // ✅ FIX: sebelumnya tidak ada, jadi tidak refetch saat ukuran perusahaan diganti
  ]);

  if (loading) {
    return (
      <Center h="60px">
        <HStack spacing={2}>
          <Spinner size="sm" color="#0284c7" thickness="3px" />
          <Text fontSize="12px" color={isDark ? "#cbd5e1" : "#666666"}>
            Memuat perusahaan...
          </Text>
        </HStack>
      </Center>
    );
  }

  if (error) {
    return (
      <Text fontSize="12px" color="#ef5350">
        ⚠️ Gagal memuat data perusahaan
      </Text>
    );
  }

  if (companies.length === 0) {
    return (
      <Text fontSize="12px" color={isDark ? "#94a3b8" : "#999999"}>
        Tidak ada data perusahaan
      </Text>
    );
  }

  return (
    <VStack spacing={0} align="stretch" w="100%">
      {companies.map((company, idx) => (
        <CompanyRow
          key={company.rank || idx}
          rank={company.rank}
          company={company.company_name}  // ✅ pakai company_name
          jobCount={company.job_count}
          percentage={company.percentage}
          companyLinkedinUrl={company.company_linkedin_url}
          isDark={currentIsDark}
        />
      ))}
    </VStack>
  );
}