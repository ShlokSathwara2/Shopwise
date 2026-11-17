import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Check, Plus, ShoppingBag } from 'lucide-react'
import { money } from '../api'
import type { Product } from '../types'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { useToast } from '../context/ToastContext'
import { Stars } from './Stars'

export function ProductImage({ src, alt, className = '' }: { src: string; alt: string; className?: string }) {
  const [failed, setFailed] = useState(false)
  return (
    <img
      src={failed ? '/static/products/placeholder.svg' : src}
      alt={alt}
      className={className}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  )
}

export function ProductCard({ product, index = 0 }: { product: Product; index?: number }) {
  const { user } = useAuth()
  const { add } = useCart()
  const { push } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [adding, setAdding] = useState(false)
  const [added, setAdded] = useState(false)

  const handleAdd = async (event: React.MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()
    if (!user) {
      push('Sign in to start your bag.', 'default')
      navigate('/login', { state: { from: location.pathname } })
      return
    }
    setAdding(true)
    try {
      await add(product.id, 1)
      setAdded(true)
      push(`${product.name} added to your bag.`, 'success')
      setTimeout(() => setAdded(false), 1400)
    } catch (error) {
      push(error instanceof Error ? error.message : 'Could not add this item.', 'error')
    } finally {
      setAdding(false)
    }
  }

  return (
    <article className="product-card" style={{ animationDelay: `${Math.min(index, 8) * 45}ms` }}>
      <Link to={`/product/${product.id}`} className="product-card__visual" aria-label={product.name}>
        <ProductImage src={product.image} alt={product.name} className="product-card__image" />
        <span className="product-card__category">{product.category}</span>
        {product.stock <= 18 && product.stock > 0 && <span className="product-card__flag">Low stock</span>}
        {product.stock === 0 && <span className="product-card__flag product-card__flag--muted">Sold out</span>}
        <button
          className={`product-card__quick ${adding ? 'is-loading' : ''} ${added ? 'is-added' : ''}`}
          onClick={handleAdd}
          disabled={product.stock === 0 || adding}
          aria-label={`Add ${product.name} to bag`}
          title={added ? 'Added to bag' : 'Quick add'}
        >
          {adding ? <span className="mini-spinner" /> : added ? <Check size={16} /> : <Plus size={17} />}
        </button>
      </Link>
      <div className="product-card__body">
        <Link to={`/product/${product.id}`} className="product-card__name">
          {product.name}
        </Link>
        <div className="product-card__meta">
          <span className="product-card__price">{money(product.price)}</span>
          <Stars rating={product.rating} count={product.review_count} size={11} showValue={false} />
        </div>
      </div>
    </article>
  )
}

export function ProductGrid({ products }: { products: Product[] }) {
  return (
    <div className="product-grid">
      {products.map((product, index) => (
        <ProductCard key={product.id} product={product} index={index} />
      ))}
    </div>
  )
}

export function ProductRail({
  title,
  subtitle,
  modelLabel,
  products,
  viewAll,
}: {
  title: string
  subtitle?: string
  modelLabel?: string
  products: Product[]
  viewAll?: string
}) {
  return (
    <section className="rail-section">
      <div className="section-heading section-heading--rail">
        <div>
          {modelLabel && <span className="eyebrow eyebrow--model"><ShoppingBag size={12} /> {modelLabel}</span>}
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {viewAll && (
          <Link to={viewAll} className="text-link">
            View all
          </Link>
        )}
      </div>
      <div className="product-rail">
        {products.map((product, index) => (
          <div className="product-rail__item" key={product.id}>
            <ProductCard product={product} index={index} />
          </div>
        ))}
      </div>
    </section>
  )
}
