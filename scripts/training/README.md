# Answer-scoring model and LLM calibration

Trains the interview's technical-accuracy scorer and compares it with the LLM evaluator on human-graded
answers (Mohler ASAG, CC BY 4.0). Raw data and intermediate files live outside the repo
(`/Volumes/Dilmith Ext/datasets/training`).

```bash
VENV="/Volumes/Dilmith Ext/datasets/train-venv"        # torch, sentence-transformers>=4, datasets, scikit-learn, onnx, onnxruntime
export HF_HOME="/Volumes/Dilmith Ext/hf-cache"
$VENV/bin/python scripts/training/prepare_mohler_splits.py        # split by question: 55 train / 12 valid / 12 test
$VENV/bin/python scripts/training/train_answer_scorer.py          # 3 cross-encoders, best on valid, ONNX int8 export
# Gemma's scores on the balanced subsets (needs the interview container and the local LLM):
for p in valid_llm test_llm; do
  MOHLER_DATA="/Volumes/Dilmith Ext/datasets/training/mohler/$p.jsonl" \
    scripts/datasets/run_mohler_eval.sh --sample all --limit 1000 --modes reference   # copy result to mohler/gemma_$p.json
done
$VENV/bin/python scripts/training/compare_scoring_methods.py      # calibration, blend, selected mode
```

Outputs in `services/interview-service/models/answer_scorer/`: `model.onnx` (int8, 125 MB), `tokenizer.json`,
`metadata.json`, and `scoring_config.json` (isotonic calibration, blend weight, selected mode), read by
`app/services/answer_scorer.py`. Set `SCORING_MODE` to force `llm`, `calibrated`, `trained` or `blend`.

## Results (18 October 2026, 147 test answers from 12 unseen questions)

| Method | Pearson | Spearman | QWK | MAE |
|---|---|---|---|---|
| Gemma 4 E4B (reference answer in prompt) | 0.741 | 0.723 | 0.613 | 0.738 |
| Gemma, isotonic calibration | 0.723 | 0.713 | 0.615 | 0.744 |
| Fine-tuned stsb-roberta-base cross-encoder (int8) | 0.656 | 0.603 | 0.598 | 0.760 |
| **Blend: 0.8 x calibrated Gemma + 0.2 x scorer** (selected on validation) | **0.766** | **0.768** | 0.596 | **0.707** |

Candidates on validation (Pearson / QWK): ms-marco-MiniLM-L6 0.29 / 0.21, stsb-distilroberta 0.45 / 0.47,
stsb-roberta-base 0.58 / 0.56. The blend's gain over Gemma alone is small and not significant at n = 147.
The scorer only applies to technical roles with a reference answer; it can give partial credit to an
off-topic answer in the right subject area, which the 0.2 weight limits.

## Retrieval fine-tuning (18 October 2026, smaller run: 1,000 passages x 3 questions)

Fine-tunes the embedding model `BAAI/bge-small-en-v1.5` (both services) and a cross-encoder re-ranker that
replaces the rule-based scorer in `services/learning-service/app/services/reranker.py`. Work files live in
`/Volumes/Dilmith Ext/datasets/training/retrieval` (`results.json` holds every number below).

```bash
cd "/Volumes/Dilmith Ext/Huggingbay" && ./start-llm.sh            # Gemma on port 8082, for step 1 only
$VENV/bin/python scripts/training/make_retrieval_pairs.py 1000     # 51 min; resumable
kill $(lsof -tiTCP:8082 -sTCP:LISTEN)                              # never train while Gemma runs
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.6 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.5   # fail, don't swap
$VENV/bin/python scripts/training/train_retrieval.py baseline      # 9 min; mines hard negatives
$VENV/bin/python scripts/training/train_retrieval.py embedder      # 10 min training + 17 min evaluation
$VENV/bin/python scripts/training/train_retrieval.py reranker      # 5 min training; ONNX int8 export
$VENV/bin/python scripts/training/train_retrieval.py export        # embedder ONNX, checks with onnxruntime
```

Data: the corpus chunked as ingestion does (25,560 chunks, 1,326 documents), documents split 80/10/10
(seed 7); 1,000 chunks sampled stratified by role/source, 3 Gemma questions each (999 chunks, 2,997
questions: 2,388 train / 270 valid / 339 test). Retrieval is over ALL chunks; only the chunk a question was
written from counts as relevant, so the numbers understate quality (neighbouring chunks often answer too).

| Test (339 questions, unseen documents) | R@1 | R@3 | R@10 | MRR@10 |
|---|---|---|---|---|
| bge-small as deployed before | 0.325 | 0.513 | 0.679 | 0.437 |
| **Fine-tuned bge-small** (ONNX fp32, deployed) | **0.437** | **0.625** | **0.758** | **0.544** |
| Fine-tuned bge-small, ONNX int8 (not deployed) | 0.443 | 0.596 | 0.743 | 0.532 |
| Re-ranking its top 10: rule-based (before) | 0.404 | 0.581 | 0.743 | 0.512 |
| Re-ranking its top 10: ms-marco-MiniLM-L6, not fine-tuned | 0.451 | 0.646 | 0.752 | 0.559 |
| **Re-ranking its top 10: fine-tuned cross-encoder** (int8, deployed) | **0.472** | **0.673** | 0.743 | **0.573** |

