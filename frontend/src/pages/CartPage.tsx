import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Minus, Plus, Trash2 } from 'lucide-react'
import { api, money } from '../api'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { useToast } from '../context/ToastContext'
import { useFetch } from '../hooks/useFetch'
import { ProductImage, ProductRail } from '../components/ProductCard'
import { Breadcrumbs, EmptyState } from '../components/UI'

export function CartPage() {
  const { user } = useAuth()
  const { cart, loading, update, remove } = useCart()
  const { push } = useToast()
  const [busy, setBusy] = useState<number | null>(null)
  const { data: recommendations } = useFetch(() => api.homeRecommendations(4), [user?.id])

  if (!user) {
    return (
      <div className="shell section">
        <EmptyState
          title="Your bag is waiting"
          text="Sign in to keep your pieces together and pick up where you left off."
          action={<Link to="/login" state={{ from: '/cart' }} className="button button--dark">Sign in to shop</Link>}
        />
      </div>
    )
  }

  const changeQuantity = async (itemId: number, quantity: number) => {
    setBusy(itemId)
    try {
      await update(itemId, quantity)
    } catch (error) {
      push(error instanceof Error ? error.message : 'Could not update your bag.', 'error')
    } finally {
      setBusy(null)
    }
  }

  const removeItem = async (itemId: number, name: string) => {
    setBusy(itemId)
    try {
      await remove(itemId)
      push(`${name} removed from your bag.`, 'default')
    } catch (error) {
      push(error instanceof Error ? error.message : 'Could not remove this item.', 'error')
    } finally {
      setBusy(null)
    }
  }

  const freeShipping = cart.subtotal >= 75
  const remaining = Math.max(0, 75 - cart.subtotal)

  return (
    <div className="shell section page-cart">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Your bag' }]} />
      <div className="page-heading">
        <span className="eyebrow">Step 1 of 3 · Your bag</span>
        <h1>Your bag <span className="page-heading__count">({cart.count})</span></h1>
      </div>

      {loading && cart.items.length === 0 ? (
        <div className="cart-layout">
          <div>{Array.from({ length: 2 }).map((_, i) => <div className="skeleton skeleton--cart" key={i} />)}</div>
          <div className="skeleton skeleton--summary" />
        </div>
      ) : cart.items.length === 0 ? (
        <EmptyState
          title="Nothing in the bag yet"
          text="There is a whole shop of considered pieces waiting for you."
          action={<Link to="/shop" className="button button--dark">Shop the collection <ArrowRight size={15} /></Link>}
        />
      ) : (
        <div className="cart-layout">
          <div className="cart-items">
            <div className="shipping-progress">
              <div className="shipping-progress__text">
                {freeShipping ? (
                  <span><strong>Complimentary delivery unlocked.</strong> A small pleasure, on us.</span>
                ) : (
                  <span>You’re <strong>{money(remaining)}</strong> away from complimentary delivery.</span>
                )}
                <span>{freeShipping ? '✓' : `${Math.round((cart.subtotal / 75) * 100)}%`}</span>
              </div>
              <div className="shipping-progress__bar"><span style={{ width: `${Math.min(100, (cart.subtotal / 75) * 100)}%` }} /></div>
            </div>

            {cart.items.map((item) => (
              <article className="cart-item" key={item.id}>
                <Link to={`/product/${item.product.id}`} className="cart-item__image">
                  <ProductImage src={item.product.image} alt={item.product.name} />
                </Link>
                <div className="cart-item__body">
                  <div className="cart-item__top">
                    <div>
                      <span className="cart-item__category">{item.product.category}</span>
                      <Link to={`/product/${item.product.id}`} className="cart-item__name">{item.product.name}</Link>
                      <span className="cart-item__stock">{item.product.stock > 0 ? 'In stock' : 'Out of stock'} · {money(item.product.price)} each</span>
                    </div>
                    <span className="cart-item__total">{money(item.line_total)}</span>
                  </div>
                  <div className="cart-item__actions">
                    <div className="quantity-stepper quantity-stepper--small">
                      <button disabled={busy === item.id || item.quantity <= 1} onClick={() => changeQuantity(item.id, item.quantity - 1)} aria-label="Decrease quantity"><Minus size={13} /></button>
                      <span>{busy === item.id ? '…' : item.quantity}</span>
                      <button disabled={busy === item.id || item.quantity >= item.product.stock} onClick={() => changeQuantity(item.id, item.quantity + 1)} aria-label="Increase quantity"><Plus size={13} /></button>
                    </div>
                    <button className="cart-item__remove" onClick={() => removeItem(item.id, item.product.name)} disabled={busy === item.id}>
                      <Trash2 size={14} /> Remove
                    </button>
                  </div>
                </div>
              </article>
            ))}

            <Link to="/shop" className="cart-continue"><ArrowRight size={14} /> Continue shopping</Link>
          </div>

          <aside className="cart-summary">
            <div className="cart-summary__head">
              <h2>Order summary</h2>
              <span>Step 1 of 3</span>
            </div>
            <div className="cart-summary__rows">
              <div><span>Subtotal</span><span>{money(cart.subtotal)}</span></div>
              <div><span>Delivery</span><span>Complimentary</span></div>
              <div className="cart-summary__note"><span>Taxes</span><span>Included</span></div>
            </div>
            <div className="cart-summary__total"><span>Total</span><strong>{money(cart.subtotal)}</strong></div>
            <Link to="/checkout" className="button button--dark button--full">
              Continue to checkout <ArrowRight size={16} />
            </Link>
            <p className="cart-summary__fineprint">Secure mock checkout · No real payment is taken</p>
            <div className="cart-summary__help">
              <span>Need a hand?</span>
              <a href="mailto:hello@shopwise.example">hello@shopwise.example</a>
            </div>
          </aside>
        </div>
      )}

      {recommendations && recommendations.items.length > 0 && (
        <div className="cart-recommendations">
          <ProductRail
            title="A little more to love"
            subtitle="Pieces we think fit neatly with your bag."
            modelLabel={recommendations.model_label}
            products={recommendations.items.slice(0, 4)}
          />
        </div>
      )}
    </div>
  )
}
