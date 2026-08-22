import { Navigate, createBrowserRouter } from 'react-router-dom'

import { AppShell } from '../layouts/AppShell'
import { LoginPage } from '../modules/auth/LoginPage'
import { ProtectedRoute } from '../modules/auth/ProtectedRoute'
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
