'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/components/auth-provider';
import { api } from '@/lib/api';
import { formatFileSize, formatDuration, getStatusColor, formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import Sidebar from '@/components/sidebar';
import {
  Video,
  Play,
  Download,
  Trash2,
  Wand2,
  FileText,
  Globe,
  Image,
  Scissors,
  Share2,
  Settings,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader,
} from 'lucide-react';
import toast from 'react-hot-toast';

interface VideoDetail {
  id: string;
  filename: string;
  status: string;
  duration?: number;
  file_size?: number;
  resolution_width?: number;
  resolution_height?: number;
  fps?: number;
  codec?: string;
  thumbnail_url?: string;
  proxy_url?: string;
  source_type: string;
  analysis?: any;
  created_at: string;
}

interface Job {
  id: string;
  agent_name: string;
  status: string;
  progress: number;
  error_message?: string;
  created_at: string;
}

export default function VideoDetailPage() {
  const { user } = useAuth();
  const router = useRouter();
  const params = useParams();
  const videoId = params.id as string;
  const [video, setVideo] = useState<VideoDetail | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchVideo();
    fetchJobs();
  }, [videoId]);

  const fetchVideo = async () => {
    try {
      const response = await api.get(`/videos/${videoId}`);
      setVideo(response.data);
    } catch (error) {
      toast.error('Failed to load video');
      router.push('/dashboard/videos');
    } finally {
      setLoading(false);
    }
  };

  const fetchJobs = async () => {
    try {
      const response = await api.get(`/videos/${videoId}/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to load jobs');
    }
  };

  const analyzeVideo = async () => {
    try {
      setProcessing(true);
      await api.post(`/videos/${videoId}/reanalyze`);
      toast.success('Video analysis started');
      fetchJobs();
    } catch (error) {
      toast.error('Failed to start analysis');
    } finally {
      setProcessing(false);
    }
  };

  const generateTranscript = async () => {
    try {
      setProcessing(true);
      await api.post('/transcripts', { video_id: videoId });
      toast.success('Transcription started');
      fetchJobs();
    } catch (error) {
      toast.error('Failed to start transcription');
    } finally {
      setProcessing(false);
    }
  };

  const generateSubtitles = async () => {
    try {
      setProcessing(true);
      await api.post(`/processing/${videoId}/subtitles/generate`);
      toast.success('Subtitle generation started');
      fetchJobs();
    } catch (error) {
      toast.error('Failed to start subtitle generation');
    } finally {
      setProcessing(false);
    }
  };

  const createExport = async () => {
    try {
      setProcessing(true);
      await api.post('/processing/export', {
        video_id: videoId,
        format: 'mp4',
        resolution: '1080p',
        quality: 'high',
      });
      toast.success('Export started');
      fetchJobs();
    } catch (error) {
      toast.error('Failed to start export');
    } finally {
      setProcessing(false);
    }
  };

  const deleteVideo = async () => {
    if (!confirm('Are you sure you want to delete this video?')) return;

    try {
      await api.delete(`/videos/${videoId}`);
      toast.success('Video deleted');
      router.push('/dashboard/videos');
    } catch (error) {
      toast.error('Failed to delete video');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Sidebar />
        <div className="ml-64 p-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded-lg mb-4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!video) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="ml-64 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{video.filename}</h1>
            <p className="text-gray-600 mt-1">
              Uploaded {formatDate(video.created_at)}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={deleteVideo}>
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <div className="aspect-video bg-gray-900 rounded-t-lg relative">
                {video.thumbnail_url ? (
                  <img
                    src={video.thumbnail_url}
                    alt={video.filename}
                    className="w-full h-full object-cover rounded-t-lg"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Video className="h-24 w-24 text-gray-600" />
                  </div>
                )}
                <div className="absolute inset-0 flex items-center justify-center">
                  <Button size="lg">
                    <Play className="mr-2 h-5 w-5" />
                    Play Video
                  </Button>
                </div>
              </div>
              <CardContent className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Duration</p>
                    <p className="font-medium">
                      {video.duration ? formatDuration(video.duration) : '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Resolution</p>
                    <p className="font-medium">
                      {video.resolution_width}x{video.resolution_height}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Size</p>
                    <p className="font-medium">
                      {video.file_size ? formatFileSize(video.file_size) : '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Format</p>
                    <p className="font-medium">{video.codec || '-'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>AI Analysis</CardTitle>
                <CardDescription>
                  Video understanding and scene detection results
                </CardDescription>
              </CardHeader>
              <CardContent>
                {video.analysis ? (
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">Summary</h4>
                      <p className="text-sm text-gray-600">
                        {video.analysis.summary || 'No summary available'}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">Scenes Detected</h4>
                      <p className="text-sm text-gray-600">
                        {video.analysis.scenes?.length || 0} scene changes detected
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">Chapters</h4>
                      <div className="space-y-2">
                        {video.analysis.chapters?.map((chapter: any, i: number) => (
                          <div key={i} className="flex items-center gap-2 text-sm">
                            <Badge variant="outline">{i + 1}</Badge>
                            <span>{chapter.title}</span>
                            <span className="text-gray-400">
                              ({formatDuration(chapter.start)} - {formatDuration(chapter.end)})
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500 mb-4">Video not yet analyzed</p>
                    <Button onClick={analyzeVideo} disabled={processing}>
                      <Wand2 className="mr-2 h-4 w-4" />
                      {processing ? 'Analyzing...' : 'Run AI Analysis'}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Processing Jobs</CardTitle>
                <CardDescription>Recent AI processing activities</CardDescription>
              </CardHeader>
              <CardContent>
                {jobs.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No jobs yet</p>
                ) : (
                  <div className="space-y-3">
                    {jobs.map((job) => (
                      <div
                        key={job.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          {job.status === 'completed' ? (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                          ) : job.status === 'failed' ? (
                            <AlertCircle className="h-5 w-5 text-red-500" />
                          ) : job.status === 'processing' ? (
                            <Loader className="h-5 w-5 text-purple-500 animate-spin" />
                          ) : (
                            <Clock className="h-5 w-5 text-gray-400" />
                          )}
                          <div>
                            <p className="font-medium text-sm">
                              {job.agent_name.replace(/_/g, ' ')}
                            </p>
                            <p className="text-xs text-gray-500">
                              {formatDate(job.created_at)}
                            </p>
                          </div>
                        </div>
                        <Badge className={getStatusColor(job.status)}>
                          {job.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={analyzeVideo}
                  disabled={processing}
                >
                  <Wand2 className="mr-2 h-4 w-4" />
                  AI Analysis
                </Button>
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={generateTranscript}
                  disabled={processing}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  Generate Transcript
                </Button>
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={generateSubtitles}
                  disabled={processing}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  Generate Subtitles
                </Button>
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={() => router.push(`/dashboard/videos/${videoId}/translate`)}
                >
                  <Globe className="mr-2 h-4 w-4" />
                  Translate
                </Button>
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={() => router.push(`/dashboard/videos/${videoId}/edit`)}
                >
                  <Scissors className="mr-2 h-4 w-4" />
                  Edit Video
                </Button>
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={createExport}
                  disabled={processing}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Export Video
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Processing Status</span>
                    <Badge className={getStatusColor(video.status)}>
                      {video.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Source</span>
                    <span className="text-sm font-medium">{video.source_type}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">FPS</span>
                    <span className="text-sm font-medium">{video.fps || '-'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
