# Shopwise Project Management Pack

Project: **Recommendation-Driven E-Commerce Platform Using Machine Learning**
Team role mapping: product owner, full-stack engineer, data/ML engineer, QA engineer.

---

## 1. Product goal and scope

Build a working recommendation-driven e-commerce platform where a shopper can browse a real product catalogue, receive personalised recommendations, add to bag, check out, and view orders; an admin can manage catalogue data and monitor model quality. The recommender must be evaluated against popularity, content, collaborative, and hybrid baselines and served through an API.

### In scope
- Real catalogue/history dataset derived from UCI Online Retail II
- Storefront, auth, cart, checkout, orders, reviews
- Admin analytics, product CRUD/archive, order inspection, model retraining
- Five recommenders and validation-selected hybrid model
- API latency and offline metric evaluation
- Report evidence: UI screenshots, plots, terminal logs, E2E/test results

### Out of scope
- Live payment processing
- Multi-seller marketplace
- Real-time streaming training

---

## 2. Sprint plan

### Sprint 1 — Foundation and storefront
**Goal:** Ship a browsable shop with auth, catalogue, cart, checkout, and order history.

| Status | Item |
|---|---|
| To do | Set up FastAPI/SQLAlchemy schema and React/Vite shell |
| In progress | Product catalogue from UCI data |
| To do | Auth, cart, checkout, order history |
| Blocked | None |

**Sprint 1 outcome:** Database schema, 1,000-product catalogue, 750-customer history, auth/cart/checkout API, storefront pages, and seed data.

**User stories**

| ID | As a… | I want… | So that… | Acceptance criteria |
|---|---|---|---|---|
| US-101 | Shopper | register and sign in | my bag/orders are saved | Registration creates a JWT session; reload keeps session; protected routes work |
| US-102 | Shopper | browse/filter/sort products | find relevant pieces quickly | Category/price/in-stock filters, sorting, and pagination update the grid |
| US-103 | Shopper | open a product detail page | judge quality before buying | Images, specs, reviews, stock and price render; view events are logged |
| US-104 | Shopper | maintain a bag | buy several pieces together | Add/update/remove/clear update quantity and totals |
| US-105 | Shopper | mock-check out | complete a purchase | Validated form creates an order and clears bag |
| US-106 | Shopper | see my orders | track purchases | History shows latest order first with status/items/address |

### Sprint 2 — Recommender and admin
**Goal:** Add admin controls, analytics, and evaluated recommendation models.

| Status | Item |
|---|---|
| To do | Interaction logging and review data |
| In progress | Five-model offline evaluation |
| To do | Admin dashboard/product CRUD |
| Blocked | None |

**Sprint 2 outcome:** Five trained recommenders, validation-tuned hybrid, API rails on home/product/cart, admin analytics and product archive/restore.

**User stories**

| ID | As a… | I want… | So that… | Acceptance criteria |
|---|---|---|---|---|
| US-201 | Shopper | see “Recommended for you” | find products for my taste | Signed-in home rail is personalised and shows model latency |
| US-202 | Shopper | see “Customers also bought” | discover compatible items | Item-CF rail appears on product and cart pages |
| US-203 | Shopper | see “Similar products” | compare alternatives | Content-based rail appears on product pages |
| US-204 | Admin | monitor sales/model KPIs | make stock decisions | Full-history revenue, orders, units, category mix, events |
| US-205 | Admin | create/edit/archive/restore products | keep catalogue accurate | CRUD modal validates and archive preserves history |
| US-206 | Admin | compare models | select the best approach | Table/plot shows Precision/Recall/Hit Rate/NDCG/Coverage |

### Sprint 3 — Hardening, evidence, and report
**Goal:** QA the full journey, benchmark the API, and assemble the final report.

| Status | Item |
|---|---|
| To do | Full browser E2E and admin retrain |
| In progress | API latency benchmark |
| To do | Final screenshots and DOCX report |
| Blocked | None |

**Sprint 3 outcome:** 32-step E2E pass, 46 report screenshots, 8-endpoint benchmark, terminal log capture, README/project docs, and DOCX report.

**User stories**

| ID | As a… | I want… | So that… | Acceptance criteria |
|---|---|---|---|---|
| US-301 | QA | run an end-to-end shopper journey | prove the shop works | Register, browse, review, cart, checkout, order history all pass |
| US-302 | Admin | retrain models from UI | keep recommendations fresh | Retrain rebuilds models and reloads serving artifact |
| US-303 | Reviewer | see model quality evidence | assess method | Metrics, split, tuning grid, plots and dataset facts are visible |
| US-304 | Reviewer | inspect response timing | assess deployment readiness | Median/p95 API timings captured over 40 samples |
| US-305 | Student | submit final report | meet MIS requirements | DOCX includes sprints, boards, screenshots, results, tests and appendix |

