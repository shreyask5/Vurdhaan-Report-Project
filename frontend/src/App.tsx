import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ValidationProvider } from "@/contexts/ValidationContext";
import { ChatProvider } from "@/contexts/ChatContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import Index from "./pages/Index";
import AdminLogin from "./pages/AdminLogin";
import Dashboard from "./pages/Dashboard";
import Admin from "./pages/Admin";
import ProjectUpload from "./pages/ProjectUpload";
import { ProjectErrorDisplay } from "./pages/ProjectErrorDisplay";
import ProjectValidation from "./pages/ProjectValidation";
import MonitoringPlanReview from "./pages/MonitoringPlanReview";
import ProjectChat from "./pages/ProjectChat";
import EmailVerification from "./pages/EmailVerification";
import EmailVerificationHandler from "./pages/EmailVerificationHandler";
import Welcome from "./pages/Welcome";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<Index />} />
            <Route path="/admin/login" element={<AdminLogin />} />

            {/* Email verification route (authenticated but not verified) */}
            <Route path="/verification" element={<EmailVerification />} />

            {/* Email verification handler (processes verification link) */}
            <Route path="/email-verification" element={<EmailVerificationHandler />} />

            {/* Welcome route (verified but profile not completed) */}
            <Route path="/welcome" element={<Welcome />} />

            {/* Protected routes (require auth, verification, and completed profile) */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/admin" element={
              <ProtectedRoute>
                <Admin />
              </ProtectedRoute>
            } />
            <Route path="/projects/:projectId/upload" element={
              <ProtectedRoute>
                <ValidationProvider>
                  <ProjectUpload />
                </ValidationProvider>
              </ProtectedRoute>
            } />
            <Route path="/projects/:projectId/errors" element={
              <ProtectedRoute>
                <ValidationProvider>
                  <ProjectErrorDisplay />
                </ValidationProvider>
              </ProtectedRoute>
            } />
            <Route path="/projects/:projectId/validation" element={
              <ProtectedRoute>
                <ValidationProvider>
                  <ProjectValidation />
                </ValidationProvider>
              </ProtectedRoute>
            } />
            <Route path="/projects/:projectId/monitoring-plan-review" element={
              <ProtectedRoute>
                <MonitoringPlanReview />
              </ProtectedRoute>
            } />
            <Route path="/projects/:projectId/chat" element={
              <ProtectedRoute>
                <ChatProvider>
                  <ProjectChat />
                </ChatProvider>
              </ProtectedRoute>
            } />

            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
