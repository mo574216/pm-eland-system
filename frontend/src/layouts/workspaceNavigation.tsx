import {
  AccountTreeOutlined,
  DashboardOutlined,
  FileUploadOutlined,
  SettingsOutlined,
  TuneOutlined,
  ViewQuiltOutlined,
  type SvgIconComponent,
} from '@mui/icons-material'

export interface WorkspaceNavigationItem {
  key: 'dashboard' | 'entities' | 'forms' | 'imports' | 'metadata' | 'settings'
  path: (workspaceId: string) => string
  icon: SvgIconComponent
}

export const workspaceNavigation: WorkspaceNavigationItem[] = [
  { key: 'dashboard', path: (id) => `/workspaces/${id}`, icon: DashboardOutlined },
  { key: 'entities', path: (id) => `/workspaces/${id}/entities`, icon: AccountTreeOutlined },
  { key: 'forms', path: (id) => `/workspaces/${id}/forms`, icon: ViewQuiltOutlined },
  { key: 'imports', path: (id) => `/workspaces/${id}/imports`, icon: FileUploadOutlined },
  { key: 'metadata', path: (id) => `/workspaces/${id}/metadata`, icon: TuneOutlined },
  { key: 'settings', path: (id) => `/workspaces/${id}/settings`, icon: SettingsOutlined },
]
