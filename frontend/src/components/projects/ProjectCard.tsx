import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  MessageSquare,
  Upload,
  Download,
  FileText,
  MoreVertical,
  Settings,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Server,
} from 'lucide-react';
import { Project } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';

interface ProjectCardProps {
  project: Project;
  onOpenChat?: (projectId: string) => void;
  onUploadCSV?: (projectId: string) => void;
  onDownload?: (projectId: string, type: 'clean' | 'errors') => void;
  onGenerateReport?: (projectId: string) => void;
  onEdit?: (projectId: string) => void;
  onDelete?: (projectId: string) => void;
}

export function ProjectCard({
  project,
  onOpenChat,
  onUploadCSV,
  onDownload,
  onGenerateReport,
  onEdit,
  onDelete,
}: ProjectCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'processing':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-3 w-3" />;
      case 'processing':
        return <Clock className="h-3 w-3 animate-spin" />;
      case 'error':
        return <AlertCircle className="h-3 w-3" />;
      default:
        return <Clock className="h-3 w-3" />;
    }
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{project.name}</CardTitle>
            {project.description && (
              <CardDescription className="mt-1">{project.description}</CardDescription>
            )}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit?.(project.id)}>
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDelete?.(project.id)}
                className="text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex flex-wrap gap-2 mt-3">
          <Badge variant="outline" className={getStatusColor(project.status)}>
            {getStatusIcon(project.status)}
            <span className="ml-1 capitalize">{project.status}</span>
          </Badge>
          {project.ai_chat_enabled && (
            <Badge variant="secondary">
              <MessageSquare className="h-3 w-3 mr-1" />
              AI Chat
            </Badge>
          )}
          {project.save_files_on_server && (
            <Badge variant="secondary">
              <Server className="h-3 w-3 mr-1" />
              Saved on Server
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Project Info */}
        <div className="text-sm text-muted-foreground">
          <p>
            Created {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
          </p>
          {project.has_file && (
            <p className="text-green-600 font-medium mt-1">
              <CheckCircle2 className="inline h-3 w-3 mr-1" />
              CSV file uploaded
            </p>
          )}
          {project.error_count > 0 && (
            <p className="text-red-600 font-medium mt-1">
              <AlertCircle className="inline h-3 w-3 mr-1" />
              {project.error_count} validation errors
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2">
          {/* Upload CSV Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onUploadCSV?.(project.id)}
            className="w-full"
          >
            <Upload className="mr-2 h-4 w-4" />
            Upload CSV
          </Button>

          {/* AI Chat Button - Only show if enabled */}
          {project.ai_chat_enabled && project.has_file && (
            <Button
              variant="default"
              size="sm"
              onClick={() => onOpenChat?.(project.id)}
              className="w-full"
            >
              <MessageSquare className="mr-2 h-4 w-4" />
              Open Chat
            </Button>
          )}

          {/* Download Clean Data */}
          {project.has_file && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDownload?.(project.id, 'clean')}
              className="w-full"
            >
              <Download className="mr-2 h-4 w-4" />
              Clean Data
            </Button>
          )}

          {/* Download Errors */}
          {project.has_file && project.error_count > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDownload?.(project.id, 'errors')}
              className="w-full"
            >
              <Download className="mr-2 h-4 w-4" />
              Errors
            </Button>
          )}

          {/* Generate Report */}
          {project.has_file && project.validation_status && (
            <Button
              variant="default"
              size="sm"
              onClick={() => onGenerateReport?.(project.id)}
              className="w-full col-span-2"
            >
              <FileText className="mr-2 h-4 w-4" />
              Generate CORSIA Report
            </Button>
          )}
        </div>

        {/* AI Chat Disabled Notice */}
        {!project.ai_chat_enabled && project.has_file && (
          <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
            💡 Enable AI Chat in settings to ask questions about your data
          </div>
        )}
      </CardContent>
    </Card>
  );
}
