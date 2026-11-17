import { Fragment, useMemo, useState } from 'react'
import { ChevronDown, ChevronLeft, ChevronRight, MapPin, Search, Truck, X } from 'lucide-react'
import { api, longDate, money, shortDate } from '../../api'
import { useFetch } from '../../hooks/useFetch'
import { ProductImage } from '../../components/ProductCard'
import { PageLoader } from '../../components/UI'

const PAGE_SIZE = 12

export function AdminOrders() {
  const { data: orders, loading } = useFetch(() => api.adminOrders(500), [])
  const { data: stats } = useFetch(api.adminStats, [])
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [expanded, setExpanded] = useState<number | null>(null)

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase()
    return (orders || []).filter(
      (order) =>
        !query ||
        order.reference.toLowerCase().includes(query) ||
        order.shipping_name.toLowerCase().includes(query) ||
        order.shipping_city.toLowerCase().includes(query),
    )
  }, [orders, search])

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  if (loading || !orders) return <PageLoader label="Loading the order book…" />

  const revenue = stats?.totals.revenue ?? orders.reduce((sum, order) => sum + order.total, 0)
  const units = stats?.totals.units ?? orders.reduce((sum, order) => sum + order.items.reduce((itemSum, item) => itemSum + item.quantity, 0), 0)
  const recent = stats
    ? stats.revenue_by_day.reduce((sum, day) => sum + day.orders, 0)
    : orders.filter((order) => new Date(order.created_at).getTime() > Date.now() - 30 * 24 * 3600 * 1000).length
  const totalOrders = stats?.totals.orders ?? orders.length

  return (
    <div className="admin-page">
      <div className="admin-page__head">
        <div>
          <span className="eyebrow">Order book</span>
          <h1>Orders</h1>
          <p>The real purchase history behind the shop and the recommender. Stats cover the full history; the table shows the latest 500 orders.</p>
        </div>
      </div>

      <div className="admin-mini-stats">
        <div><span>Total orders</span><strong>{totalOrders.toLocaleString()}</strong></div>
        <div><span>Total revenue</span><strong>{money(revenue)}</strong></div>
        <div><span>Units sold</span><strong>{units.toLocaleString()}</strong></div>
        <div><span>Last 30 days</span><strong>{recent.toLocaleString()}</strong></div>
      </div>

      <section className="admin-card">
        <div className="admin-toolbar">
          <div className="admin-search">
            <Search size={16} />
            <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search by reference, customer or city…" />
            {search && <button onClick={() => setSearch('')} aria-label="Clear search"><X size={14} /></button>}
          </div>
          <span className="admin-toolbar__count">{filtered.length} orders</span>
        </div>
        <div className="admin-table-wrap">
          <table className="admin-table admin-table--orders">
            <thead>
              <tr><th>Reference</th><th>Customer</th><th>Delivery</th><th>Items</th><th>Total</th><th>Status</th><th>Placed</th><th /></tr>
            </thead>
            <tbody>
              {visible.map((order) => (
                <Fragment key={order.id}>
                  <tr className={expanded === order.id ? 'is-expanded' : ''}>
                    <td><strong>{order.reference}</strong></td>
                    <td>{order.shipping_name || 'Shopwise customer'}<span className="table-sub">{order.shipping_country}</span></td>
                    <td>{order.shipping_city}<span className="table-sub">{order.shipping_postcode}</span></td>
                    <td>{order.items.reduce((sum, item) => sum + item.quantity, 0)}</td>
                    <td>{money(order.total)}</td>
                    <td><span className={`status-pill status-pill--${order.status.toLowerCase()}`}>{order.status}</span></td>
                    <td>{shortDate(order.created_at)}</td>
                    <td><button className="table-expand" onClick={() => setExpanded(expanded === order.id ? null : order.id)} aria-label="Toggle order details"><ChevronDown size={15} className={expanded === order.id ? 'is-flipped' : ''} /></button></td>
                  </tr>
                  {expanded === order.id && (
                    <tr className="order-expanded-row">
                      <td colSpan={8}>
                        <div className="admin-order-detail">
                          <div className="admin-order-detail__items">
                            {order.items.map((item) => (
                              <div className="admin-order-line" key={`${item.product_id ?? item.product_code}-${item.quantity}-${item.unit_price}`}>
                                <div className="admin-order-line__image"><ProductImage src={item.image} alt={item.product_name} /></div>
                                <div><strong>{item.product_name}</strong><span>{item.product_code} · Qty {item.quantity} · {money(item.unit_price)} each</span></div>
                                <span>{money(item.line_total)}</span>
                              </div>
                            ))}
                          </div>
                          <div className="admin-order-detail__side">
                            <div><MapPin size={15} /><span><strong>Ship to</strong>{order.shipping_name}<br />{order.shipping_address}<br />{order.shipping_city} {order.shipping_postcode}<br />{order.shipping_country}</span></div>
                            <div><Truck size={15} /><span><strong>Placed</strong>{longDate(order.created_at)}<br />{order.payment_method} ending {order.payment_last4}</span></div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
        <div className="admin-pagination">
          <span>Showing {visible.length ? (page - 1) * PAGE_SIZE + 1 : 0}–{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length}</span>
          <div>
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} aria-label="Previous page"><ChevronLeft size={15} /></button>
            <span>{page} / {pages}</span>
            <button disabled={page >= pages} onClick={() => setPage((p) => p + 1)} aria-label="Next page"><ChevronRight size={15} /></button>
          </div>
        </div>
      </section>
    </div>
  )
}
