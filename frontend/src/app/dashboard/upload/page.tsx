'use client';

import { useCallback, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { useAuth } from '@/components/auth-provider';
import { useLanguage } from '@/components/language-provider';
import { api } from '@/lib/api';
import { formatFileSize } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Sidebar from '@/components/sidebar';
import { Upload, Video, X, CheckCircle, AlertCircle, Link as LinkIcon } from 'lucide-react';
import toast from 'react-hot-toast';

export default function UploadPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [projectId, setProjectId] = useState('');
  const [projects, setProjects] = useState<any[]>([]);
  const [importUrl, setImportUrl] = useState('');
  const [importType, setImportType] = useState<'youtube' | 'url'>('youtube');

  useEffect(() => { fetchProjects(); }, []);

  const fetchProjects = async () => {
    try {
      const res = await api.get('/projects?per_page=50');
      setProjects(res.data.items || []);
      if (res.data.items?.length) setProjectId(res.data.items[0].id);
    } catch { toast.error(t.common.error); }
  };

  const onDrop = useCallback((accepted: File[]) => {
    setFiles(prev => [...prev, ...accepted]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm'] }, maxSize: 10 * 1024 * 1024 * 1024, multiple: true,
  });

  const removeFile = (i: number) => setFiles(prev => prev.filter((_, idx) => idx !== i));

  const uploadFiles = async () => {
    if (!projectId) { toast.error(t.upload_page.selectProjectFirst); return; }
    setUploading(true);
    for (const file of files) {
      try {
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }));
        const res = await api.post('/videos/upload', { project_id: projectId, filename: file.name, file_size: file.size });
        setUploadProgress(prev => ({ ...prev, [file.name]: 100 }));
        toast.success(t.upload_page.uploadSuccess.replace('{name}', file.name));
      } catch (err: any) {
        setUploadProgress(prev => ({ ...prev, [file.name]: -1 }));
        toast.error(t.upload_page.uploadFailed.replace('{name}', file.name));
      }
    }
    setUploading(false);
    setFiles([]);
    router.push('/dashboard/videos');
  };

  const handleImport = async () => {
    if (!importUrl || !projectId) { toast.error(t.upload_page.selectProjectFirst); return; }
    try {
      await api.post(`/videos/import/url?project_id=${projectId}&url=${encodeURIComponent(importUrl)}`);
      toast.success(t.upload_page.importStarted);
      router.push('/dashboard/videos');
    } catch (err: any) { toast.error(err.response?.data?.detail || t.common.error); }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <div className="mr-64 p-8" style={{ direction: 'rtl' }}>
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{t.upload_page.title}</h1>
          <p className="text-gray-600 mt-1">{t.upload_page.subtitle}</p>
        </div>

        <div className="mb-6">
          <label className="text-sm font-medium text-gray-700 mb-2 block">{t.upload_page.selectProject}</label>
          <select value={projectId} onChange={e => setProjectId(e.target.value)} className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500">
            <option value="">--</option>
            {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                {t.upload_page.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive ? 'border-purple-500 bg-purple-50' : 'border-gray-300 hover:border-gray-400'}`}>
                <input {...getInputProps()} />
                <Video className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                {isDragActive ? <p className="text-purple-600 font-medium">{t.upload_page.dragDrop}</p> : (
                  <div>
                    <p className="text-gray-600 font-medium">{t.upload_page.dragDrop}</p>
                    <p className="text-sm text-gray-500 mt-2">{t.upload_page.formats}</p>
                  </div>
                )}
              </div>
              {files.length > 0 && (
                <div className="mt-4 space-y-2">
                  {files.map((file, i) => (
                    <div key={`${file.name}-${i}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Video className="h-5 w-5 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium">{file.name}</p>
                          <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {uploadProgress[file.name] === 100 && <CheckCircle className="h-5 w-5 text-green-500" />}
                        {uploadProgress[file.name] === -1 && <AlertCircle className="h-5 w-5 text-red-500" />}
                        <button onClick={() => removeFile(i)} className="text-gray-400 hover:text-red-500"><X className="h-5 w-5" /></button>
                      </div>
                    </div>
                  ))}
                  <Button onClick={uploadFiles} disabled={uploading || !projectId} className="w-full mt-4">
                    {uploading ? t.common.processing : t.upload_page.uploadBtn.replace('{count}', String(files.length))}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LinkIcon className="h-5 w-5" />
                {t.upload_page.importFromUrl}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <button onClick={() => setImportType('youtube')} className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${importType === 'youtube' ? 'border-red-500 bg-red-50 text-red-700' : 'border-gray-300 hover:bg-gray-50'}`}>
                    YouTube
                  </button>
                  <button onClick={() => setImportType('url')} className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${importType === 'url' ? 'border-purple-500 bg-purple-50 text-purple-700' : 'border-gray-300 hover:bg-gray-50'}`}>
                    {t.upload_page.url}
                  </button>
                </div>
                <Input placeholder={importType === 'youtube' ? t.upload_page.youtubePlaceholder : t.upload_page.urlPlaceholder} value={importUrl} onChange={e => setImportUrl(e.target.value)} />
                <Button onClick={handleImport} disabled={!importUrl || !projectId} className="w-full">{t.upload_page.importBtn}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
