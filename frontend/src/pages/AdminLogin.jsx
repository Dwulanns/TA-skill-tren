import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Box,
  VStack,
  HStack,
  Button,
  Input,
  Heading,
  Text,
  Alert,
  AlertIcon,
  Flex,
  Container,
  InputGroup,
  InputRightElement,
  Icon,
  FormControl,
  FormLabel,
  useToast,
  keyframes,
} from "@chakra-ui/react";
import { Lock, Eye, EyeOff, Mail, BarChart3, Sparkles, TrendingUp, Users } from "lucide-react";
import { API_ENDPOINTS } from "../config/api";

// Animations
const floatAnimation = keyframes`
  0% { transform: translateY(0px) scale(1); }
  50% { transform: translateY(-10px) scale(1.02); }
  100% { transform: translateY(0px) scale(1); }
`;

const shimmerAnimation = keyframes`
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
`;

const glowPulse = keyframes`
  0% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
  100% { opacity: 0.3; transform: scale(1); }
`;

const slideUp = keyframes`
  0% { opacity: 0; transform: translateY(30px); }
  100% { opacity: 1; transform: translateY(0); }
`;

const AdminLogin = ({ onLoginSuccess }) => {
  const navigate = useNavigate();
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (!email || !password) {
      setError("Email/Username dan password harus diisi");
      setLoading(false);
      return;
    }

    try {
      console.log("🔐 Starting login attempt...", { email, password: "***" });

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const backendUrl = import.meta.env.VITE_API_URL || "";
      console.log("🌐 Backend URL:", backendUrl);
      console.log("🌐 Login URL:", API_ENDPOINTS.ADMIN.LOGIN);

      const response = await fetch(API_ENDPOINTS.ADMIN.LOGIN, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      console.log("📡 Response status:", response.status, response.statusText);

      const data = await response.json();
      console.log("📦 Response data:", data);

      if (response.ok) {
        console.log("✅ Login successful!");
        localStorage.setItem("admin_token", data.access_token);
        localStorage.setItem("admin_email", data.email);
        localStorage.setItem("admin_username", data.username);

        console.log("💾 Token saved to localStorage:", {
          token: data.access_token.substring(0, 20) + "...",
          email: data.email,
        });

        toast({
          title: "Login Berhasil",
          description: `Selamat datang kembali, ${data.username}!`,
          status: "success",
          duration: 2000,
          isClosable: true,
        });

        if (onLoginSuccess) {
          onLoginSuccess();
        }

        console.log("🚀 Navigating to /admin...");
        navigate("/admin", { replace: true });
      } else {
        console.log("❌ Login failed:", data);
        setError(data.detail || "Login gagal. Coba lagi.");
        toast({
          title: "Login Gagal",
          description: data.detail || "Email/Username atau password salah",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (err) {
      clearTimeout();
      console.error("💥 Login error:", err);
      console.error("Error name:", err.name);
      console.error("Error message:", err.message);

      let errorMsg = "Gagal terhubung ke server. Coba lagi.";

      if (err.name === "AbortError") {
        errorMsg =
          "⏱️ Request timeout - Backend tidak merespons dalam 10 detik. Pastikan backend sudah running!";
        console.error(
          `🔥 TIMEOUT: Backend di ${backendUrl || "relative proxy"} tidak merespons`
        );
      } else if (
        err instanceof TypeError &&
        err.message.includes("Failed to fetch")
      ) {
        errorMsg =
          "🚫 Tidak bisa terhubung ke backend. Cek apakah backend sudah running di port 8000";
        console.error("🔥 CONNECTION ERROR: Backend mungkin tidak running");
      }

      setError(errorMsg);
      toast({
        title: "Error",
        description: errorMsg,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Flex
      minH="100vh"
      bg="linear-gradient(145deg, #0a1628 0%, #1a2a4a 25%, #2d4a6b 50%, #1a2a4a 75%, #0a1628 100%)"
      align="center"
      justify="center"
      p={4}
      position="relative"
      overflow="hidden"
    >
      {/* Animated Background Orbs */}
      <Box
        position="absolute"
        top="-30%"
        right="-10%"
        w="800px"
        h="800px"
        borderRadius="full"
        bg="radial-gradient(circle, rgba(74, 144, 217, 0.15) 0%, rgba(74, 144, 217, 0.05) 40%, transparent 70%)"
        animation={`${glowPulse} 6s ease-in-out infinite`}
      />
      <Box
        position="absolute"
        bottom="-30%"
        left="-10%"
        w="700px"
        h="700px"
        borderRadius="full"
        bg="radial-gradient(circle, rgba(107, 163, 224, 0.12) 0%, rgba(107, 163, 224, 0.04) 40%, transparent 70%)"
        animation={`${glowPulse} 8s ease-in-out infinite reverse`}
      />
      <Box
        position="absolute"
        top="50%"
        left="50%"
        transform="translate(-50%, -50%)"
        w="600px"
        h="600px"
        borderRadius="full"
        bg="radial-gradient(circle, rgba(74, 144, 217, 0.08) 0%, transparent 70%)"
        animation={`${glowPulse} 10s ease-in-out infinite`}
      />

      {/* Background Chart - Elegant Blur */}
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        bottom="0"
        zIndex="0"
        opacity="0.12"
        filter="blur(6px)"
      >
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 1400 900"
          preserveAspectRatio="xMidYMid slice"
          style={{ position: "absolute", top: 0, left: 0 }}
        >
          <defs>
            <linearGradient id="chartGrad1" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style={{ stopColor: "#4a90d9", stopOpacity: 0.5 }} />
              <stop offset="100%" style={{ stopColor: "#4a90d9", stopOpacity: 0.02 }} />
            </linearGradient>
            <linearGradient id="chartGrad2" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style={{ stopColor: "#6ba3e0", stopOpacity: 0.4 }} />
              <stop offset="100%" style={{ stopColor: "#6ba3e0", stopOpacity: 0.01 }} />
            </linearGradient>
          </defs>

          {/* Grid */}
          <g stroke="rgba(74, 144, 217, 0.15)" strokeWidth="0.5">
            <line x1="0" y1="150" x2="1400" y2="150" />
            <line x1="0" y1="300" x2="1400" y2="300" />
            <line x1="0" y1="450" x2="1400" y2="450" />
            <line x1="0" y1="600" x2="1400" y2="600" />
            <line x1="0" y1="750" x2="1400" y2="750" />
          </g>

          {/* Main Area Chart */}
          <path
            d="M0,650 C100,620 200,560 300,520 C400,480 500,420 600,390 
               C700,360 800,320 900,340 C1000,360 1100,420 1200,460 
               C1300,500 1350,520 1400,530 L1400,900 L0,900 Z"
            fill="url(#chartGrad1)"
          />

          {/* Secondary Area Chart */}
          <path
            d="M0,750 C150,720 300,660 450,620 C600,580 750,540 900,560 
               C1050,580 1150,620 1250,650 C1350,680 1400,700 1400,700 
               L1400,900 L0,900 Z"
            fill="url(#chartGrad2)"
          />

          {/* Main Line */}
          <path
            d="M0,650 C100,620 200,560 300,520 C400,480 500,420 600,390 
               C700,360 800,320 900,340 C1000,360 1100,420 1200,460 
               C1300,500 1350,520 1400,530"
            stroke="#4a90d9"
            strokeWidth="2.5"
            fill="none"
            opacity="0.6"
          />

          {/* Secondary Line */}
          <path
            d="M0,750 C150,720 300,660 450,620 C600,580 750,540 900,560 
               C1050,580 1150,620 1250,650 C1350,680 1400,700"
            stroke="#6ba3e0"
            strokeWidth="2"
            fill="none"
            opacity="0.4"
          />

          {/* Bars */}
          {[
            [120, 530, 120],
            [220, 490, 160],
            [320, 450, 200],
            [420, 410, 240],
            [520, 370, 280],
            [620, 340, 310],
            [720, 310, 340],
            [820, 320, 330],
            [920, 340, 310],
            [1020, 390, 260],
            [1120, 430, 220],
            [1220, 470, 180],
          ].map(([x, y, height], i) => (
            <rect
              key={i}
              x={x}
              y={y}
              width="24"
              height={height}
              fill={i % 2 === 0 ? "#4a90d9" : "#6ba3e0"}
              opacity="0.15"
              rx="4"
            />
          ))}

          {/* Scatter Points */}
          {[
            [150, 590],
            [250, 530],
            [350, 490],
            [450, 450],
            [550, 410],
            [650, 380],
            [750, 350],
            [850, 335],
            [950, 350],
            [1050, 390],
            [1150, 430],
            [1250, 480],
          ].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r="4" fill="#4a90d9" opacity="0.4" />
          ))}

          {/* Subtle Text */}
          <g fill="rgba(74, 144, 217, 0.06)" fontSize="40" fontFamily="Arial, sans-serif" fontWeight="300">
            <text x="60" y="80">SKILL TREND ANALYTICS</text>
            <text x="60" y="130">DATA SCIENCE · AI · MACHINE LEARNING</text>
          </g>
        </svg>
      </Box>

      {/* Glass Overlay */}
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        bottom="0"
        zIndex="1"
        bg="linear-gradient(to bottom, rgba(10, 22, 40, 0.3) 0%, rgba(26, 42, 74, 0.5) 40%, rgba(10, 22, 40, 0.7) 100%)"
      />

      {/* Login Container */}
      <Container maxW="440px" w="full" position="relative" zIndex="2">
        <VStack spacing={8} align="stretch" animation={`${slideUp} 0.8s ease-out`}>
          {/* Logo / Header */}
          <VStack spacing={5} textAlign="center">
            <Box
              p={4}
              bg="rgba(255, 255, 255, 0.08)"
              backdropFilter="blur(20px)"
              borderRadius="2xl"
              display="inline-flex"
              alignItems="center"
              justifyContent="center"
              border="1px solid rgba(255, 255, 255, 0.12)"
              boxShadow="0 20px 60px rgba(74, 144, 217, 0.2)"
              animation={`${floatAnimation} 4s ease-in-out infinite`}
            >
              <Icon as={Sparkles} boxSize={8} color="#6ba3e0" />
            </Box>
            <VStack spacing={2}>
              <Heading
                size="xl"
                color="#ffffff"
                fontWeight="400"
                letterSpacing="-1px"
                textShadow="0 2px 20px rgba(0,0,0,0.3)"
              >
                Skill Trend
                <Text as="span" color="#6ba3e0" fontWeight="600" ml={2}>
                  Admin
                </Text>
              </Heading>
              <Text color="rgba(255,255,255,0.5)" fontSize="sm" fontWeight="400" letterSpacing="wider">
                LOGIN UNTUK AKSES DASHBOARD
              </Text>
            </VStack>
          </VStack>

          {/* Login Form - Premium Glass */}
          <Box
            bg="rgba(255, 255, 255, 0.06)"
            backdropFilter="blur(30px)"
            border="1px solid rgba(255, 255, 255, 0.1)"
            borderRadius="2xl"
            p={8}
            as="form"
            onSubmit={handleLogin}
            boxShadow="0 30px 80px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.08)"
            transition="all 0.4s ease"
            _hover={{
              borderColor: "rgba(255, 255, 255, 0.15)",
              boxShadow: "0 40px 100px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.12)",
            }}
          >
            <VStack spacing={6} align="stretch">
              {/* Error Alert */}
              {error && (
                <Alert
                  status="error"
                  borderRadius="xl"
                  bg="rgba(229, 62, 62, 0.2)"
                  border="1px solid rgba(229, 62, 62, 0.3)"
                  color="#fca5a5"
                  fontSize="sm"
                  backdropFilter="blur(10px)"
                >
                  <AlertIcon color="#fc8181" />
                  {error}
                </Alert>
              )}

              {/* Email/Username Input */}
              <FormControl>
                <FormLabel color="rgba(255,255,255,0.7)" fontSize="xs" fontWeight="600" letterSpacing="wider">
                  EMAIL / USERNAME
                </FormLabel>
                <InputGroup size="lg">
                  <Input
                    type="text"
                    placeholder="Masukkan email atau username"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    bg="rgba(255, 255, 255, 0.06)"
                    border="1px solid rgba(255, 255, 255, 0.12)"
                    color="#ffffff"
                    autoComplete="username"
                    _placeholder={{ color: "rgba(255,255,255,0.3)", fontSize: "sm", fontWeight: "400" }}
                    _focus={{
                      border: "1px solid",
                      borderColor: "rgba(74, 144, 217, 0.6)",
                      boxShadow: "0 0 0 4px rgba(74, 144, 217, 0.1)",
                      bg: "rgba(255, 255, 255, 0.08)",
                    }}
                    _hover={{
                      border: "1px solid rgba(255, 255, 255, 0.2)",
                    }}
                    borderRadius="xl"
                    pr={12}
                    fontSize="sm"
                    h="14"
                    transition="all 0.3s ease"
                  />
                  <InputRightElement h="14">
                    <Icon as={Mail} boxSize={5} color="rgba(255,255,255,0.3)" />
                  </InputRightElement>
                </InputGroup>
              </FormControl>

              {/* Password Input */}
              <FormControl>
                <FormLabel color="rgba(255,255,255,0.7)" fontSize="xs" fontWeight="600" letterSpacing="wider">
                  PASSWORD
                </FormLabel>
                <InputGroup size="lg">
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder="Masukkan password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    bg="rgba(255, 255, 255, 0.06)"
                    border="1px solid rgba(255, 255, 255, 0.12)"
                    color="#ffffff"
                    autoComplete="current-password"
                    _placeholder={{ color: "rgba(255,255,255,0.3)", fontSize: "sm", fontWeight: "400" }}
                    _focus={{
                      border: "1px solid",
                      borderColor: "rgba(74, 144, 217, 0.6)",
                      boxShadow: "0 0 0 4px rgba(74, 144, 217, 0.1)",
                      bg: "rgba(255, 255, 255, 0.08)",
                    }}
                    _hover={{
                      border: "1px solid rgba(255, 255, 255, 0.2)",
                    }}
                    borderRadius="xl"
                    pr={12}
                    fontSize="sm"
                    h="14"
                    transition="all 0.3s ease"
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        handleLogin(e);
                      }
                    }}
                  />
                  <InputRightElement h="14">
                    <Button
                      variant="ghost"
                      onClick={() => setShowPassword(!showPassword)}
                      _hover={{ bg: "transparent" }}
                      size="sm"
                      h="14"
                    >
                      <Icon
                        as={showPassword ? EyeOff : Eye}
                        boxSize={5}
                        color="rgba(255,255,255,0.3)"
                      />
                    </Button>
                  </InputRightElement>
                </InputGroup>
              </FormControl>

              {/* Login Button - Shimmer Effect */}
              <Button
                type="submit"
                isLoading={loading}
                loadingText="Memproses..."
                size="lg"
                bg="linear-gradient(135deg, #4a90d9 0%, #6ba3e0 50%, #4a90d9 100%)"
                backgroundSize="200% auto"
                animation={`${shimmerAnimation} 3s linear infinite`}
                _hover={{
                  bg: "linear-gradient(135deg, #3a80c9 0%, #5b93d0 50%, #3a80c9 100%)",
                  boxShadow: "0 10px 40px rgba(74, 144, 217, 0.4)",
                  transform: "translateY(-2px)",
                }}
                _active={{
                  transform: "translateY(0)",
                }}
                color="#ffffff"
                fontWeight="600"
                borderRadius="xl"
                w="full"
                h="14"
                mt={2}
                transition="all 0.3s ease"
                letterSpacing="wide"
                fontSize="md"
              >
                Login ke Admin Panel
              </Button>

              {/* Info Text */}
              <Text color="rgba(255,255,255,0.3)" fontSize="xs" textAlign="center" pt={2} fontWeight="400" letterSpacing="wide">
                GUNAKAN AKUN ADMIN YANG TELAH TERDAFTAR
              </Text>
            </VStack>
          </Box>

          {/* Footer */}
          <VStack spacing={2}>
            <Text color="rgba(255,255,255,0.2)" fontSize="xs" textAlign="center" fontWeight="400" letterSpacing="wide">
              © 2024 SKILL TREND ANALYSIS — ADMIN DASHBOARD
            </Text>
            <HStack spacing={4} justify="center" fontSize="xs" color="rgba(255,255,255,0.15)" fontWeight="400">
              <Text>✦ SECURE ACCESS</Text>
              <Text>•</Text>
              <Text>✦ REAL-TIME ANALYTICS</Text>
            </HStack>
          </VStack>
        </VStack>
      </Container>
    </Flex>
  );
};

export default AdminLogin;