import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Boxes,
  BrainCircuit,
  CircleDollarSign,
  Eye,
  MousePointerClick,
  Package,
  ReceiptText,
  RefreshCw,
  ShoppingBag,
  Users,
} from 'lucide-react'
import { api, money, shortDate } from '../../api'
import { useAuth } from '../../context/AuthContext'
import { useFetch } from '../../hooks/useFetch'
import { PageLoader } from '../../components/UI'

const CHART_COLOURS = ['#C16A47', '#7E9270', '#D2A13F', '#5A7D8C', '#9C7A98', '#B2A184', '#6E7F6A']

const tooltipStyle = {
  background: '#fbf8f1',
  border: '1px solid #e2dacb',
  borderRadius: 10,
  fontSize: 12,
  boxShadow: '0 10px 30px rgba(35,48,41,.08)',
}

export function AdminDashboard() {
  const { user } = useAuth()
  const { data, loading, error, reload } = useFetch(api.adminStats, [])
  const greet = new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 18 ? 'Good afternoon' : 'Good evening'

  const categoryData = useMemo(() => (data?.revenue_by_category || []).slice(0, 7), [data])
  const revenueData = useMemo(() => (data?.revenue_by_day || []).map((row) => ({ ...row, label: row.date.slice(5).replace('-', '/') })), [data])

  if (loading || !data) return <PageLoader label="Pulling together the numbers…" />
  if (error) return <div className="admin-error"><AlertTriangle size={20} /><p>{error}</p><button onClick={reload} className="button button--dark button--small">Retry</button></div>

  const { totals, model } = data
  const hybrid = model.metrics?.Hybrid
  const kpis = [
    { label: 'Revenue', value: money(totals.revenue), icon: CircleDollarSign, detail: 'Across all historical orders', tone: 'terracotta' },
    { label: 'Orders', value: totals.orders.toLocaleString(), icon: ReceiptText, detail: 'Real UCI-derived baskets', tone: 'sage' },
    { label: 'Customers', value: totals.customers.toLocaleString(), icon: Users, detail: 'With a seeded account', tone: 'ochre' },
    { label: 'Average order', value: money(totals.avg_order), icon: ShoppingBag, detail: 'Basket value', tone: 'blue' },
  ]

  return (
    <div className="admin-page">
      <div className="admin-page__head">
        <div>
          <span className="eyebrow">Overview · {shortDate(new Date().toISOString())}</span>
          <h1>{greet}, {user?.name.split(' ')[0]}.</h1>
          <p>Here’s how the shop, the customers and the recommender are doing.</p>
        </div>
        <div className="admin-page__actions">
          <button className="button button--ghost button--small" onClick={reload}><RefreshCw size={14} /> Refresh</button>
          <Link to="/admin/model" className="button button--dark button--small"><BrainCircuit size={15} /> Model lab</Link>
        </div>
      </div>

      <div className="kpi-grid">
        {kpis.map((kpi) => (
          <article className={`kpi-card kpi-card--${kpi.tone}`} key={kpi.label}>
            <div className="kpi-card__top"><span>{kpi.label}</span><span className="kpi-card__icon"><kpi.icon size={18} /></span></div>
            <strong>{kpi.value}</strong>
            <p>{kpi.detail}</p>
            <div className="kpi-card__spark"><span /><span /><span /><span /><span /></div>
          </article>
        ))}
      </div>

      <div className="admin-grid admin-grid--main">
        <section className="admin-card admin-card--chart">
          <div className="admin-card__head">
            <div><span className="eyebrow">Sales pulse</span><h2>Revenue over time</h2></div>
            <span className="admin-card__meta">Last 30 days</span>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={revenueData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#C16A47" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#C16A47" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 6" stroke="#e9e2d5" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#8b8578' }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10, fill: '#8b8578' }} axisLine={false} tickLine={false} tickFormatter={(value) => `$${Math.round(value / 1000)}k`} width={38} />
                <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [money(Number(value)), 'Revenue']} />
                <Area type="monotone" dataKey="revenue" stroke="#C16A47" strokeWidth={2.2} fill="url(#revenueFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="admin-card">
          <div className="admin-card__head">
            <div><span className="eyebrow">Category mix</span><h2>Revenue by edit</h2></div>
            <Link to="/admin/products" className="admin-card__link">Products <ArrowUpRight size={13} /></Link>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={categoryData} layout="vertical" margin={{ top: 4, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 6" stroke="#e9e2d5" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: '#8b8578' }} axisLine={false} tickLine={false} tickFormatter={(value) => `$${Math.round(value / 1000)}k`} />
                <YAxis type="category" dataKey="category" tick={{ fontSize: 10, fill: '#454637' }} width={112} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [money(Number(value)), 'Revenue']} />
                <Bar dataKey="revenue" radius={[0, 5, 5, 0]} barSize={13}>
                  {categoryData.map((_entry, index) => <Cell key={index} fill={CHART_COLOURS[index % CHART_COLOURS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <div className="admin-grid admin-grid--three">
        <section className="admin-card">
          <div className="admin-card__head">
            <div><span className="eyebrow">Top sellers</span><h2>Most wanted</h2></div>
            <Link to="/admin/products" className="admin-card__link">All <ArrowUpRight size={13} /></Link>
          </div>
          <div className="top-products">
            {data.top_products.slice(0, 5).map((product, index) => (
              <div className="top-product" key={product.id}>
                <span className="top-product__rank">{String(index + 1).padStart(2, '0')}</span>
                <img src={product.image} alt="" />
                <div><strong>{product.name}</strong><span>{product.category} · {product.units.toLocaleString()} units</span></div>
                <span>{money(product.revenue)}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="admin-card">
          <div className="admin-card__head">
            <div><span className="eyebrow">Engagement</span><h2>Interaction stream</h2></div>
          </div>
          <div className="event-stats">
            <div><span className="event-stats__icon event-stats__icon--view"><Eye size={17} /></span><div><strong>{(data.events.view || 0).toLocaleString()}</strong><span>Product views</span></div></div>
            <div><span className="event-stats__icon event-stats__icon--cart"><ShoppingBag size={17} /></span><div><strong>{(data.events.cart_add || 0).toLocaleString()}</strong><span>Add to bag</span></div></div>
            <div><span className="event-stats__icon event-stats__icon--buy"><MousePointerClick size={17} /></span><div><strong>{(data.events.purchase || 0).toLocaleString()}</strong><span>Purchases</span></div></div>
          </div>
          <div className="event-bar">
            <span className="event-bar__view" style={{ flex: data.events.view || 1 }} />
            <span className="event-bar__cart" style={{ flex: data.events.cart_add || 1 }} />
            <span className="event-bar__buy" style={{ flex: data.events.purchase || 1 }} />
          </div>
          <div className="admin-note"><Boxes size={15} /><span>Every view, cart add and purchase feeds your account’s recommendation profile.</span></div>
          <div className="stock-alert"><AlertTriangle size={16} /><div><strong>{totals.low_stock} products low on stock</strong><span>Under 25 units · replenish in Products</span></div><Link to="/admin/products">Review</Link></div>
        </section>

        <section className="admin-card admin-card--model">
          <div className="admin-card__head">
            <div><span className="eyebrow">Recommender health</span><h2>{model.best_model || 'Hybrid'} model</h2></div>
            <span className="status-live"><span /> Live</span>
          </div>
          {hybrid ? (
            <>
              <div className="model-stat"><span>NDCG@10</span><strong>{(hybrid['ndcg@10'] * 100).toFixed(1)}%</strong><small>Ranking quality</small></div>
              <div className="model-stat-row">
                <div><span>Hit rate</span><strong>{(hybrid['hit_rate@10'] * 100).toFixed(1)}%</strong></div>
                <div><span>Precision@10</span><strong>{(hybrid['precision@10'] * 100).toFixed(2)}%</strong></div>
              </div>
              <div className="mini-bars">
                {Object.entries(model.metrics || {}).map(([name, score]) => (
                  <div className="mini-bar" key={name}>
                    <span>{name}</span>
                    <div><span style={{ width: `${Math.min(100, score['ndcg@10'] * 700)}%` }} className={name === 'Hybrid' ? 'is-best' : ''} /></div>
                    <strong>{score['ndcg@10'].toFixed(3)}</strong>
                  </div>
                ))}
              </div>
              <Link to="/admin/model" className="button button--outline button--small button--full">Open model lab <ArrowRight size={14} /></Link>
            </>
          ) : <p className="admin-muted">Train the models to see metrics.</p>}
        </section>
      </div>

      <section className="admin-card">
        <div className="admin-card__head">
          <div><span className="eyebrow">Latest activity</span><h2>Recent orders</h2></div>
          <Link to="/admin/orders" className="admin-card__link">View all orders <ArrowUpRight size={13} /></Link>
        </div>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead><tr><th>Reference</th><th>Customer</th><th>Items</th><th>Total</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>
              {data.recent_orders.map((order) => (
                <tr key={order.id}>
                  <td><strong>{order.reference}</strong></td>
                  <td>Shopwise customer</td>
                  <td>{order.items}</td>
                  <td>{money(order.total)}</td>
                  <td><span className={`status-pill status-pill--${order.status.toLowerCase()}`}>{order.status}</span></td>
                  <td>{shortDate(order.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="admin-footnote">
        <Package size={14} /> Live data from the Shopwise SQLite database · {totals.products} active products · {totals.orders.toLocaleString()} orders
      </div>
    </div>
  )
}
