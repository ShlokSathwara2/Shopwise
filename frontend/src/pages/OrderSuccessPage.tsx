import { Link, useParams } from 'react-router-dom'
import { ArrowRight, Check, Package, Truck } from 'lucide-react'
import { api, longDate, money } from '../api'
import { useFetch } from '../hooks/useFetch'
import { ProductImage } from '../components/ProductCard'
import { PageLoader } from '../components/UI'

export function OrderSuccessPage() {
  const { id } = useParams()
  const { data: order, loading } = useFetch(() => api.order(id!), [id])

  if (loading) return <PageLoader label="Confirming your order…" />
  if (!order) {
    return (
      <div className="shell section">
        <div className="empty-state">
          <h3>We couldn’t find that order</h3>
          <p>Check your order history, or get in touch and we’ll help.</p>
          <Link to="/orders" className="button button--dark">View my orders</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="page-success">
      <div className="shell">
        <div className="success-card">
          <div className="success-card__mark"><Check size={28} /></div>
          <span className="eyebrow">Order confirmed</span>
          <h1>Thank you{order.shipping_name ? `, ${order.shipping_name.split(' ')[0]}` : ''}.<br /><em>It’s all yours.</em></h1>
          <p className="success-card__lead">
            A confirmation is on its way to your inbox. Your pieces will be wrapped with care and dispatched within 1–2 working days.
          </p>
          <div className="success-card__reference">
            <div><span>Order reference</span><strong>{order.reference}</strong></div>
            <div><span>Placed</span><strong>{longDate(order.created_at)}</strong></div>
            <div><span>Total</span><strong>{money(order.total)}</strong></div>
          </div>

          <div className="success-card__items">
            {order.items.map((item) => (
              <div className="success-item" key={item.product_id ?? item.product_code}>
                <div className="success-item__image"><ProductImage src={item.image} alt={item.product_name} /></div>
                <div><strong>{item.product_name}</strong><span>Qty {item.quantity}</span></div>
                <span>{money(item.line_total)}</span>
              </div>
            ))}
          </div>

          <div className="success-card__steps">
            <div className="is-done"><span><Check size={14} /></span><div><strong>Order placed</strong><small>{longDate(order.created_at)}</small></div></div>
            <div><span><Package size={14} /></span><div><strong>Being wrapped</strong><small>Within 1–2 working days</small></div></div>
            <div><span><Truck size={14} /></span><div><strong>On its way</strong><small>{order.shipping_city}, {order.shipping_country}</small></div></div>
          </div>

          <div className="success-card__actions">
            <Link to="/orders" className="button button--dark">View my orders</Link>
            <Link to="/shop" className="button button--ghost">Keep exploring <ArrowRight size={15} /></Link>
          </div>
          <p className="success-card__address">Delivering to {order.shipping_address}, {order.shipping_city} {order.shipping_postcode}, {order.shipping_country}</p>
        </div>
      </div>
    </div>
  )
}
