import { useState, useEffect, useCallback } from "react";
import { useToast } from "@chakra-ui/react";
import useApi from "./useApi";
import { API_ENDPOINTS, getErrorMessage } from "../config/api";

const POPULAR_SKILLS = [
  { display: "SQL", value: "SQL", category: "Tech Stack" },
  { display: "Python", value: "Python", category: "Tech Stack" },
  { display: "Excel", value: "Excel", category: "Tech Stack" },
  { display: "Tableau", value: "Tableau", category: "Tech Stack" },
  { display: "Power BI", value: "Power BI", category: "Tech Stack" },
  { display: "SAS", value: "SAS", category: "Tech Stack" },
  { display: "Looker", value: "Looker", category: "Tech Stack" },
  { display: "SPSS", value: "SPSS", category: "Tech Stack" },
  { display: "Google Sheets", value: "Google Sheets", category: "Tech Stack" },
  { display: "VBA", value: "VBA", category: "Tech Stack" },
  { display: "Data Analysis", value: "Data Analysis", category: "Technical" },
  { display: "Data Visualization", value: "Data Visualization", category: "Technical" },
  { display: "Machine Learning", value: "Machine Learning", category: "Technical" },
  { display: "Statistical Analysis", value: "Statistical Analysis", category: "Technical" },
  { display: "Data Science", value: "Data Science", category: "Technical" },
  { display: "Data Modeling", value: "Data Modeling", category: "Technical" },
  { display: "Data Governance", value: "Data Governance", category: "Technical" },
  { display: "Business Intelligence", value: "Business Intelligence", category: "Technical" },
  { display: "Looker Studio", value: "Looker Studio", category: "Technical" },
  { display: "Communication", value: "Communication", category: "Soft Skill" },
  { display: "Problem Solving", value: "Problem Solving", category: "Soft Skill" },
  { display: "Critical Thinking", value: "Critical Thinking", category: "Soft Skill" },
  { display: "Teamwork", value: "Teamwork", category: "Soft Skill" },
  { display: "Leadership", value: "Leadership", category: "Soft Skill" },
];

const SKILL_TYPE_FILTERS = [
  { value: "all", label: "Semua Skill" },
  { value: "tech_stack", label: "Tech Stack" },
  { value: "technical_skill", label: "Technical Skill" },
  { value: "soft_skill", label: "Soft Skill" },
];

/**
 * Custom hook to encapsulate the logic, state, and API requests of the SkillMatcher page.
 */
