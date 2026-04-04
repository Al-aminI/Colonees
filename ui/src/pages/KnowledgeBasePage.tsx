import { useState, useRef, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import {
  Plus,
  Database,
  Trash2,
  Upload,
  FileText,
  Search,
  X,
} from 'lucide-react'
import {
  useKnowledgeBases,
  useKnowledgeBase,
  useKBFiles,
  useCreateKnowledgeBase,
  useDeleteKnowledgeBase,
  useUploadFile,
  useDeleteKBFile,
  useSearchKB,
} from '@/hooks/useKnowledgeBases'
import { useToast } from '@/components/ui/toast'
import type { KnowledgeBaseDefinition, KBSearchResult } from '@/types'

const kbFormSchema = z.object({
  name: z
    .string()
    .regex(/^[a-z0-9_-]+$/, 'Only lowercase letters, numbers, hyphens, underscores')
    .min(2),
  display_name: z.string().min(2),
  description: z.string().min(5),
  type: z.enum(['files', 'database', 'api']),
})

type KBFormValues = z.infer<typeof kbFormSchema>

export function KnowledgeBasePage() {
  const { data, isLoading } = useKnowledgeBases()
  const createKB = useCreateKnowledgeBase()
  const deleteKB = useDeleteKnowledgeBase()
  const { toast } = useToast()

  const [selected, setSelected] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  const knowledgeBases = data?.knowledge_bases ?? []

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete knowledge base "${name}"?`)) return
    await deleteKB.mutateAsync(name)
    if (selected === name) setSelected(null)
    toast({ title: 'Knowledge base deleted', variant: 'info' })
  }

  return (
    <div>
      <PageHeader
        title="Knowledge Bases"
        description="Manage document collections and searchable knowledge"
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-2" /> New Knowledge Base
          </Button>
        }
      />

      {isLoading ? (
        <div className="grid grid-cols-[280px_1fr] gap-6 h-[calc(100vh-12rem)]">
          <Skeleton className="h-full" />
          <Skeleton className="h-full" />
        </div>
      ) : knowledgeBases.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
          <Database className="h-12 w-12 opacity-20" />
          <p className="text-sm">No knowledge bases created yet.</p>
          <Button variant="outline" onClick={() => setShowCreate(true)}>
            Create your first knowledge base
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-[280px_1fr] gap-6 h-[calc(100vh-12rem)]">
          {/* Left panel - list */}
          <Card className="overflow-y-auto">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Knowledge Bases</CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              <div className="space-y-1">
                {knowledgeBases.map((kb) => (
                  <button
                    key={kb.name}
                    onClick={() => setSelected(kb.name)}
                    className={`w-full text-left rounded-md px-3 py-2 text-sm transition-colors ${
                      selected === kb.name
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                  >
                    <div className="font-medium truncate">{kb.display_name}</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                        {kb.type}
                      </Badge>
                      <span className="text-xs opacity-60">
                        {kb.stats.total_files} file{kb.stats.total_files !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Right panel - detail */}
          <Card className="flex flex-col overflow-hidden">
            {!selected ? (
              <CardContent className="flex-1 flex items-center justify-center">
                <p className="text-sm text-muted-foreground">
                  Select a knowledge base from the left panel.
                </p>
              </CardContent>
            ) : (
              <KBDetailPanel
                name={selected}
                onDelete={() => handleDelete(selected)}
              />
            )}
          </Card>
        </div>
      )}

      <CreateKBDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreate={async (values) => {
          await createKB.mutateAsync({
            name: values.name,
            display_name: values.display_name,
            description: values.description,
            type: values.type,
          })
          toast({ title: 'Knowledge base created', variant: 'success' })
        }}
      />
    </div>
  )
}

/* ── KB Detail Panel ───────────────────────────────────────────────────── */

