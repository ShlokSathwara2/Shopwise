import { useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  Database,
  RefreshCw,
  Sparkles,
  Split,
  X,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, shortDate } from '../../api'
import { useFetch } from '../../hooks/useFetch'
import { useToast } from '../../context/ToastContext'
import { PageLoader } from '../../components/UI'

const MODEL_COLOURS: Record<string, string> = {
  Popularity: '#B2A184',
  'Content-Based': '#7E9270',
  'Item-CF': '#5A7D8C',
  'SVD (MF)': '#9C7A98',
  Hybrid: '#C16A47',
}

const tooltipStyle = {
  background: '#fbf8f1',
  border: '1px solid #e2dacb',
  borderRadius: 10,
  fontSize: 12,
  boxShadow: '0 10px 30px rgba(35,48,41,.08)',
}

const pct = (value: number, digits = 1) => `${(value * 100).toFixed(digits)}%`
const ms = (value: number) => `${value < 1 ? value.toFixed(2) : value.toFixed(1)} ms`

function weightLabel(key: string) {
  if (key === 'content_weight') return 'Content'
  if (key === 'item_cf_weight') return 'Item-CF'
  if (key === 'svd_weight') return 'SVD'
  return key
}

export function AdminModel() {
  const { push } = useToast()
  const { data, loading, error, reload } = useFetch(api.adminMetrics, [])
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [retraining, setRetraining] = useState(false)
  const [retrainNote, setRetrainNote] = useState('')

  const comparison = useMemo(() => {
    if (!data) return []
    return Object.entries(data.models).map(([name, score]) => ({
      name,
      'NDCG@10': Number((score['ndcg@10'] * 100).toFixed(2)),
      'Hit rate@10': Number((score['hit_rate@10'] * 100).toFixed(2)),
      'Precision@10': Number((score['precision@10'] * 100).toFixed(2)),
      'Recall@10': Number((score['recall@10'] * 100).toFixed(2)),
      coverage: Number((score['coverage@10'] * 100).toFixed(2)),
    }))
  }, [data])

  const precisionRecall = useMemo(() => {
    if (!data) return []
    return Object.entries(data.models).map(([name, score]) => ({
      name,
      '@5 precision': Number((score['precision@5'] * 100).toFixed(2)),
      '@10 precision': Number((score['precision@10'] * 100).toFixed(2)),
      '@5 recall': Number((score['recall@5'] * 100).toFixed(2)),
      '@10 recall': Number((score['recall@10'] * 100).toFixed(2)),
    }))
  }, [data])

  const tuning = useMemo(() => {
    if (!data) return []
    return data.validation.grid_best_per_alpha.map((point) => ({
      name: `${Math.round(point.content_weight * 100)}/${Math.round(point.item_cf_weight * 100)}/${Math.round(point.svd_weight * 100)}`,
      content: Math.round(point.content_weight * 100),
      'NDCG@10': Number((point['ndcg@10'] * 100).toFixed(2)),
      'Hit rate@10': Number((point['hit_rate@10'] * 100).toFixed(2)),
    }))
  }, [data])

  if (loading || !data) return <PageLoader label="Reading the model card…" />
  if (error) {
    return (
      <div className="admin-error">
        <AlertTriangle size={20} />
        <p>{error}</p>
        <button onClick={reload} className="button button--dark button--small">Retry</button>
      </div>
    )
  }

  const modelNames = Object.keys(data.models)
  const best = data.models[data.best_model] || data.models.Hybrid || data.models[modelNames[0]]
  const selected = data.validation.selected
  const dataset = data.dataset

  const retrain = async () => {
    setRetraining(true)
    setRetrainNote('')
    try {
      const result = await api.adminRetrain()
      setConfirmOpen(false)
      setRetrainNote(result.message)
      push(result.message, 'success')
      reload()
    } catch (err) {
      push(err instanceof Error ? err.message : 'Retraining failed. Check the API log.', 'error')
    } finally {
      setRetraining(false)
    }
  }

  return (
    <div className="admin-page">
      <div className="admin-page__head">
        <div>
          <span className="eyebrow">Machine learning</span>
          <h1>Model laboratory</h1>
          <p>Five recommenders, one time-aware evaluation and the hybrid that serves every Shopwise rail.</p>
        </div>
        <div className="admin-page__actions">
          <span className="status-live"><span /> Serving live</span>
          <button className="button button--dark button--small" onClick={() => setConfirmOpen(true)}>
            <RefreshCw size={15} /> Retrain models
          </button>
        </div>
      </div>

      {retrainNote && <div className="admin-inline-note"><CheckCircle2 size={16} /><span>{retrainNote}</span></div>}

      <div className="model-hero-grid">
        <section className="model-hero">
          <div className="model-hero__top">
            <span className="model-hero__icon"><BrainCircuit size={24} /></span>
            <span className="model-hero__badge"><Sparkles size={13} /> Winning model</span>
          </div>
          <span className="eyebrow eyebrow--light">Live recommendation strategy</span>
          <h2>{data.best_model}</h2>
          <p>{best.description}</p>
          <div className="model-hero__metrics">
            <div><strong>{pct(best['ndcg@10'])}</strong><span>NDCG@10</span></div>
            <div><strong>{pct(best['hit_rate@10'])}</strong><span>Hit rate@10</span></div>
            <div><strong>{pct(best['precision@10'], 2)}</strong><span>Precision@10</span></div>
            <div><strong>{pct(best['coverage@10'])}</strong><span>Coverage@10</span></div>
          </div>
          <div className="model-hero__footer">
            <span><Clock3 size={14} /> {ms(best.offline_ms_per_user)} per user offline</span>
            <span><Activity size={14} /> Trained {shortDate(data.trained_at)}</span>
          </div>
        </section>

        <section className="admin-card admin-card--chart model-chart">
          <div className="admin-card__head">
            <div><span className="eyebrow">Model comparison</span><h2>Ranking quality at K = 10</h2></div>
            <span className="admin-card__meta">{modelNames.length} models</span>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={272}>
              <BarChart data={comparison} margin={{ top: 6, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 6" stroke="#e9e2d5" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#6e6c60' }} axisLine={false} tickLine={false} interval={0} />
                <YAxis tick={{ fontSize: 10, fill: '#8b8578' }} axisLine={false} tickLine={false} tickFormatter={(value) => `${value}%`} />
                <Tooltip contentStyle={tooltipStyle} formatter={(value: number, name: string) => [`${value}%`, name]} />
                <Legend iconType="circle" iconSize={7} wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                <Bar dataKey="NDCG@10" fill="#C16A47" radius={[4, 4, 0, 0]} barSize={15} />
                <Bar dataKey="Hit rate@10" fill="#7E9270" radius={[4, 4, 0, 0]} barSize={15} />
                <Bar dataKey="Precision@10" fill="#D2A13F" radius={[4, 4, 0, 0]} barSize={15} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <div className="admin-grid admin-grid--two">
        <section className="admin-card admin-card--chart">
          <div className="admin-card__head">
            <div><span className="eyebrow">Precision / recall</span><h2>Relevance at K = 5 and K = 10</h2></div>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={precisionRecall} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 6" stroke="#e9e2d5" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#6e6c60' }} axisLine={false} tickLine={false} interval={0} />
                <YAxis tick={{ fontSize: 10, fill: '#8b8578' }} axisLine={false} tickLine={false} tickFormatter={(value) => `${value}%`} />
                <Tooltip contentStyle={tooltipStyle} formatter={(value: number, name: string) => [`${value}%`, name]} />
                <Legend iconType="circle" iconSize={7} wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                <Line type="monotone" dataKey="@5 precision" stroke="#C16A47" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="@10 precision" stroke="#D2A13F" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 3 }} />
                <Line type="monotone" dataKey="@5 recall" stroke="#7E9270" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="@10 recall" stroke="#5A7D8C" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="admin-card">
          <div className="admin-card__head">
            <div><span className="eyebrow">Validation tuning</span><h2>Choosing the hybrid blend</h2></div>
            <span className="admin-card__meta">{data.validation.validation_users} users</span>
          </div>
          <div className="weight-row">
            {(['content_weight', 'item_cf_weight', 'svd_weight'] as const).map((key) => (
              <div className="weight-card" key={key}>
                <span>{weightLabel(key)}</span>
                <strong>{Math.round(selected[key] * 100)}%</strong>
                <div><span style={{ width: `${selected[key] * 100}%` }} /></div>
              </div>
            ))}
          </div>
          <div className="tuning-table">
            <div className="tuning-table__head"><span>Content / CF / SVD</span><span>NDCG@10</span><span>Hit@10</span></div>
            {data.validation.grid_top5.slice(0, 4).map((point) => (
              <div className="tuning-table__row" key={`${point.content_weight}-${point.item_cf_weight}`}>
                <span>{Math.round(point.content_weight * 100)} / {Math.round(point.item_cf_weight * 100)} / {Math.round(point.svd_weight * 100)}</span>
                <strong>{pct(point['ndcg@10'], 2)}</strong>
                <span>{pct(point['hit_rate@10'])}</span>
              </div>
            ))}
          </div>
          <p className="admin-muted">Weights are selected by validation NDCG@10, then the winning blend is evaluated once on the untouched test split.</p>
        </section>
      </div>

      <section className="admin-card">
        <div className="admin-card__head">
          <div><span className="eyebrow">Leaderboard</span><h2>Every model, side by side</h2></div>
          <span className="admin-card__meta">750 test users · last-item split</span>
        </div>
        <div className="admin-table-wrap">
          <table className="admin-table admin-table--models">
            <thead>
              <tr><th>Model</th><th>Precision@10</th><th>Recall@10</th><th>Hit rate@10</th><th>NDCG@10</th><th>Coverage@10</th><th>Latency / user</th><th>Parameters</th></tr>
            </thead>
            <tbody>
              {modelNames.map((name) => {
                const score = data.models[name]
                const isBest = name === data.best_model
                return (
                  <tr key={name} className={isBest ? 'is-best-model' : ''}>
                    <td>
                      <div className="model-name-cell">
                        <span className="model-swatch" style={{ background: MODEL_COLOURS[name] || '#B2A184' }} />
                        <div><strong>{name}</strong>{isBest && <span className="best-tag">Serving</span>}</div>
                      </div>
                    </td>
                    <td>{pct(score['precision@10'], 2)}</td>
                    <td>{pct(score['recall@10'], 2)}</td>
                    <td>{pct(score['hit_rate@10'])}</td>
                    <td><strong>{pct(score['ndcg@10'], 2)}</strong></td>
                    <td>{pct(score['coverage@10'])}</td>
                    <td>{ms(score.offline_ms_per_user)}</td>
                    <td>
                      <div className="param-chips">
                        {Object.entries(score.params || {}).slice(0, 3).map(([key, value]) => (
                          <span key={key}>{key.replace(/_/g, ' ')}: {Array.isArray(value) ? `${value.length} values` : String(value)}</span>
                        ))}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <p className="admin-muted admin-muted--pad">Offline latency is the average scoring time per customer, excluding network and database hydration. Live API timings are shown on each recommendation rail.</p>
      </section>

      <div className="admin-grid admin-grid--two">
        <section className="admin-card">
          <div className="admin-card__head">
            <div><span className="eyebrow">Data foundation</span><h2>The interaction dataset</h2></div>
            <Database size={18} className="admin-card__icon" />
          </div>
          <div className="data-facts">
            <div><span>Source</span><strong>{data.source.name}</strong></div>
            <div><span>Raw transaction lines</span><strong>{data.source.raw_lines.toLocaleString()}</strong></div>
            <div><span>Catalog after curation</span><strong>{dataset.catalog_products.toLocaleString()} products</strong></div>
            <div><span>Customers</span><strong>{dataset.customers.toLocaleString()}</strong></div>
            <div><span>Purchase lines</span><strong>{dataset.purchase_lines.toLocaleString()}</strong></div>
            <div><span>Unique user–item pairs</span><strong>{dataset.unique_user_product_pairs.toLocaleString()}</strong></div>
            <div><span>Train pairs</span><strong>{dataset.train_pairs.toLocaleString()}</strong></div>
            <div><span>Validation / test pairs</span><strong>{dataset.validation_pairs.toLocaleString()} / {dataset.test_pairs.toLocaleString()}</strong></div>
            <div><span>Matrix sparsity</span><strong>{pct(dataset.sparsity)}</strong></div>
            <div><span>Avg. test items per customer</span><strong>{dataset.avg_test_items_per_customer}</strong></div>
          </div>
          <div className="admin-note"><Split size={15} /><span>{dataset.split_method}. No future purchases leak into training.</span></div>
        </section>

        <section className="admin-card">
          <div className="admin-card__head">
            <div><span className="eyebrow">Serving notes</span><h2>From signal to storefront</h2></div>
            <BarChart3 size={18} className="admin-card__icon" />
          </div>
          <div className="pipeline-list">
            <div><span>01</span><p><strong>User profile</strong>Purchases, views and cart additions are weighted and sent to the hybrid scorer.</p></div>
            <div><span>02</span><p><strong>Candidate blend</strong>TF-IDF content, item-to-item cosine and SVD scores are min-max normalised and blended.</p></div>
            <div><span>03</span><p><strong>Business rules</strong>Cart and purchased items are excluded, categories are re-ranked and no single edit fills the rail.</p></div>
            <div><span>04</span><p><strong>API response</strong>Hydrated products return with strategy and timing metadata for the interface.</p></div>
          </div>
          <div className="api-endpoints">
            <code>GET /api/recommendations/home</code>
            <code>GET /api/recommendations/similar/:id</code>
            <code>GET /api/recommendations/also-bought/:id</code>
            <code>POST /api/admin/retrain</code>
          </div>
        </section>
      </div>

      <section className="admin-card">
        <div className="admin-card__head">
          <div><span className="eyebrow">Generated by the training pipeline</span><h2>Evaluation figures</h2></div>
          <span className="admin-card__meta">Saved to backend / artifacts / plots</span>
        </div>
        <div className="plot-grid">
          {[
            { file: 'model_comparison.png', title: 'Model comparison', text: 'NDCG, hit rate and precision across all five recommenders.' },
            { file: 'precision_recall_at_k.png', title: 'Precision & recall', text: 'Relevance at K = 5 and K = 10 on the held-out test set.' },
            { file: 'coverage.png', title: 'Catalogue coverage', text: 'How much of the 1,000-product catalogue each model reaches.' },
            { file: 'response_times.png', title: 'Scoring time', text: 'Offline milliseconds per customer for each model.' },
          ].map((plot) => (
            <figure className="plot-card" key={plot.file}>
              <img src={`/static/plots/${plot.file}?v=${encodeURIComponent(data.trained_at)}`} alt={plot.title} loading="lazy" />
              <figcaption><strong>{plot.title}</strong><span>{plot.text}</span></figcaption>
            </figure>
          ))}
        </div>
      </section>

      <p className="admin-footnote">
        Training run completed in {data.training_seconds.toFixed(1)} s · best model selected on validation, reported on the test split · retraining rebuilds the artifact without interrupting live traffic.
      </p>

      {confirmOpen && (
        <div className="modal">
          <div className="modal__backdrop" onClick={() => !retraining && setConfirmOpen(false)} />
          <div className="modal__panel modal__panel--confirm">
            <span className="modal__warning"><RefreshCw size={20} /></span>
            <h2>Retrain the recommender?</h2>
            <p>
              The pipeline will rebuild all five models from the interaction history, retune the hybrid weights and replace
              the serving artifact. The shop stays online; this normally takes under a minute.
            </p>
            <div className="retrain-detail"><Clock3 size={14} /> Last trained {shortDate(data.trained_at)} · {data.training_seconds.toFixed(1)} s</div>
            <div className="modal__actions">
              <button className="button button--ghost" onClick={() => setConfirmOpen(false)} disabled={retraining}>Not now</button>
              <button className="button button--dark" onClick={retrain} disabled={retraining}>
                {retraining ? <span className="btn-spinner" /> : <RefreshCw size={15} />} {retraining ? 'Training five models…' : 'Start retraining'}
              </button>
            </div>
            {retraining && <p className="retrain-progress">Fitting TF-IDF, item-CF, SVD and validation grid…</p>}
          </div>
        </div>
      )}
    </div>
  )
}
