import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, MapPin, Package, Receipt, Truck } from 'lucide-react'
import { api, longDate, money } from '../api'
import { useAuth } from '../context/AuthContext'
import { useFetch } from '../hooks/useFetch'
import { ProductImage } from '../components/ProductCard'
import { Breadcrumbs, EmptyState, PageLoader } from '../components/UI'

export function OrdersPage() {
  const { user } = useAuth()
  const { data: orders, loading, error } = useFetch(api.orders, [user?.id])
  const [filter, setFilter] = useState('All')

  if (loading) return <PageLoader label="Finding your orders…" />
  if (error) return <div className="shell section"><EmptyState title="We couldn’t load your orders" text={error} action={<button className="button button--dark" onClick={() => window.location.reload()}>Try again</button>} /></div>

  const list = orders || []
  const filters = ['All', 'Confirmed', 'Delivered']
  const filtered = filter === 'All' ? list : list.filter((order) => order.status === filter)
  const spend = list.reduce((sum, order) => sum + order.total, 0)

  return (
    <div className="shell section page-orders">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'My account' }, { label: 'Orders' }]} />
      <div className="orders-head">
        <div>
          <span className="eyebrow">Your account</span>
          <h1>Order history</h1>
          <p>Every considered piece, every moment it arrived.</p>
        </div>
        <div className="orders-stats">
          <div><span>Orders</span><strong>{list.length}</strong></div>
          <div><span>Lifetime spend</span><strong>{money(spend)}</strong></div>
          <div><span>Since</span><strong>{list.length ? new Date(list[list.length - 1].created_at).getFullYear() : new Date().getFullYear()}</strong></div>
        </div>
      </div>

      {list.length === 0 ? (
        <EmptyState
          title="Your story starts with one piece"
          text="When you place your first order, it will live here — ready to revisit, reorder or track."
          action={<Link to="/shop" className="button button--dark">Find something lovely</Link>}
        />
      ) : (
        <>
          <div className="orders-filter">
            {filters.map((status) => <button key={status} className={filter === status ? 'is-active' : ''} onClick={() => setFilter(status)}>{status} <span>{status === 'All' ? list.length : list.filter((o) => o.status === status).length}</span></button>)}
          </div>
          <div className="orders-list">
            {filtered.map((order) => {
              const itemCount = order.items.reduce((sum, item) => sum + item.quantity, 0)
              return (
                <article className="order-card" key={order.id}>
                  <div className="order-card__top">
                    <div className="order-card__identity">
                      <span className="order-card__icon"><Receipt size={18} /></span>
                      <div><strong>{order.reference}</strong><span>{longDate(order.created_at)}</span></div>
                    </div>
                    <div className="order-card__summary">
                      <div><span>Status</span><span className={`status-pill status-pill--${order.status.toLowerCase()}`}>{order.status}</span></div>
                      <div><span>Total</span><strong>{money(order.total)}</strong></div>
                    </div>
                  </div>
                  <div className="order-card__body">
                    <div className="order-card__thumbs">
                      {order.items.slice(0, 4).map((item) => (
                        <div className="order-thumb" key={item.product_id ?? item.product_code}>
                          <ProductImage src={item.image} alt={item.product_name} />
                        </div>
                      ))}
                      {order.items.length > 4 && <span className="order-thumb order-thumb--more">+{order.items.length - 4}</span>}
                    </div>
                    <p className="order-card__items">
                      {order.items.slice(0, 2).map((item) => item.product_name).join(', ')}
                      {order.items.length > 2 ? ` and ${order.items.length - 2} more` : ''}
                      <span>{itemCount} items · {order.shipping_city}</span>
                    </p>
                    <span className="order-card__delivery"><Truck size={15} /> {order.status === 'Delivered' ? 'Delivered' : 'Preparing for dispatch'}</span>
                  </div>
                  <details className="order-details">
                    <summary>View order details <ChevronDown size={15} /></summary>
                    <div className="order-details__grid">
                      <div className="order-details__items">
                        {order.items.map((item) => (
                          <div className="order-detail-item" key={item.product_id ?? item.product_code}>
                            <div className="order-detail-item__image"><ProductImage src={item.image} alt={item.product_name} /></div>
                            <div><strong>{item.product_name}</strong><span>{item.product_code} · Qty {item.quantity} · {money(item.unit_price)} each</span></div>
                            <span>{money(item.line_total)}</span>
                          </div>
                        ))}
                      </div>
                      <div className="order-details__side">
                        <div><MapPin size={15} /><span><strong>Delivery address</strong>{order.shipping_name}<br />{order.shipping_address}<br />{order.shipping_city}, {order.shipping_postcode}<br />{order.shipping_country}</span></div>
                        <div><Package size={15} /><span><strong>Payment</strong>{order.payment_method} ending {order.payment_last4}<br />Total {money(order.total)}</span></div>
                      </div>
                    </div>
                  </details>
                </article>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
