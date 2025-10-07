import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { Menu, X, Moon, Sun } from 'lucide-react';
import { useState, useEffect } from 'react';
import { AuthModal } from '@/components/auth/AuthModal';

export const Header = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<'login' | 'signup'>('login');

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const dark = localStorage.getItem('theme') === 'dark';
    setIsDark(dark);
    document.documentElement.classList.toggle('dark', dark);
  }, []);

  const toggleTheme = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    localStorage.setItem('theme', newDark ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', newDark);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
    setIsMenuOpen(false);
  };

  const scrollToSection = (id: string) => {
    setIsMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header
      className={`sticky top-0 z-50 w-full transition-all duration-300 ${
        isScrolled
          ? 'bg-background/80 backdrop-blur-lg border-b border-border shadow-sm'
          : 'bg-transparent'
      }`}
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="h-8 w-8 rounded-lg bg-gradient-primary flex items-center justify-center transition-transform group-hover:scale-110">
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <span className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              ServicePro
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <button
              onClick={() => scrollToSection('features')}
              className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
            >
              Features
            </button>
            <button
              onClick={() => scrollToSection('pricing')}
              className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
            >
              Pricing
            </button>
            <button
              onClick={() => scrollToSection('demo')}
              className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
            >
              Book Demo
            </button>
          </nav>

          {/* Desktop Actions */}
          <div className="hidden md:flex items-center space-x-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="rounded-full"
            >
              {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>

            {user ? (
              <>
                <Button
                  variant="ghost"
                  onClick={() => navigate(isAdmin ? '/admin' : '/dashboard')}
                >
                  Dashboard
                </Button>
                <Button variant="outline" onClick={handleLogout}>
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" onClick={() => {
                  setAuthModalTab('login');
                  setAuthModalOpen(true);
                }}>
                  Login
                </Button>
                <Button
                  className="bg-gradient-primary hover:opacity-90 transition-opacity"
                  onClick={() => {
                    setAuthModalTab('signup');
                    setAuthModalOpen(true);
                  }}
                >
                  Sign Up
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center space-x-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="rounded-full"
            >
              {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden border-t border-border bg-background/95 backdrop-blur-lg">
          <nav className="container mx-auto px-4 py-4 flex flex-col space-y-4">
            <button
              onClick={() => scrollToSection('features')}
              className="text-left text-sm font-medium text-foreground/80 hover:text-foreground"
            >
              Features
            </button>
            <button
              onClick={() => scrollToSection('pricing')}
              className="text-left text-sm font-medium text-foreground/80 hover:text-foreground"
            >
              Pricing
            </button>
            <button
              onClick={() => scrollToSection('demo')}
              className="text-left text-sm font-medium text-foreground/80 hover:text-foreground"
            >
              Book Demo
            </button>
            <div className="pt-4 border-t border-border space-y-2">
              {user ? (
                <>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      navigate(isAdmin ? '/admin' : '/dashboard');
                      setIsMenuOpen(false);
                    }}
                  >
                    Dashboard
                  </Button>
                  <Button variant="outline" className="w-full" onClick={handleLogout}>
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      setAuthModalTab('login');
                      setAuthModalOpen(true);
                      setIsMenuOpen(false);
                    }}
                  >
                    Login
                  </Button>
                  <Button
                    className="w-full bg-gradient-primary"
                    onClick={() => {
                      setAuthModalTab('signup');
                      setAuthModalOpen(true);
                      setIsMenuOpen(false);
                    }}
                  >
                    Sign Up
                  </Button>
                </>
              )}
            </div>
          </nav>
        </div>
      )}
      
      <AuthModal 
        open={authModalOpen} 
        onOpenChange={setAuthModalOpen}
        defaultTab={authModalTab}
      />
    </header>
  );
};
