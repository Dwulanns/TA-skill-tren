import { Box, Flex } from "@chakra-ui/react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { useSidebar } from "../context/SidebarContext";
import { useState, useEffect } from "react";

export default function Layout() {
  const { isOpen } = useSidebar();
  const [userRole, setUserRole] = useState("user");

  // Check if admin is logged in to determine sidebar role
  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    setUserRole(token ? "admin" : "user");
  }, []);

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
      {/* SIDEBAR - Overlay at top left with dynamic role */}
      <Sidebar
        headerTitle={userRole === "admin" ? "Admin" : "Skills"}
        headerSubtitle={userRole === "admin" ? "Panel" : "Analytics"}
        role={userRole}
        showFloatingButton={true}
      />

      {/* HEADER - Below sidebar z-index, spans full width */}
      <Header isLanding={false} />

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
