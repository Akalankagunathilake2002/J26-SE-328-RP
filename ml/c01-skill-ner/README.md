# C01 skill NER

NER models that find skill mentions in job ads, for the Job Market Intelligence Engine
(`services/job-market-intelligence-engine`). They are compared with the service's lexicon matcher
(`config/skills_lexicon.yaml`), which stays the default until the evaluation shows otherwise.

```text
OCR text → NER model → raw skill mentions → SSKS /normalize/skills → ssk_id → demand per role
```

## Layout

```text
ml/c01-skill-ner/
├── src/            data preparation, training, export and evaluation scripts
├── configs/        spaCy training config, Label Studio labelling interface
├── reports/        evaluation.md and evaluation.json (committed)
├── LABELLING.md    guide for labelling the topjobs test set
├── data/           SkillSpan files, topjobs test set   (git-ignored)
└── models/         trained models                      (git-ignored)
```

## Setup

Python 3.12 (spaCy and PyTorch don't support 3.14 yet), with [uv](https://docs.astral.sh/uv/):

```bash
cd ml/c01-skill-ner
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python -e "../../services/job-market-intelligence-engine[dev]"
.venv/bin/python -m spacy download en_core_web_md
```

## Steps

```bash
.venv/bin/python src/prepare_skillspan.py         # 1. SkillSpan → data/skillspan/
.venv/bin/python src/train_spacy.py               # 3. model A: spaCy (CPU, ~10 min)
.venv/bin/python src/train_jobbert.py             # 3. model B: JobBERT (~40 min on an Apple M4 GPU; Colab steps inside)
.venv/bin/python src/export_label_studio.py       # 2. draw the 100 topjobs test ads (needs 100+ ads)
.venv/bin/python src/evaluate.py --ssks-url http://localhost:8005/ssks   # 5. → reports/evaluation.md
```

- **Labels.** SkillSpan marks *skills* (abilities, often phrases: avg. 4.4 words) and *knowledge*
  (names such as "docker": avg. 1.9 words). The models keep the two labels apart while training;
  for evaluation and in the service both are one kind of mention. Where the two overlap, the
  knowledge span is kept (133 training spans).
- **Test set.** 100 topjobs ads drawn at random with seed 42, leaving out the 5 ads the lexicon
  was tuned on. Labelled by hand (LABELLING.md), never used for training.
- **Seed.** 42 everywhere. Each model folder has a `metadata.json` with the version, settings,
  data fingerprints, package versions and validation scores.

## Using a model in the service

```bash
SKILLBRIDGE_SKILL_EXTRACTOR=ner \
SKILLBRIDGE_NER_MODEL=ml/c01-skill-ner/models/spacy-skill-ner-0.1.0/model-best \
SKILLBRIDGE_SSKS_URL=http://localhost:8080/ssks \
python -m app.processing.skills
```

The service then needs its `ner` extra (`pip install -e ".[ner]"`, Python 3.12).

## Data and model licences

- **SkillSpan:** Zhang, Jensen, Sonniks and Plank (2022). *SkillSpan: Hard and Soft Skill
  Extraction from English Job Postings.* NAACL 2022. CC-BY-4.0. Downloaded with
  `load_dataset("jjzha/skillspan")`.
- **JobBERT** (`jjzha/jobbert-base-cased`), from the same paper. Its model page states no licence,
  so it is cited and kept out of git.
- **en_core_web_md** (spaCy, MIT licence).
- topjobs ad texts stay on this computer (`data/` is git-ignored) and are not uploaded anywhere.
