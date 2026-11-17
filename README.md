# Shopwise — Recommendation-Driven E-Commerce Platform

Shopwise is a full-stack MIS capstone build: a real e-commerce storefront, an admin console, and a live recommender API. The shop runs on **1,000 products and 7,463 historical orders** derived from the UCI **Online Retail II** dataset. Five recommenders are trained offline (popularity, TF-IDF content, item-CF, SVD, and a validation-tuned hybrid); the best artifact is served through FastAPI at under **16 ms median** response time.

**Current best model:** Hybrid recommender — content 20%, item-CF 20%, SVD 60% — with category-aware re-ranking and a two-per-category diversity cap.

---

## 1. Demo credentials

| Role | Email | Password |
|---|---|---|
| Shopper | `demo@shopwise.com` | `demo1234` |
| Admin | `admin@shopwise.com` | `admin1234` |

The shopper demo has an existing purchase history, so the home page immediately shows personalised recommendations.

---

## 2. Feature map

### Storefront
- Register / login / protected routes, JWT session persistence
- Browse, search, category filters, price range, in-stock filter, sorting, pagination
- Product detail page with specs, reviews, review submission, “Similar products”, and “Customers also bought”
- Cart with add / update / remove / clear and cross-sell recommendations
- Mock checkout with validated delivery and payment details
- Order confirmation and searchable/filterable order history
- Empty, loading, and 404 states; responsive desktop/mobile layouts

### Admin console
- Full-history KPI dashboard: revenue, orders, units, customers, active products, low stock, events, category mix, daily revenue
- Product CRUD with soft archive/restore (historical orders remain intact)
- Recent 500-order table with search, pagination, and expandable order lines
- Model lab: five-model comparison, precision/recall, coverage, validation tuning grid, generated plots, dataset facts
- One-click model retrain with live artifact reload

### Recommendation API
- `GET /api/recommendations/home` — “Recommended for you”
- `GET /api/recommendations/trending` — popular right now
- `GET /api/recommendations/similar/{id}` — content-based similar products
- `GET /api/recommendations/also-bought/{id}` — item-CF co-purchase products
- `POST /api/events` — view/cart_add/purchase interaction logging
- `POST /api/admin/retrain` — rebuilds all five models and reloads the serving artifact

---

## 3. Architecture

```
shopwise/
├── backend/
│   ├── app/
│   │   ├── main.py                 FastAPI app, static + SPA serving, health
│   │   ├── models.py / schemas.py  SQLAlchemy + Pydantic
│   │   ├── routers/                auth, products, cart, orders, admin, recommendations, events
│   │   ├── ml/
│   │   │   ├── build_dataset.py    UCI Online Retail II -> clean shop dataset
│   │   │   ├── train.py            five models, validation grid, metrics, plots, artifact
│   │   │   └── recommender.py      in-process serving model
│   │   ├── seed.py                 products, users, reviews, orders, interactions
│   │   ├── config.py / security.py / database.py / deps.py
│   ├── artifacts/                  model.joblib, metrics.json, plots
│   ├── data/                       catalog/customers/orders/order_items, UCI raw cache
│   ├── static/                     product/category art, auth/hero art, served plots
│   └── shopwise.db                 seeded SQLite database
├── frontend/
│   ├── src/
│   │   ├── pages/                  storefront and admin pages
│   │   ├── components/ context/ hooks/
│   │   ├── api.ts / types.ts
│   │   └── styles/                 modular CSS
├── reports/assets/                 screenshots, plots, API timing, logs, E2E evidence
└── scripts/                        dataset/artwork generation, E2E, screenshots, logs
```

### Data snapshot
- Raw source: UCI Online Retail II, 775,918 cleaned transaction lines, 5,852 customers, 4,608 products
- Built catalogue: **1,000 products, 13 categories**
- Built history: **750 customers, 7,463 orders, 139,381 order lines, $2,013,661.88 revenue**
- Seeded shop DB: 1,000 products, 751 accounts (750 shoppers + admin), 3,955 reviews, 43,385 interaction events
- Historical dates: 2025-03-24 to 2026-11-04

---

## 4. Model results

Evaluation split: per-customer temporal holdout (latest 20% of distinct products for test; preceding 20% for validation). The hybrid weights were selected on validation and reported on the test split.

