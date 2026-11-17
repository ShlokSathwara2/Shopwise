import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Quote } from 'lucide-react'

export function AuthLayout({
  eyebrow,
  title,
  subtitle,
  children,
  image = '/static/auth-visual.svg',
  quote = 'The things you live with should earn their place.',
}: {
  eyebrow: string
  title: ReactNode
  subtitle: string
  children: ReactNode
  image?: string
  quote?: string
}) {
  return (
    <div className="auth-page">
      <div className="auth-visual">
        <img src={image} alt="" />
        <div className="auth-visual__overlay" />
        <Link to="/" className="brand brand--light auth-visual__brand">shopwise<span className="brand__dot">.</span></Link>
        <div className="auth-visual__quote">
          <Quote size={26} />
          <blockquote>{quote}</blockquote>
          <span>The Shopwise studio</span>
        </div>
        <span className="auth-visual__index">Est. 2026 · New York</span>
      </div>
      <div className="auth-panel">
        <Link to="/" className="auth-back"><ArrowLeft size={15} /> Back to shop</Link>
        <div className="auth-box">
          <span className="eyebrow">{eyebrow}</span>
          <h1>{title}</h1>
          <p className="auth-subtitle">{subtitle}</p>
          {children}
        </div>
        <p className="auth-fineprint">By continuing you agree to our friendly terms, privacy policy and the occasional good recommendation.</p>
      </div>
    </div>
  )
}
