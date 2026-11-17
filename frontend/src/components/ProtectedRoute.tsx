import type { ReactNode } from 'react'
import { Navigate, Link, useLocation } from 'react-router-dom'
import { LockKeyhole } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { PageLoader } from './UI'

export function ProtectedRoute({ children, admin = false }: { children: ReactNode; admin?: boolean }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <PageLoader label="Checking your account…" />
  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname + location.search }} replace />
  }
  if (admin && !user.is_admin) {
    return (
      <div className="shell section">
        <div className="empty-state">
          <span className="empty-state__icon"><LockKeyhole size={24} /></span>
          <h3>This room is for staff only</h3>
          <p>Your account does not have access to the admin studio.</p>
          <Link to="/" className="button button--dark">Back to the shop</Link>
        </div>
      </div>
    )
  }
  return <>{children}</>
}
