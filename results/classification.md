# Spend classification from descriptions vs PSC categories

Lines: 31,067 non-zero lines with a PSC category; 11 categories. Test set: 7,773 lines from 6,404 awards held out by award.

| Method | Accuracy | Macro F1 | Spend-weighted accuracy |
|---|---:|---:|---:|
| Keyword rules (fire on 39% of lines) | 0.226 | 0.297 | 0.163 |
| TF-IDF + logistic regression | 0.745 | 0.698 | 0.639 |
| Hybrid: model, rule overrides when model < 0.5 | 0.738 | 0.678 | 0.560 |

When a keyword rule fires it is right 58% of the time, and even as a tie-breaker for unsure model predictions they lower accuracy: the trained model should replace the rules for ERP clients. Unmatched keyword lines count as wrong (Unclassified). Spend-weighted accuracy weights each line by its absolute obligation, which is what a category manager cares about.
