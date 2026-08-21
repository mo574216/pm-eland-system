import { Navigate, createBrowserRouter } from 'react-router-dom'

import { AppShell } from '../layouts/AppShell'
import { LoginPage } from '../modules/auth/LoginPage'
import { WorkspaceListPage } from '../modules/workspaces/WorkspaceListPage'
import { NotFoundPage } from '../pages/NotFoundPage'

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/workspaces" replace /> },
  { path: '/login', element: <LoginPage /> },
  {
    element: <AppShell />,
    children: [{ path: '/workspaces', element: <WorkspaceListPage /> }],
  },
  { path: '*', element: <NotFoundPage /> },
])
