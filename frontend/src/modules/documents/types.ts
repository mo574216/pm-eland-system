export interface DocumentVersion {
  id: string
  document_id: string
  version_number: number
  original_file_name: string
  content_type: string | null
  file_extension: string | null
  file_size_bytes: number
  checksum_sha256: string | null
  scan_status: 'PENDING' | 'CLEAN' | 'INFECTED' | 'FAILED'
  preview_status: 'NOT_REQUESTED' | 'QUEUED' | 'READY' | 'FAILED'
  uploaded_by: string | null
  uploaded_at: string
  comment: string | null
  metadata: Record<string, unknown>
}

export interface Document {
  id: string
  workspace_id: string
  entity_id: string | null
  title: string
  description: string | null
  document_type: string | null
  lifecycle_status: 'ACTIVE' | 'ARCHIVED' | 'DELETED'
  current_version_id: string | null
  current_version: DocumentVersion | null
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface DocumentList {
  items: Document[]
  page: number
  page_size: number
  total: number
}

export interface DocumentVersionList {
  items: DocumentVersion[]
  page: number
  page_size: number
  total: number
}

export interface DocumentUploadResult {
  document_id: string
  version_id: string
  version_number: number
  scan_status: 'PENDING'
}

export interface DownloadAccess {
  url: string
  expires_at: string
}

export interface PreviewAccess {
  status: 'NOT_REQUESTED' | 'QUEUED' | 'READY' | 'FAILED'
  preview_type: 'PDF' | 'IMAGE' | null
  url: string | null
  expires_at: string | null
}
