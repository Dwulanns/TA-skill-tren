import { Routes, Route } from "react-router-dom";
import { SidebarProvider } from "./context/SidebarContext";
import Layout from "./components/Layout";
import AdminLayoutComponent from "./layouts/AdminLayoutComponent";
import LandingPage from "./pages/LandingPage";
import TrenSkill from "./pages/TrenSkill";
import DetailAnalisis from "./pages/DetailAnalisis";
import AdminPanel from "./pages/AdminPanel";
import AdminLogin from "./pages/AdminLogin";
import AdminDashboard from "./pages/AdminDashboard";
import AdminScraping from "./pages/AdminScraping";
import AdminSkillExtraction from "./pages/AdminSkillExtraction";
import AdminDatabaseManagement from "./pages/AdminDatabaseManagement";
import AdminKeywordManagement from "./pages/AdminKeywordManagement";
import ManualPage from "./pages/ManualPage";
import SkillMatcher from "./pages/SkillMatcher";
import SkillNetwork from "./pages/SkillNetwork";
import ProtectedAdminRoute from "./components/ProtectedAdminRoute";

/**
 * UNIFIED SIDEBAR STATE MANAGEMENT
 *
 * ONE SidebarProvider wraps all routes
 * Both user and admin pages use the same sidebar state
 * No more separate AdminSidebarContext
 */
function App() {
  console.log("App rendered");
  return (
    <SidebarProvider>
      <Routes>
        {/* Landing Page - No Sidebar */}
        <Route path="/" element={<LandingPage />} />

        {/* Admin Login - No Sidebar */}
        <Route path="/admin/login" element={<AdminLogin />} />

        {/* Admin Routes with Layout & Sidebar */}
        <Route
          element={
            <ProtectedAdminRoute>
              <AdminLayoutComponent />
            </ProtectedAdminRoute>
          }
        >
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/admin/tren-skills" element={<TrenSkill />} />
          <Route path="/admin/detail-analysis" element={<DetailAnalisis />} />
          <Route path="/admin/scraping" element={<AdminScraping />} />
          <Route path="/admin/extraction" element={<AdminSkillExtraction />} />
          <Route path="/admin/database" element={<AdminDatabaseManagement />} />
          <Route path="/admin/keywords" element={<AdminKeywordManagement />} />
          <Route path="/admin/skill-network" element={<SkillNetwork />} />
        </Route>

        {/* User Pages with Layout (Sidebar + Header) */}
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<TrenSkill />} />
          <Route path="/detail" element={<DetailAnalisis />} />
          <Route path="/manual" element={<ManualPage />} />
          <Route path="/skill-matcher" element={<SkillMatcher />} />
          <Route path="/skill-network" element={<SkillNetwork />} />
        </Route>
      </Routes>
    </SidebarProvider>
  );
}

export default App;
