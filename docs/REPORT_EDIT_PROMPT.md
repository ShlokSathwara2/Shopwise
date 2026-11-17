# Report Editing Prompt

Use the prompt below with a report editor/AI assistant. Do **not** use it to regenerate application code.

```text
You are editing a formal SRM B.Tech project report. Do NOT rewrite the app or invent content. Use the actual Shopwise project evidence and make the report match the sample report format.

PROJECT / REPORT PATHS
- Report to edit: “PREDICTIVE_ROAD_DEGRADATION_ANALYSIS_USING_IoT_AND_MACHINE_LEARNING_updated.docx”
- Project folder: “shopwise/”
- Format/structure reference: use the headings, front matter, chapter flow, sprint sections, result discussion and appendix layout from the existing sample report.
- Primary project docs:
  - shopwise/README.md
  - shopwise/docs/PROJECT_MANAGEMENT.md
- Evidence:
  - shopwise/reports/assets/e2e_results.json
  - shopwise/reports/assets/api_benchmark.json
  - shopwise/reports/assets/api_response_times.png
  - shopwise/reports/assets/terminal_log.png
  - shopwise/reports/assets/terminal_log.txt
  - shopwise/reports/assets/screenshots/
  - shopwise/reports/assets/model_comparison.png
  - shopwise/reports/assets/precision_recall_at_k.png
  - shopwise/reports/assets/coverage.png
  - shopwise/reports/assets/hybrid_tuning.png
  - shopwise/reports/assets/response_times.png
- Backend metrics:
  - shopwise/backend/artifacts/metrics.json
- Dataset facts:
  - shopwise/backend/data/dataset_stats.json
  - shopwise/backend/data/seed_stats.json

TITLE
Change the report title to:
“RECOMMENDATION-DRIVEN E-COMMERCE PLATFORM USING MACHINE LEARNING”
Keep personal names/reg numbers/supervisor/head/examiner details as placeholders if they are not already correct.

REPORT SCOPE
The report should describe Shopwise: a full-stack e-commerce platform with shopper storefront, auth, cart, mock checkout, order history, reviews, admin dashboard/catalogue CRUD/order inspection, and an API-served machine-learning recommender.

Keep these facts exactly:
- Dataset source: UCI Online Retail II.
- Raw data: 775,918 cleaned transaction lines, 5,852 customers, 4,608 products.
- Built shop dataset: 1,000 products, 13 categories, 750 customers, 7,463 historical orders, 139,381 order lines, $2,013,661.88 revenue.
- Seeded DB also includes 3,955 reviews and 43,385 interaction events.
- Five models: Popularity, TF-IDF Content-Based, Item-CF, SVD, and weighted Hybrid.
- Final serving model: Hybrid.
- Validation-selected weights: content 20%, item-CF 20%, SVD 60%.
- Evaluation split: per-customer temporal holdout; latest 20% of distinct products for test, preceding 20% for validation.
- Final test metrics:
  - Popularity: Precision@10 7.43%, Recall@10 3.99%, Hit Rate@10 48.00%, NDCG@10 8.18%, Coverage@10 2.80%
  - Content-Based: Precision@10 8.24%, Recall@10 5.53%, Hit Rate@10 45.47%, NDCG@10 9.73%, Coverage@10 65.70%
  - Item-CF: Precision@10 7.77%, Recall@10 5.32%, Hit Rate@10 46.53%, NDCG@10 9.04%, Coverage@10 38.60%
  - SVD: Precision@10 9.56%, Recall@10 5.92%, Hit Rate@10 52.27%, NDCG@10 11.18%, Coverage@10 34.80%
  - Hybrid: Precision@10 10.89%, Recall@10 7.04%, Hit Rate@10 56.67%, NDCG@10 12.40%, Coverage@10 40.70%
- Live API timing, 40 samples after warm-up:
  - For-you: median 15.41 ms, p95 51.79 ms
  - Trending: median 6.88 ms, p95 30.09 ms
  - Similar: median 6.42 ms, p95 29.10 ms
  - Also-bought: median 6.22 ms, p95 28.81 ms
  - Cart: median 15.04 ms, p95 28.61 ms
  - Catalogue: median 4.77 ms, p95 28.60 ms
  - Search: median 6.55 ms, p95 30.30 ms
  - Product detail: median 3.27 ms, p95 26.09 ms

REQUIRED STRUCTURE
1. Front matter:
   - Title page
   - Plagiarism declaration
   - Acknowledgements
   - Bonafide certificate
   - Abstract
   - Table of Contents
   - List of Figures
   - List of Tables
   - Abbreviations

2. Chapter 1 — Introduction:
   - Introduction
   - Motivation
   - Problem statement
   - Product vision
   - Product goal
   - Product backlog table
   - Sprint/board screenshot or project-management table
   - Release plan

3. Chapter 2 — Sprint Planning and Execution:
   - Sprint 1: Foundation and storefront
   - Sprint 2: Recommender and admin
   - Sprint 3: Hardening, evidence and report
   For each sprint include:
   - Sprint goal
   - User stories table
   - Functional document/features
   - Architecture/design notes
   - Functional test cases
   - Committed vs completed user stories
   - Sprint retrospective

4. Chapter 3 — Results and Discussion:
   - Project outcomes
   - Dataset construction and statistics
   - Recommender architecture and models
   - Model performance table
   - Model plots
   - API response-time table and chart
   - UI screenshots with captions
   - E2E/testing evidence
   - Live terminal log evidence
   - Limitations

5. Chapter 4 — Conclusion and Future Enhancements

6. Appendix:
   - Sample backend code excerpts
   - Sample recommendation/training code excerpts
   - Sample frontend API/page code excerpt
   - Optional run instructions

SCREENSHOTS TO INCLUDE
Use screenshots from:
shopwise/reports/assets/screenshots/

Include at least:
- 01-home.png
- 02-shop.png
- 03-shop-category.png
- 04-shop-search.png
- 05-shop-empty.png
- 06-product.png
- 07-product-similar.png
- 08-product-also-bought.png
- 09-home-personalized.png
- 10-recommended-for-you.png
- 11-trending-now.png
- 12-product-review-form.png
- 13-product-reviews.png
- 14-cart.png
- 15-cart-recommendations.png
- 16-checkout.png
- 17-order-success.png
- 18-order-history.png
- 19-cart-empty.png
- 20-admin-dashboard.png
- 21-admin-products.png
- 22-admin-product-modal.png
- 23-admin-product-created.png
- 24-admin-delete-modal.png
- 25-admin-product-archived.png
- 26-admin-orders.png
- 27-admin-model.png
- 28-admin-retrain-modal.png
- 29-admin-model-retrained.png
- 22-login.png
- 23-register.png
- 24-not-found.png
- 25-home-mobile.png
- 26-shop-mobile.png
- terminal_log.png

Give every image a numbered caption such as:
“Figure 2.1 — Shopwise storefront homepage”

TABLES TO INCLUDE
- Product backlog
- Sprint 1 user stories
- Sprint 2 user stories
- Sprint 3 user stories
- Sprint features
- Functional test cases
- Committed vs completed user stories
- Dataset statistics
- Model performance comparison
- API latency benchmark
- Risk register / limitations if useful

STYLE RULES
- Formal academic tone.
- No marketing filler.
- Do not claim real payment processing; clearly state checkout is a mock/demo payment.
- Do not invent performance numbers; use the values above.
- Do not fabricate team member names or marks.
- Keep screenshots clear and readable.
- Use numbered figures and tables consistently.
- Add page breaks before major chapters.
- Ensure every figure/table is referenced in the body text.
- Ensure the Table of Contents, List of Figures and List of Tables match the final document.
- Keep the report self-contained and suitable for final submission.

DO NOT
- Do not modify the Shopwise application code.
- Do not delete or regenerate screenshots.
- Do not replace the dataset with another dataset.
- Do not claim Streamlit or a separate dashboard unless it actually exists.
- Do not copy unrelated road-degradation/IoT content into the final report.
- Do not leave sample report project-specific text behind.
```
