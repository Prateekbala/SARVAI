'use client';

import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { memoryAPI } from '@/lib/api';
import { toast } from 'sonner';
import { Upload, FileText, Image, File, Mic, Loader2, Check } from 'lucide-react';

export function UploadPage() {
  const [textContent, setTextContent] = useState('');
  const queryClient = useQueryClient();

  const uploadTextMutation = useMutation({
    mutationFn: (text: string) => memoryAPI.createText(text),
    onSuccess: () => {
      toast.success('Text memory saved successfully!');
      setTextContent('');
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['recent-memories'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to save text');
    },
  });

  const uploadFileMutation = useMutation({
    mutationFn: ({ file, type }: { file: File; type: 'image' | 'pdf' | 'audio' }) => {
      if (type === 'image') return memoryAPI.uploadImage(file);
      if (type === 'pdf') return memoryAPI.uploadPDF(file);
      return memoryAPI.uploadAudio(file);
    },
    onSuccess: (_, variables) => {
      toast.success(`${variables.type.toUpperCase()} uploaded successfully!`);
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['recent-memories'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Upload failed');
    },
  });

  const handleTextSubmit = () => {
    if (!textContent.trim()) {
      toast.error('Please enter some text');
      return;
    }
    uploadTextMutation.mutate(textContent);
  };

  const FileUploadZone = ({ type, accept, icon: Icon }: { type: 'image' | 'pdf' | 'audio'; accept: string; icon: any }) => {
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      accept: { [accept]: [] },
      maxFiles: 1,
      onDrop: (acceptedFiles) => {
        if (acceptedFiles.length > 0) {
          uploadFileMutation.mutate({ file: acceptedFiles[0], type });
        }
      },
    });

    return (
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
            : 'border-gray-300 dark:border-gray-700 hover:border-purple-400 dark:hover:border-purple-600'
        }`}
      >
        <input {...getInputProps()} />
        <Icon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
        <p className="text-lg font-medium mb-2">
          {isDragActive ? `Drop your ${type} here` : `Drag & drop ${type} here`}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          or click to browse
        </p>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold mb-2">Upload Memory</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Add content to your AI memory in any format
        </p>
      </div>

      <Tabs defaultValue="text" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="text">
            <FileText className="h-4 w-4 mr-2" />
            Text
          </TabsTrigger>
          <TabsTrigger value="image">
            <Image className="h-4 w-4 mr-2" />
            Image
          </TabsTrigger>
          <TabsTrigger value="pdf">
            <File className="h-4 w-4 mr-2" />
            PDF
          </TabsTrigger>
          <TabsTrigger value="audio">
            <Mic className="h-4 w-4 mr-2" />
            Audio
          </TabsTrigger>
        </TabsList>

        <TabsContent value="text">
          <Card>
            <CardHeader>
              <CardTitle>Text Memory</CardTitle>
              <CardDescription>
                Store notes, articles, or any text content
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="text-content">Content</Label>
                <Textarea
                  id="text-content"
                  placeholder="Enter your text here..."
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  rows={12}
                  disabled={uploadTextMutation.isPending}
                />
              </div>
              <Button
                onClick={handleTextSubmit}
                disabled={uploadTextMutation.isPending}
                className="w-full"
              >
                {uploadTextMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Check className="mr-2 h-4 w-4" />
                    Save Text Memory
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="image">
          <Card>
            <CardHeader>
              <CardTitle>Image Memory</CardTitle>
              <CardDescription>
                Upload images with automatic OCR text extraction
              </CardDescription>
            </CardHeader>
            <CardContent>
              {uploadFileMutation.isPending ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-12 w-12 animate-spin text-purple-600 mb-4" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">Uploading and processing...</p>
                </div>
              ) : (
                <FileUploadZone type="image" accept="image/*" icon={Image} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pdf">
          <Card>
            <CardHeader>
              <CardTitle>PDF Memory</CardTitle>
              <CardDescription>
                Upload PDF documents with automatic text extraction
              </CardDescription>
            </CardHeader>
            <CardContent>
              {uploadFileMutation.isPending ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-12 w-12 animate-spin text-purple-600 mb-4" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">Uploading and processing...</p>
                </div>
              ) : (
                <FileUploadZone type="pdf" accept="application/pdf" icon={File} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audio">
          <Card>
            <CardHeader>
              <CardTitle>Audio Memory</CardTitle>
              <CardDescription>
                Upload audio files with automatic transcription
              </CardDescription>
            </CardHeader>
            <CardContent>
              {uploadFileMutation.isPending ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-12 w-12 animate-spin text-purple-600 mb-4" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">Uploading and transcribing...</p>
                </div>
              ) : (
                <FileUploadZone type="audio" accept="audio/*" icon={Mic} />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
