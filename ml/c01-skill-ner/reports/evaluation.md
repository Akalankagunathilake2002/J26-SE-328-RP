# C01 skill extraction: evaluation

Generated 2026-10-18T11:54:56+00:00 by `src/evaluate.py`. All numbers are measured; nothing is estimated.

Scoring: character spans after trimming punctuation and bullets. **Exact** = same start and end; **partial** = any overlap (precision counts predicted spans that overlap a gold span, recall counts gold spans that overlap a prediction). SKILL and KNOWLEDGE are merged into one label. F1 95% CI: 1000 bootstrap resamples of the documents (seed 42).

## Models

| Model | Trained | Minutes | Device | Validation (SkillSpan) |
|---|---|--:|---|---|
| spaCy NER 0.1.0 | 2026-10-18T10:59:01+00:00 | 8.9 | cpu | exact span F1 0.450 (two labels) |
| JobBERT NER 0.1.0 | 2026-10-18T11:10:09+00:00 | 41.0 | mps | exact span F1 0.563 (two labels) |

## 1. SkillSpan test split (checks that training worked)

3569 sentences, 2259 gold spans.

| Method | Predicted | Exact P | Exact R | Exact F1 (95% CI) | Partial P | Partial R | Partial F1 (95% CI) |
|---|--:|--:|--:|--:|--:|--:|--:|
| Lexicon (baseline) | 1283 | 0.331 | 0.188 | 0.240 (0.215–0.263) | 0.599 | 0.325 | 0.421 (0.395–0.446) |
| spaCy NER 0.1.0 | 1923 | 0.517 | 0.440 | 0.475 (0.450–0.504) | 0.765 | 0.701 | 0.731 (0.713–0.750) |
| JobBERT NER 0.1.0 | 2582 | 0.537 | 0.614 | 0.573 (0.550–0.596) | 0.838 | 0.907 | 0.871 (0.859–0.885) |

812 test sentences also appear word for word in the training split (101 of the gold spans are in them). Without those sentences (2757 sentences, 2158 gold spans):

| Method | Predicted | Exact P | Exact R | Exact F1 (95% CI) | Partial P | Partial R | Partial F1 (95% CI) |
|---|--:|--:|--:|--:|--:|--:|--:|
| Lexicon (baseline) | 1182 | 0.341 | 0.187 | 0.241 (0.217–0.265) | 0.612 | 0.320 | 0.420 (0.395–0.446) |
| spaCy NER 0.1.0 | 1829 | 0.505 | 0.428 | 0.463 (0.435–0.489) | 0.758 | 0.692 | 0.724 (0.704–0.743) |
| JobBERT NER 0.1.0 | 2490 | 0.528 | 0.609 | 0.565 (0.540–0.589) | 0.835 | 0.908 | 0.870 (0.856–0.884) |

The lexicon was not built for these (mostly international tech) postings; it is shown for reference.

## 2. topjobs test set: lexicon vs NER (main result)

**Not measured yet:** waiting for the hand-labelled test set (`data/topjobs_test/labelled.json`; see LABELLING.md).

## 5. SSKS match of extracted skills

SSKS: http://127.0.0.1:8005/ssks, snapshot v20261018-3ce7a25c856b (1842 skills, 3361 verified skill aliases, 3 domains). Only exact and verified-alias matches count.
Lexicon coverage: 66 of 145 lexicon skills (46%) have an SSKS ID through their name or a verified alias.

Extracted mentions on the SkillSpan test set:

| Method | Mentions | Exact | Alias | Fuzzy only | Unmatched |
|---|--:|--:|--:|--:|--:|
| Lexicon (baseline) | 1283 | 19% | 6% | 11% | 64% |
| spaCy NER 0.1.0 | 1923 | 10% | 2% | 6% | 83% |
| JobBERT NER 0.1.0 | 2582 | 8% | 2% | 7% | 83% |
