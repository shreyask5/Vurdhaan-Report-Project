import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Plus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { projectsApi } from '@/services/api';
import { SchemeSelector } from '@/components/project/SchemeSelector';
import { SchemeType } from '@/types/validation';

interface CreateProjectDialogProps {
  onProjectCreated?: () => void;
}

export function CreateProjectDialog({ onProjectCreated }: CreateProjectDialogProps) {
  const [open, setOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    scheme: '' as '' | SchemeType,
    ai_chat_enabled: true,
    save_files_on_server: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.scheme) {
      toast.error('Please select a scheme');
      return;
    }

    setIsLoading(true);
    try {
      const response = await projectsApi.create({
        scheme: formData.scheme,
        ai_chat_enabled: formData.ai_chat_enabled,
        save_files_on_server: formData.save_files_on_server,
      });

      toast.success('Project created successfully!');
      setOpen(false);

      // Reset form
      setFormData({
        scheme: '',
        ai_chat_enabled: true,
        save_files_on_server: false,
      });

      // Trigger refresh
      if (onProjectCreated) {
        onProjectCreated();
      }
    } catch (error: any) {
      console.error('Failed to create project:', error);
      toast.error(error.message || 'Failed to create project');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Create Report
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Report</DialogTitle>
            <DialogDescription>
              Create a new flight data analysis report with customizable settings.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Scheme Selector within dialog */}
            <div className="grid gap-2">
              <SchemeSelector
                selectedScheme={formData.scheme as SchemeType}
                onSelect={(scheme) => setFormData({ ...formData, scheme })}
              />
            </div>

            {/* AI Chat Toggle */}
            <div className="flex items-center justify-between space-x-2 rounded-lg border p-4">
              <div className="flex-1 space-y-0.5">
                <Label htmlFor="ai-chat" className="text-base cursor-pointer">
                  Enable AI Chat
                </Label>
                <p className="text-sm text-muted-foreground">
                  Allow natural language queries on your flight data
                </p>
              </div>
              <Switch
                id="ai-chat"
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
                <Label htmlFor="save-files" className="text-base cursor-pointer">
                  Save Files on Server
                </Label>
                <p className="text-sm text-muted-foreground">
                  Store uploaded CSV files permanently on the server
                </p>
              </div>
              <Switch
                id="save-files"
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
              onClick={() => setOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Report'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
