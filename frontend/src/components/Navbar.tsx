import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { ChevronDown, LayoutDashboard, LogOut, Menu, Package, Search, ShoppingBag, UserRound, X } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { useToast } from '../context/ToastContext'

const NAV_LINKS = [
  { label: 'Shop all', to: '/shop' },
  { label: 'Kitchen', to: '/shop?category=Kitchen%20%26%20Dining' },
  { label: 'Home', to: '/shop?category=Home%20Decor' },
  { label: 'Lighting', to: '/shop?category=Lighting' },
  { label: 'Gifts', to: '/shop?category=Festive%20%26%20Gifts' },
]

function initials(name: string) {
  return name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()
}

export function Navbar() {
  const { user, logout } = useAuth()
  const { cart } = useCart()
  const { push } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [search, setSearch] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const profileRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 15)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    setMenuOpen(false)
    setProfileOpen(false)
    setMobileOpen(false)
  }, [location.pathname, location.search])

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [mobileOpen])

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) setProfileOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault()
    const query = search.trim()
    navigate(query ? `/shop?search=${encodeURIComponent(query)}` : '/shop')
    setMobileOpen(false)
  }

  const handleLogout = () => {
    logout()
    push('You have been signed out.', 'default')
    navigate('/')
  }

  return (
    <>
      <div className="announcement">
        <span>Complimentary delivery over $75</span>
        <span className="announcement__dot">·</span>
        <span>30-day easy returns</span>
        <span className="announcement__dot">·</span>
        <span>Considered packaging, always</span>
      </div>
      <header className={`site-header ${scrolled ? 'is-scrolled' : ''}`}>
        <div className="shell site-header__inner">
          <button className="icon-button site-header__menu" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu size={22} />
          </button>
          <Link to="/" className="brand" aria-label="Shopwise home">
            shopwise<span className="brand__dot">.</span>
          </Link>
          <nav className="primary-nav" aria-label="Main navigation">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.label}
                to={link.to}
                className={({ isActive }) => `primary-nav__link ${isActive && link.to === '/shop' ? 'is-active' : ''}`}
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="site-header__actions">
            <form className={`header-search ${menuOpen ? 'is-open' : ''}`} onSubmit={submitSearch}>
              <Search size={16} />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search the shop"
                aria-label="Search products"
                onFocus={() => setMenuOpen(true)}
              />
            </form>
            {!user ? (
              <Link to="/login" className="header-action header-action--login">
                <UserRound size={18} />
                <span>Sign in</span>
              </Link>
            ) : (
              <div className="profile" ref={profileRef}>
                <button className="profile__trigger" onClick={() => setProfileOpen((open) => !open)} aria-expanded={profileOpen}>
                  <span className="profile__avatar">{initials(user.name)}</span>
                  <ChevronDown size={13} />
                </button>
                {profileOpen && (
                  <div className="profile__menu">
                    <div className="profile__hello">
                      <span>Hello, {user.name.split(' ')[0]}</span>
                      <small>{user.email}</small>
                    </div>
                    <Link to="/orders"><Package size={15} /> My orders</Link>
                    {user.is_admin && <Link to="/admin"><LayoutDashboard size={15} /> Admin studio</Link>}
                    <button onClick={handleLogout}><LogOut size={15} /> Sign out</button>
                  </div>
                )}
              </div>
            )}
            <Link to={user ? '/cart' : '/login'} className="header-action header-action--bag" aria-label="Shopping bag">
              <ShoppingBag size={19} />
              <span className="header-action__label">Bag</span>
              {cart.count > 0 && <span key={cart.count} className="bag-count">{cart.count}</span>}
            </Link>
          </div>
        </div>
      </header>

      {mobileOpen && (
        <div className="mobile-nav">
          <div className="mobile-nav__top">
            <Link to="/" className="brand">shopwise<span className="brand__dot">.</span></Link>
            <button className="icon-button" onClick={() => setMobileOpen(false)} aria-label="Close menu"><X size={22} /></button>
          </div>
          <form className="mobile-search" onSubmit={submitSearch}>
            <Search size={17} />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search products, categories…" />
          </form>
          <nav className="mobile-nav__links">
            {NAV_LINKS.map((link) => <Link key={link.label} to={link.to}>{link.label}</Link>)}
          </nav>
          <div className="mobile-nav__account">
            {user ? (
              <>
                <Link to="/orders"><Package size={17} /> My orders</Link>
                {user.is_admin && <Link to="/admin"><LayoutDashboard size={17} /> Admin studio</Link>}
                <button onClick={handleLogout}><LogOut size={17} /> Sign out</button>
              </>
            ) : (
              <Link to="/login" className="button button--dark">Sign in / Register</Link>
            )}
          </div>
          <p className="mobile-nav__note">Considered things for everyday living.</p>
        </div>
      )}
    </>
  )
}
