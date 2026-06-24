'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth-provider';
import { api } from '@/lib/api';
import { formatFileSize, formatDuration, getStatusColor, formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Sidebar from '@/components/sidebar';
import { Video, Upload, Search, Filter, Trash2, Play, MoreVertical } from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';

interface VideoItem {
  id: string;
  filename: string;
  status: string;
  duration?: number;
  file_size?: number;
  resolution_width?: number;
  resolution_height?: number;
  thumbnail_url?: string;
  source_type: string;
  created_at: string;
}

export default function VideosPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 20;

  useEffect(() => {
    fetchVideos();
  }, [page]);

  const fetchVideos = async () => {
    try {
      setLoading(true);
      const response = await api.get(
        `/videos?page=${page}&per_page=${perPage}${search ? `&search=${search}` : ''}`
      );
      setVideos(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      toast.error('Failed to load videos');
    } finally {
      setLoading(false);
    }
  };

  const deleteVideo = async (videoId: string) => {
    if (!confirm('Are you sure you want to delete this video?')) return;

    try {
      await api.delete(`/videos/${videoId}`);
      setVideos((prev) => prev.filter((v) => v.id !== videoId));
      toast.success('Video deleted');
    } catch (error) {
      toast.error('Failed to delete video');
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchVideos();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="ml-64 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Videos</h1>
            <p className="text-gray-600 mt-1">
              Manage and process your videos
            </p>
          </div>
          <Link href="/dashboard/upload">
            <Button>
              <Upload className="mr-2 h-4 w-4" />
              Upload Video
            </Button>
          </Link>
        </div>

        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search videos..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-10"
              />
            </div>
          </div>
          <Button variant="outline">
            <Filter className="mr-2 h-4 w-4" />
            Filter
          </Button>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <div className="h-40 bg-gray-200 rounded-t-lg"></div>
                <CardContent className="p-4">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : videos.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Video className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No videos found
              </h3>
              <p className="text-gray-500 mb-4">
                Upload your first video to get started
              </p>
              <Link href="/dashboard/upload">
                <Button>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Video
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {videos.map((video) => (
                <Card
                  key={video.id}
                  className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => router.push(`/dashboard/videos/${video.id}`)}
                >
                  <div className="h-40 bg-gray-900 relative group">
                    {video.thumbnail_url ? (
                      <img
                        src={video.thumbnail_url}
                        alt={video.filename}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Video className="h-12 w-12 text-gray-600" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Button size="lg" variant="secondary">
                        <Play className="mr-2 h-5 w-5" />
                        View
                      </Button>
                    </div>
                    <div className="absolute top-2 right-2">
                      <Badge className={getStatusColor(video.status)}>
                        {video.status}
                      </Badge>
                    </div>
                    {video.duration && (
                      <div className="absolute bottom-2 right-2 bg-black/75 text-white text-xs px-2 py-1 rounded">
                        {formatDuration(video.duration)}
                      </div>
                    )}
                  </div>
                  <CardContent className="p-4">
                    <h3 className="font-medium text-gray-900 truncate mb-1">
                      {video.filename}
                    </h3>
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <span>
                        {video.resolution_width}x{video.resolution_height}
                      </span>
                      <span>{video.file_size ? formatFileSize(video.file_size) : '-'}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-400 mt-2">
                      <span>{formatDate(video.created_at)}</span>
                      <span>{video.source_type}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="flex items-center justify-between mt-6">
              <p className="text-sm text-gray-500">
                Showing {videos.length} of {total} videos
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={videos.length < perPage}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
