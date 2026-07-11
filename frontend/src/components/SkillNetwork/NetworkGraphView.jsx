import { useEffect, useRef, useState } from "react";
import {
  Box,
  Heading,
  Flex,
  Spinner,
  Badge,
  Icon,
  VStack,
  IconButton,
  Divider,
  HStack,
  Text,
} from "@chakra-ui/react";
import {
  Network,
  AlertCircle,
  ZoomIn,
  ZoomOut,
  Maximize2,
} from "lucide-react";
import ForceGraph2D from "react-force-graph-2d";
import { forceCollide } from "d3-force";
import { useTheme } from "../../context/ThemeContext";

/**
 * Visualizer canvas component for rendering the co-occurrence network using ForceGraph2D.
 * Integrates D3 simulation logic, zoom controls, responsive resizing, and canvas rendering.
 */
export default function NetworkGraphView({
  activeSkill,
  graphData,
  loadingGraph,
  selectedNode,
  setSelectedNode,
  neighbors,
  fgRef,
  handleZoomIn,
  handleZoomOut,
  handleResetZoom,
  handleFetchCooccurrence,
}) {
  const { isDark } = useTheme();

  // Style tokens
  const cardBg = isDark ? "gray.800" : "white";
  const cardBorder = isDark ? "gray.700" : "gray.100";
  const cardShadow = isDark
    ? "0 8px 25px rgba(0,0,0,0.5)"
    : "0 8px 25px rgba(0,0,0,0.05)";
  const textColor = isDark ? "white" : "gray.800";
  const subTextColor = isDark ? "gray.400" : "gray.600";

  // Graph Layout & Refs
  const graphContainerRef = useRef(null);
  const [graphDimensions, setGraphDimensions] = useState({
    width: 600,
    height: 450,
  });

  // Setup ResizeObserver for responsive graph canvas
  useEffect(() => {
    if (graphContainerRef.current) {
      const resizeObserver = new ResizeObserver((entries) => {
        for (let entry of entries) {
          setGraphDimensions({
            width: entry.contentRect.width || 600,
            height: entry.contentRect.height || 450,
          });
        }
      });
      resizeObserver.observe(graphContainerRef.current);
      return () => resizeObserver.disconnect();
    }
  }, [graphData]);

  // Tune force simulation whenever graph data changes
  useEffect(() => {
    if (!fgRef.current || !graphData) return;
    fgRef.current.d3Force("charge")?.strength(-260).distanceMax(500);
    fgRef.current.d3Force("link")?.distance((link) => {
      const weight = link.weight || 1;
      return 100 + Math.max(0, 50 - weight * 5);
    });
    fgRef.current.d3Force(
      "collision",
      forceCollide((node) => Math.sqrt(node.frequency || 10) * 0.4 + 18)
    );
    fgRef.current.d3ReheatSimulation();
    const timer = setTimeout(() => {
      fgRef.current?.zoomToFit(600, 40);
    }, 700);
    return () => clearTimeout(timer);
  }, [graphData, fgRef]);

  return (
    <Box
      gridColumn={{ base: "span 1", lg: "span 8" }}
      bg={cardBg}
      borderWidth="1px"
      borderColor={cardBorder}
      borderRadius="xl"
      boxShadow={cardShadow}
      p={5}
      display="flex"
      flexDirection="column"
      minH="500px"
      position="relative"
    >
      <Heading
        as="h2"
        size="xs"
        fontWeight="700"
        mb={3}
        display="flex"
        alignItems="center"
      >
        <Icon as={Network} mr={2} color="cyan.500" />
        Peta Relasi Skill
        {activeSkill && (
          <Badge ml={3} colorScheme="cyan" fontSize="xs">
            {activeSkill}
          </Badge>
        )}
      </Heading>

      <Divider mb={4} borderColor={isDark ? "gray.700" : "gray.200"} />

      <Flex
        flex="1"
        direction="column"
        justify="center"
        align="center"
        position="relative"
        minH="350px"
      >
        {loadingGraph && (
          <Flex
            position="absolute"
            top="0"
            left="0"
            w="100%"
            h="100%"
            bg={isDark ? "rgba(10,14,23,0.7)" : "rgba(255,255,255,0.7)"}
            zIndex="5"
            justify="center"
            align="center"
            borderRadius="xl"
          >
            <VStack spacing={2}>
              <Spinner size="lg" color="cyan.500" />
              <Text fontSize="xs" color="cyan.500" fontWeight="600">
                Memetakan relasi co-occurrence...
              </Text>
            </VStack>
          </Flex>
        )}

        {!activeSkill ? (
          <VStack py={10} spacing={3} textAlign="center" maxW="md">
            <Icon as={Network} boxSize="48px" color="gray.500" />
            <Heading as="h3" size="xs" color={textColor} fontWeight="700">
              Jaringan Skill Belum Dimuat
            </Heading>
            <Text fontSize="xs" color={subTextColor}>
              Cari nama skill di atas atau pilih dari daftar kompetensi terpopuler di sebelah kiri untuk melihat visualisasi hubungannya.
            </Text>
          </VStack>
        ) : graphData && graphData.nodes?.length > 0 ? (
          <Box
            ref={graphContainerRef}
            w="100%"
            h="450px"
            bg={isDark ? "gray.950" : "gray.55"}
            borderRadius="xl"
            borderWidth="1px"
            borderColor={cardBorder}
            overflow="hidden"
            position="relative"
          >
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              width={graphDimensions.width}
              height={graphDimensions.height}
              nodeRelSize={1}
              d3AlphaDecay={0.02}
              d3VelocityDecay={0.25}
              cooldownTicks={150}
              onEngineStop={() => fgRef.current?.zoomToFit(400, 40)}
              linkDirectionalParticles={2}
              linkDirectionalParticleSpeed={0.006}
              linkWidth={(link) => {
                const isHighlighted =
                  selectedNode &&
                  ((typeof link.source === "object"
                    ? link.source.id
                    : link.source) === selectedNode.id ||
                    (typeof link.target === "object"
                      ? link.target.id
                      : link.target) === selectedNode.id);
                const baseWidth = Math.sqrt(link.weight || 1) * 0.4 + 1.2;
                return isHighlighted ? baseWidth * 2.2 : baseWidth;
              }}
              linkColor={(link) => {
                if (!selectedNode) return isDark ? "#334155" : "#cbd5e0";
                const sourceId =
                  typeof link.source === "object"
                    ? link.source.id
                    : link.source;
                const targetId =
                  typeof link.target === "object"
                    ? link.target.id
                    : link.target;
                const isConnected =
                  sourceId === selectedNode.id ||
                  targetId === selectedNode.id;
                return isConnected
                  ? "#06b6d4"
                  : isDark
                    ? "#1e293b"
                    : "#f1f5f9";
              }}
              onNodeClick={(node) => setSelectedNode(node)}
              onNodeDragEnd={(node) => {
                node.fx = node.x;
                node.fy = node.y;
              }}
              nodeCanvasObject={(node, ctx, globalScale) => {
                const label = node.id;
                const radius = Math.sqrt(node.frequency || 10) * 0.4 + 5;

                ctx.beginPath();
                ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);

                const isCenter = node.id === activeSkill;
                const isSelected =
                  selectedNode && node.id === selectedNode.id;
                const isNeighbor = selectedNode && neighbors.has(node.id);

                if (selectedNode) {
                  ctx.fillStyle = isSelected
                    ? "#00ffff"
                    : isNeighbor
                      ? "#38bdf8"
                      : isDark
                        ? "#1e293b"
                        : "#e2e8f0";
                } else {
                  ctx.fillStyle = isCenter ? "#3182ce" : "#06b6d4";
                }
                ctx.fill();

                ctx.strokeStyle = isCenter
                  ? "#3182ce"
                  : isDark
                    ? "#f8fafc"
                    : "#0f172a";
                ctx.lineWidth = isSelected || isCenter ? 1.8 : 0.6;
                ctx.stroke();

                const fontSize = Math.max(radius * 0.7, 10 / globalScale);
                ctx.font = `${isCenter ? "bold " : ""}${fontSize}px Inter, sans-serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                const textWidth = ctx.measureText(label).width;
                const bckgDimensions = [textWidth + 5, fontSize + 3];
                ctx.fillStyle = isDark
                  ? "rgba(10,14,23,0.85)"
                  : "rgba(255,255,255,0.85)";
                ctx.fillRect(
                  node.x - bckgDimensions[0] / 2,
                  node.y - radius - bckgDimensions[1] - 3,
                  bckgDimensions[0],
                  bckgDimensions[1]
                );

                if (selectedNode) {
                  ctx.fillStyle = isSelected
                    ? "#00ffff"
                    : isNeighbor
                      ? isDark
                        ? "#f8fafc"
                        : "#0f172a"
                      : "#64748b";
                } else {
                  ctx.fillStyle = isCenter
                    ? "#3182ce"
                    : isDark
                      ? "#f8fafc"
                      : "#0f172a";
                }
                ctx.fillText(
                  label,
                  node.x,
                  node.y - radius - bckgDimensions[1] / 2 - 3
                );
              }}
            />

            {/* Zoom Controls */}
            <VStack
              position="absolute"
              top={3}
              right={3}
              spacing={1.5}
              bg={isDark ? "rgba(20,26,38,0.92)" : "rgba(255,255,255,0.92)"}
              p={1.5}
              borderRadius="lg"
              borderWidth="1px"
              borderColor={cardBorder}
            >
              <IconButton
                size="xs"
                icon={<ZoomIn size={14} />}
                onClick={handleZoomIn}
                variant="ghost"
                aria-label="Zoom In"
              />
              <IconButton
                size="xs"
                icon={<ZoomOut size={14} />}
                onClick={handleZoomOut}
                variant="ghost"
                aria-label="Zoom Out"
              />
              <Divider borderColor={cardBorder} />
              <IconButton
                size="xs"
                icon={<Maximize2 size={14} />}
                onClick={handleResetZoom}
                variant="ghost"
                aria-label="Fit to Screen"
              />
            </VStack>

            {/* Legend Box */}
            <Box
              position="absolute"
              bottom={3}
              left={3}
              bg={isDark ? "rgba(20,26,38,0.92)" : "rgba(255,255,255,0.92)"}
              p={3}
              borderRadius="lg"
              borderWidth="1px"
              borderColor={cardBorder}
              fontSize="2xs"
              pointerEvents="none"
            >
              <Text fontWeight="700" mb={1.5}>
                Petunjuk Graf:
              </Text>
              <HStack spacing={2} mb={1}>
                <Box w={2.5} h={2.5} borderRadius="full" bg="#3182ce" />
                <Text>= Kompetensi Utama</Text>
              </HStack>
              <HStack spacing={2} mb={1}>
                <Box w={2.5} h={2.5} borderRadius="full" bg="cyan.400" />
                <Text>= Kompetensi Terkait</Text>
              </HStack>
              <Text mt={1}>• Ukuran Node = Frekuensi Kemunculan</Text>
              <Text>• Tebal Garis = Kekuatan Hubungan</Text>
              <Text>• Klik node untuk info & eksplorasi</Text>
            </Box>
          </Box>
        ) : (
          <VStack py={10} spacing={2} textAlign="center">
            <Icon as={AlertCircle} boxSize="32px" color="yellow.500" />
            <Heading as="h3" size="xs" color={textColor}>
              Data Jaringan Kosong
            </Heading>
            <Text fontSize="xs" color={subTextColor}>
              Tidak ditemukan data hubungan co-occurrence untuk skill "{activeSkill}".
            </Text>
          </VStack>
        )}
      </Flex>
    </Box>
  );
}
