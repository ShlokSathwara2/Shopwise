import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  ArrowRight,
  Check,
  ChevronDown,
  Heart,
  Minus,
  PackageCheck,
  Plus,
  RotateCcw,
  ShieldCheck,
  ShoppingBag,
  Star,
  Truck,
} from 'lucide-react'
import { api, money, shortDate } from '../api'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { ProductImage, ProductRail } from '../components/ProductCard'
import { Stars } from '../components/Stars'
import { Breadcrumbs, EmptyState, PageLoader } from '../components/UI'
import type { Recommendation, Review } from '../types'

export function ProductPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const { add } = useCart()
  const { push } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const { data: product, loading, error } = useFetch(() => api.product(id!), [id])
  const [related, setRelated] = useState<{ similar: Recommendation; also: Recommendation } | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [quantity, setQuantity] = useState(1)
  const [adding, setAdding] = useState(false)
  const [justAdded, setJustAdded] = useState(false)
  const [saved, setSaved] = useState(false)
  const [reviewOpen, setReviewOpen] = useState(false)
  const [reviewRating, setReviewRating] = useState(5)
  const [reviewTitle, setReviewTitle] = useState('')
  const [reviewComment, setReviewComment] = useState('')
  const [submittingReview, setSubmittingReview] = useState(false)
  const loggedView = useRef<number | null>(null)

  useEffect(() => {
    setQuantity(1)
    setReviewOpen(false)
    setReviewTitle('')
    setReviewComment('')
    setReviewRating(5)
    setRelated(null)
    setReviews([])
    if (!id) return
    let cancelled = false
    Promise.all([api.reviews(id), api.similar(id, 8), api.alsoBought(id, 8)])
      .then(([reviewData, similar, also]) => {
        if (!cancelled) {
          setReviews(reviewData)
          setRelated({ similar, also })
        }
      })
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [id])

  useEffect(() => {
    if (product && loggedView.current !== product.id) {
      loggedView.current = product.id
      void api.logEvent(product.id, 'view')
    }
  }, [product])

  const distribution = useMemo(() => {
    return [5, 4, 3, 2, 1].map((star) => {
      const count = reviews.filter((review) => review.rating === star).length
      return { star, count, percent: reviews.length ? (count / reviews.length) * 100 : 0 }
    })
  }, [reviews])

  if (loading) return <PageLoader label="Unwrapping this piece…" />
  if (error || !product) {
    return (
      <div className="shell section">
        <EmptyState title="We couldn't find that piece" text={error || 'It may have moved or sold out.'} action={<Link to="/shop" className="button button--dark">Back to the shop</Link>} />
      </div>
    )
  }

  const handleAdd = async () => {
    if (!user) {
      push('Sign in to add pieces to your bag.', 'default')
      navigate('/login', { state: { from: location.pathname } })
      return
    }
    setAdding(true)
    try {
      await add(product.id, quantity)
      setJustAdded(true)
      push(`${quantity} × ${product.name} added to your bag.`, 'success')
      setTimeout(() => setJustAdded(false), 1600)
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not add this item.', 'error')
    } finally {
      setAdding(false)
    }
  }

  const submitReview = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!user) {
      navigate('/login', { state: { from: location.pathname } })
      return
    }
    setSubmittingReview(true)
    try {
      const created = await api.createReview(product.id, { rating: reviewRating, title: reviewTitle, comment: reviewComment })
      setReviews((current) => [created, ...current.filter((review) => review.id !== created.id)])
      setReviewOpen(false)
      setReviewTitle('')
      setReviewComment('')
      push('Thank you — your review is live.', 'success')
    } catch (err) {
      push(err instanceof Error ? err.message : 'Could not publish your review.', 'error')
    } finally {
      setSubmittingReview(false)
    }
  }

  return (
    <div className="product-page">
      <div className="shell">
        <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Shop', to: '/shop' }, { label: product.category, to: `/shop?category=${encodeURIComponent(product.category)}` }, { label: product.name }]} />

        <div className="product-main">
          <div className="product-visual">
            <div className="product-visual__stage">
              <ProductImage src={product.image} alt={product.name} className="product-visual__image" />
              <span className="product-visual__code">{product.code}</span>
              <span className="product-visual__category">{product.category}</span>
            </div>
            <div className="product-visual__notes">
              <span><PackageCheck size={16} /> In our permanent collection</span>
              <span><ShieldCheck size={16} /> Quality checked by our studio</span>
            </div>
          </div>

          <div className="product-info">
            <div className="product-info__intro">
              <div className="product-info__topline">
                <Link to={`/shop?category=${encodeURIComponent(product.category)}`} className="eyebrow">{product.category}</Link>
                <span className={`stock-pill ${product.stock <= 18 ? 'stock-pill--low' : ''}`}>
                  <span /> {product.stock === 0 ? 'Sold out' : product.stock <= 18 ? `Only ${product.stock} left` : 'In stock'}
                </span>
              </div>
              <h1>{product.name}</h1>
              <a href="#reviews" className="product-info__reviews">
                <Stars rating={product.rating} count={product.review_count} size={14} />
                <span className="product-info__review-link">Read {product.review_count} reviews</span>
              </a>
              <div className="product-info__price">
                <span>{money(product.price)}</span>
                <small>Includes all taxes</small>
              </div>
              <p className="product-info__description">{product.description}</p>
            </div>

            <dl className="product-specs">
              <div><dt>Material</dt><dd>{product.material || 'Mixed materials'}</dd></div>
              <div><dt>Colour</dt><dd>{product.colour || 'Natural'}</dd></div>
              <div><dt>Reference</dt><dd>{product.code}</dd></div>
              <div><dt>Edit</dt><dd>{product.category}</dd></div>
            </dl>

            <div className="product-buy">
              <div className="quantity-stepper">
                <button onClick={() => setQuantity((q) => Math.max(1, q - 1))} disabled={quantity <= 1} aria-label="Decrease quantity"><Minus size={15} /></button>
                <span>{quantity}</span>
                <button onClick={() => setQuantity((q) => Math.min(product.stock, q + 1))} disabled={quantity >= product.stock} aria-label="Increase quantity"><Plus size={15} /></button>
              </div>
              <button
                className={`button button--dark product-buy__add ${justAdded ? 'is-added' : ''}`}
                onClick={handleAdd}
                disabled={adding || product.stock === 0}
              >
                {adding ? <span className="btn-spinner" /> : justAdded ? <Check size={17} /> : <ShoppingBag size={17} />}
                {product.stock === 0 ? 'Sold out' : adding ? 'Adding…' : justAdded ? 'Added to bag!' : 'Add to bag'}
              </button>
              <button className={`save-button ${saved ? 'is-saved' : ''}`} onClick={() => { setSaved((value) => !value); push(saved ? 'Removed from your saved list.' : 'Saved for later.', 'default') }} aria-label="Save for later">
                <Heart size={19} fill={saved ? 'currentColor' : 'none'} />
              </button>
            </div>

            <div className="product-assurances">
              <div><Truck size={18} /><span><strong>Free delivery over $75</strong><small>Dispatched in 1–2 working days</small></span></div>
              <div><RotateCcw size={18} /><span><strong>30-day returns</strong><small>Change your mind, no questions asked</small></span></div>
              <div><ShieldCheck size={18} /><span><strong>Considered packaging</strong><small>Plastic-free wherever we can</small></span></div>
            </div>

            <details className="accordion" open>
              <summary>Why we chose it <ChevronDown size={16} /></summary>
              <p>{product.description} Selected for its material quality, everyday usefulness and the way it settles into a room.</p>
            </details>
            <details className="accordion">
              <summary>Delivery & returns <ChevronDown size={16} /></summary>
              <p>Standard delivery is complimentary over $75 and takes 2–4 working days. Returns are accepted within 30 days in original condition.</p>
            </details>
          </div>
        </div>

        {reviews.length > 0 && (
          <section className="reviews" id="reviews">
            <div className="reviews__summary">
              <span className="eyebrow">In their words</span>
              <h2>Loved in real homes</h2>
              <div className="reviews__score">
                <strong>{product.rating.toFixed(1)}</strong>
                <div>
                  <Stars rating={product.rating} size={16} showValue={false} />
                  <span>Based on {reviews.length} reviews</span>
                </div>
              </div>
              <div className="review-bars">
                {distribution.map(({ star, count, percent }) => (
                  <div className="review-bars__row" key={star}>
                    <span>{star}</span>
                    <div><span style={{ width: `${percent}%` }} /></div>
                    <small>{count}</small>
                  </div>
                ))}
              </div>
              <button className="button button--outline button--small" onClick={() => setReviewOpen((open) => !open)}>
                Write a review
              </button>
            </div>

            <div className="reviews__list">
              {reviewOpen && (
                <form className="review-form" onSubmit={submitReview}>
                  <h3>Share your thoughts</h3>
                  {!user && <p className="form-note">You can write a review once you <Link to="/login">sign in</Link>.</p>}
                  <div className="review-form__stars">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button type="button" key={star} onClick={() => setReviewRating(star)} aria-label={`${star} stars`}>
                        <Star size={23} className={star <= reviewRating ? 'star star--filled' : 'star'} />
                      </button>
                    ))}
                  </div>
                  <label>Title<input value={reviewTitle} onChange={(e) => setReviewTitle(e.target.value)} placeholder="A lovely everyday piece" required /></label>
                  <label>Your review<textarea value={reviewComment} onChange={(e) => setReviewComment(e.target.value)} rows={3} placeholder="What did you notice about the quality, finish or size?" required /></label>
                  <div className="review-form__actions">
                    <button type="button" className="button button--ghost button--small" onClick={() => setReviewOpen(false)}>Cancel</button>
                    <button className="button button--dark button--small" disabled={submittingReview}>{submittingReview ? 'Publishing…' : 'Publish review'}</button>
                  </div>
                </form>
              )}
              {reviews.slice(0, 6).map((review) => (
                <article className="review-card" key={review.id}>
                  <div className="review-card__top">
                    <div>
                      <Stars rating={review.rating} size={12} showValue={false} />
                      <h4>{review.title}</h4>
                    </div>
                    <span>{shortDate(review.created_at)}</span>
                  </div>
                  <p>{review.comment}</p>
                  <div className="review-card__author">
                    <span>{review.user_name.slice(0, 1).toUpperCase()}</span>
                    <div><strong>{review.user_name}</strong><small>Verified shopper</small></div>
                    <Check size={14} />
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        {related && (
          <div className="product-recommendations">
            {related.similar.items.length > 0 && (
              <div>
                <ProductRail
                  title={related.similar.title}
                  subtitle={related.similar.subtitle}
                  modelLabel={related.similar.model_label}
                  products={related.similar.items}
                />
                <div className="model-note model-note--compact">
                  <span className="model-note__pulse" />
                  Content model · {related.similar.generated_ms.toFixed(0)} ms
                </div>
              </div>
            )}
            {related.also.items.length > 0 && (
              <div>
                <ProductRail
                  title={related.also.title}
                  subtitle={related.also.subtitle}
                  modelLabel={related.also.model_label}
                  products={related.also.items}
                />
                <div className="model-note model-note--compact">
                  <span className="model-note__pulse" />
                  Item-CF model · {related.also.generated_ms.toFixed(0)} ms
                </div>
              </div>
            )}
          </div>
        )}

        <div className="product-next">
          <Link to="/shop" className="text-link">Continue browsing the shop <ArrowRight size={15} /></Link>
        </div>
      </div>
    </div>
  )
}
