import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Facebook, Instagram, Mail, Twitter } from 'lucide-react'
import { useToast } from '../context/ToastContext'

const SHOP_LINKS = [
  { label: 'All products', to: '/shop' },
  { label: 'Kitchen & dining', to: '/shop?category=Kitchen%20%26%20Dining' },
  { label: 'Home decor', to: '/shop?category=Home%20Decor' },
  { label: 'Lighting', to: '/shop?category=Lighting' },
  { label: 'Gifts & festive', to: '/shop?category=Festive%20%26%20Gifts' },
]

const HELP_LINKS = [
  { label: 'My orders', to: '/orders' },
  { label: 'My bag', to: '/cart' },
  { label: 'Sign in', to: '/login' },
  { label: 'Create an account', to: '/register' },
]

export function Footer() {
  const [email, setEmail] = useState('')
  const { push } = useToast()
  const subscribe = (event: React.FormEvent) => {
    event.preventDefault()
    if (!email.includes('@')) {
      push('Enter a valid email address.', 'error')
      return
    }
    push('You are on the list. A little inspiration is on its way.', 'success')
    setEmail('')
  }

  return (
    <footer className="site-footer">
      <div className="shell">
        <div className="footer-newsletter">
          <div>
            <span className="eyebrow">Notes from the studio</span>
            <h2>Slow living, good objects<br />and the occasional offer.</h2>
          </div>
          <form onSubmit={subscribe} className="newsletter-form">
            <Mail size={18} />
            <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Your email address" aria-label="Email address" />
            <button type="submit">Join the list <ArrowUpRight size={16} /></button>
          </form>
        </div>
        <div className="footer-grid">
          <div className="footer-brand">
            <Link to="/" className="brand brand--light">shopwise<span className="brand__dot">.</span></Link>
            <p>Considered pieces for the everyday — discovered with a little help from data, chosen with a human eye.</p>
            <div className="footer-socials">
              <a href="#" aria-label="Instagram"><Instagram size={17} /></a>
              <a href="#" aria-label="Facebook"><Facebook size={17} /></a>
              <a href="#" aria-label="Twitter"><Twitter size={17} /></a>
            </div>
          </div>
          <div>
            <h4>Shop</h4>
            {SHOP_LINKS.map((link) => <Link key={link.label} to={link.to}>{link.label}</Link>)}
          </div>
          <div>
            <h4>Account</h4>
            {HELP_LINKS.map((link) => <Link key={link.label} to={link.to}>{link.label}</Link>)}
          </div>
          <div>
            <h4>Visit</h4>
            <p>14 Mercer Walk<br />New York, NY 10012</p>
            <p>Mon–Sat, 10am–6pm<br />hello@shopwise.example</p>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© 2026 Shopwise. Academic concept store.</span>
          <span>Recommendations powered by a hybrid ML model</span>
          <span>Privacy · Terms · Shipping</span>
        </div>
      </div>
    </footer>
  )
}
