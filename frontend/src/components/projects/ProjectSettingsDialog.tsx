import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { projectsApi, Project } from '@/services/api';

interface ProjectSettingsDialogProps {
  project: Project;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSettingsUpdated?: () => void;
}

export function ProjectSettingsDialog({
  project,
  open,
  onOpenChange,
  onSettingsUpdated,
}: ProjectSettingsDialogProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    ai_chat_enabled: project.ai_chat_enabled || false,
    save_files_on_server: project.save_files_on_server || false,
  });

  // Update form data when project changes
  useEffect(() => {
    setFormData({
      ai_chat_enabled: project.ai_chat_enabled || false,
      save_files_on_server: project.save_files_on_server || false,
    });
  }, [project]);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await projectsApi.update(project.id, {
        name: project.name,  // Explicitly preserve name
        description: project.description,  // Explicitly preserve description
        ai_chat_enabled: formData.ai_chat_enabled,
        save_files_on_server: formData.save_files_on_server,
      });

      toast.success('Project settings updated successfully!');
      onOpenChange(false);

      // Trigger refresh
      if (onSettingsUpdated) {
        onSettingsUpdated();
      }
    } catch (error: any) {
      console.error('Failed to update project settings:', error);
      toast.error(error.message || 'Failed to update project settings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    // Reset form data to original values
    setFormData({
      ai_chat_enabled: project.ai_chat_enabled || false,
      save_files_on_server: project.save_files_on_server || false,
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Project Settings</DialogTitle>
          <DialogDescription>
            Configure settings for {project.name}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* AI Chat Toggle */}
          <div className="flex items-center justify-between space-x-2 rounded-lg border p-4">
            <div className="flex-1 space-y-0.5">
              <Label htmlFor="ai-chat-setting" className="text-base cursor-pointer">
                Enable AI Chat
              </Label>
              <p className="text-sm text-muted-foreground">
                Allow natural language queries on your flight data
              </p>
            </div>
            <Switch
              id="ai-chat-setting"
              checked={formData.ai_chat_enabled}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, ai_chat_enabled: checked })
              }
              disabled={isLoading}
            />
          </div>

          {/* Save Files on Server Toggle */}
          <div className="flex items-center justify-between space-x-2 rounded-lg border p-4">
            <div className="flex-1 space-y-0.5">
              <Label htmlFor="save-files-setting" className="text-base cursor-pointer">
                Save Files on Server
              </Label>
              <p className="text-sm text-muted-foreground">
                Store uploaded data permanently on the server
              </p>
            </div>
            <Switch
              id="save-files-setting"
              checked={formData.save_files_on_server}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, save_files_on_server: checked })
              }
              disabled={isLoading}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button type="button" onClick={handleSave} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
