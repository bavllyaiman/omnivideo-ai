'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/components/auth-provider';
import { Video, Zap, Globe, ArrowRight } from 'lucide-react';

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Video className="h-8 w-8 text-purple-400" />
            <span className="text-2xl font-bold text-white">OmniVideo AI</span>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <Link href="/dashboard">
                <Button>Dashboard</Button>
              </Link>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" className="text-white">
                    Login
                  </Button>
                </Link>
                <Link href="/register">
                  <Button>Get Started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl font-bold text-white mb-6">
            AI-Powered Video Editing
          </h1>
          <p className="text-xl text-gray-300 mb-10">
            Transform your videos with intelligent AI agents. Upload, analyze, edit,
            translate, and export professional-quality content automatically.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg" className="text-lg px-8">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 border border-white/20">
            <Zap className="h-12 w-12 text-purple-400 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              Multi-Agent AI
            </h3>
            <p className="text-gray-300">
              9 specialized AI agents work together to understand, analyze, and
              enhance your videos automatically.
            </p>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 border border-white/20">
            <Globe className="h-12 w-12 text-purple-400 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              100+ Languages
            </h3>
            <p className="text-gray-300">
              Translate your content into over 100 languages with context-aware
              AI translation and subtitle generation.
            </p>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 border border-white/20">
            <Video className="h-12 w-12 text-purple-400 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              Auto-Repurpose
            </h3>
            <p className="text-gray-300">
              Automatically convert your videos into blog posts, social media
              content, newsletters, and more.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
