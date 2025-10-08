/**
 * ProjectChat Page
 * AI-powered chat interface for natural language queries on flight data
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ArrowLeft, Database, Download, FileBarChart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { ChatInterface } from '@/components/project/ChatInterface';
import { projectsApi } from '@/services/api';
import { validationService } from '@/services/validation';
import type { Project } from '@/services/api';

export default function ProjectChat() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [sessionId, setSessionId] = useState<string>();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (projectId) {
      loadProject();
    }
  }, [projectId]);

  const loadProject = async () => {
    try {
      const projectData = await projectsApi.get(projectId!);
      setProject(projectData);

      // Check if project has AI chat enabled
      if (!projectData.ai_chat_enabled) {
        toast.error('AI Chat is not enabled for this project');
        navigate('/dashboard');
        return;
      }

      // Check if project has data
      if (!projectData.has_file) {
        toast.warning('No flight data found. Please upload a CSV file first.');
      }
    } catch (error: any) {
      toast.error('Failed to load project');
      navigate('/dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadClean = async () => {
    if (!projectId) return;

    try {
      const blob = await validationService.downloadCSV(projectId, 'clean');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project?.name}_clean_data.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Downloaded clean data');
    } catch (error: any) {
      toast.error('Download failed');
    }
  };

  const handleGenerateReport = async () => {
    if (!projectId) return;

    try {
      const blob = await validationService.generateReport(projectId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project?.name}_corsia_report.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('CORSIA report generated');
    } catch (error: any) {
      toast.error('Report generation failed');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-hero">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading project...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-hero flex flex-col">
      {/* Header */}
      <header className="bg-card border-b border-border flex-shrink-0">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" asChild>
                <Link to="/dashboard">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Dashboard
                </Link>
              </Button>
              <div className="h-8 w-px bg-border" />
              <div>
                <h1 className="text-lg font-semibold">{project.name}</h1>
                <p className="text-xs text-muted-foreground">AI Chat Assistant</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {project.has_file && (
                <>
                  <Button variant="outline" size="sm" onClick={handleDownloadClean}>
                    <Download className="mr-2 h-4 w-4" />
                    Download Data
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleGenerateReport}>
                    <FileBarChart className="mr-2 h-4 w-4" />
                    Generate Report
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 grid lg:grid-cols-4 gap-6 overflow-hidden">
          {/* Sidebar */}
          <aside className="lg:col-span-1 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Project Info</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <p className="text-muted-foreground text-xs mb-1">Status</p>
                  <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                    {project.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs mb-1">AI Chat</p>
                  <Badge variant={project.ai_chat_enabled ? 'default' : 'secondary'}>
                    {project.ai_chat_enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs mb-1">Data Status</p>
                  <Badge variant={project.has_file ? 'default' : 'secondary'}>
                    {project.has_file ? 'Loaded' : 'No Data'}
                  </Badge>
                </div>
                {project.error_count !== undefined && project.error_count > 0 && (
                  <div>
                    <p className="text-muted-foreground text-xs mb-1">Validation Errors</p>
                    <Badge variant="destructive">{project.error_count}</Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  About AI Chat
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground space-y-2">
                <p>
                  Ask questions about your flight data in natural language. The AI will analyze your
                  data and provide insights.
                </p>
                <p>
                  Example queries:
                </p>
                <ul className="list-disc list-inside space-y-1 pl-2">
                  <li>Total flights</li>
                  <li>Fuel consumption by route</li>
                  <li>Flights from specific airport</li>
                  <li>Average flight duration</li>
                </ul>
              </CardContent>
            </Card>
          </aside>

          {/* Chat Interface */}
          <div className="lg:col-span-3 flex flex-col overflow-hidden">
            {!project.has_file ? (
              <Card className="flex-1 flex items-center justify-center">
                <CardContent className="text-center p-12">
                  <Database className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <CardTitle className="mb-2">No Flight Data</CardTitle>
                  <CardDescription className="mb-6">
                    Upload a CSV file to start chatting with your flight data
                  </CardDescription>
                  <Button asChild>
                    <Link to={`/projects/${projectId}/upload`}>
                      Upload CSV File
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="flex-1 overflow-hidden">
                <ChatInterface
                  projectId={projectId!}
                  sessionId={sessionId}
                  onSessionCreated={setSessionId}
                />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
