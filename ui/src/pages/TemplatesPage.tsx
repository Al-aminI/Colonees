import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogHeader } from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { LayoutTemplate, Bot, Server, Database, Sparkles } from 'lucide-react'
import {
  useTemplates,
  useTemplateCategories,
  useApplyTemplate,
} from '@/hooks/useTemplates'
import { useToast } from '@/components/ui/toast'
import type { UseCaseTemplate } from '@/types'

export function TemplatesPage() {
  const [category, setCategory] = useState<string>('all')
  const { data: categoriesData, isLoading: catLoading } = useTemplateCategories()
  const { data: templatesData, isLoading: templatesLoading } = useTemplates(
    category === 'all' ? undefined : category,
  )
  const applyTemplate = useApplyTemplate()
  const { toast } = useToast()
  const navigate = useNavigate()

  const [selectedTemplate, setSelectedTemplate] = useState<UseCaseTemplate | null>(null)

  const categories = categoriesData?.categories ?? []
  const templates = templatesData?.templates ?? []
  const isLoading = catLoading || templatesLoading

  const handleApply = async (name: string) => {
    try {
      const result = await applyTemplate.mutateAsync(name)
      setSelectedTemplate(null)
      toast({
        title: 'Template applied',
        description: `Workspace "${result.workspace}" created with ${result.colonees_created.length} colonee(s).`,
        variant: 'success',
      })
      navigate('/workspaces')
    } catch (err) {
      toast({
        title: 'Failed to apply template',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'error',
      })
    }
  }

  return (
    <div>
      <PageHeader
        title="Templates"
        description="Quickly set up pre-configured workspaces with colonees and knowledge bases"
      />

      {/* Category tabs */}
      <Tabs value={category} onValueChange={setCategory} className="mb-6">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          {catLoading
            ? Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-7 w-20 rounded-md" />
              ))
            : categories.map((cat) => (
                <TabsTrigger key={cat.name} value={cat.name}>
                  {cat.icon && <span className="mr-1">{cat.icon}</span>}
                  {cat.display_name}
                  <span className="ml-1.5 text-xs opacity-60">{cat.count}</span>
                </TabsTrigger>
              ))}
        </TabsList>

        {/* Content for all tabs rendered via templates list below */}
        <TabsContent value={category}>
          {isLoading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 mt-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-52" />
              ))}
            </div>
          ) : templates.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
              <LayoutTemplate className="h-12 w-12 opacity-20" />
              <p className="text-sm">No templates found in this category.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 mt-4">
              {templates.map((t) => (
                <TemplateCard
                  key={t.name}
                  template={t}
                  onClick={() => setSelectedTemplate(t)}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Template detail dialog */}
      {selectedTemplate && (
        <TemplateDetailDialog
          template={selectedTemplate}
          open={!!selectedTemplate}
          onClose={() => setSelectedTemplate(null)}
          onApply={() => handleApply(selectedTemplate.name)}
          isApplying={applyTemplate.isPending}
        />
      )}
    </div>
  )
}

/* ── Template Card ─────────────────────────────────────────────────────── */

function TemplateCard({
  template,
  onClick,
}: {
  template: UseCaseTemplate
  onClick: () => void
}) {
  const gradientColor = template.color || '#6366f1'

  return (
    <Card
      className="flex flex-col cursor-pointer hover:border-primary/40 transition-colors overflow-hidden"
      onClick={onClick}
    >
      {/* Color accent header */}
      <div
        className="h-2"
        style={{
          background: `linear-gradient(135deg, ${gradientColor}, ${gradientColor}88)`,
        }}
      />
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          {template.icon && <span className="text-lg">{template.icon}</span>}
          <CardTitle className="truncate">{template.display_name}</CardTitle>
        </div>
        <Badge variant="outline" className="w-fit text-[10px]">
          {template.category}
        </Badge>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="text-sm text-muted-foreground line-clamp-3">
          {template.description}
        </p>
        <div className="flex items-center gap-3 mt-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Bot className="h-3.5 w-3.5" />
            {template.colonees.length} colonee{template.colonees.length !== 1 ? 's' : ''}
          </span>
          {template.mcp_server_suggestions.length > 0 && (
            <span className="flex items-center gap-1">
              <Server className="h-3.5 w-3.5" />
              {template.mcp_server_suggestions.length} MCP
            </span>
          )}
          {template.recommended_knowledge_bases.length > 0 && (
            <span className="flex items-center gap-1">
              <Database className="h-3.5 w-3.5" />
              {template.recommended_knowledge_bases.length} KB
            </span>
          )}
        </div>
      </CardContent>
      <CardFooter className="pt-0">
        <div className="flex flex-wrap gap-1">
          {template.tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="secondary" className="text-[10px]">
              {tag}
            </Badge>
          ))}
          {template.tags.length > 3 && (
            <Badge variant="secondary" className="text-[10px]">
              +{template.tags.length - 3}
            </Badge>
          )}
        </div>
      </CardFooter>
    </Card>
  )
}

/* ── Template Detail Dialog ────────────────────────────────────────────── */

function TemplateDetailDialog({
  template,
  open,
  onClose,
  onApply,
  isApplying,
}: {
  template: UseCaseTemplate
  open: boolean
  onClose: () => void
  onApply: () => void
  isApplying: boolean
}) {
  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogHeader
        title={`${template.icon ? template.icon + ' ' : ''}${template.display_name}`}
        onClose={onClose}
      />

      <div className="space-y-5">
        <div>
          <Badge variant="outline">{template.category}</Badge>
          <p className="text-sm text-muted-foreground mt-2">{template.description}</p>
          {template.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-3">
              {template.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-[10px]">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>

        <Separator />

        {/* Colonees */}
        {template.colonees.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
              <Bot className="h-4 w-4" /> Colonees ({template.colonees.length})
            </h3>
            <div className="space-y-2">
              {template.colonees.map((c, i) => {
                const name = (c as Record<string, unknown>).display_name ?? (c as Record<string, unknown>).name ?? `Colonee ${i + 1}`
                const desc = (c as Record<string, unknown>).description ?? ''
                return (
                  <div key={i} className="rounded-md border px-3 py-2">
                    <p className="text-sm font-medium">{String(name)}</p>
                    {desc && (
                      <p className="text-xs text-muted-foreground mt-0.5">{String(desc)}</p>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {/* MCP Server Suggestions */}
        {template.mcp_server_suggestions.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
              <Server className="h-4 w-4" /> MCP Server Suggestions
            </h3>
            <div className="space-y-2">
              {template.mcp_server_suggestions.map((s) => (
                <div key={s.name} className="rounded-md border px-3 py-2">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">{s.name}</p>
                    <Badge variant="outline" className="text-[10px]">
                      {s.transport}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{s.description}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Recommended Knowledge Bases */}
        {template.recommended_knowledge_bases.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold mb-2 text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
              <Database className="h-4 w-4" /> Recommended Knowledge Bases
            </h3>
            <div className="flex flex-wrap gap-2">
              {template.recommended_knowledge_bases.map((kb) => (
                <Badge key={kb} variant="secondary">
                  {kb}
                </Badge>
              ))}
            </div>
          </section>
        )}

        <Separator />

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={onApply} disabled={isApplying}>
            <Sparkles className="h-4 w-4 mr-1" />
            {isApplying ? 'Applying...' : 'Apply Template'}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}
