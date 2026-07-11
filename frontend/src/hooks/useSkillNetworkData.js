import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useToast } from "@chakra-ui/react";
import useApi from "./useApi";
import { API_ENDPOINTS, getErrorMessage } from "../config/api";

/**
 * Custom hook to manage state and logic for the Skill Network Page.
 * Decouples state, D3 layout controls, autocomplete, and API fetching from presentation.
 */
export default function useSkillNetworkData() {
  const toast = useToast();
  const api = useApi();

  // Search autocomplete state
  const [skillInput, setSkillInput] = useState("");
  const [allSkills, setAllSkills] = useState([]);
  const [suggestedSkills, setSuggestedSkills] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Filters State
  const [keywordId, setKeywordId] = useState("");
  const [employeeSize, setEmployeeSize] = useState("");
  const [filterOptions, setFilterOptions] = useState(null);
  const [employeeSizeOptions, setEmployeeSizeOptions] = useState([]);
  const [loadingFilters, setLoadingFilters] = useState(false);

  // Categorized dynamic skills lists
  const [techStackSkills, setTechStackSkills] = useState([]);
  const [technicalSkills, setTechnicalSkills] = useState([]);
  const [softSkills, setSoftSkills] = useState([]);
  const [loadingCategorySkills, setLoadingCategorySkills] = useState(false);

  // Accordion state
  const [openCategories, setOpenCategories] = useState([]);

  // Network Graph States
  const [activeSkill, setActiveSkill] = useState("");
  const [graphData, setGraphData] = useState(null);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);

  // Graph Ref
  const fgRef = useRef(null);

  // Load Filter options on mount
  useEffect(() => {
    const loadFilters = async () => {
      try {
        setLoadingFilters(true);
        const resFilters = await api.get(API_ENDPOINTS.FILTERS);
        setFilterOptions(resFilters);

        // Fetch employee sizes
        const sizeRes = await api.get(API_ENDPOINTS.EMPLOYEE_SIZES);
        setEmployeeSizeOptions(Array.isArray(sizeRes) ? sizeRes : []);

        // Fetch autocomplete suggestions list
        const apiBase = API_ENDPOINTS.STATISTICS.replace("/stats", "");
        const skillsListRes = await api.get(`${apiBase}/skills/list`);
        setAllSkills(skillsListRes || []);
      } catch (err) {
        console.error("Gagal memuat filter:", err);
        toast({
          title: "Gagal memuat filter",
          description: err.message || getErrorMessage(err),
          status: "error",
          duration: 4000,
          isClosable: true,
        });
      } finally {
        setLoadingFilters(false);
      }
    };
    loadFilters();
  }, [toast, api]);

  // Load categorized skills based on active filters
  const loadCategorizedSkills = useCallback(async () => {
    try {
      setLoadingCategorySkills(true);
      const params = {};
      if (keywordId) params.keyword_id = keywordId;
      if (employeeSize) params.employee_size = employeeSize;

      // 1. Tech Stack (skill_type_id: 3)
      const resTech = await api.get(
        API_ENDPOINTS.DASHBOARD.ALL_SKILLS_BY_TYPE,
        { ...params, skill_type_id: 3 }
      );
      setTechStackSkills(resTech || []);

      // 2. Technical Skill (skill_type_id: 2)
      const resTechSkill = await api.get(
        API_ENDPOINTS.DASHBOARD.ALL_SKILLS_BY_TYPE,
        { ...params, skill_type_id: 2 }
      );
      setTechnicalSkills(resTechSkill || []);

      // 3. Soft Skill (skill_type_id: 1)
      const resSoft = await api.get(
        API_ENDPOINTS.DASHBOARD.ALL_SKILLS_BY_TYPE,
        { ...params, skill_type_id: 1 }
      );
      setSoftSkills(resSoft || []);
    } catch (err) {
      console.error("Gagal memuat kategori skill:", err);
    } finally {
      setLoadingCategorySkills(false);
    }
  }, [keywordId, employeeSize, api]);

  // Fetch Co-occurrence Network logic
  const handleFetchCooccurrence = useCallback(async (skillName) => {
    if (!skillName || !skillName.trim()) return;
    const cleanSkill = skillName.trim();
    setActiveSkill(cleanSkill);
    setSkillInput(cleanSkill);
    setShowSuggestions(false);
    setSelectedNode(null);
    try {
      setLoadingGraph(true);
      const apiBase = API_ENDPOINTS.STATISTICS.replace("/stats", "");
      const resData = await api.get(`${apiBase}/skill-cooccurrence`, {
        skill: cleanSkill,
        keyword_id: keywordId || undefined,
        employee_size: employeeSize || undefined,
      });
      setGraphData(resData);
      if (
        resData?.nodes?.length === 0 ||
        (resData?.nodes?.length === 1 && resData?.nodes[0].frequency === 0)
      ) {
        toast({
          title: "Skill Tidak Ditemukan",
          description: `Tidak ada data hubungan co-occurrence untuk skill "${cleanSkill}" dengan filter yang aktif.`,
          status: "warning",
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (err) {
      toast({
        title: "Gagal memuat visualisasi",
        description: err.message || getErrorMessage(err),
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoadingGraph(false);
    }
  }, [keywordId, employeeSize, toast, api]);

  // Reload categorized skills when filters change
  useEffect(() => {
    loadCategorizedSkills();
    // If activeSkill exists, reload the graph with the new filters!
    if (activeSkill) {
      handleFetchCooccurrence(activeSkill);
    }
  }, [keywordId, employeeSize, loadCategorizedSkills, handleFetchCooccurrence, activeSkill]);

  // Handle local autocomplete suggestions filtering
  useEffect(() => {
    if (!skillInput || skillInput.trim().length < 1) {
      setSuggestedSkills([]);
      setShowSuggestions(false);
      return;
    }

    const inputLower = skillInput.toLowerCase().trim();
    const filtered = allSkills
      .filter((s) => s.toLowerCase().includes(inputLower))
      .slice(0, 8);

    setSuggestedSkills(filtered);
    setShowSuggestions(filtered.length > 0);
  }, [skillInput, allSkills]);

  // Zoom controls helper functions
  const handleZoomIn = useCallback(() => {
    if (!fgRef.current) return;
    fgRef.current.zoom(fgRef.current.zoom() * 1.4, 300);
  }, []);

  const handleZoomOut = useCallback(() => {
    if (!fgRef.current) return;
    fgRef.current.zoom(fgRef.current.zoom() / 1.4, 300);
  }, []);

  const handleResetZoom = useCallback(() => {
    if (!fgRef.current) return;
    fgRef.current.zoomToFit(400, 40);
  }, []);

  // Compute neighboring nodes of the highlighted node
  const neighbors = useMemo(() => {
    const set = new Set();
    if (!selectedNode || !graphData?.links) return set;
    graphData.links.forEach((link) => {
      const sourceId =
        typeof link.source === "object" ? link.source.id : link.source;
      const targetId =
        typeof link.target === "object" ? link.target.id : link.target;
      if (sourceId === selectedNode.id) set.add(targetId);
      else if (targetId === selectedNode.id) set.add(sourceId);
    });
    return set;
  }, [selectedNode, graphData]);

  return {
    skillInput,
    setSkillInput,
    suggestedSkills,
    showSuggestions,
    setShowSuggestions,
    keywordId,
    setKeywordId,
    employeeSize,
    setEmployeeSize,
    filterOptions,
    employeeSizeOptions,
    loadingFilters,
    techStackSkills,
    technicalSkills,
    softSkills,
    loadingCategorySkills,
    openCategories,
    setOpenCategories,
    activeSkill,
    setActiveSkill,
    graphData,
    setGraphData,
    loadingGraph,
    selectedNode,
    setSelectedNode,
    fgRef,
    handleFetchCooccurrence,
    handleZoomIn,
    handleZoomOut,
    handleResetZoom,
    neighbors,
  };
}
