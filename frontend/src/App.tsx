import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ValidationProvider } from "@/contexts/ValidationContext";
import { ChatProvider } from "@/contexts/ChatContext";
import Index from "./pages/Index";
import AdminLogin from "./pages/AdminLogin";
import Dashboard from "./pages/Dashboard";
import Admin from "./pages/Admin";
import ProjectUpload from "./pages/ProjectUpload";
import { ProjectErrorDisplay } from "./pages/ProjectErrorDisplay";
import ProjectValidation from "./pages/ProjectValidation";
import ProjectChat from "./pages/ProjectChat";
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
            <Route path="/" element={<Index />} />
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/projects/:projectId/upload" element={
              <ValidationProvider>
                <ProjectUpload />
              </ValidationProvider>
            } />
            <Route path="/projects/:projectId/errors" element={
              <ValidationProvider>
                <ProjectErrorDisplay />
              </ValidationProvider>
            } />
            <Route path="/projects/:projectId/validation" element={
              <ValidationProvider>
                <ProjectValidation />
              </ValidationProvider>
            } />
            <Route path="/projects/:projectId/chat" element={
              <ChatProvider>
                <ProjectChat />
              </ChatProvider>
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
