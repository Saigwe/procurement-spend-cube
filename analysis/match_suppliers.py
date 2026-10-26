"""Supplier entity resolution, scored against UEI ground truth.

Each record is a distinct (recipient_uei, recipient_name_raw) pair as typed on the contract action.
Records sharing a UEI are the same legal entity, so the UEI is the answer key for name matching:
  - baseline: exact match on a normalised name (uppercase, no punctuation, no legal suffixes)
  - fuzzy:    rapidfuzz token_sort_ratio within blocks of the same first 4 normalised characters,
              clustered with union-find, at several thresholds
Scores are pairwise precision / recall / F1 over record pairs.

Usage: python analysis/match_suppliers.py --db warehouse/spend.duckdb --out results/supplier_matching.md
"""
import argparse
import re
import time
from collections import Counter, defaultdict

import duckdb
from rapidfuzz import fuzz, process

SUFFIXES = {"INC", "LLC", "CORP", "CO", "LTD", "LP", "LLP", "CORPORATION", "INCORPORATED", "COMPANY", "THE", "PLLC", "PC"}


def normalise(name: str) -> str:
    tokens = re.sub(r"[^A-Z0-9 ]", " ", name.upper().replace("&", " AND ")).split()
    return " ".join(t for t in tokens if t not in SUFFIXES)


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, i):
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, a, b):
        self.parent[self.find(a)] = self.find(b)


def pairs(labels):
    return sum(c * (c - 1) // 2 for c in Counter(labels).values())


def score(pred, truth):
    tp = pairs(list(zip(pred, truth)))
    p_pairs, t_pairs = pairs(pred), pairs(truth)
    precision = tp / p_pairs if p_pairs else 1.0
    recall = tp / t_pairs if t_pairs else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1, len(set(pred))


def fuzzy_clusters(norm, threshold):
    uf = UnionFind(len(norm))
    first = {}
    for i, n in enumerate(norm):  # identical normalised names always merge
        if n in first:
            uf.union(i, first[n])
        else:
            first[n] = i
    blocks = defaultdict(list)
    for n, i in first.items():
        blocks[n[:4]].append(i)
    for idx in blocks.values():
        if len(idx) < 2:
            continue
        names = [norm[i] for i in idx]
        sim = process.cdist(names, names, scorer=fuzz.token_sort_ratio, score_cutoff=threshold, workers=-1)
        for a, b in zip(*sim.nonzero()):
            if a < b:
                uf.union(idx[a], idx[b])
    return [uf.find(i) for i in range(len(norm))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="warehouse/spend.duckdb")
    ap.add_argument("--out", default="results/supplier_matching.md")
    args = ap.parse_args()

    con = duckdb.connect(args.db, read_only=True)
    rows = con.sql("""
        select distinct recipient_uei, recipient_name_raw
        from bronze.contract_transactions
        where recipient_uei is not null and recipient_name_raw is not null
    """).fetchall()
    truth = [r[0] for r in rows]
    norm = [normalise(r[1]) for r in rows]
    raw_variants = con.sql("""
        select count(*) filter (where n > 1), max(n) from (
            select recipient_uei, count(distinct recipient_name_raw) n
            from bronze.contract_transactions where recipient_uei is not null group by 1)
    """).fetchone()
    parents = con.sql("""
        select count(*), count(*) filter (where child_entities > 1), max(child_entities),
               (select count(distinct supplier_id) from gold.fct_spend_line),
               (select count(*) from (select supplier_id from gold.fct_spend_line
                                      group by 1 having count(distinct parent_supplier_id) > 1))
        from gold.dim_supplier
    """).fetchone()

    results = [("Normalised name, exact (baseline)", *score(norm, truth))]
    for t in (95, 90, 85):
        start = time.time()
        results.append((f"Fuzzy token_sort_ratio >= {t}", *score(fuzzy_clusters(norm, t), truth)))
        print(f"threshold {t}: {time.time() - start:.1f}s")

    lines = [
        "# Supplier matching against UEI ground truth",
        "",
        f"Records: {len(rows):,} distinct (UEI, raw name) pairs covering {len(set(truth)):,} UEIs. "
        f"{raw_variants[0]:,} UEIs were typed under more than one raw name (up to {raw_variants[1]}).",
        "",
        "| Method | Precision | Recall | F1 | Clusters |",
        "|---|---:|---:|---:|---:|",
    ]
    lines += [f"| {m} | {p:.3f} | {r:.3f} | {f:.3f} | {c:,} |" for m, p, r, f, c in results]
    lines += [
        "",
        f"Parent rollup (dim_supplier): {parents[3]:,} UEIs roll up into {parents[0]:,} parents; "
        f"{parents[1]:,} parents have more than one child entity (largest: {parents[2]}). "
        f"{parents[4]} UEIs changed parent during the year and count under each parent they reported.",
        "",
        "Pairwise scores: a pair of records is a true match when both carry the same UEI. "
        "Precision falls below 1 when different legal entities share a name (franchisees, joint ventures, "
        "regional subsidiaries), which is why the warehouse keys suppliers on UEI and uses name matching "
        "only for client extracts that have no registry ID.",
    ]
    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
