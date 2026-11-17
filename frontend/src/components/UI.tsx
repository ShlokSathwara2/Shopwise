import type { ReactNode } from 'react'
import { LoaderCircle, PackageOpen } from 'lucide-react'
import { Link } from 'react-router-dom'

export function PageLoader({ label = 'Gathering the good things…' }: { label?: string }) {
  return (
    <div className="page-loader">
      <LoaderCircle size={26} className="spin" />
      <p>{label}</p>
    </div>
  )
}

export function EmptyState({
  title,
  text,
  action,
}: {
  title: string
  text: string
  action?: ReactNode
}) {
  return (
    <div className="empty-state">
      <span className="empty-state__icon"><PackageOpen size={24} /></span>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  )
}

export function SectionHeading({
  eyebrow,
  title,
  subtitle,
  action,
  center = false,
}: {
  eyebrow?: string
  title: string
  subtitle?: string
  action?: ReactNode
  center?: boolean
}) {
  return (
    <div className={`section-heading ${center ? 'section-heading--center' : ''}`}>
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function Breadcrumbs({ items }: { items: { label: string; to?: string }[] }) {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      {items.map((item, i) => (
        <span key={i}>
          {item.to ? <Link to={item.to}>{item.label}</Link> : <span>{item.label}</span>}
          {i < items.length - 1 && <span className="breadcrumbs__sep">/</span>}
        </span>
      ))}
    </nav>
  )
}
