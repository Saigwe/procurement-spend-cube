"""Spend classification from free text, scored against PSC-derived categories.

Federal contracts carry a Product/Service Code, so every line already has a category the warehouse trusts.
Client ERP extracts usually do not: a line has only its description. This script hides the PSC and asks how
well the description alone recovers the category:
  - keyword rules: the seeds/keyword_rules.csv taxonomy the dbt model falls back on
  - TF-IDF (word 1-2 grams) + logistic regression
  - hybrid: model, except a keyword rule overrides it when the model is unsure (top probability < 0.5)
Train/test split is grouped by award so modifications of one contract never sit on both sides.
An LLM or embedding classifier is on the roadmap; it needs an API key, so it is not run here.

Usage: python analysis/classify_spend.py --db warehouse/spend.duckdb --out results/classification.md
"""
import argparse
import csv

import duckdb
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit


def keyword_classify(descriptions, rules):
    out = []
    for d in descriptions:
        d = d.lower()
        hits = [r for r in rules if r[0] in d]
        out.append(min(hits, key=lambda r: (r[2], -len(r[0])))[1] if hits else None)
    return out


def metrics(y_true, y_pred, weights):
    y_pred = [p if p is not None else "Unclassified" for p in y_pred]
    correct = np.array([t == p for t, p in zip(y_true, y_pred)])
    return (
        accuracy_score(y_true, y_pred),
        f1_score(y_true, y_pred, average="macro", labels=sorted(set(y_true)), zero_division=0),
        float((correct * weights).sum() / weights.sum()),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="warehouse/spend.duckdb")
    ap.add_argument("--rules", default="dbt/seeds/keyword_rules.csv")
    ap.add_argument("--out", default="results/classification.md")
    args = ap.parse_args()

    con = duckdb.connect(args.db, read_only=True)
    rows = con.sql("""
        select award_id, description, category, abs(amount_usd)
        from gold.fct_spend_line
        where category_source = 'psc code' and description is not null and amount_usd <> 0
    """).fetchall()
    awards = np.array([r[0] for r in rows])
    text = np.array([r[1] for r in rows])
    y = np.array([r[2] for r in rows])
    w = np.array([float(r[3]) for r in rows])
    with open(args.rules, encoding="utf-8") as f:
        rules = [(r["keyword"].lower(), r["category"], int(r["priority"])) for r in csv.DictReader(f)]

    train, test = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42).split(text, y, awards))
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    model = LogisticRegression(max_iter=2000, C=5.0)
    model.fit(vec.fit_transform(text[train]), y[train])

    kw = keyword_classify(text[test], rules)
    proba = model.predict_proba(vec.transform(text[test]))
    ml = list(model.classes_[proba.argmax(axis=1)])
    hybrid = [k if k is not None and p < 0.5 else m for k, m, p in zip(kw, ml, proba.max(axis=1))]
    fired = [i for i, k in enumerate(kw) if k is not None]
    coverage = len(fired) / len(kw)
    rule_precision = sum(kw[i] == y[test][i] for i in fired) / len(fired)

    results = [
        (f"Keyword rules (fire on {coverage:.0%} of lines)", *metrics(y[test], kw, w[test])),
        ("TF-IDF + logistic regression", *metrics(y[test], ml, w[test])),
        ("Hybrid: model, rule overrides when model < 0.5", *metrics(y[test], hybrid, w[test])),
    ]
    lines = [
        "# Spend classification from descriptions vs PSC categories",
        "",
        f"Lines: {len(rows):,} non-zero lines with a PSC category; {len(set(y))} categories. "
        f"Test set: {len(test):,} lines from {len(set(awards[test])):,} awards held out by award.",
        "",
        "| Method | Accuracy | Macro F1 | Spend-weighted accuracy |",
        "|---|---:|---:|---:|",
    ]
    lines += [f"| {m} | {a:.3f} | {f:.3f} | {s:.3f} |" for m, a, f, s in results]
    lines += [
        "",
        f"When a keyword rule fires it is right {rule_precision:.0%} of the time, and even as a tie-breaker for unsure "
        "model predictions they lower accuracy: the trained model should replace the rules for ERP clients. Unmatched keyword lines count as wrong (Unclassified). Spend-weighted accuracy weights each line "
        "by its absolute obligation, which is what a category manager cares about.",
    ]
    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
