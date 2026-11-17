"""Data preparation for the offline recommender experiments.

Interactions come straight from the shop's order tables, so the model is trained
on exactly what the API serves. Each customer's distinct products are ordered by
their last purchase date; the most recent 20% is held out for testing and the
preceding 20% for validation. This is a per-user temporal holdout.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Order, OrderItem, Product


@dataclass
class TrainingData:
    catalog: pd.DataFrame
    pairs: pd.DataFrame
    train_pairs: pd.DataFrame
    val_pairs: pd.DataFrame
    test_pairs: pd.DataFrame
    product_ids: list[int]
    user_ids: list[int]
    product_index: dict[int, int]
    user_index: dict[int, int]
    X_train: csr_matrix
    X_train_binary: csr_matrix
    X_full: csr_matrix
    X_full_binary: csr_matrix
    train_seen: dict[int, set[int]]
    val_relevant: dict[int, set[int]]
    test_relevant: dict[int, set[int]]
    stats: dict = field(default_factory=dict)


def load_training_data(session: Session, test_fraction: float = 0.2) -> TrainingData:
    catalog = pd.read_sql(
        select(
            Product.id,
            Product.name,
            Product.description,
            Product.category,
            Product.material,
            Product.colour,
            Product.price,
            Product.popularity,
        ).where(Product.is_active.is_(True)),
        session.bind,
    ).rename(columns={"id": "product_id"})

    purchases = pd.read_sql(
        select(
            OrderItem.product_id,
            Order.user_id,
            OrderItem.quantity,
            Order.created_at,
            Order.id.label("order_id"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(Product.is_active.is_(True)),
        session.bind,
    )
    purchases["created_at"] = pd.to_datetime(purchases["created_at"])

    # Keep only products in the active catalog; count unique order lines and units.
    purchases = purchases[purchases["product_id"].isin(catalog["product_id"])]
    pairs = (
        purchases.groupby(["user_id", "product_id"], as_index=False)
        .agg(
            purchase_count=("order_id", "nunique"),
            units=("quantity", "sum"),
            last_purchase=("created_at", "max"),
            first_purchase=("created_at", "min"),
        )
        .reset_index(drop=True)
    )

    product_ids = sorted(catalog["product_id"].astype(int).tolist())
    user_ids = sorted(pairs["user_id"].astype(int).unique().tolist())
    product_index = {pid: i for i, pid in enumerate(product_ids)}
    user_index = {uid: i for i, uid in enumerate(user_ids)}

    train_records, val_records, test_records = [], [], []
    train_seen: dict[int, set[int]] = {uid: set() for uid in user_ids}
    val_relevant: dict[int, set[int]] = {uid: set() for uid in user_ids}
    test_relevant: dict[int, set[int]] = {uid: set() for uid in user_ids}

    for uid, group in pairs.groupby("user_id"):
        group = group.sort_values(["last_purchase", "product_id"], ascending=[False, True])
        n = len(group)
        if n < 5:
            train = group
            test = group.iloc[0:0]
            val = group.iloc[0:0]
        else:
            n_test = max(1, int(round(n * test_fraction)))
            n_val = max(1, int(round(n * test_fraction))) if n >= 10 else 0
            test = group.iloc[:n_test]
            val = group.iloc[n_test : n_test + n_val]
            train = group.iloc[n_test + n_val :]

        train_records.append(train)
        val_records.append(val)
        test_records.append(test)
        train_seen[int(uid)] = set(train["product_id"].astype(int))
        val_relevant[int(uid)] = set(val["product_id"].astype(int))
        test_relevant[int(uid)] = set(test["product_id"].astype(int))

    train_pairs = pd.concat(train_records, ignore_index=True)
    val_pairs = pd.concat(val_records, ignore_index=True)
    test_pairs = pd.concat(test_records, ignore_index=True)

    def make_matrix(frame: pd.DataFrame, weighted: bool = True, binary: bool = False) -> csr_matrix:
        rows = frame["user_id"].map(user_index).to_numpy()
        cols = frame["product_id"].map(product_index).to_numpy()
        values = np.log1p(frame["purchase_count"].to_numpy(dtype=float)) if weighted else np.ones(len(frame))
        if binary:
            values = np.ones(len(frame))
        shape = (len(user_ids), len(product_ids))
        return csr_matrix((values.astype(np.float32), (rows, cols)), shape=shape, dtype=np.float32)

    X_train = make_matrix(train_pairs, weighted=True)
    X_train_binary = make_matrix(train_pairs, weighted=True, binary=True)
    X_full = make_matrix(pairs, weighted=True)
    X_full_binary = make_matrix(pairs, weighted=True, binary=True)

    n_possible = len(user_ids) * len(product_ids)
    stats = {
        "catalog_products": int(len(product_ids)),
        "customers": int(len(user_ids)),
        "purchase_lines": int(len(purchases)),
        "unique_user_product_pairs": int(len(pairs)),
        "sale_orders": int(purchases["order_id"].nunique()),
        "train_pairs": int(len(train_pairs)),
        "validation_pairs": int(len(val_pairs)),
        "test_pairs": int(len(test_pairs)),
        "evaluation_users": int((test_pairs.groupby("user_id").size() > 0).sum()) if len(test_pairs) else 0,
        "validation_users": int((val_pairs.groupby("user_id").size() > 0).sum()) if len(val_pairs) else 0,
        "sparsity": round(1 - len(pairs) / n_possible, 4),
        "avg_distinct_products_per_customer": round(len(pairs) / max(1, len(user_ids)), 1),
        "avg_test_items_per_customer": round(len(test_pairs) / max(1, len(test_pairs["user_id"].unique())), 1) if len(test_pairs) else 0,
        "split_method": "Per-customer temporal holdout - latest 20% of distinct products for test, preceding 20% for validation",
        "date_range": [str(purchases["created_at"].min()), str(purchases["created_at"].max())],
        "test_fraction": test_fraction,
    }

    return TrainingData(
        catalog=catalog.reset_index(drop=True),
        pairs=pairs,
        train_pairs=train_pairs.reset_index(drop=True),
        val_pairs=val_pairs.reset_index(drop=True),
        test_pairs=test_pairs.reset_index(drop=True),
        product_ids=product_ids,
        user_ids=user_ids,
        product_index=product_index,
        user_index=user_index,
        X_train=X_train,
        X_train_binary=X_train_binary,
        X_full=X_full,
        X_full_binary=X_full_binary,
        train_seen=train_seen,
        val_relevant=val_relevant,
        test_relevant=test_relevant,
        stats=stats,
    )