Paired bootstrap 95% intervals of the MRR@10 gain: embedder vs before +0.061 to +0.131; cross-encoder vs
the embedder's own order +0.005 to +0.077. The rule-based re-ranker scored below no re-ranking on valid and
test. Embedder: 2 epochs, epoch 1 kept (valid MRR 0.507, tied with epoch 2); int8 lost 0.012 MRR with no
speed gain, so fp32 (127 MB) is deployed. Re-ranker: 9,526 pairs (positive + 3 hard negatives from other
documents per question), 1 epoch; int8 is 22 MB, about 120 ms per query for 10 candidates on CPU.

Notes:
- Plain MultipleNegativesRankingLoss at batch 32 keeps activations for 96 texts of up to 256 tokens (about
  11 GB) and swapped this 16 GB Mac to a stall (65 s/step). `CachedMultipleNegativesRankingLoss`
  (mini-batch 8, same in-batch negatives) runs at about 4 s/step in about 4 GB; it needs eager attention on MPS.
- Hard negatives come only from other documents: neighbouring chunks overlap the positive.
- The questions are Gemma's, about the learning corpus. The interview service uses the same embedder for its
  question bank, which was not evaluated here.

Deployment: `models/embedder` in both services (`LOCAL_EMBEDDING_MODEL=models/embedder`, the new default,
loaded with onnxruntime by `OnnxEmbedder` in `embedding_service.py`: CLS vector, normalised, 384
dimensions; `LOCAL_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5` goes back to fastembed) and `models/reranker` in
the learning service (rule-based scorer as fallback, `rerank_method` in each result). The learning-service
image now copies `models/`. The model files are not in git. After changing the embedder, delete the
`learning_chunks`/`learning_documents` and `interview_chunks`/`interview_documents` rows and restart both
services to re-ingest (same dimension, so it is not automatic). Tests: `tests/test_onnx_embedder.py` (both
services), `tests/test_reranker.py` (learning).

Environment: venv `/Volumes/Dilmith Ext/datasets/train-venv` (torch 2.14, sentence-transformers 6.1),
`HF_HOME=/Volumes/Dilmith Ext/hf-cache`; everything downloads to the external drive. Docker:
`docker compose -p skill-bridge -f infrastructure/docker-compose.yml -f ~/.skillbridge-local/docker-compose.override.yml`.
Do not commit or push. Keep progress checks rare; report at the end of each stage.

## Interview question search with the fine-tuned embedder (22 November 2026)

`eval_interview_retrieval.py` measures the interview service's use of the embedder: query
"<role> <level> <topic>" against the role's bank items (title, topic, question and expected answer, as
`ingest_rubrics.py` embeds them); relevant = same role and topic. 355 bank items, 10 roles, 352 queries.

| Embedder | MRR@10 | Hit@1 | Precision@5 | Level match@5 |
|---|---|---|---|---|
| bge-small-en-v1.5 (original) | 0.846 | 0.776 | 0.190 | 0.187 |
| fine-tuned (`models/embedder`) | 0.838 | 0.767 | 0.188 | 0.185 |

Difference −0.008 MRR, p = 0.41 (paired permutation test): no measurable change either way, so the
fine-tuned model is fine for both services and the interview service gains nothing from it. Almost every topic has a
single question (352 queries for 355 items), so precision@5 can't go much above 0.2. A useful interview test
needs several questions per topic or graded relevance. Results: `/Volumes/Dilmith Ext/datasets/results/interview-retrieval-eval.json`.

## Human grades for non-technical roles (tooling ready, grades needed)

Technical scoring was checked against human graders (Mohler); behavioural and competency answers (HR,
marketing, finance, design, writing) were not, as there is no public graded set. `export_grading_sheet.py
export` writes recent LLM-graded answers of those roles to a CSV with empty human columns; two people grade
independently with the LLM columns hidden; `export_grading_sheet.py score sheet.csv sheet2.csv` gives
human–LLM and human–human agreement (Pearson, Spearman, QWK, MAE). The sheet holds candidate transcripts:
share it only with the graders and delete it afterwards. Aim for 100+ answers across the roles.

## Next: larger retrieval fine-tune (prepared, not run)

The 1,000-passage run used 1,000 of the 4,000+ chunks. A full run needs about 3–4 h of Gemma for the questions
(about 3 per chunk) plus about 1 h of training on this Mac; keep Gemma free of interviews meanwhile.

```bash
"$VENV/bin/python" scripts/training/make_retrieval_pairs.py 4000      # Gemma writes questions (resumable)
"$VENV/bin/python" scripts/training/train_retrieval.py                 # same settings as above
# compare test MRR@10 with the 0.544 above before deploying; then re-ingest both services
```

## Next: more material for thin roles (needs approval of sources)

Roles with few curriculum documents get weaker lessons and fewer interview questions. Candidate openly licensed sources
to review before adding: MDN Web Docs (CC-BY-SA, frontend), the Kubernetes and Docker docs (CC-BY 4.0,
DevOps), OpenStax Principles of Marketing / Principles of Finance / Organizational Behavior (CC-BY 4.0, for
the marketing, finance and HR roles). Check each licence and attribution requirement before ingesting; nothing has
been downloaded.
