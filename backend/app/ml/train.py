"""Train, compare and persist the Shopwise recommendation models.

Run from the shopwise directory:
    python -m backend.app.ml.train
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from ..config import ARTIFACTS_DIR, DATA_DIR
from ..database import SessionLocal
from .data import TrainingData, load_training_data

PLOT_DIR = ARTIFACTS_DIR / "plots"
PALETTE = {
    "ink": "#233029",
    "cream": "#FAF6ED",
    "terracotta": "#C16A47",
    "sage": "#7E9270",
    "ochre": "#D2A13F",
    "blue": "#5A7D8C",
    "muted": "#8F8A7C",
}
MODEL_COLOURS = {
    "Popularity": PALETTE["muted"],
    "Content-Based": PALETTE["sage"],
    "Item-CF": PALETTE["ochre"],
    "SVD (MF)": PALETTE["blue"],
    "Hybrid": PALETTE["terracotta"],
}
TRAIN_LOCK = threading.Lock()


def normalise_rows(scores: np.ndarray) -> np.ndarray:
    minima = scores.min(axis=1, keepdims=True)
    maxima = scores.max(axis=1, keepdims=True)
    span = maxima - minima
    span[span == 0] = 1.0
    return (scores - minima) / span


def seen_mask(data: TrainingData) -> np.ndarray:
    mask = np.zeros((len(data.user_ids), len(data.product_ids)), dtype=bool)
    rows = data.train_pairs["user_id"].map(data.user_index).to_numpy()
    cols = data.train_pairs["product_id"].map(data.product_index).to_numpy()
    mask[rows, cols] = True
    return mask


def _is_relevant(relevant: dict[int, set[int]], uid: int, item_ids: np.ndarray) -> set[int]:
    return relevant.get(uid, set())


def evaluate_scores(
    scores: np.ndarray,
    data: TrainingData,
    mask: np.ndarray,
    relevant: dict[int, set[int]],
    k_values: tuple[int, ...] = (5, 10),
    include_users: list[int] | None = None,
) -> dict:
    """Precision/Recall/HitRate/NDCG@K and catalogue coverage."""
    scores = scores.astype(np.float64, copy=True)
    scores[mask] = -np.inf
    max_k = max(k_values)
    top = np.argsort(-scores, axis=1)[:, :max_k]

    user_indices = np.arange(len(data.user_ids))
    eval_mask = np.array([len(relevant.get(uid, set())) > 0 for uid in data.user_ids])
    if include_users is not None:
        wanted = set(include_users)
        eval_mask &= np.array([uid in wanted for uid in data.user_ids])
    eval_indices = user_indices[eval_mask]
    if len(eval_indices) == 0:
        return {}

    metrics: dict[str, float | int] = {"evaluated_users": int(len(eval_indices))}
    all_recommended: dict[int, set[int]] = {k: set() for k in k_values}
    for k in k_values:
        precisions, recalls, hits, ndcgs = [], [], [], []
        for ui in eval_indices:
            uid = data.user_ids[ui]
            rel = relevant.get(uid, set())
            rec_idx = top[ui, :k]
            rec = {data.product_ids[j] for j in rec_idx}
            all_recommended[k].update(rec)
            hit_count = len(rec & rel)
            precisions.append(hit_count / k)
            recalls.append(hit_count / len(rel))
            hits.append(1.0 if hit_count else 0.0)
            dcg = sum(1.0 / np.log2(rank + 2) for rank, j in enumerate(rec_idx) if data.product_ids[j] in rel)
            ideal_hits = min(len(rel), k)
            idcg = sum(1.0 / np.log2(rank + 2) for rank in range(ideal_hits))
            ndcgs.append(dcg / idcg if idcg else 0.0)
        metrics[f"precision@{k}"] = round(float(np.mean(precisions)), 4)
        metrics[f"recall@{k}"] = round(float(np.mean(recalls)), 4)
        metrics[f"hit_rate@{k}"] = round(float(np.mean(hits)), 4)
        metrics[f"ndcg@{k}"] = round(float(np.mean(ndcgs)), 4)
        metrics[f"coverage@{k}"] = round(len(all_recommended[k]) / len(data.product_ids), 4)
    return metrics


def content_text(catalog: pd.DataFrame) -> pd.Series:
    """Title-weighted text so specific product nouns outrank shared copy."""
    return (
        (catalog["name"].fillna("") + " ") * 3
        + catalog["description"].fillna("")
        + " "
        + (catalog["category"].fillna("") + " ") * 2
        + catalog["material"].fillna("")
        + " "
        + catalog["colour"].fillna("")
    )


def build_content_scores(data: TrainingData) -> tuple[np.ndarray, TfidfVectorizer, object, np.ndarray]:
    catalog = data.catalog.set_index("product_id").loc[data.product_ids]
    text = content_text(catalog)
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        max_features=15000,
        sublinear_tf=True,
    )
    item_matrix = vectorizer.fit_transform(text)
    item_matrix = normalize(item_matrix)
    profiles = normalize(data.X_train_binary @ item_matrix)
    scores = (profiles @ item_matrix.T).toarray().astype(np.float32)
    content_sim = (item_matrix @ item_matrix.T).toarray().astype(np.float32)
    np.fill_diagonal(content_sim, 0.0)
    return scores, vectorizer, item_matrix, content_sim


def build_item_cf(data: TrainingData, matrix=None) -> tuple[np.ndarray, np.ndarray]:
    binary = data.X_train_binary if matrix is None else matrix
    item_sim = cosine_similarity(binary.T, dense_output=True).astype(np.float32)
    np.fill_diagonal(item_sim, 0.0)
    scores = np.asarray(binary @ item_sim).astype(np.float32)
    return scores, item_sim


def build_svd(data: TrainingData, rank: int) -> tuple[np.ndarray, TruncatedSVD]:
    svd = TruncatedSVD(n_components=rank, random_state=42, n_iter=7)
    svd.fit(data.X_train)
    scores = svd.inverse_transform(svd.transform(data.X_train)).astype(np.float32)
    return scores, svd


def make_plots(metrics: dict, validation: dict, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_paths = []
    models = [m for m in ["Popularity", "Content-Based", "Item-CF", "SVD (MF)", "Hybrid"] if m in metrics]
    colors = [MODEL_COLOURS[m] for m in models]
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#C9C2B4",
            "axes.labelcolor": PALETTE["ink"],
            "text.color": PALETTE["ink"],
            "xtick.color": PALETTE["ink"],
            "ytick.color": PALETTE["ink"],
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
        }
    )

    # 1. Headline comparison
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1.55, 1]})
    fig.patch.set_facecolor(PALETTE["cream"])
    for ax in axes:
        ax.set_facecolor(PALETTE["cream"])
    x = np.arange(len(models))
    width = 0.36
    ndcg10 = [metrics[m]["ndcg@10"] for m in models]
    recall10 = [metrics[m]["recall@10"] for m in models]
    axes[0].bar(x - width / 2, ndcg10, width, label="NDCG@10", color=colors, edgecolor="none")
    axes[0].bar(x + width / 2, recall10, width, label="Recall@10", color=colors, alpha=0.45, edgecolor="none", hatch="//")
    axes[0].set_xticks(x, [m.replace(" (MF)", "\n(MF)").replace("Content-Based", "Content\nBased") for m in models], fontsize=8.5)
    axes[0].set_ylabel("Score")
    axes[0].set_title("Ranking quality by model (K = 10)")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].grid(axis="y", alpha=0.18)
    axes[0].set_axisbelow(True)
    for i, (a, b) in enumerate(zip(ndcg10, recall10)):
        axes[0].text(i - width / 2, a + 0.002, f"{a:.3f}", ha="center", fontsize=7.3)
        axes[0].text(i + width / 2, b + 0.002, f"{b:.3f}", ha="center", fontsize=7.3)

    hit = [metrics[m]["hit_rate@10"] for m in models]
    axes[1].barh(models[::-1], hit[::-1], color=colors[::-1], height=0.55)
    axes[1].set_xlabel("Hit rate@10")
    axes[1].set_title("Users with at least one hit")
    axes[1].set_xlim(0, 1)
    for i, v in enumerate(hit[::-1]):
        axes[1].text(v + 0.02, i, f"{v:.0%}", va="center", fontsize=8)
    axes[1].grid(axis="x", alpha=0.18)
    axes[1].set_axisbelow(True)
    fig.tight_layout()
    path = output_dir / "model_comparison.png"
    fig.savefig(path, dpi=190, facecolor=fig.get_facecolor())
    plt.close(fig)
    plot_paths.append(str(path))

    # 2. Precision and recall at 5 and 10
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    fig.patch.set_facecolor(PALETTE["cream"])
    for ax, metric_name, title in [
        (axes[0], "precision", "Precision@K"),
        (axes[1], "recall", "Recall@K"),
    ]:
        ax.set_facecolor(PALETTE["cream"])
        for offset, k, alpha in [(-0.19, 5, 0.48), (0.19, 10, 0.95)]:
            vals = [metrics[m][f"{metric_name}@{k}"] for m in models]
            ax.bar(x + offset, vals, 0.36, label=f"K = {k}", color=colors, alpha=alpha, edgecolor="none")
        ax.set_xticks(x, [m.replace(" (MF)", "\n(MF)").replace("Content-Based", "Content\nBased") for m in models], fontsize=8.5)
        ax.set_title(title)
        ax.set_ylabel("Mean score per user")
        ax.legend(frameon=False, fontsize=8)
        ax.grid(axis="y", alpha=0.18)
        ax.set_axisbelow(True)
    fig.tight_layout()
    path = output_dir / "precision_recall_at_k.png"
    fig.savefig(path, dpi=190, facecolor=fig.get_facecolor())
    plt.close(fig)
    plot_paths.append(str(path))

    # 3. Coverage
    fig, ax = plt.subplots(figsize=(8, 4.2))
    fig.patch.set_facecolor(PALETTE["cream"])
    ax.set_facecolor(PALETTE["cream"])
    cov5 = [metrics[m]["coverage@5"] for m in models]
    cov10 = [metrics[m]["coverage@10"] for m in models]
    ax.bar(x - 0.19, cov5, 0.36, label="Coverage@5", color=colors, alpha=0.5, edgecolor="none")
    ax.bar(x + 0.19, cov10, 0.36, label="Coverage@10", color=colors, edgecolor="none")
    ax.set_xticks(x, [m.replace(" (MF)", "\n(MF)").replace("Content-Based", "Content\nBased") for m in models], fontsize=8.5)
    ax.set_ylabel("Share of catalogue recommended")
    ax.set_title("Catalogue coverage")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.18)
    ax.set_axisbelow(True)
    fig.tight_layout()
    path = output_dir / "coverage.png"
    fig.savefig(path, dpi=190, facecolor=fig.get_facecolor())
    plt.close(fig)
    plot_paths.append(str(path))

    # 4. Offline scoring time
    fig, ax = plt.subplots(figsize=(8, 4.0))
    fig.patch.set_facecolor(PALETTE["cream"])
    ax.set_facecolor(PALETTE["cream"])
    times = [metrics[m].get("offline_ms_per_user", 0) for m in models]
    ax.barh(models[::-1], times[::-1], color=colors[::-1], height=0.55)
    ax.set_xlabel("Milliseconds per user (batch scoring)")
    ax.set_title("Offline recommendation generation time")
    for i, v in enumerate(times[::-1]):
        ax.text(v + 0.05, i, f"{v:.2f} ms", va="center", fontsize=8)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
    fig.tight_layout()
    path = output_dir / "response_times.png"
    fig.savefig(path, dpi=190, facecolor=fig.get_facecolor())
    plt.close(fig)
    plot_paths.append(str(path))

    # 5. Hybrid validation curve
    grid = validation.get("grid_best_per_alpha", [])
    if grid:
        fig, ax = plt.subplots(figsize=(8, 4.0))
        fig.patch.set_facecolor(PALETTE["cream"])
        ax.set_facecolor(PALETTE["cream"])
        alphas = [g["content_weight"] for g in grid]
        ndcgs = [g["ndcg@10"] for g in grid]
        ax.plot(alphas, ndcgs, marker="o", color=PALETTE["terracotta"], linewidth=2.2)
        best = validation.get("selected", {})
        ax.scatter([best.get("content_weight", 0.5)], [best.get("ndcg@10", 0)], s=90, color=PALETTE["ink"], zorder=5, label="Selected")
        ax.set_xlabel("Content weight (remainder is collaborative)")
        ax.set_ylabel("Validation NDCG@10")
        ax.set_title("Hybrid weight tuning on the validation split")
        ax.grid(alpha=0.18)
        ax.legend(frameon=False)
        fig.tight_layout()
        path = output_dir / "hybrid_tuning.png"
        fig.savefig(path, dpi=190, facecolor=fig.get_facecolor())
        plt.close(fig)
        plot_paths.append(str(path))
    return plot_paths


def train_pipeline(force: bool = True) -> dict:
    """Train all models, evaluate, tune the hybrid and persist serving artifacts."""
    with TRAIN_LOCK:
        started = time.perf_counter()
        session = SessionLocal()
        try:
            data = load_training_data(session)
        finally:
            session.close()

        print(f"[ml] data: {data.stats}")
        mask = seen_mask(data)
        n_users = len(data.user_ids)
        n_items = len(data.product_ids)

        metrics: dict[str, dict] = {}
        score_matrices: dict[str, np.ndarray] = {}

        # 1. Popularity baseline -------------------------------------------------
        t0 = time.perf_counter()
        popularity_counts = np.asarray(data.X_train_binary.sum(axis=0)).ravel().astype(np.float32)
        pop_scores = np.tile(popularity_counts, (n_users, 1))
        gen_ms = (time.perf_counter() - t0) / n_users * 1000
        metrics["Popularity"] = {
            **evaluate_scores(pop_scores, data, mask, data.test_relevant),
            "offline_ms_per_user": round(gen_ms, 3),
            "description": "Most purchased items ranked by number of unique buyers in the training period.",
            "params": {"signal": "unique buyers", "personalised": False},
        }
        score_matrices["Popularity"] = pop_scores

        # 2. Content-based -------------------------------------------------------
        t0 = time.perf_counter()
        content_scores, vectorizer, item_tfidf, content_sim = build_content_scores(data)
        gen_ms = (time.perf_counter() - t0) / n_users * 1000
        metrics["Content-Based"] = {
            **evaluate_scores(content_scores, data, mask, data.test_relevant),
            "offline_ms_per_user": round(gen_ms, 3),
            "description": "TF-IDF over product title, description and category, scored with cosine similarity to the user's purchase profile.",
            "params": {"features": int(item_tfidf.shape[1]), "ngrams": "1-2", "similarity": "cosine"},
        }
        score_matrices["Content-Based"] = content_scores

        # 3. Item-based collaborative filtering ---------------------------------
        t0 = time.perf_counter()
        cf_scores, item_cf_sim = build_item_cf(data)
        gen_ms = (time.perf_counter() - t0) / n_users * 1000
        metrics["Item-CF"] = {
            **evaluate_scores(cf_scores, data, mask, data.test_relevant),
            "offline_ms_per_user": round(gen_ms, 3),
            "description": "Customers who bought this also bought: item-item cosine similarity over the binary purchase matrix.",
            "params": {"neighbourhood": "all items", "similarity": "cosine"},
        }
        score_matrices["Item-CF"] = cf_scores

        # 4. SVD matrix factorisation -------------------------------------------
        t0 = time.perf_counter()
        svd_candidates = [16, 24, 32, 48]
        svd_validation = []
        best_rank = 32
        best_rank_score = -1.0
        best_svd_scores = None
        best_svd = None
        for rank in svd_candidates:
            rank_scores, rank_model = build_svd(data, rank)
            rank_metrics = evaluate_scores(rank_scores, data, mask, data.val_relevant)
            svd_validation.append({"rank": rank, "ndcg@10": rank_metrics.get("ndcg@10", 0), "hit_rate@10": rank_metrics.get("hit_rate@10", 0)})
            if rank_metrics.get("ndcg@10", 0) > best_rank_score:
                best_rank_score = rank_metrics.get("ndcg@10", 0)
                best_rank = rank
                best_svd_scores = rank_scores
                best_svd = rank_model
        gen_ms = (time.perf_counter() - t0) / n_users * 1000
        metrics["SVD (MF)"] = {
            **evaluate_scores(best_svd_scores, data, mask, data.test_relevant),
            "offline_ms_per_user": round(gen_ms, 3),
            "description": "Truncated SVD on the log-scaled implicit feedback matrix; reconstructs user-item preference scores.",
            "params": {"rank": best_rank, "rank_selection": svd_validation, "random_state": 42},
        }
        score_matrices["SVD (MF)"] = best_svd_scores

        # 5. Hybrid --------------------------------------------------------------
        content_norm = normalise_rows(content_scores)
        cf_norm = normalise_rows(cf_scores)
        svd_norm = normalise_rows(best_svd_scores)
        alphas = [round(a, 2) for a in np.arange(0.10, 0.95, 0.10)]
        betas = [0.25, 0.5, 0.75]
        validation_users = [uid for uid in data.user_ids if data.val_relevant.get(uid)]
        grid_results = []
        best_config = None

        for alpha in alphas:
            best_for_alpha = None
            for beta in betas:
                blend = alpha * content_norm + (1 - alpha) * (beta * cf_norm + (1 - beta) * svd_norm)
                val_metrics = evaluate_scores(blend, data, mask, data.val_relevant, k_values=(10,), include_users=validation_users)
                row = {
                    "content_weight": float(alpha),
                    "item_cf_weight": float(round((1 - alpha) * beta, 4)),
                    "svd_weight": float(round((1 - alpha) * (1 - beta), 4)),
                    "ndcg@10": val_metrics.get("ndcg@10", 0),
                    "hit_rate@10": val_metrics.get("hit_rate@10", 0),
                    "precision@10": val_metrics.get("precision@10", 0),
                }
                grid_results.append(row)
                if best_for_alpha is None or row["ndcg@10"] > best_for_alpha["ndcg@10"]:
                    best_for_alpha = row
                if best_config is None or row["ndcg@10"] > best_config["ndcg@10"]:
                    best_config = row
            # Keep the grid plot readable: one best beta per content weight.
            if best_for_alpha:
                # store separately below
                pass

        best_per_alpha = []
        for alpha in alphas:
            candidates = [r for r in grid_results if r["content_weight"] == alpha]
            best_per_alpha.append(max(candidates, key=lambda r: (r["ndcg@10"], r["hit_rate@10"])))

        alpha = best_config["content_weight"]
        beta = best_config["item_cf_weight"] / max(1e-9, 1 - alpha)
        hybrid_scores = alpha * content_norm + (1 - alpha) * (beta * cf_norm + (1 - beta) * svd_norm)
        metrics["Hybrid"] = {
            **evaluate_scores(hybrid_scores, data, mask, data.test_relevant),
            "offline_ms_per_user": round(metrics["Content-Based"]["offline_ms_per_user"] + metrics["Item-CF"]["offline_ms_per_user"], 3),
            "description": "Weighted blend of content similarity and collaborative signals (item-CF + SVD). Weights selected on the validation split.",
            "params": {
                "content_weight": alpha,
                "item_cf_weight": round((1 - alpha) * beta, 4),
                "svd_weight": round((1 - alpha) * (1 - beta), 4),
                "tuning_metric": "validation NDCG@10",
            },
        }
        score_matrices["Hybrid"] = hybrid_scores

        validation = {
            "selected": {
                "content_weight": alpha,
                "item_cf_weight": round((1 - alpha) * beta, 4),
                "svd_weight": round((1 - alpha) * (1 - beta), 4),
                **{k: best_config[k] for k in ("ndcg@10", "hit_rate@10", "precision@10")},
            },
            "grid_top5": sorted(grid_results, key=lambda r: r["ndcg@10"], reverse=True)[:5],
            "grid_best_per_alpha": best_per_alpha,
            "validation_users": len(validation_users),
            "svd_rank_selection": svd_validation,
        }

        # Persist the final serving model trained on ALL interactions. The
        # evaluation above uses only the training slice, so reported metrics are
        # honest holdout results; the live model gets to use the full history.
        content_full, full_vectorizer, full_item_tfidf, full_content_sim = build_content_scores_full(data)
        cf_full_scores, cf_full_sim = build_item_cf_full(data)
        svd_full = TruncatedSVD(n_components=best_rank, random_state=42, n_iter=7)
        svd_full.fit(data.X_full)
        svd_user_factors = svd_full.transform(data.X_full).astype(np.float32)
        svd_components = svd_full.components_.astype(np.float32)
        popularity_full = np.asarray(data.X_full_binary.sum(axis=0)).ravel().astype(np.float32)
        popularity_order = np.argsort(-popularity_full)

        artifact = {
            "trained_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "alpha": float(alpha),
            "beta": float(beta),
            "item_ids": np.array(data.product_ids, dtype=np.int64),
            "user_ids": np.array(data.user_ids, dtype=np.int64),
            "product_index": data.product_index,
            "user_index": data.user_index,
            "content_vectorizer": full_vectorizer,
            "content_item_matrix": full_item_tfidf,
            "content_sim": full_content_sim,
            "item_cf_sim": cf_full_sim,
            "svd_components": svd_components,
            "svd_user_factors": svd_user_factors,
            "svd_rank": int(best_rank),
            "popularity_scores": popularity_full,
            "popularity_order_ids": np.array([data.product_ids[i] for i in popularity_order], dtype=np.int64),
        }
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(artifact, ARTIFACTS_DIR / "model.joblib", compress=3)

        elapsed = time.perf_counter() - started
        dataset_stats = {}
        dataset_stats_path = DATA_DIR / "dataset_stats.json"
        if dataset_stats_path.exists():
            dataset_stats = json.loads(dataset_stats_path.read_text(encoding="utf-8"))

        output = {
            "trained_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "training_seconds": round(elapsed, 2),
            "best_model": "Hybrid",
            "models": metrics,
            "validation": validation,
            "dataset": data.stats,
            "source": {
                "name": "UCI Online Retail II",
                "url": "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
                "raw_lines": dataset_stats.get("raw_transaction_lines"),
                "raw_customers": dataset_stats.get("raw_customers"),
                "raw_products": dataset_stats.get("raw_products"),
            },
            "plots": {},
        }
        PLOT_DIR.mkdir(parents=True, exist_ok=True)
        output["plots"] = {Path(p).stem: p for p in make_plots(metrics, validation, PLOT_DIR)}
        (ARTIFACTS_DIR / "metrics.json").write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")

        # Keep a tidy copy for the report generator.
        report_assets = ARTIFACTS_DIR.parent.parent / "reports" / "assets"
        report_assets.mkdir(parents=True, exist_ok=True)
        for p in output["plots"].values():
            target = report_assets / Path(p).name
            target.write_bytes(Path(p).read_bytes())

        print("[ml] model comparison (test split)")
        for name in ["Popularity", "Content-Based", "Item-CF", "SVD (MF)", "Hybrid"]:
            m = metrics[name]
            print(
                f"  {name:<14} P@5={m['precision@5']:.4f} P@10={m['precision@10']:.4f} "
                f"R@10={m['recall@10']:.4f} NDCG@10={m['ndcg@10']:.4f} Hit@10={m['hit_rate@10']:.4f} "
                f"Cov@10={m['coverage@10']:.2%}"
            )
        print(f"[ml] hybrid weights: content={alpha:.2f}, item-cf={(1-alpha)*beta:.2f}, svd={(1-alpha)*(1-beta):.2f}")
        print(f"[ml] saved artifacts to {ARTIFACTS_DIR} in {elapsed:.1f}s")
        return output


# Full-data variants used by the serving artifact only.
def build_content_scores_full(data: TrainingData):
    catalog = data.catalog.set_index("product_id").loc[data.product_ids]
    text = content_text(catalog)
    vectorizer = TfidfVectorizer(
        stop_words="english", ngram_range=(1, 2), min_df=1, max_features=15000, sublinear_tf=True
    )
    item_matrix = normalize(vectorizer.fit_transform(text))
    profiles = normalize(data.X_full_binary @ item_matrix)
    scores = (profiles @ item_matrix.T).toarray().astype(np.float32)
    content_sim = (item_matrix @ item_matrix.T).toarray().astype(np.float32)
    np.fill_diagonal(content_sim, 0.0)
    return scores, vectorizer, item_matrix, content_sim


def build_item_cf_full(data: TrainingData):
    item_sim = cosine_similarity(data.X_full_binary.T, dense_output=True).astype(np.float32)
    np.fill_diagonal(item_sim, 0.0)
    scores = np.asarray(data.X_full_binary @ item_sim).astype(np.float32)
    return scores, item_sim


if __name__ == "__main__":
    train_pipeline(force=True)
