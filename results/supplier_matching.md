# Supplier matching against UEI ground truth

Records: 11,097 distinct (UEI, raw name) pairs covering 10,373 UEIs. 703 UEIs were typed under more than one raw name (up to 3).

| Method | Precision | Recall | F1 | Clusters |
|---|---:|---:|---:|---:|
| Normalised name, exact (baseline) | 0.634 | 0.773 | 0.696 | 10,349 |
| Fuzzy token_sort_ratio >= 95 | 0.629 | 0.784 | 0.698 | 10,330 |
| Fuzzy token_sort_ratio >= 90 | 0.623 | 0.816 | 0.707 | 10,292 |
| Fuzzy token_sort_ratio >= 85 | 0.564 | 0.827 | 0.671 | 10,226 |

Parent rollup (dim_supplier): 10,373 UEIs roll up into 10,180 parents; 106 parents have more than one child entity (largest: 23). 40 UEIs changed parent during the year and count under each parent they reported.

Pairwise scores: a pair of records is a true match when both carry the same UEI. Precision falls below 1 when different legal entities share a name (franchisees, joint ventures, regional subsidiaries), which is why the warehouse keys suppliers on UEI and uses name matching only for client extracts that have no registry ID.
