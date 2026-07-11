import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Box, Spinner, Flex } from "@chakra-ui/react";

export default function ProtectedAdminRoute({ children }) {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Check authentication immediately on component mount
    const token = localStorage.getItem("admin_token");
    console.log("🔐 ProtectedAdminRoute: Checking for admin token...");

    if (!token) {
      console.log("❌ NO TOKEN FOUND - Redirecting to /admin/login");
      setIsAuthenticated(false);
      setIsChecking(false);
      // Redirect to login immediately
      navigate("/admin/login", { replace: true });
      return;
    }

    // Token exists - user is authenticated
    console.log("✅ TOKEN FOUND - User is authenticated");
    setIsAuthenticated(true);
    setIsChecking(false);
  }, [navigate]);

  // While checking authentication status
  if (isChecking) {
    console.log("⏳ Checking authentication...");
    return (
      <Flex minH="100vh" align="center" justify="center" bg="#0f172a">
        <Spinner size="xl" color="#0284c7" thickness="4px" />
      </Flex>
    );
  }

  // Not authenticated - don't render anything (already redirected)
  if (!isAuthenticated) {
    console.log("🚫 Not authenticated - returning null");
    return null;
  }

  // User is authenticated - render protected content
  console.log("✔️ User authenticated - rendering admin panel");
  return <>{children}</>;
}
