import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  VStack,
  HStack,
  Heading,
  Text,
  Input,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useToast,
  Spinner,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  FormControl,
  FormLabel,
  IconButton,
  InputGroup,
  InputLeftElement,
  Badge,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
} from "@chakra-ui/react";
import {
  DeleteIcon,
  EditIcon,
  AddIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  SearchIcon,
} from "@chakra-ui/icons";
import { useTheme } from "../context/ThemeContext";

const AdminKeywordManagement = () => {
  const { isDark } = useTheme();
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const toast = useToast();

  const { isOpen, onOpen, onClose } = useDisclosure();
  const [editingId, setEditingId] = useState(null);
  const [formValue, setFormValue] = useState("");

  // Alert Dialog untuk konfirmasi hapus
  const [isAlertOpen, setIsAlertOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [deleteKeyword, setDeleteKeyword] = useState("");
  const onAlertClose = () => setIsAlertOpen(false);
  const cancelRef = React.useRef();

  // Theme colors - Dark mode lebih terang seperti Admin Database
  const bgColor = isDark ? "#0d1117" : "#f0f4f8";
  const cardBg = isDark ? "rgba(22, 27, 34, 0.92)" : "rgba(255, 255, 255, 0.85)";
  const cardBorder = isDark ? "rgba(88, 166, 255, 0.2)" : "rgba(66, 153, 225, 0.1)";
  const textColor = isDark ? "#f0f6fc" : "#2d3748";
  const subTextColor = isDark ? "#c9d1d9" : "#718096";
  const hoverBg = isDark ? "rgba(88, 166, 255, 0.15)" : "rgba(66, 153, 225, 0.05)";
  
  // Warna solid seperti LinkedIn - sama dengan Admin Database
  const linkedinBlue = isDark ? "#1f6feb" : "#0a66c2";
  const tableHeaderBg = linkedinBlue;
  const tableHeaderText = "#ffffff";
  
  const inputBg = isDark ? "rgba(22, 27, 34, 0.8)" : "gray.50";
  const inputBorder = isDark ? "rgba(88, 166, 255, 0.2)" : "rgba(66, 153, 225, 0.2)";
  const modalBg = isDark ? "rgba(22, 27, 34, 0.95)" : "white";
  const modalBorder = isDark ? "rgba(88, 166, 255, 0.2)" : "rgba(66, 153, 225, 0.1)";
  const accentColor = isDark ? "#58a6ff" : "#4299e1";

  // Efek shadow dengan sentuhan biru
  const rowShadow = isDark 
    ? "0 1px 3px rgba(88, 166, 255, 0.1)" 
    : "0 1px 3px rgba(66, 153, 225, 0.08)";

  const rowHoverShadow = isDark
    ? "0 2px 8px rgba(88, 166, 255, 0.2)"
    : "0 2px 6px rgba(66, 153, 225, 0.15)";

  // Efek glass morphism untuk tabel
  const glassBg = isDark
    ? "rgba(22, 27, 34, 0.92)"
    : "rgba(255, 255, 255, 0.8)";
  const glassBorder = isDark
    ? "rgba(88, 166, 255, 0.15)"
    : "rgba(66, 153, 225, 0.1)";

  useEffect(() => {
    loadKeywords();
  }, []);

  const loadKeywords = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/api/admin/keywords");
      const data = await response.json();
      const keywordList = Array.isArray(data) ? data : data.keywords || [];
      setKeywords(keywordList);
    } catch (error) {
      console.error("Error loading keywords:", error);
      toast({
        title: "Error",
        description: "Gagal memuat keyword",
        status: "error",
        duration: 3000,
        position: "top-right",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddClick = () => {
    setEditingId(null);
    setFormValue("");
    onOpen();
  };

  const handleEditClick = (keyword) => {
    setEditingId(keyword.id);
    setFormValue(keyword.keyword);
    onOpen();
  };

  const handleSave = async () => {
    if (!formValue.trim()) {
      toast({
        title: "Error",
        description: "Keyword tidak boleh kosong",
        status: "error",
        duration: 3000,
        position: "top-right",
      });
      return;
    }

    try {
      if (editingId) {
        const response = await fetch(
          `http://localhost:8000/api/admin/keywords/${editingId}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keyword: formValue.trim() }),
          }
        );
        if (!response.ok) throw new Error("Update failed");
        toast({
          title: "Success",
          description: "Keyword berhasil diupdate",
          status: "success",
          duration: 3000,
          position: "top-right",
        });
      } else {
        const response = await fetch(
          "http://localhost:8000/api/admin/keywords",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keyword: formValue.trim() }),
          }
        );
        if (!response.ok) throw new Error("Create failed");
        toast({
          title: "Success",
          description: "Keyword berhasil ditambahkan",
          status: "success",
          duration: 3000,
          position: "top-right",
        });
      }
      onClose();
      loadKeywords();
    } catch (error) {
      console.error("Error saving keyword:", error);
      toast({
        title: "Error",
        description: editingId
          ? "Gagal update keyword"
          : "Gagal tambah keyword",
        status: "error",
        duration: 3000,
        position: "top-right",
      });
    }
  };

  const handleDeleteClick = (id, keyword) => {
    setDeleteId(id);
    setDeleteKeyword(keyword);
    setIsAlertOpen(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/admin/keywords/${deleteId}`,
        {
          method: "DELETE",
        }
      );
      if (!response.ok) throw new Error("Delete failed");
      toast({
        title: "Success",
        description: `Keyword "${deleteKeyword}" berhasil dihapus`,
        status: "success",
        duration: 3000,
        position: "top-right",
      });
      loadKeywords();
    } catch (error) {
      console.error("Error deleting keyword:", error);
      toast({
        title: "Error",
        description: "Gagal menghapus keyword",
        status: "error",
        duration: 3000,
        position: "top-right",
      });
    } finally {
      setIsAlertOpen(false);
      setDeleteId(null);
      setDeleteKeyword("");
    }
  };

  // Filter dan sorting
  const filteredKeywords = keywords
    .filter((k) =>
      k.keyword.toLowerCase().includes(searching.toLowerCase())
    )
    .sort((a, b) => a.id - b.id);

  // Pagination logic
  const totalPages = Math.ceil(filteredKeywords.length / itemsPerPage);
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentKeywords = filteredKeywords.slice(
    indexOfFirstItem,
    indexOfLastItem
  );

  const goToPage = (page) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const cardShadow = isDark 
    ? "0 4px 20px rgba(0, 0, 0, 0.3)" 
    : "0 4px 20px rgba(0, 0, 0, 0.08)";

  if (loading) {
    return (
      <Box
        p={8}
        display="flex"
        justifyContent="center"
        alignItems="center"
        minH="400px"
        bg={isDark ? "#0d1117" : "#f0f4f8"}
      >
        <Spinner size="xl" color="blue.500" thickness="3px" />
      </Box>
    );
  }

  return (
    <Box
      px={{ base: 4, md: 6, lg: 8 }}
      py={{ base: 5, md: 6, lg: 8 }}
      w="100%"
      bg={isDark ? "#0d1117" : "#f0f4f8"}
      minH="100vh"
    >
      {/* Header - Warna Hitam */}
      <Box mb={6}>
        <Heading
          as="h1"
          size={{ base: "lg", md: "xl" }}
          fontWeight="800"
          mb={1}
          letterSpacing="tight"
          color={isDark ? "#f0f6fc" : "black"}
        >
          Manajemen Keyword
        </Heading>
        <Text color={isDark ? "#c9d1d9" : "#718096"} fontWeight="500">
          Kelola kata kunci untuk scraping lowongan pekerjaan
        </Text>
      </Box>

      {/* Search and Add Row - Improved */}
      <HStack justify="space-between" flexWrap="wrap" spacing={4} mb={5}>
        <InputGroup w={{ base: "100%", sm: "250px" }}>
          <InputLeftElement pointerEvents="none" height="36px">
            <SearchIcon color={accentColor} fontSize="sm" />
          </InputLeftElement>
          <Input
            placeholder="Cari keyword..."
            value={searching}
            onChange={(e) => setSearching(e.target.value)}
            bg={inputBg}
            borderColor={inputBorder}
            color={textColor}
            _hover={{ borderColor: accentColor }}
            _focus={{ 
              borderColor: accentColor,
              boxShadow: `0 0 0 3px ${isDark ? 'rgba(88, 166, 255, 0.25)' : 'rgba(66, 153, 225, 0.15)'}`
            }}
            borderRadius="md"
            size="sm"
            height="36px"
            fontSize="sm"
          />
        </InputGroup>
        <Button
          leftIcon={<AddIcon boxSize={2.5} />}
          size="sm"
          bg={linkedinBlue}
          color="white"
          _hover={{ 
            bg: isDark ? "#1a5fcf" : "#0a58b8",
            transform: "translateY(-1px)",
            boxShadow: `0 2px 8px ${isDark ? 'rgba(88, 166, 255, 0.3)' : 'rgba(66, 153, 225, 0.25)'}`
          }}
          _active={{ bg: isDark ? "#1a4a9f" : "#0a4a9f" }}
          borderRadius="md"
          onClick={handleAddClick}
          fontSize="sm"
          px={3.5}
          height="36px"
          transition="all 0.2s"
          fontWeight="700"
        >
          Tambah Keyword
        </Button>
      </HStack>

      {/* Table - Ukuran Lebih Kecil */}
      <Box
        bg={glassBg}
        borderRadius="lg"
        borderWidth="1px"
        borderColor={glassBorder}
        overflow="hidden"
        backdropFilter="blur(12px)"
        boxShadow={`0 4px 16px ${isDark ? 'rgba(88, 166, 255, 0.06)' : 'rgba(66, 153, 225, 0.06)'}`}
      >
        <Table variant="simple" size="sm">
          <Thead bg={tableHeaderBg}>
            <Tr>
              <Th
                width="50px"
                color={tableHeaderText}
                fontSize="xs"
                fontWeight="800"
                letterSpacing="0.5px"
                textTransform="uppercase"
                py={2.5}
                textAlign="center"
                borderBottom="none"
                px={2}
                bg={tableHeaderBg}
              >
                ID
              </Th>
              <Th
                color={tableHeaderText}
                fontSize="xs"
                fontWeight="800"
                letterSpacing="0.5px"
                textTransform="uppercase"
                py={2.5}
                textAlign="center"
                borderBottom="none"
                px={2}
                bg={tableHeaderBg}
              >
                Keyword
              </Th>
              <Th
                width="100px"
                color={tableHeaderText}
                fontSize="xs"
                fontWeight="800"
                letterSpacing="0.5px"
                textTransform="uppercase"
                py={2.5}
                textAlign="center"
                borderBottom="none"
                px={2}
                bg={tableHeaderBg}
              >
                Aksi
              </Th>
            </Tr>
          </Thead>
          <Tbody>
            {currentKeywords.length === 0 ? (
              <Tr>
                <Td colSpan={3} textAlign="center" py={4}>
                  <Text fontSize="sm" color={isDark ? "#8b949e" : "gray.400"}>
                    {searching ? "Keyword tidak ditemukan" : "Belum ada keyword"}
                  </Text>
                </Td>
              </Tr>
            ) : (
              currentKeywords.map((keyword, index) => (
                <Tr
                  key={keyword.id}
                  bg={index % 2 === 0 
                    ? (isDark ? "rgba(88, 166, 255, 0.06)" : "rgba(66, 153, 225, 0.02)")
                    : "transparent"
                  }
                  boxShadow={rowShadow}
                  transition="all 0.15s"
                  _hover={{
                    boxShadow: rowHoverShadow,
                    bg: isDark ? "rgba(88, 166, 255, 0.15)" : "rgba(66, 153, 225, 0.06)",
                    transform: "scale(1.001)",
                  }}
                  sx={{
                    "& td:first-child": { borderRadius: "md 0 0 md" },
                    "& td:last-child": { borderRadius: "0 md md 0" },
                  }}
                >
                  <Td py={1.5} px={2} textAlign="center">
                    <Badge
                      colorScheme="blue"
                      variant="subtle"
                      fontSize="xs"
                      fontWeight="800"
                      px={2}
                      py={0.5}
                      borderRadius="full"
                      bg={isDark ? "rgba(88, 166, 255, 0.2)" : "rgba(66, 153, 225, 0.1)"}
                      color={isDark ? "#58a6ff" : "#2b6cb0"}
                      borderWidth="1px"
                      borderColor={isDark ? "rgba(88, 166, 255, 0.3)" : "rgba(66, 153, 225, 0.2)"}
                    >
                      {keyword.id}
                    </Badge>
                  </Td>
                  <Td py={1.5} px={2} textAlign="center">
                    <Box
                      display="inline-block"
                      px={2.5}
                      py={0.5}
                      bg={isDark ? "rgba(88, 166, 255, 0.12)" : "rgba(66, 153, 225, 0.06)"}
                      borderRadius="full"
                      borderWidth="1px"
                      borderColor={isDark ? "rgba(88, 166, 255, 0.2)" : "rgba(66, 153, 225, 0.1)"}
                    >
                      <Text fontWeight="700" fontSize="sm" color={textColor}>
                        {keyword.keyword}
                      </Text>
                    </Box>
                  </Td>
                  <Td py={1.5} px={2} textAlign="center">
                    <HStack spacing={1} justify="center">
                      <IconButton
                        icon={<EditIcon boxSize={3} />}
                        size="xs"
                        variant="ghost"
                        colorScheme="blue"
                        onClick={() => handleEditClick(keyword)}
                        aria-label="Edit"
                        borderRadius="full"
                        _hover={{ 
                          bg: isDark ? "rgba(88, 166, 255, 0.2)" : "rgba(66, 153, 225, 0.1)",
                          transform: "scale(1.05)"
                        }}
                        transition="all 0.15s"
                        color={isDark ? "#58a6ff" : "#3182ce"}
                      />
                      <IconButton
                        icon={<DeleteIcon boxSize={3} />}
                        size="xs"
                        variant="ghost"
                        colorScheme="red"
                        onClick={() => handleDeleteClick(keyword.id, keyword.keyword)}
                        aria-label="Delete"
                        borderRadius="full"
                        _hover={{ 
                          bg: isDark ? "rgba(229, 62, 62, 0.2)" : "rgba(229, 62, 62, 0.08)",
                          transform: "scale(1.05)"
                        }}
                        transition="all 0.15s"
                        color={isDark ? "#fc8181" : "#e53e3e"}
                      />
                    </HStack>
                  </Td>
                </Tr>
              ))
            )}
          </Tbody>
        </Table>
      </Box>

      {/* Pagination - Lebih Kecil */}
      {totalPages > 1 && (
        <HStack justify="space-between" mt={3} flexWrap="wrap" spacing={2}>
          <Text fontSize="2xs" color={isDark ? "#8b949e" : "gray.400"} fontWeight="400">
            Menampilkan {indexOfFirstItem + 1} -{" "}
            {Math.min(indexOfLastItem, filteredKeywords.length)} dari{" "}
            {filteredKeywords.length} keyword
          </Text>
          <HStack spacing={1}>
            <Button
              size="2xs"
              variant="outline"
              onClick={() => goToPage(currentPage - 1)}
              isDisabled={currentPage === 1}
              borderColor={isDark ? "rgba(88, 166, 255, 0.3)" : "blue.300"}
              color={accentColor}
              _hover={{ 
                bg: isDark ? "rgba(88, 166, 255, 0.1)" : "blue.50", 
                borderColor: accentColor 
              }}
              _disabled={{ opacity: 0.4, cursor: "not-allowed" }}
              height="24px"
              minW="24px"
              fontWeight="600"
              fontSize="2xs"
              px={1.5}
            >
              <ChevronLeftIcon boxSize={2.5} />
            </Button>
            <HStack spacing={0.5}>
              {[...Array(totalPages)].map((_, idx) => {
                const pageNum = idx + 1;
                if (
                  pageNum === 1 ||
                  pageNum === totalPages ||
                  (pageNum >= currentPage - 1 && pageNum <= currentPage + 1)
                ) {
                  const isActive = currentPage === pageNum;
                  return (
                    <Button
                      key={pageNum}
                      size="2xs"
                      variant={isActive ? "solid" : "outline"}
                      bg={isActive ? linkedinBlue : "transparent"}
                      color={isActive ? "white" : accentColor}
                      borderColor={isDark ? "rgba(88, 166, 255, 0.3)" : "blue.300"}
                      _hover={{
                        bg: isActive 
                          ? (isDark ? "#1a5fcf" : "#0a58b8") 
                          : (isDark ? "rgba(88, 166, 255, 0.1)" : "blue.50"),
                        borderColor: accentColor,
                      }}
                      onClick={() => goToPage(pageNum)}
                      minW="24px"
                      h="24px"
                      fontSize="2xs"
                      fontWeight="700"
                      px={1.5}
                    >
                      {pageNum}
                    </Button>
                  );
                } else if (
                  (pageNum === currentPage - 2 && currentPage > 3) ||
                  (pageNum === currentPage + 2 && currentPage < totalPages - 2)
                ) {
                  return (
                    <Text
                      key={pageNum}
                      px={0.5}
                      fontSize="2xs"
                      color={isDark ? "#8b949e" : "gray.400"}
                    >
                      …
                    </Text>
                  );
                }
                return null;
              })}
            </HStack>
            <Button
              size="2xs"
              variant="outline"
              onClick={() => goToPage(currentPage + 1)}
              isDisabled={currentPage === totalPages}
              borderColor={isDark ? "rgba(88, 166, 255, 0.3)" : "blue.300"}
              color={accentColor}
              _hover={{ 
                bg: isDark ? "rgba(88, 166, 255, 0.1)" : "blue.50", 
                borderColor: accentColor 
              }}
              _disabled={{ opacity: 0.4, cursor: "not-allowed" }}
              height="24px"
              minW="24px"
              fontWeight="600"
              fontSize="2xs"
              px={1.5}
            >
              <ChevronRightIcon boxSize={2.5} />
            </Button>
          </HStack>
        </HStack>
      )}

      {/* Modal Add/Edit */}
      <Modal isOpen={isOpen} onClose={onClose} isCentered size="sm">
        <ModalOverlay backdropFilter="blur(6px)" bg={isDark ? "rgba(0,0,0,0.5)" : "rgba(66, 153, 225, 0.05)"} />
        <ModalContent
          bg={modalBg}
          borderRadius="lg"
          borderColor={modalBorder}
          borderWidth="1px"
          boxShadow={`0 12px 40px ${isDark ? 'rgba(88, 166, 255, 0.15)' : 'rgba(66, 153, 225, 0.15)'}`}
        >
          <ModalHeader
            pb={1.5}
            borderBottomWidth="1px"
            borderColor={modalBorder}
            fontSize="sm"
            fontWeight="700"
            color={textColor}
            bg={isDark ? "rgba(22, 27, 34, 0.95)" : "rgba(255, 255, 255, 0.9)"}
            py={2.5}
            px={4}
          >
            {editingId ? "Edit Keyword" : "Tambah Keyword"}
          </ModalHeader>
          <ModalCloseButton size="sm" color={isDark ? "#8b949e" : "gray.500"} />
          <ModalBody pt={3} px={4}>
            <FormControl>
              <FormLabel fontSize="xs" fontWeight="600" color={textColor} mb={1}>
                Keyword
              </FormLabel>
              <Input
                placeholder="Contoh: Python Developer"
                value={formValue}
                onChange={(e) => setFormValue(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSave()}
                autoFocus
                bg={isDark ? "rgba(22, 27, 34, 0.8)" : "gray.50"}
                borderColor={inputBorder}
                color={textColor}
                _focus={{ 
                  borderColor: accentColor,
                  boxShadow: `0 0 0 3px ${isDark ? 'rgba(88, 166, 255, 0.25)' : 'rgba(66, 153, 225, 0.15)'}`
                }}
                borderRadius="md"
                size="xs"
                fontWeight="400"
                height="34px"
                fontSize="xs"
              />
            </FormControl>
          </ModalBody>
          <ModalFooter
            borderTopWidth="1px"
            borderColor={modalBorder}
            pt={2.5}
            px={4}
            pb={3}
          >
            <Button
              variant="ghost"
              onClick={onClose}
              mr={2}
              size="xs"
              color={isDark ? "#8b949e" : "gray.600"}
              _hover={{ bg: isDark ? "rgba(255,255,255,0.05)" : "gray.100" }}
              fontWeight="600"
              height="32px"
            >
              Batal
            </Button>
            <Button
              size="xs"
              bg={linkedinBlue}
              color="white"
              _hover={{ 
                bg: isDark ? "#1a5fcf" : "#0a58b8",
                transform: "translateY(-1px)",
                boxShadow: `0 2px 8px ${isDark ? 'rgba(88, 166, 255, 0.3)' : 'rgba(66, 153, 225, 0.25)'}`
              }}
              _active={{ bg: isDark ? "#1a4a9f" : "#0a4a9f" }}
              onClick={handleSave}
              transition="all 0.15s"
              fontWeight="700"
              height="32px"
            >
              {editingId ? "Update" : "Simpan"}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Alert Dialog Konfirmasi Hapus */}
      <AlertDialog
        isOpen={isAlertOpen}
        leastDestructiveRef={cancelRef}
        onClose={onAlertClose}
        isCentered
      >
        <AlertDialogOverlay backdropFilter="blur(4px)" bg="rgba(0,0,0,0.3)">
          <AlertDialogContent
            bg={isDark ? "rgba(22, 27, 34, 0.95)" : "white"}
            borderRadius="lg"
            borderColor={isDark ? "rgba(229, 62, 62, 0.3)" : "red.300"}
            borderWidth="1px"
            boxShadow={isDark 
              ? "0 12px 40px rgba(229, 62, 62, 0.15)" 
              : "0 12px 40px rgba(229, 62, 62, 0.08)"
            }
          >
            <AlertDialogHeader fontSize="sm" fontWeight="700" color={textColor} py={3}>
              <HStack spacing={2}>
                <Text color="red.500">⚠️</Text>
                <Text>Konfirmasi Hapus</Text>
              </HStack>
            </AlertDialogHeader>

            <AlertDialogBody fontSize="xs" color={subTextColor} py={1}>
              <Text mb={1.5}>Apakah Anda yakin ingin menghapus keyword ini?</Text>
              <Box
                p={2}
                bg={isDark ? "rgba(229, 62, 62, 0.1)" : "rgba(229, 62, 62, 0.05)"}
                borderRadius="md"
                borderWidth="1px"
                borderColor={isDark ? "rgba(229, 62, 62, 0.2)" : "rgba(229, 62, 62, 0.1)"}
                textAlign="center"
              >
                <Text fontWeight="700" color="red.500" fontSize="sm">
                  "{deleteKeyword}"
                </Text>
              </Box>
            </AlertDialogBody>

            <AlertDialogFooter pt={2} pb={3}>
              <Button
                ref={cancelRef}
                onClick={onAlertClose}
                size="xs"
                variant="ghost"
                color={isDark ? "#8b949e" : "gray.600"}
                _hover={{ bg: isDark ? "rgba(255,255,255,0.05)" : "gray.100" }}
                fontWeight="600"
                height="32px"
              >
                Batal
              </Button>
              <Button
                size="xs"
                bg="red.500"
                color="white"
                _hover={{ 
                  bg: "red.600",
                  transform: "translateY(-1px)",
                  boxShadow: "0 2px 8px rgba(229, 62, 62, 0.3)"
                }}
                _active={{ bg: "red.700" }}
                onClick={handleDeleteConfirm}
                ml={2}
                fontWeight="700"
                height="32px"
              >
                Hapus
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Box>
  );
};

export default AdminKeywordManagement;