import { Navigate, createBrowserRouter } from 'react-router-dom'

import { AppShell } from '../layouts/AppShell'
import { LoginPage } from '../modules/auth/LoginPage'
import { ProtectedRoute } from '../modules/auth/ProtectedRoute'
import { EntityExplorerPage } from '../modules/entities/EntityExplorerPage'
import { EntityDetailPage } from '../modules/entities/EntityDetailPage'
import { EntityTypeEditor } from '../modules/metadata/EntityTypeEditor'
import { EntityTypeList } from '../modules/metadata/EntityTypeList'
import { WorkspaceListPage } from '../modules/workspaces/WorkspaceListPage'
import { WorkspaceSettingsPage } from '../modules/workspaces/WorkspaceSettingsPage'
import { NotFoundPage } from '../pages/NotFoundPage'

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/workspaces" replace /> },
  { path: '/login', element: <LoginPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: '/workspaces', element: <WorkspaceListPage /> },
          { path: '/workspaces/:workspaceId/entities', element: <EntityExplorerPage /> },
          {
            path: '/workspaces/:workspaceId/entities/:entityId',
            element: <EntityDetailPage />,
          },
          { path: '/workspaces/:workspaceId/metadata', element: <EntityTypeList /> },
          {
            path: '/workspaces/:workspaceId/metadata/:entityTypeId',
            element: <EntityTypeEditor />,
          },
          {
            path: '/workspaces/:workspaceId/settings',
            element: <WorkspaceSettingsPage />,
          },
        ],
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
])
