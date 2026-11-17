import { NavLink, Outlet, Link, useNavigate } from 'react-router-dom'
import { ArrowUpRight, BarChart3, BrainCircuit, LayoutDashboard, LogOut, Package, ReceiptText, Store } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'

const LINKS = [
  { to: '/admin', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/admin/products', label: 'Products', icon: Package },
  { to: '/admin/orders', label: 'Orders', icon: ReceiptText },
  { to: '/admin/model', label: 'Model lab', icon: BrainCircuit },
]

export function AdminLayout() {
  const { user, logout } = useAuth()
  const { push } = useToast()
  const navigate = useNavigate()
  const initial = user?.name.split(' ').map((word) => word[0]).join('').slice(0, 2).toUpperCase()

  const signOut = () => {
    logout()
    push('Signed out of the admin studio.', 'default')
    navigate('/')
  }

  return (
    <div className="admin">
      <aside className="admin-sidebar">
        <Link to="/admin" className="admin-brand">
          <span>shopwise<span className="brand__dot">.</span></span>
          <small>Admin studio</small>
        </Link>
        <nav className="admin-nav">
          <span className="admin-nav__label">Workspace</span>
          {LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className={({ isActive }) => (isActive ? 'is-active' : '')}>
              <link.icon size={17} /> {link.label}
            </NavLink>
          ))}
          <span className="admin-nav__label">Shortcuts</span>
          <Link to="/"><Store size={17} /> View storefront <ArrowUpRight size={13} className="admin-nav__external" /></Link>
          <Link to="/admin/model"><BarChart3 size={17} /> Model metrics</Link>
        </nav>
        <div className="admin-sidebar__bottom">
          <div className="admin-user">
            <span className="admin-user__avatar">{initial}</span>
            <div><strong>{user?.name}</strong><small>{user?.email}</small></div>
          </div>
          <button onClick={signOut} className="admin-signout"><LogOut size={15} /> Sign out</button>
          <p className="admin-sidebar__note">Shopwise MIS · v1.0</p>
        </div>
      </aside>
      <main className="admin-main">
        <header className="admin-topbar">
          <div className="admin-topbar__crumb">Admin studio <span>/</span> <strong>Workspace</strong></div>
          <div className="admin-topbar__right">
            <span className="live-dot"><span /> API online</span>
            <Link to="/" className="text-link">Storefront <ArrowUpRight size={14} /></Link>
          </div>
        </header>
        <div className="admin-content">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