export default function useSkillMatcherData() {
  const toast = useToast();
  const api = useApi();

  // States
  const [jobOptions, setJobOptions] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [targetJobTitle, setTargetJobTitle] = useState("");
  const [employeeSize, setEmployeeSize] = useState("");
  const [employeeSizeOptions, setEmployeeSizeOptions] = useState([]);
  const [loadingEmployeeSizes, setLoadingEmployeeSizes] = useState(false);
  const [skillInput, setSkillInput] = useState("");
  const [userSkills, setUserSkills] = useState([]);
  const [dbSkills, setDbSkills] = useState([]);
  const [dbSkillsType, setDbSkillsType] = useState(null);
  const [loadingDbSkills, setLoadingDbSkills] = useState(false);
  const [matchingResults, setMatchingResults] = useState(null);
  const [loadingMatch, setLoadingMatch] = useState(false);

  const [suggestedSkills, setSuggestedSkills] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [skillTypeFilter, setSkillTypeFilter] = useState("all");
  const [showAllMissing, setShowAllMissing] = useState(false);

  // Load employee sizes
  const loadEmployeeSizes = useCallback(async () => {
    try {
      setLoadingEmployeeSizes(true);
      const res = await api.get(API_ENDPOINTS.EMPLOYEE_SIZES);
      setEmployeeSizeOptions(Array.isArray(res) ? res : []);
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
  }, [api]);

  // Load job options & sizes on mount
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        setLoadingOptions(true);
        const res = await api.get(API_ENDPOINTS.FILTERS);
        if (res?.keywords) {
          setJobOptions(res.keywords);
        }
        await loadEmployeeSizes();
      } catch (err) {
        console.error("Gagal memuat daftar job title:", err);
      } finally {
        setLoadingOptions(false);
      }
    };
    fetchOptions();
  }, [api, loadEmployeeSizes]);

  // Fetch local autocomplete suggestions for skills
  useEffect(() => {
    if (!skillInput || skillInput.length < 2) {
      setSuggestedSkills([]);
      setShowSuggestions(false);
      return;
    }
    const inputLower = skillInput.toLowerCase();
    const matches = POPULAR_SKILLS.filter(
      (s) =>
        s.value.toLowerCase().includes(inputLower) ||
        s.display.toLowerCase().includes(inputLower)
    );
    setSuggestedSkills(matches.slice(0, 10));
    setShowSuggestions(matches.length > 0);
  }, [skillInput]);

  // Add/Remove skill logic
  const handleAddSkill = useCallback((skillName) => {
    if (!skillName || !skillName.trim()) return;
    const cleanSkill = skillName.trim();
    const isDuplicate = userSkills.some(
      (s) => s.toLowerCase() === cleanSkill.toLowerCase()
    );
    if (isDuplicate) {
      toast({
        title: "Skill sudah ada",
        description: `"${cleanSkill}" sudah ada dalam daftar skill Anda.`,
        status: "warning",
        duration: 2000,
        isClosable: true,
      });
      setSkillInput("");
      setShowSuggestions(false);
      return;
    }
    setUserSkills((prev) => [...prev, cleanSkill]);
    setSkillInput("");
    setShowSuggestions(false);
  }, [userSkills, toast]);

  const handleRemoveSkill = useCallback((indexToRemove) => {
    setUserSkills((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  }, []);

  const handleKeyPress = useCallback((e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (suggestedSkills.length > 0) {
        handleAddSkill(suggestedSkills[0].value);
      } else {
        handleAddSkill(skillInput);
      }
    }
  }, [suggestedSkills, skillInput, handleAddSkill]);

  // Fetch reference skills from database
  const fetchDbSkills = useCallback(async (typeId) => {
    if (typeId === null || typeId === undefined) return;
    setLoadingDbSkills(true);
    setDbSkillsType(typeId);
    try {
      const selectedJobOption = jobOptions.find(
        (job) => job.keyword === targetJobTitle
      );
      const keywordId = selectedJobOption ? selectedJobOption.id : undefined;

      const params = { skill_type_id: typeId };
      if (keywordId) params.keyword_id = keywordId;
      if (employeeSize) params.employee_size = employeeSize;

      const resData = await api.get(API_ENDPOINTS.DASHBOARD.ALL_SKILLS_BY_TYPE, params);
      setDbSkills(resData || []);
    } catch (err) {
      console.error("Gagal mengambil skill dari database:", err);
      toast({
        title: "Gagal memuat skill",
        description: "Tidak bisa menghubungkan ke database.",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoadingDbSkills(false);
    }
  }, [jobOptions, targetJobTitle, employeeSize, api, toast]);

  // Refetch database reference skills when filters change
  useEffect(() => {
    if (dbSkillsType !== null) {
      fetchDbSkills(dbSkillsType);
    } else {
      setDbSkills([]);
    }
  }, [targetJobTitle, employeeSize, dbSkillsType, fetchDbSkills]);

  // Calculate Match logic
  const handleCalculateMatch = useCallback(async () => {
    if (!targetJobTitle) {
      toast({
        title: "Peringatan",
        description: "Silakan pilih Target Job Title terlebih dahulu.",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    if (userSkills.length === 0) {
      toast({
        title: "Peringatan",
        description: "Silakan tambahkan minimal satu skill terlebih dahulu.",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      setLoadingMatch(true);
      const apiBase = API_ENDPOINTS.STATISTICS.replace("/stats", "");

      const resData = await api.post(`${apiBase}/skill-matcher`, {
        targetJobTitle,
        userSkills,
        skillType: skillTypeFilter,
        employeeSize: employeeSize || null,
      });

      setMatchingResults(resData);
      setShowAllMissing(false);

      const filterLabel =
        SKILL_TYPE_FILTERS.find((f) => f.value === skillTypeFilter)?.label ||
        "Semua Skill";
      toast({
        title: "Analisis Selesai",
        description: `Score kecocokan (${filterLabel}): ${resData.matchScore}%.`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (err) {
      toast({
        title: "Gagal memproses analisis",
        description: err.message || getErrorMessage(err),
        status: "error",
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setLoadingMatch(false);
    }
  }, [targetJobTitle, userSkills, skillTypeFilter, employeeSize, api, toast]);

  return {
    jobOptions,
    loadingOptions,
    targetJobTitle,
    setTargetJobTitle,
    employeeSize,
    setEmployeeSize,
    employeeSizeOptions,
    loadingEmployeeSizes,
    skillInput,
    setSkillInput,
    userSkills,
    setUserSkills,
    dbSkills,
    dbSkillsType,
    loadingDbSkills,
    matchingResults,
    loadingMatch,
    suggestedSkills,
    setSuggestedSkills,
    showSuggestions,
    setShowSuggestions,
    skillTypeFilter,
    setSkillTypeFilter,
    showAllMissing,
    setShowAllMissing,
    handleAddSkill,
    handleRemoveSkill,
    handleKeyPress,
    fetchDbSkills,
    handleCalculateMatch,
    SKILL_TYPE_FILTERS,
    POPULAR_SKILLS,
  };
}
