import { apiRequest } from '../../api/client'
import type {
  Document,
  DocumentList,
  DocumentUploadResult,
  DocumentVersionList,
  DownloadAccess,
  PreviewAccess,
} from './types'

export function listEntityDocuments(entityId: string): Promise<DocumentList> {
  return apiRequest<DocumentList>(`/entities/${entityId}/documents?page=1&page_size=100`)
}

export function getDocument(documentId: string): Promise<Document> {
  return apiRequest<Document>(`/documents/${documentId}`)
}

export function listDocumentVersions(documentId: string): Promise<DocumentVersionList> {
  return apiRequest<DocumentVersionList>(`/documents/${documentId}/versions?page=1&page_size=100`)
}

export function uploadDocument(
  entityId: string,
  values: { file: File; title: string; description: string; documentType: string },
): Promise<DocumentUploadResult> {
  const body = new FormData()
  body.set('file', values.file)
  body.set('title', values.title)
  if (values.description.trim()) body.set('description', values.description.trim())
  if (values.documentType.trim()) body.set('document_type', values.documentType.trim())
  return apiRequest<DocumentUploadResult>(`/entities/${entityId}/documents`, {
    method: 'POST',
    body,
  })
}

export function uploadDocumentVersion(
  documentId: string,
  file: File,
  comment: string,
): Promise<DocumentUploadResult> {
  const body = new FormData()
  body.set('file', file)
  if (comment.trim()) body.set('comment', comment.trim())
  return apiRequest<DocumentUploadResult>(`/documents/${documentId}/versions`, {
    method: 'POST',
    body,
  })
}

export function getDocumentDownload(versionId: string): Promise<DownloadAccess> {
  return apiRequest<DownloadAccess>(`/document-versions/${versionId}/download`)
}

export function getDocumentPreview(versionId: string): Promise<PreviewAccess> {
  return apiRequest<PreviewAccess>(`/document-versions/${versionId}/preview`)
}
