import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Bug } from 'lucide-react';

export const ProjectHeader = () => {
  const handleDashboardClick = () => {
    window.location.href = 'https://tools.vurdhaan.com/dashboard';
  };

  const handleDebugClick = () => {
    // Placeholder for future debug implementation
    console.log('Debug button clicked - implementation pending');
  };

  return (
    <header className="bg-card border-b border-border">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link to="/" className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg bg-gradient-primary flex items-center justify-center">
              <span className="text-white font-bold text-lg">V</span>
            </div>
            <span className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              Vurdhaan Reports
            </span>
          </Link>
          <div className="flex items-center space-x-4">
            <Button variant="outline" onClick={handleDashboardClick}>
              Dashboard
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDebugClick}
              title="Debug (Coming Soon)"
            >
              <Bug className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};
