import { Box, Flex } from "@chakra-ui/react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { useSidebar } from "../context/SidebarContext";

export default function AdminLayoutComponent() {
  // Use the SAME state as user pages - unified state management
  const { isOpen } = useSidebar();

  return (
    <Box
      h="100vh"
      bg="var(--bg-primary)"
      overflow="hidden"
      display="flex"
      flexDirection="column"
      sx={{
        backgroundColor: "var(--bg-primary) !important",
        color: "var(--text-primary) !important",
      }}
    >
      {/* SIDEBAR - Overlay at top left with "Admin Panel" header */}
      <Sidebar
        headerTitle="Admin"
        headerSubtitle="Panel"
        role="admin"
        showFloatingButton={false}
      />

      {/* HEADER - Below sidebar z-index, spans full width */}
      <Header isLanding={false} showAdminBadge={true} zIndex="1000" />

      {/* MAIN CONTENT - Flexible width, shifts right when sidebar opens */}
      <Box
        flex="1"
        overflowY="auto"
        ml={isOpen ? "240px" : "0"}
        transition="margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
        bg="var(--bg-primary)"
        pt="70px"
        sx={{
          backgroundColor: "var(--bg-primary) !important",
          color: "var(--text-primary) !important",
          "&::-webkit-scrollbar": {
            width: "8px",
          },
          "&::-webkit-scrollbar-track": {
            bg: "var(--bg-tertiary)",
          },
          "&::-webkit-scrollbar-thumb": {
            bg: "var(--accent-primary)",
            borderRadius: "4px",
            border: "2px solid var(--bg-secondary)",
            "&:hover": {
              bg: "var(--accent-secondary)",
            },
          },
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
