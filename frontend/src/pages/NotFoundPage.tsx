import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Compass, Search } from 'lucide-react'

export function NotFoundPage() {
  return (
    <div className="not-found">
      <div className="shell not-found__grid">
        <div className="not-found__copy">
          <span className="eyebrow"><Compass size={13} /> A small detour</span>
          <h1>404</h1>
          <h2>This shelf is empty.</h2>
          <p>
            The page you were looking for may have been moved, retired or never made it into the edit.
            The rest of the shop is right where you left it.
          </p>
          <div className="not-found__actions">
            <Link to="/" className="button button--dark"><ArrowLeft size={16} /> Back to the shop</Link>
            <Link to="/shop" className="button button--ghost"><Search size={16} /> Browse everything</Link>
          </div>
          <div className="not-found__links">
            <span>Try instead</span>
            <Link to="/shop?category=Kitchen%20%26%20Dining">Kitchen & dining <ArrowRight size={13} /></Link>
            <Link to="/orders">Order history <ArrowRight size={13} /></Link>
            <Link to="/cart">Your bag <ArrowRight size={13} /></Link>
          </div>
        </div>
        <div className="not-found__visual" aria-hidden="true">
          <span className="not-found__number">404</span>
          <div className="not-found__frame">
            <img src="/static/auth-visual.svg" alt="" />
          </div>
          <span className="not-found__caption">Even the best edits have a gap.</span>
        </div>
      </div>
    </div>
  )
}
