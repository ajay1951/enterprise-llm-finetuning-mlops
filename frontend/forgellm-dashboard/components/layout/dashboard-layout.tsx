'use client';

import Link from "next/link";
import { usePathname, useParams, useRouter } from "next/navigation";
import { 
  LayoutDashboard, FolderKanban, Database, Activity, Beaker, Box, 
  Settings, Search, Bell, Moon, Sun, Key, ShieldAlert, ChevronDown, Check,
  PanelLeftClose, PanelRightClose
} from "lucide-react";
import { useState, useEffect } from "react";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const params = useParams() as { projectId?: string };
  const pathname = usePathname();
  const router = useRouter();
  const projectId = params.projectId;
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [theme, setTheme] = useState('dark');

  // Bypass layout for auth pages
  if (pathname === '/' || pathname?.startsWith('/login') || pathname?.startsWith('/register')) {
    return <>{children}</>;
  }

  const basePath = projectId ? `/projects/${projectId}` : '';

  const mainNav = [
    { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
    { name: "Projects", href: "/projects", icon: FolderKanban },
    { name: "Models", href: projectId ? `${basePath}/models` : "/projects", icon: Box },
    { name: "Training", href: projectId ? `${basePath}/training` : "/projects", icon: Activity },
    { name: "Deployments", href: projectId ? `${basePath}/deployments` : "/projects", icon: Activity },
    { name: "Experiments", href: projectId ? `${basePath}/experiments` : "/projects", icon: Beaker },
  ];

  const securityNav = [
    { name: "API Keys", href: "/settings/api-keys", icon: Key },
    { name: "Audit Logs", href: "/settings/audit-logs", icon: ShieldAlert },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden text-sm">
      {/* Sidebar */}
      <aside 
        className={`border-r border-border bg-card flex flex-col shrink-0 transition-all duration-300 ease-in-out ${isSidebarOpen ? 'w-64' : 'w-16'}`}
      >
        <div className="h-14 flex items-center justify-between px-4 border-b border-border shrink-0">
          {isSidebarOpen ? (
            <Link href="/dashboard" className="font-semibold tracking-tight text-foreground flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-foreground text-background flex items-center justify-center font-bold text-xs">F</div>
              ForgeLLM
            </Link>
          ) : (
            <Link href="/dashboard" className="mx-auto w-6 h-6 rounded bg-foreground text-background flex items-center justify-center font-bold text-xs">
              F
            </Link>
          )}
        </div>
        
        <div className="flex-1 py-4 overflow-y-auto flex flex-col gap-6">
          <nav className="space-y-1 px-2">
            {mainNav.map((item) => {
              const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  title={!isSidebarOpen ? item.name : undefined}
                  className={`flex items-center space-x-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive 
                      ? 'bg-secondary text-foreground' 
                      : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
                  } ${!isSidebarOpen ? 'justify-center' : ''}`}
                >
                  <item.icon className="h-[18px] w-[18px] shrink-0" />
                  {isSidebarOpen && <span>{item.name}</span>}
                </Link>
              );
            })}
          </nav>

          <div className="px-2">
            {isSidebarOpen && (
              <div className="px-3 mb-2 text-caption">Security & Platform</div>
            )}
            <nav className="space-y-1">
              {securityNav.map((item) => {
                const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    title={!isSidebarOpen ? item.name : undefined}
                    className={`flex items-center space-x-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      isActive 
                        ? 'bg-secondary text-foreground' 
                        : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
                    } ${!isSidebarOpen ? 'justify-center' : ''}`}
                  >
                    <item.icon className="h-[18px] w-[18px] shrink-0" />
                    {isSidebarOpen && <span>{item.name}</span>}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Sidebar Toggle */}
        <div className="p-4 border-t border-border flex justify-end">
          <button 
            onClick={() => setSidebarOpen(!isSidebarOpen)}
            className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded-md hover:bg-secondary"
          >
            {isSidebarOpen ? <PanelLeftClose size={18} /> : <PanelRightClose size={18} />}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Topbar */}
        <header className="h-14 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center px-6 shrink-0 justify-between z-10">
          
          {/* Left Context Group */}
          <div className="flex items-center space-x-2">
            <button className="flex items-center gap-2 hover:bg-secondary px-2 py-1.5 rounded-md transition-colors text-sm font-medium">
              <div className="w-5 h-5 rounded-sm bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[10px] text-white font-bold">FL</div>
              <span>ForgeLabs</span>
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            </button>
            <span className="text-muted-foreground/50">/</span>
            <button className="flex items-center gap-2 hover:bg-secondary px-2 py-1.5 rounded-md transition-colors text-sm font-medium text-muted-foreground hover:text-foreground">
              <span>Customer Support AI</span>
              <ChevronDown className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Right Action Group */}
          <div className="flex items-center space-x-4">
            <button className="flex items-center gap-2 px-3 py-1.5 bg-secondary text-muted-foreground hover:text-foreground border border-border rounded-md text-xs font-medium transition-colors w-64 justify-between">
              <span className="flex items-center gap-2"><Search size={14} /> Search...</span>
              <kbd className="font-sans px-1.5 py-0.5 bg-background rounded border border-border text-[10px]">⌘K</kbd>
            </button>

            <div className="h-4 w-[1px] bg-border" />
            
            <button className="text-muted-foreground hover:text-foreground transition-colors relative">
              <Bell size={18} />
              <span className="absolute top-0 right-0 w-2 h-2 rounded-full bg-destructive border border-background"></span>
            </button>
            
            <div className="relative">
              <button 
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="h-7 w-7 rounded-full bg-secondary border border-border flex items-center justify-center font-bold text-xs hover:bg-accent transition-colors"
              >
                AG
              </button>
              
              {isProfileOpen && (
                <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-card border border-border z-50">
                  <div className="py-1">
                    <div className="px-4 py-2 border-b border-border">
                      <p className="text-sm text-foreground font-medium">Admin User</p>
                      <p className="text-xs text-muted-foreground truncate">admin@company.com</p>
                    </div>
                    <button
                      onClick={() => {
                        setIsProfileOpen(false);
                        router.push('/');
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-destructive hover:bg-secondary transition-colors"
                    >
                      Log out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto bg-background">
          {children}
        </div>
      </main>
    </div>
  );
}