| Model | Precision@10 | Recall@10 | Hit Rate@10 | NDCG@10 | Coverage@10 |
|---|---:|---:|---:|---:|---:|
| Popularity | 7.43% | 3.99% | 48.00% | 8.18% | 2.80% |
| Content-Based | 8.24% | 5.53% | 45.47% | 9.73% | 65.70% |
| Item-CF | 7.77% | 5.32% | 46.53% | 9.04% | 38.60% |
| SVD (MF) | 9.56% | 5.92% | 52.27% | 11.18% | 34.80% |
| **Hybrid** | **10.89%** | **7.04%** | **56.67%** | **12.40%** | **40.70%** |

Validation-selected weights: **content 0.20 / item-CF 0.20 / SVD 0.60**.

Live API timing (40 samples after warm-up, final trained model):

| Endpoint | Median | p95 |
|---|---:|---:|
| Personalised for-you | 15.41 ms | 51.79 ms |
| Trending | 6.88 ms | 30.09 ms |
| Similar product | 6.42 ms | 29.10 ms |
| Also-bought | 6.22 ms | 28.81 ms |
| Cart | 15.04 ms | 28.61 ms |
| Catalogue list | 4.77 ms | 28.60 ms |
| Search | 6.55 ms | 30.30 ms |
| Product detail | 3.27 ms | 26.09 ms |

Full timings are in `reports/assets/api_benchmark.json`; the chart is `reports/assets/api_response_times.png`.

---

## 5. Run locally

### Requirements
- Python 3.11+
- Node.js 20+
- All Python dependencies are listed in `backend/requirements.txt`.

### 1) Backend
From the **`shopwise/` folder** (not the parent workspace):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The API and built frontend are served at <http://127.0.0.1:8000>. Health check: <http://127.0.0.1:8000/api/health>.

> If launched from the parent workspace, the import may fail with `ModuleNotFoundError: No module named 'backend'`; always launch from `shopwise/`.

### 2) Frontend build (already included)
```powershell
cd frontend
npm install
npm run build
```

For live frontend development:
```powershell
cd frontend
npm run dev
```
Then open the Vite URL (CORS is configured for ports 5173).

### Optional reset
The included `backend/shopwise.db` is already seeded. To rebuild from source data:
```powershell
cd backend
python -m app.seed
```

### Optional model retrain
Either use **Admin → Model → Retrain models**, or:
```powershell
python -c "from backend.app.ml.train import train_pipeline; print(train_pipeline(force=True))"
```

---

## 6. Scripts and quality checks

```powershell
# Browser E2E: public, registration, cart, checkout, admin CRUD, retrain
python scripts/e2e.py

# API latency benchmark only
python scripts/e2e.py --benchmark-only

# TypeScript check
cd frontend
npx tsc --noEmit

# Backend API smoke tests
python -m pytest backend/tests -q
```

Report assets are under `reports/assets/`:
- 46 named UI screenshots (`screenshots/01-home.png` through `29-admin-model-retrained.png`, plus mobile and probe shots)
- Five model plots
- API timing chart and raw benchmark
- E2E result/registration evidence
- Live terminal log screenshot

---

## 7. Notes
- Checkout is deliberately a mock payment flow for the capstone; no real charge occurs.
- Product images are deterministic generated SVGs derived from real product codes/titles.
- Product deletion in admin is a soft archive so historical orders and reports remain accurate.
- `reports/` contains project-management documentation, screenshots, and evidence; the final DOCX/PDF are in `report/`.

---

## 8. Deployment

### Backend on Render

Create a **Web Service** from this repository with:

| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/health` |
| Instance Type | Free |

Environment variables:

```env
PYTHON_VERSION=3.11.9
SHOPWISE_JWT_SECRET=<long-random-string>
SHOPWISE_CORS_ORIGINS=https://<your-vercel-app>.vercel.app
```

Do not set `PORT`; Render provides it. On the free plan the filesystem is ephemeral, so new users/orders reset when the service restarts. The committed `backend/shopwise.db` provides the seeded demo data. For persistent writes, attach a paid disk at `/var/data`, set `SHOPWISE_DATABASE_URL=sqlite:////var/data/shopwise.db`, and use the start command `python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

### Frontend on Vercel

Import the repository with:

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

The frontend uses relative `/api` and `/static` paths, so copy `frontend/vercel.json.example` to `frontend/vercel.json`, replace `YOUR-SERVICE` with the Render hostname, and deploy. The rewrite file also adds the SPA fallback needed for React Router deep links.

Verify `https://<your-app>.vercel.app/api/health` returns the Render health JSON, product images load from `/static/...`, and refreshing `/shop` does not 404.
