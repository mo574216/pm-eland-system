import {
  AccountTreeOutlined,
  DashboardOutlined,
  FormatListNumberedRtlOutlined,
  HistoryOutlined,
  SettingsOutlined,
  TuneOutlined,
  ViewQuiltOutlined,
  type SvgIconComponent,
} from '@mui/icons-material'

export interface WorkspaceNavigationItem {
  key: 'dashboard' | 'phases' | 'entities' | 'forms' | 'metadata' | 'audit' | 'settings'
  path: (workspaceId: string) => string
  icon: SvgIconComponent
}

export const workspaceNavigation: WorkspaceNavigationItem[] = [
  { key: 'dashboard', path: (id) => `/workspaces/${id}`, icon: DashboardOutlined },
  { key: 'phases', path: (id) => `/workspaces/${id}/phases`, icon: FormatListNumberedRtlOutlined },
  { key: 'entities', path: (id) => `/workspaces/${id}/entities`, icon: AccountTreeOutlined },
  { key: 'forms', path: (id) => `/workspaces/${id}/forms`, icon: ViewQuiltOutlined },
  { key: 'metadata', path: (id) => `/workspaces/${id}/metadata`, icon: TuneOutlined },
  { key: 'audit', path: (id) => `/workspaces/${id}/audit`, icon: HistoryOutlined },
  { key: 'settings', path: (id) => `/workspaces/${id}/settings`, icon: SettingsOutlined },
]
