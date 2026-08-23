import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { Alert, Box, Button, CircularProgress, IconButton, Stack, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { type ReactNode, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { getEntityTree, type EntityTreeNode } from './entityApi'

const ROOT_KEY = '__root__'

interface IndexedTree {
  nodes: Record<string, EntityTreeNode>
  children: Record<string, string[]>
}

function mergeTree(current: IndexedTree, incoming: EntityTreeNode[]): IndexedTree {
  const nodes = { ...current.nodes }
  const childSets = Object.fromEntries(
    Object.entries(current.children).map(([key, values]) => [key, new Set(values)]),
  ) as Record<string, Set<string>>
  for (const node of incoming) {
    nodes[node.id] = node
    const parentKey = node.parent_id ?? ROOT_KEY
    childSets[parentKey] ??= new Set<string>()
    childSets[parentKey].add(node.id)
  }
  return {
    nodes,
    children: Object.fromEntries(
      Object.entries(childSets).map(([key, values]) => [key, [...values]]),
    ),
  }
}

export interface EntityTreeViewerProps {
  workspaceId: string
  rootId?: string
  selectedEntityId?: string
  onSelect: (entityId: string) => void
  renderNodeActions?: (node: EntityTreeNode) => ReactNode
}

export function EntityTreeViewer({
  workspaceId,
  rootId,
  selectedEntityId,
  onSelect,
  renderNodeActions,
}: EntityTreeViewerProps) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [branches, setBranches] = useState<Record<string, EntityTreeNode[]>>({})
  const [loading, setLoading] = useState<Set<string>>(new Set())
  const [failed, setFailed] = useState<Set<string>>(new Set())
  const initialTree = useQuery({
    queryKey: ['entity-tree', workspaceId, rootId ?? null],
    queryFn: () => getEntityTree(workspaceId, { rootId, depth: 1 }),
  })

  const branchPrefix = `${workspaceId}:`
  const tree = useMemo(() => {
    let result = mergeTree({ nodes: {}, children: {} }, initialTree.data?.items ?? [])
    for (const [key, items] of Object.entries(branches)) {
      if (key.startsWith(branchPrefix)) result = mergeTree(result, items)
    }
    return result
  }, [branchPrefix, branches, initialTree.data])
  const initiallyLoaded = new Set(
    initialTree.data?.items.filter((node) => node.depth === 0).map((node) => node.id) ?? [],
  )

  const loadChildren = async (node: EntityTreeNode) => {
    setLoading((current) => new Set(current).add(node.id))
    setFailed((current) => {
      const next = new Set(current)
      next.delete(node.id)
      return next
    })
    try {
      const result = await getEntityTree(workspaceId, { rootId: node.id, depth: 1 })
      setBranches((current) => ({
        ...current,
        [`${branchPrefix}${node.id}`]: result.items,
      }))
    } catch {
      setFailed((current) => new Set(current).add(node.id))
    } finally {
      setLoading((current) => {
        const next = new Set(current)
        next.delete(node.id)
        return next
      })
    }
  }

  const toggleNode = (node: EntityTreeNode) => {
    const willExpand = !expanded.has(node.id)
    setExpanded((current) => {
      const next = new Set(current)
      if (willExpand) next.add(node.id)
      else next.delete(node.id)
      return next
    })
    const branchLoaded = branches[`${branchPrefix}${node.id}`] !== undefined
    if (willExpand && node.has_children && !initiallyLoaded.has(node.id) && !branchLoaded) {
      void loadChildren(node)
    }
  }

  const renderNode = (nodeId: string): ReactNode => {
    const node = tree.nodes[nodeId]
    if (node === undefined) return null
    const isExpanded = expanded.has(node.id)
    const childIds = tree.children[node.id] ?? []
    return (
      <Box
        component="li"
        key={node.id}
        role="treeitem"
        aria-expanded={node.has_children ? isExpanded : undefined}
        aria-selected={selectedEntityId === node.id}
        sx={{ listStyle: 'none' }}
      >
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          {node.has_children ? (
            <IconButton
              aria-label={isExpanded ? t('entities.collapse') : t('entities.expand')}
              onClick={() => toggleNode(node)}
              size="small"
            >
              {isExpanded ? <ExpandMoreIcon /> : <ChevronLeftIcon />}
            </IconButton>
          ) : (
            <Box sx={{ width: 34 }} />
          )}
          <Button
            aria-pressed={selectedEntityId === node.id}
            color={selectedEntityId === node.id ? 'primary' : 'inherit'}
            onClick={() => onSelect(node.id)}
            sx={{ justifyContent: 'flex-start', textAlign: 'start' }}
          >
            {node.name}
          </Button>
          {node.entity_type ? (
            <Typography color="text.secondary" variant="caption">
              {node.entity_type.name}
            </Typography>
          ) : null}
          {renderNodeActions?.(node)}
          {loading.has(node.id) ? (
            <CircularProgress aria-label={t('entities.loadingChildren')} size={18} />
          ) : null}
        </Stack>
        {failed.has(node.id) ? (
          <Alert
            action={<Button onClick={() => void loadChildren(node)}>{t('entities.retry')}</Button>}
            severity="error"
          >
            {t('entities.childrenLoadFailed')}
          </Alert>
        ) : null}
        {isExpanded && childIds.length > 0 ? (
          <Box component="ul" role="group" sx={{ m: 0, ps: 4 }}>
            {childIds.map(renderNode)}
          </Box>
        ) : null}
      </Box>
    )
  }

  if (initialTree.isPending) return <CircularProgress aria-label={t('entities.loading')} />
  if (initialTree.isError) {
    return (
      <Alert
        action={<Button onClick={() => void initialTree.refetch()}>{t('entities.retry')}</Button>}
        severity="error"
      >
        {t('entities.loadFailed')}
      </Alert>
    )
  }
  const rootIds = rootId === undefined ? (tree.children[ROOT_KEY] ?? []) : [rootId]
  if (rootIds.length === 0) return <Alert severity="info">{t('entities.empty')}</Alert>
  return (
    <Box aria-label={t('entities.treeLabel')} component="ul" role="tree" sx={{ m: 0, p: 0 }}>
      {rootIds.map(renderNode)}
    </Box>
  )
}