function KBDetailPanel({ name, onDelete }: { name: string; onDelete: () => void }) {
  const { data: kb, isLoading } = useKnowledgeBase(name)
  const { data: filesData, isLoading: filesLoading } = useKBFiles(name)
  const uploadFile = useUploadFile()
  const deleteFile = useDeleteKBFile()
  const searchKB = useSearchKB()
  const { toast } = useToast()

  const fileInputRef = useRef<HTMLInputElement>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<KBSearchResult[]>([])
  const [isDragging, setIsDragging] = useState(false)

  const files = filesData?.files ?? []

  const handleUpload = useCallback(
    async (fileList: FileList | null) => {
      if (!fileList) return
      for (let i = 0; i < fileList.length; i++) {
        try {
          await uploadFile.mutateAsync({ kbName: name, file: fileList[i] })
          toast({ title: `Uploaded ${fileList[i].name}`, variant: 'success' })
        } catch (err) {
          toast({
            title: `Failed to upload ${fileList[i].name}`,
            description: err instanceof Error ? err.message : 'Unknown error',
            variant: 'error',
          })
        }
      }
    },
    [name, uploadFile, toast],
  )

  const handleDeleteFile = async (filename: string) => {
    if (!confirm(`Delete file "${filename}"?`)) return
    await deleteFile.mutateAsync({ kbName: name, filename })
    toast({ title: 'File deleted', variant: 'info' })
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    const result = await searchKB.mutateAsync({ name, query: searchQuery })
    setSearchResults(result.results)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleUpload(e.dataTransfer.files)
  }

  if (isLoading) {
    return (
      <CardContent className="space-y-4 p-6">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-32" />
      </CardContent>
    )
  }

  if (!kb) {
    return (
      <CardContent className="flex-1 flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Knowledge base not found.</p>
      </CardContent>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Info */}
      <div>
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">{kb.display_name}</h2>
            <p className="text-xs text-muted-foreground font-mono">{kb.name}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-destructive hover:text-destructive"
            onClick={onDelete}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-sm text-muted-foreground mt-2">{kb.description}</p>
        <div className="flex gap-2 mt-3">
          <Badge variant="info">{kb.type}</Badge>
          <Badge variant="secondary">
            {kb.stats.total_files} file{kb.stats.total_files !== 1 ? 's' : ''}
          </Badge>
          <Badge variant="secondary">{kb.stats.total_chunks} chunks</Badge>
          <Badge variant="secondary">
            {(kb.stats.total_size_bytes / 1024).toFixed(1)} KB
          </Badge>
        </div>
      </div>

      <Separator />

      {/* File Upload */}
      <div>
        <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">
          Files
        </h3>
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleUpload(e.target.files)}
          className="hidden"
          multiple
        />
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-muted-foreground'
          }`}
        >
          <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Drop files here or click to upload
          </p>
          {uploadFile.isPending && (
            <p className="text-xs text-primary mt-1">Uploading...</p>
          )}
        </div>

        {/* File list */}
        {filesLoading ? (
          <div className="space-y-2 mt-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        ) : files.length === 0 ? (
          <p className="text-sm text-muted-foreground mt-3">No files uploaded yet.</p>
        ) : (
          <div className="space-y-1 mt-3">
            {files.map((f) => (
              <div
                key={f.name}
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-accent"
              >
                <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span className="flex-1 truncate">{f.name}</span>
                <span className="text-xs text-muted-foreground shrink-0">
                  {(f.size / 1024).toFixed(1)} KB
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 shrink-0 text-destructive hover:text-destructive"
                  onClick={() => handleDeleteFile(f.name)}
                  disabled={deleteFile.isPending}
                >
                  <X className="h-3.5 w-3.5" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      <Separator />

      {/* Search */}
      <div>
        <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">
          Search
        </h3>
        <div className="flex gap-2">
          <Input
            placeholder="Search knowledge base..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Button onClick={handleSearch} disabled={searchKB.isPending || !searchQuery.trim()}>
            <Search className="h-4 w-4 mr-1" />
            {searchKB.isPending ? 'Searching...' : 'Search'}
          </Button>
        </div>

        {searchResults.length > 0 && (
          <div className="space-y-3 mt-4">
            {searchResults.map((result, i) => (
              <Card key={i}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-muted-foreground font-mono truncate">
                      {result.source}
                    </span>
                    <Badge variant="outline" className="text-[10px] shrink-0">
                      {(result.score * 100).toFixed(0)}% match
                    </Badge>
                  </div>
                  <p className="text-sm whitespace-pre-wrap">{result.content}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Create Dialog ─────────────────────────────────────────────────────── */

function CreateKBDialog({
  open,
  onClose,
  onCreate,
}: {
  open: boolean
  onClose: () => void
  onCreate: (values: KBFormValues) => Promise<void>
}) {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<KBFormValues>({
    resolver: zodResolver(kbFormSchema),
    defaultValues: { type: 'files' },
  })

  const handleClose = () => {
    reset()
    onClose()
  }

  const onSubmit = async (values: KBFormValues) => {
    setIsSubmitting(true)
    try {
      await onCreate(values)
      handleClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogHeader title="Create Knowledge Base" onClose={handleClose} />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label>Name (slug)</Label>
          <Input {...register('name')} placeholder="my-knowledge-base" className="mt-1" />
          {errors.name && (
            <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>
          )}
        </div>

        <div>
          <Label>Display Name</Label>
          <Input {...register('display_name')} placeholder="My Knowledge Base" className="mt-1" />
          {errors.display_name && (
            <p className="mt-1 text-xs text-destructive">{errors.display_name.message}</p>
          )}
        </div>

        <div>
          <Label>Description</Label>
          <Textarea
            {...register('description')}
            placeholder="What kind of knowledge does this contain?"
            className="mt-1"
            rows={2}
          />
          {errors.description && (
            <p className="mt-1 text-xs text-destructive">{errors.description.message}</p>
          )}
        </div>

        <div>
          <Label>Type</Label>
          <Select {...register('type')} className="mt-1 w-full">
            <option value="files">Files</option>
            <option value="database">Database</option>
            <option value="api">API</option>
          </Select>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create Knowledge Base'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
