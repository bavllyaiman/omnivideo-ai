'use client';

import { useCallback, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { useAuth } from '@/components/auth-provider';
import { api } from '@/lib/api';
import { formatFileSize } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Sidebar from '@/components/sidebar';
import {
  Upload,
  Video,
  X,
  CheckCircle,
  AlertCircle,
  Link as LinkIcon,
  Youtube,
  Cloud,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function UploadPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [projectId, setProjectId] = useState<string>('');
  const [projects, setProjects] = useState<any[]>([]);
  const [importUrl, setImportUrl] = useState('');
  const [importType, setImportType] = useState<'youtube' | 'url' | 'drive' | 'dropbox'>('youtube');

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await api.get('/projects?per_page=50');
      setProjects(response.data.items);
      if (response.data.items.length > 0) {
        setProjectId(response.data.items[0].id);
      }
    } catch (error) {
      toast.error('Failed to load projects');
    }
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prev) => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv'],
    },
    maxSize: 10 * 1024 * 1024 * 1024,
    multiple: true,
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (!projectId) {
      toast.error('Please select a project');
      return;
    }

    setUploading(true);
    const results = [];

    for (const file of files) {
      try {
        setUploadProgress((prev) => ({ ...prev, [file.name]: 0 }));

        const response = await api.post('/videos/upload-url', {
          project_id: projectId,
          filename: file.name,
          content_type: file.type,
          file_size: file.size,
        });

        const { upload_url, video_id, s3_key } = response.data;

        await fetch(upload_url, {
          method: 'PUT',
          body: file,
          headers: { 'Content-Type': file.type },
        });

        setUploadProgress((prev) => ({ ...prev, [file.name]: 100 }));
        results.push({ filename: file.name, video_id, status: 'success' });
        toast.success(`${file.name} uploaded successfully`);
      } catch (error: any) {
        setUploadProgress((prev) => ({ ...prev, [file.name]: -1 }));
        results.push({ filename: file.name, status: 'failed', error: error.message });
        toast.error(`Failed to upload ${file.name}`);
      }
    }

    setUploading(false);
    setFiles([]);

    if (results.some((r) => r.status === 'success')) {
      router.push('/dashboard/videos');
    }
  };

  const handleImportUrl = async () => {
    if (!importUrl || !projectId) {
      toast.error('Please enter a URL and select a project');
      return;
    }

    try {
      if (importType === 'youtube') {
        await api.post(`/videos/import/youtube?project_id=${projectId}&url=${encodeURIComponent(importUrl)}`);
      } else {
        await api.post(`/videos/import/url?project_id=${projectId}&url=${encodeURIComponent(importUrl)}`);
      }
      toast.success('Video import started');
      router.push('/dashboard/videos');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Import failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="ml-64 p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Upload Videos</h1>
          <p className="text-gray-600 mt-1">
            Upload videos from your device or import from external sources
          </p>
        </div>

        <div className="mb-6">
          <label className="text-sm font-medium text-gray-700 mb-2 block">
            Select Project
          </label>
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Select a project</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                File Upload
              </CardTitle>
              <CardDescription>
                Drag and drop videos or click to browse
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                <Video className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                {isDragActive ? (
                  <p className="text-purple-600 font-medium">
                    Drop the videos here...
                  </p>
                ) : (
                  <div>
                    <p className="text-gray-600 font-medium">
                      Drag & drop videos here, or click to select
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      MP4, MOV, AVI, MKV up to 10GB each
                    </p>
                  </div>
                )}
              </div>

              {files.length > 0 && (
                <div className="mt-4 space-y-2">
                  {files.map((file, index) => (
                    <div
                      key={`${file.name}-${index}`}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <Video className="h-5 w-5 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium">{file.name}</p>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(file.size)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {uploadProgress[file.name] === 100 && (
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        )}
                        {uploadProgress[file.name] === -1 && (
                          <AlertCircle className="h-5 w-5 text-red-500" />
                        )}
                        <button
                          onClick={() => removeFile(index)}
                          className="text-gray-400 hover:text-red-500"
                        >
                          <X className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  ))}
                  <Button
                    onClick={uploadFiles}
                    disabled={uploading || !projectId}
                    className="w-full mt-4"
                  >
                    {uploading ? 'Uploading...' : `Upload ${files.length} video(s)`}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LinkIcon className="h-5 w-5" />
                Import from URL
              </CardTitle>
              <CardDescription>
                Import videos from YouTube, Google Drive, Dropbox, or URLs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <button
                    onClick={() => setImportType('youtube')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                      importType === 'youtube'
                        ? 'border-red-500 bg-red-50 text-red-700'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <Youtube className="h-4 w-4" />
                    YouTube
                  </button>
                  <button
                    onClick={() => setImportType('drive')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                      importType === 'drive'
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <Cloud className="h-4 w-4" />
                    Google Drive
                  </button>
                  <button
                    onClick={() => setImportType('dropbox')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                      importType === 'dropbox'
                        ? 'border-blue-400 bg-blue-50 text-blue-600'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <Cloud className="h-4 w-4" />
                    Dropbox
                  </button>
                  <button
                    onClick={() => setImportType('url')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                      importType === 'url'
                        ? 'border-purple-500 bg-purple-50 text-purple-700'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <LinkIcon className="h-4 w-4" />
                    URL
                  </button>
                </div>

                <Input
                  placeholder={
                    importType === 'youtube'
                      ? 'https://www.youtube.com/watch?v=...'
                      : importType === 'drive'
                      ? 'https://drive.google.com/file/d/...'
                      : importType === 'dropbox'
                      ? 'https://www.dropbox.com/s/...'
                      : 'https://example.com/video.mp4'
                  }
                  value={importUrl}
                  onChange={(e) => setImportUrl(e.target.value)}
                />

                <Button
                  onClick={handleImportUrl}
                  disabled={!importUrl || !projectId}
                  className="w-full"
                >
                  Import Video
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
