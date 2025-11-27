'use client';

import { useEffect, useState } from 'react';
import { useAtom } from 'jotai';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { currentNamespaceIdAtom, namespacesAtom } from '@/lib/atoms';
import {
  useLoadNamespaces,
  useCreateNamespace,
  useSelectNamespace,
  useDeleteNamespace,
} from '@/lib/jotai-hooks';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

export function NamespacesPage() {
  const [currentNamespace] = useAtom(currentNamespaceIdAtom);
  const [namespaces] = useAtom(namespacesAtom);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState<string | null>(null);
  const [newNamespace, setNewNamespace] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const loadNamespaces = useLoadNamespaces();
  const createNamespace = useCreateNamespace();
  const selectNamespace = useSelectNamespace();
  const deleteNamespace = useDeleteNamespace();

  // Load namespaces on mount
  useEffect(() => {
    loadNamespaces().catch((error) => {
      toast.error('Failed to load namespaces');
      console.error(error);
    });
  }, []);

  const handleCreateNamespace = async () => {
    if (!newNamespace.trim()) {
      toast.error('Namespace is required');
      return;
    }

    setIsLoading(true);
    try {
      await createNamespace(newNamespace.trim());
      toast.success('Namespace created successfully!');
      setNewNamespace('');
      setIsCreateDialogOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create namespace');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectNamespace = async (namespace: string) => {
    try {
      const ns = namespaces.find((n) => n.namespace === namespace);
      if (ns) {
        selectNamespace(ns);
        toast.success('Namespace switched!');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to select namespace');
    }
  };

  const handleDeleteNamespace = async (namespace: string) => {
    try {
      await deleteNamespace(namespace);
      toast.success('Namespace deleted successfully');
      setIsDeleteDialogOpen(null);
      if (currentNamespace === namespace) {
        // Clear current namespace if deleting active one
        localStorage.removeItem('namespace');
        localStorage.removeItem('token');
        window.location.reload();
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete namespace');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-500">Namespaces</h1>
        <p className="text-muted-foreground text-lg">Manage your workspaces and create new ones</p>
      </div>

      {/* Create New Namespace */}
      <Card className="hover-lift border border-red-900/20 shadow-lg overflow-hidden bg-gradient-to-br from-black to-gray-900">
        <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-orange-500/5" />
        <CardHeader className="relative">
          <CardTitle className="text-xl">Create New Namespace</CardTitle>
          <CardDescription>Start a new workspace with its own memory and settings</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-lg hover:shadow-xl transition-all hover:scale-105 border border-red-500">Create Namespace</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Namespace</DialogTitle>
                <DialogDescription>
                  Create a new namespace to organize your memories and conversations
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="namespace">Namespace</Label>
                  <Input
                    id="namespace"
                    placeholder="e.g., my-workspace"
                    value={newNamespace}
                    onChange={(e) => setNewNamespace(e.target.value)}
                    disabled={isLoading}
                  />
                  <p className="text-xs text-muted-foreground">
                    Unique identifier for this workspace (alphanumeric, hyphens, underscores)
                  </p>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button onClick={handleCreateNamespace} disabled={isLoading}>
                  {isLoading ? 'Creating...' : 'Create'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>

      {/* Namespaces List */}
      <Card className="hover-lift border border-red-900/20 shadow-lg bg-gradient-to-br from-black to-gray-900">
        <CardHeader>
          <CardTitle className="text-xl">Your Namespaces</CardTitle>
          <CardDescription>
            {namespaces.length} {namespaces.length === 1 ? 'namespace' : 'namespaces'} available
          </CardDescription>
        </CardHeader>
        <CardContent>
          {namespaces.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No namespaces yet. Create one to get started!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {namespaces.map((ns, index) => (
                <div
                  key={ns.namespace}
                  className="group flex items-center justify-between p-5 border-2 border-red-900/30 rounded-xl hover:bg-gradient-to-r hover:from-red-950/30 hover:to-orange-950/30 hover:border-red-700 transition-all duration-300"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex-1">
                    <div className="font-medium">
                      {ns.namespace}
                      {currentNamespace === ns.namespace && (
                        <span className="ml-2 text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                          Active
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Created {new Date(ns.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {currentNamespace !== ns.namespace && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleSelectNamespace(ns.namespace)}
                      >
                        Select
                      </Button>
                    )}

                    {/* Delete Button with inline confirmation dialog */}
                    <Dialog open={isDeleteDialogOpen === ns.namespace} onOpenChange={(open) => {
                      setIsDeleteDialogOpen(open ? ns.namespace : null);
                    }}>
                      <DialogTrigger asChild>
                        <Button
                          size="sm"
                          variant="destructive"
                          disabled={currentNamespace === ns.namespace}
                        >
                          Delete
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Delete Namespace?</DialogTitle>
                          <DialogDescription>
                            This action cannot be undone. All memories and data in "{ns.namespace}"
                            will be permanently deleted.
                          </DialogDescription>
                        </DialogHeader>
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            onClick={() => setIsDeleteDialogOpen(null)}
                          >
                            Cancel
                          </Button>
                          <Button
                            variant="destructive"
                            onClick={() => handleDeleteNamespace(ns.namespace)}
                          >
                            Delete
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
