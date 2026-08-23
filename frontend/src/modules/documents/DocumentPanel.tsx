import {
  DownloadOutlined,
  HistoryOutlined,
  PreviewOutlined,
  UploadFileOutlined,
} from '@mui/icons-material'
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import {
  getDocumentDownload,
  getDocumentPreview,
  listDocumentVersions,
  listEntityDocuments,
  uploadDocument,
  uploadDocumentVersion,
} from './documentApi'
import type { Document, PreviewAccess } from './types'

const maximumBytes = 50 * 1024 * 1024
const allowedExtensions = new Set([
  'pdf', 'docx', 'xlsx', 'csv', 'png', 'jpg', 'jpeg', 'svg', 'bpmn', 'xml', 'vpp',
])

function validFile(file: File): boolean {
  const extension = file.name.split('.').pop()?.toLowerCase() ?? ''
  return file.size > 0 && file.size <= maximumBytes && allowedExtensions.has(extension)
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.ceil(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function VersionHistory({ document, canUpload }: { document: Document; canUpload: boolean }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [comment, setComment] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [previewAccess, setPreviewAccess] = useState<PreviewAccess | null>(null)
  const versions = useQuery({
    queryKey: ['document-versions', document.id],
    queryFn: () => listDocumentVersions(document.id),
  })
  const addVersion = useMutation({
    mutationFn: () => uploadDocumentVersion(document.id, file!, comment),
    onSuccess: async () => {
      setFile(null); setComment(''); setError(null)
      await queryClient.invalidateQueries({ queryKey: ['document-versions', document.id] })
      await queryClient.invalidateQueries({ queryKey: ['documents', document.entity_id] })
    },
    onError: () => setError(t('documents.uploadFailed')),
  })
  const download = useMutation({
    mutationFn: getDocumentDownload,
    onSuccess: (access) => window.open(access.url, '_blank', 'noopener,noreferrer'),
    onError: () => setError(t('documents.downloadUnavailable')),
  })
  const preview = useMutation({
    mutationFn: getDocumentPreview,
    onSuccess: (access) => {
      if (access.status === 'READY' && access.url !== null && access.preview_type !== null) {
        setPreviewAccess(access); setError(null)
      } else {
        setError(t('documents.previewUnavailable'))
      }
    },
    onError: () => setError(t('documents.previewUnavailable')),
  })
  const submitVersion = () => {
    if (file === null || !validFile(file)) { setError(t('documents.invalidFile')); return }
    addVersion.mutate()
  }
  return <Stack spacing={2} sx={{ mt: 2 }}>
    <Divider />
    {error ? <Alert severity="error">{error}</Alert> : null}
    {canUpload ? <Stack spacing={1}>
      <Typography component="h4" variant="subtitle1">{t('documents.addVersion')}</Typography>
      <Button component="label" startIcon={<UploadFileOutlined />} variant="outlined">
        {file?.name ?? t('documents.chooseFile')}
        <input aria-label={t('documents.chooseVersionFile')} hidden onChange={(event) => setFile(event.target.files?.[0] ?? null)} type="file" />
      </Button>
      <TextField label={t('documents.comment')} onChange={(event) => setComment(event.target.value)} value={comment} />
      <Button disabled={addVersion.isPending} onClick={submitVersion} variant="contained">{t('documents.uploadVersion')}</Button>
    </Stack> : null}
    {versions.isPending ? <CircularProgress aria-label={t('documents.loadingVersions')} /> : null}
    {versions.isError ? <Alert severity="error">{t('documents.loadFailed')}</Alert> : null}
    {versions.data?.items.map((version) => <Card key={version.id} variant="outlined"><CardContent>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
        <Typography sx={{ fontWeight: 800 }}>{t('documents.version', { version: version.version_number })}</Typography>
        <Chip label={t(`documents.scan.${version.scan_status}`)} size="small" />
        <Chip label={t(`documents.preview.${version.preview_status}`)} size="small" variant="outlined" />
      </Stack>
      <Typography color="text.secondary">{version.original_file_name} · {formatSize(version.file_size_bytes)}</Typography>
      {version.comment ? <Typography>{version.comment}</Typography> : null}
    </CardContent><CardActions>
      <Button disabled={version.scan_status !== 'CLEAN' || version.preview_status !== 'READY' || preview.isPending} onClick={() => preview.mutate(version.id)} startIcon={<PreviewOutlined />}>{t('documents.openPreview')}</Button>
      <Button disabled={version.scan_status !== 'CLEAN' || download.isPending} onClick={() => download.mutate(version.id)} startIcon={<DownloadOutlined />}>{t('documents.download')}</Button>
    </CardActions></Card>)}
    <Dialog fullWidth maxWidth="lg" onClose={() => setPreviewAccess(null)} open={previewAccess !== null}>
      <DialogTitle>{t('documents.previewTitle')}</DialogTitle>
      <DialogContent sx={{ minHeight: 520 }}>
        {previewAccess?.preview_type === 'PDF' && previewAccess.url ? (
          <Box component="iframe" referrerPolicy="no-referrer" src={previewAccess.url} sx={{ border: 0, height: 520, width: '100%' }} title={t('documents.pdfPreview')} />
        ) : null}
        {previewAccess?.preview_type === 'IMAGE' && previewAccess.url ? (
          <Box alt={t('documents.imagePreview')} component="img" referrerPolicy="no-referrer" src={previewAccess.url} sx={{ display: 'block', maxHeight: 700, maxWidth: '100%', mx: 'auto' }} />
        ) : null}
      </DialogContent>
      <DialogActions><Button onClick={() => setPreviewAccess(null)}>{t('documents.closePreview')}</Button></DialogActions>
    </Dialog>
  </Stack>
}

export function DocumentPanel({ entityId, canRead, canUpload }: { entityId: string; canRead: boolean; canUpload: boolean }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [activeId, setActiveId] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [documentType, setDocumentType] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const documents = useQuery({
    queryKey: ['documents', entityId],
    queryFn: () => listEntityDocuments(entityId),
    enabled: canRead,
  })
  const create = useMutation({
    mutationFn: () => uploadDocument(entityId, { file: file!, title, description, documentType }),
    onSuccess: async () => {
      setTitle(''); setDescription(''); setDocumentType(''); setFile(null); setError(null)
      await queryClient.invalidateQueries({ queryKey: ['documents', entityId] })
    },
    onError: () => setError(t('documents.uploadFailed')),
  })
  const submit = () => {
    if (!title.trim() || file === null || !validFile(file)) { setError(t('documents.invalidFile')); return }
    create.mutate()
  }
  if (!canRead) return <Alert severity="warning">{t('documents.noReadPermission')}</Alert>
  return <Stack spacing={3}>
    <Typography component="h2" variant="h5">{t('documents.title')}</Typography>
    {canUpload ? <Card><CardContent><Stack spacing={2}>
      <Typography component="h3" variant="h6">{t('documents.upload')}</Typography>
      {error ? <Alert severity="error">{error}</Alert> : null}
      <TextField label={t('documents.documentTitle')} onChange={(event) => setTitle(event.target.value)} required value={title} />
      <TextField label={t('documents.documentType')} onChange={(event) => setDocumentType(event.target.value)} value={documentType} />
      <TextField label={t('documents.description')} multiline onChange={(event) => setDescription(event.target.value)} value={description} />
      <Button component="label" startIcon={<UploadFileOutlined />} variant="outlined">{file?.name ?? t('documents.chooseFile')}<input aria-label={t('documents.chooseFile')} data-testid="new-document-file" hidden onChange={(event) => setFile(event.target.files?.[0] ?? null)} type="file" /></Button>
      <Button disabled={create.isPending} onClick={submit} variant="contained">{t('documents.upload')}</Button>
    </Stack></CardContent></Card> : null}
    {documents.isPending ? <CircularProgress aria-label={t('documents.loading')} /> : null}
    {documents.isError ? <Alert severity="error">{t('documents.loadFailed')}</Alert> : null}
    {documents.data?.items.length === 0 ? <Alert severity="info">{t('documents.empty')}</Alert> : null}
    {documents.data?.items.map((document) => <Card key={document.id} variant="outlined"><CardContent>
      <Typography component="h3" variant="h6">{document.title}</Typography>
      <Typography color="text.secondary">{document.document_type ?? t('documents.noType')}</Typography>
      {document.current_version ? <Stack direction="row" spacing={1} sx={{ mt: 1 }}><Chip label={t('documents.version', { version: document.current_version.version_number })} size="small" /><Chip label={t(`documents.scan.${document.current_version.scan_status}`)} size="small" /></Stack> : null}
    </CardContent><CardActions><Button onClick={() => setActiveId((value) => value === document.id ? null : document.id)} startIcon={<HistoryOutlined />}>{t('documents.history')}</Button></CardActions>
      {activeId === document.id ? <CardContent><VersionHistory canUpload={canUpload} document={document} /></CardContent> : null}
    </Card>)}
  </Stack>
}
