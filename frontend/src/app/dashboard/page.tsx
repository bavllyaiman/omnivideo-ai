'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth-provider';
import { api } from '@/lib/api';
import { formatFileSize, getStatusColor, formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import Sidebar from '@/components/sidebar';
import {
  Video,
  Upload,
  FolderOpen,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
  Settings,
  CreditCard,
  BarChart3,
  Bell,
  Search,
  ChevronRight,
} from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';

interface DashboardStats {
  total_videos: number;
  total_projects: number;
  total_processing_hours: number;
  total_exports: number;
  credits_used: number;
  credits_remaining: number;
}

interface VideoItem {
  id: string;
  filename: string;
  status: string;
  duration?: number;
  file_size?: number;
  thumbnail_url?: string;
  created_at: string;
}

interface ProjectItem {
  id: string;
  name: string;
  video_count: number;
  created_at: string;
}

export default function DashboardPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }

    if (user) {
      fetchData();
    }
  }, [user, authLoading]);

  const fetchData = async () => {
    try {
      const [statsRes, videosRes, projectsRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/videos?per_page=5'),
        api.get('/projects?per_page=5'),
      ]);
      setStats(statsRes.data);
      setVideos(videosRes.data.items);
      setProjects(projectsRes.data.items);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="ml-64 p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back, {user?.full_name || user?.email}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total Videos
              </CardTitle>
              <Video className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_videos || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Projects
              </CardTitle>
              <FolderOpen className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_projects || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Credits Used
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.credits_used || 0}</div>
              <Progress
                value={((stats?.credits_used || 0) / ((stats?.credits_used || 0) + (stats?.credits_remaining || 1))) * 100}
                className="mt-2"
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Exports
              </CardTitle>
              <CheckCircle className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_exports || 0}</div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recent Videos</CardTitle>
                <CardDescription>Your latest uploads</CardDescription>
              </div>
              <Link href="/dashboard/videos">
                <Button variant="ghost" size="sm">
                  View All <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {videos.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Video className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No videos yet</p>
                  <Link href="/dashboard/upload">
                    <Button className="mt-4" size="sm">
                      <Upload className="mr-2 h-4 w-4" /> Upload Video
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  {videos.map((video) => (
                    <div
                      key={video.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                      onClick={() => router.push(`/dashboard/videos/${video.id}`)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-12 w-16 bg-gray-200 rounded flex items-center justify-center">
                          <Video className="h-6 w-6 text-gray-400" />
                        </div>
                        <div>
                          <p className="font-medium text-sm">{video.filename}</p>
                          <p className="text-xs text-gray-500">
                            {formatDate(video.created_at)}
                          </p>
                        </div>
                      </div>
                      <Badge className={getStatusColor(video.status)}>
                        {video.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Projects</CardTitle>
                <CardDescription>Your video projects</CardDescription>
              </div>
              <Link href="/dashboard/projects">
                <Button variant="ghost" size="sm">
                  View All <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {projects.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <FolderOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No projects yet</p>
                  <Link href="/dashboard/projects/new">
                    <Button className="mt-4" size="sm">
                      <Plus className="mr-2 h-4 w-4" /> Create Project
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  {projects.map((project) => (
                    <div
                      key={project.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                      onClick={() => router.push(`/dashboard/projects/${project.id}`)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-12 w-16 bg-purple-100 rounded flex items-center justify-center">
                          <FolderOpen className="h-6 w-6 text-purple-600" />
                        </div>
                        <div>
                          <p className="font-medium text-sm">{project.name}</p>
                          <p className="text-xs text-gray-500">
                            {project.video_count} videos • {formatDate(project.created_at)}
                          </p>
                        </div>
                      </div>
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Get started with common tasks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Link href="/dashboard/upload">
                <Button variant="outline" className="w-full h-24 flex flex-col items-center justify-center gap-2">
                  <Upload className="h-6 w-6" />
                  <span>Upload Video</span>
                </Button>
              </Link>
              <Link href="/dashboard/projects/new">
                <Button variant="outline" className="w-full h-24 flex flex-col items-center justify-center gap-2">
                  <Plus className="h-6 w-6" />
                  <span>New Project</span>
                </Button>
              </Link>
              <Link href="/dashboard/billing">
                <Button variant="outline" className="w-full h-24 flex flex-col items-center justify-center gap-2">
                  <CreditCard className="h-6 w-6" />
                  <span>Billing</span>
                </Button>
              </Link>
              <Link href="/dashboard/settings">
                <Button variant="outline" className="w-full h-24 flex flex-col items-center justify-center gap-2">
                  <Settings className="h-6 w-6" />
                  <span>Settings</span>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