---

## 3. Board snapshots

### Sprint 1 board — “Foundation & storefront”
| Backlog | Ready | In progress | Review | Done |
|---|---|---|---|---|
| Product detail reviews | Catalogue filters | Checkout flow | Auth session persistence | FastAPI/React skeleton, schema, catalogue seed, cart, orders |

### Sprint 2 board — “Recommender & admin”
| Backlog | Ready | In progress | Review | Done |
|---|---|---|---|---|
| Model lab plots | Admin order inspector | Hybrid tuning | Recommendation diversity | Interaction events, five models, API rails, dashboard, product CRUD |

### Sprint 3 board — “Hardening & evidence”
| Backlog | Ready | In progress | Review | Done |
|---|---|---|---|---|
| Appendix code | Report formatting | Latency chart | Final screenshots | E2E, retrain, benchmark, README, project pack |

---

## 4. Test cases and evidence

| ID | Test | Steps | Expected | Status |
|---|---|---|---|---|
| TC-01 | Registration | Register unique email | Session created, profile initials visible | Pass |
| TC-02 | Session persistence | Reload authenticated page | Profile/menu remains | Pass |
| TC-03 | Category filter | Shop → category | URL updates and grid filters | Pass |
| TC-04 | Search | Search “bowl” | Matching products shown | Pass |
| TC-05 | Empty search | Search invalid string | Empty state with clear filters | Pass |
| TC-06 | Product rails | Product 291 | Similar + also-bought rails render | Pass |
| TC-07 | Review submission | Submit review on product 291 | Review appears immediately | Pass |
| TC-08 | Cart add/update/remove | Add product 4, increase, remove | Bag returns to three seeded lines | Pass |
| TC-09 | Checkout validation | Fill delivery, use test card | Checkout completes, order created | Pass |
| TC-10 | Order history | Open orders | Latest order first, reference `SW-2026-F8A503` | Pass |
| TC-11 | Empty bag | After checkout | Empty state shown | Pass |
| TC-12 | Admin dashboard | Admin login | Full-history KPIs and charts render | Pass |
| TC-13 | Product create | Add “QA Stoneware Vase” | Product appears in search/table | Pass |
| TC-14 | Product edit | Change price/stock | Table reflects `$69.00`, stock 40 | Pass |
| TC-15 | Soft archive | Remove product | Status archived, historical orders retained | Pass |
| TC-16 | Restore | Restore archived product | Status live | Pass |
| TC-17 | Admin orders | Expand first row | Items/address visible | Pass |
| TC-18 | Model lab | Open model page | Five models, tuning grid, plots render | Pass |
| TC-19 | Retrain | Start retrain | Success message, metrics/plots refresh | Pass |
| TC-20 | 404 state | Visit unknown route | Styled 404 page with actions | Pass |
| TC-21 | Mobile layout | 390px viewport | Home/shop responsive without console errors | Pass |
| TC-22 | API timing | Benchmark 8 endpoints | Median/p95 recorded, recommendations under 16 ms median | Pass |

E2E evidence: `reports/assets/e2e_results.json`.
Terminal evidence: `reports/assets/terminal_log.png` / `terminal_log.txt`.
Screenshots: `reports/assets/screenshots/`.

---

## 5. Risk register

| Risk | Impact | Mitigation | Status |
|---|---|---|---|
| Sparse interaction matrix hurts CF | Low metrics | Use weighted hybrid + content + popularity fallback | Addressed |
| Wholesale-style product names | Poor content similarity | Title-weighted TF-IDF, category re-ranking/diversity | Addressed |
| Admin hard-delete breaks history | Data loss | Soft archive/restore only | Addressed |
| Slow recommendations under load | Poor UX | Precomputed artifact + in-process scoring; benchmark shows 4–11 ms median | Addressed |
| Mock payment may look incomplete | Reviewer doubt | Explicit banner, test card helper, order creation demonstrated | Accepted for capstone |

---

## 6. Deliverable checklist

- [x] Storefront + auth + cart + checkout + orders
- [x] Product details + reviews
- [x] Search/filter/sort/pagination
- [x] Recommendation rails on home/product/cart
- [x] Five-model offline comparison and hybrid serving
- [x] Admin dashboard/product CRUD/orders/model retrain
- [x] Dataset built from UCI Online Retail II
- [x] E2E browser validation
- [x] API latency benchmark
- [x] Backend API smoke tests
- [x] Screenshots, plots, terminal log
- [x] README and project-management pack
- [x] Final DOCX report (`report/21MGO103T_MANAGEMENT_INFORMATION_SYSTEM_PROJECT_REPORT_FINAL.docx`)
- [x] Render/Vercel deployment configuration and notes
