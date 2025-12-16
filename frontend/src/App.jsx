import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import DashboardPage from "./pages/DashboardPage";
import ContractsPage from "./pages/ContractsPage";
import ContractDetailPage from "./pages/ContractDetailPage";
import ContractUploadPage from "./pages/ContractUploadPage";
import AnalysisPage from "./pages/AnalysisPage";
import ReportsPage from "./pages/ReportsPage";
// import LegalDatabasePage from './pages/LegalDatabasePage'
import ProfilePage from "./pages/ProfilePage";
import LegalDatabasePage from "./pages/LegalDatabasePage";

function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="contracts" element={<ContractsPage />} />
        <Route path="contracts/upload" element={<ContractUploadPage />} />
        <Route path="contracts/:id" element={<ContractDetailPage />} />
        <Route path="analysis" element={<AnalysisPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="legal-database" element={<LegalDatabasePage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
