'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/auth-provider';
import { useLanguage } from '@/components/language-provider';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Video,
  Upload,
  FolderOpen,
  BarChart3,
  Settings,
  CreditCard,
  LogOut,
  Home,
  FileText,
  Globe,
  Image,
} from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { t, language, setLanguage } = useLanguage();

  const navItems = [
    { href: '/dashboard', label: t.nav.dashboard, icon: Home },
    { href: '/dashboard/upload', label: t.nav.upload, icon: Upload },
    { href: '/dashboard/videos', label: t.nav.videos, icon: Video },
    { href: '/dashboard/projects', label: t.nav.projects, icon: FolderOpen },
    { href: '/dashboard/subtitles', label: t.nav.subtitles, icon: FileText },
    { href: '/dashboard/translations', label: t.nav.translations, icon: Globe },
    { href: '/dashboard/thumbnails', label: t.nav.thumbnails, icon: Image },
    { href: '/dashboard/analytics', label: t.nav.analytics, icon: BarChart3 },
    { href: '/dashboard/billing', label: t.nav.billing, icon: CreditCard },
    { href: '/dashboard/settings', label: t.nav.settings, icon: Settings },
  ];

  return (
    <div className="fixed right-0 top-0 h-full w-64 bg-white border-l border-gray-200 flex flex-col" style={{ direction: 'rtl' }}>
      <div className="p-6 border-b border-gray-200">
        <Link href="/dashboard" className="flex items-center gap-2">
          <Video className="h-8 w-8 text-purple-600" />
          <span className="text-xl font-bold">OmniVideo AI</span>
        </Link>
      </div>

      <div className="px-4 pt-2">
        <button
          onClick={() => setLanguage(language === 'ar' ? 'en' : 'ar')}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100"
        >
          <Globe className="h-4 w-4" />
          {language === 'ar' ? 'English' : 'العربية'}
        </button>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
            <span className="text-purple-600 font-medium">
              {user?.email?.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {user?.full_name || user?.email}
            </p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          className="w-full justify-start text-gray-600"
          onClick={logout}
        >
          <LogOut className="ml-2 h-4 w-4" />
          {t.nav.signOut}
        </Button>
      </div>
    </div>
  );
}
