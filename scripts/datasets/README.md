# Public datasets

Scripts that fetch the public datasets behind the learning assistant's curriculum and the interview
evaluator's accuracy check. Raw downloads stay outside the repo (default `/Volumes/Dilmith Ext/datasets`).

| Dataset | Used for | Licence |
|---|---|---|
| [Kubernetes docs](https://github.com/kubernetes/website) (`content/en/docs/concepts`) | Learning: DevOps | CC BY 4.0 |
| [Docker docs](https://github.com/docker/docs) (build, compose, engine, get-started) | Learning: DevOps | Apache-2.0 |
| [MDN Web Docs](https://github.com/mdn/content) (HTTP, security, JS guide, Fetch, storage, performance) | Learning: Backend, Full-Stack | CC BY-SA 2.5 (Mozilla Contributors) |
| [PostgreSQL 18 docs](https://www.postgresql.org/docs/18/) (45 chapters) | Learning: Database, Backend | [PostgreSQL Licence](https://www.postgresql.org/about/licence/) |
| [Azure Architecture Center](https://github.com/MicrosoftDocs/architecture-center) (patterns, styles, best practices, microservices) | Learning: Backend, DevOps | CC BY 4.0 |
| [The Open Guide to AWS](https://github.com/open-guides/og-aws) | Learning: DevOps (cloud) | CC BY 4.0 |
| [The System Design Primer](https://github.com/donnemartin/system-design-primer) | Learning + interview: system design | CC BY 4.0 |
| [The Art of Command Line](https://github.com/jlevy/the-art-of-command-line) | Learning: DevOps (Linux) | CC BY-SA 4.0 |
| [Generative AI for Beginners](https://github.com/microsoft/generative-ai-for-beginners) (15 lessons) | Learning: AI & RAG | MIT |
| [Prometheus docs](https://github.com/prometheus/docs) | Learning: DevOps (monitoring) | Apache-2.0 |
| [Kubernetes the Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way) | Learning: DevOps | Apache-2.0 |
| [GitHub Docs](https://github.com/github/docs) (Git, pull requests, Actions) | Learning: Git, CI/CD (all roles) | CC BY 4.0 |
| [SQLite docs](https://www.sqlite.org/copyright.html) (25 pages) | Learning: Database | Public domain |
| [test-your-sysadmin-skills](https://github.com/trimstray/test-your-sysadmin-skills) | Interview: DevOps questions with answers | MIT |
| [reactjs-interview-questions](https://github.com/sudheerj/reactjs-interview-questions) | Interview: Full-Stack questions with answers | MIT |
| [Front-end Developer Interview Questions](https://github.com/h5bp/Front-end-Developer-Interview-Questions) | Interview: Full-Stack questions | MIT |
| [Mohler ASAG](https://huggingface.co/datasets/nkazi/MohlerASAG) (2,273 graded CS answers) | Interview: evaluator vs human graders | CC BY 4.0 |

## Learning assistant curriculum

```bash
scripts/datasets/fetch_datasets.sh                       # sparse clones + PostgreSQL pages + Mohler
"/Volumes/Dilmith Ext/datasets/.venv/bin/python" scripts/datasets/build_learning_corpus.py
```

`build_learning_corpus.py` writes `services/learning-service/data/external/` (about 1,000 documents):
clean markdown with `<!-- role / topic / source / license / url -->` headers that the learning-service
loader reads, and `ATTRIBUTION.md`. Pages under 600 characters are dropped. Rebuild the learning-service
image afterwards; on startup it embeds any documents the database doesn't have yet, in the background
(about 10-15 minutes for the full corpus on CPU).

MDN and The Art of Command Line are CC BY-SA: if those generated files are redistributed, they stay CC BY-SA
with attribution.

## Interview question bank

```bash
scripts/datasets/build_interview_bank.sh                 # after the corpus is loaded; needs the local LLM
```

1. `extract_interview_candidates.py` collects about 245 candidates: questions from the three MIT interview
   sets and the System Design Primer (with their own answers where they have one), plus curriculum
   documents to write questions from for roles no open set covers (Database Engineer above all).
2. `generate_interview_bank.py` runs in the learning-service container. For each candidate it retrieves
   the closest curriculum passages and has the LLM keep or reject the question (trivia, opinion,
   unsupported by the material), set the level, and write the spoken question, a reference answer and
   rubric criteria from the source answer and passages only. Resumable; rejections keep their reason.
3. Kept items go to `services/interview-service/data/public_question_bank.json` with their source,
   licence and the documents that ground them (`provenance`). The interview service loads every JSON
   file in `data/` on startup when the files hold more questions than the database.

The reference answers are LLM-written from the cited material; spot-check them before relying on the
bank for assessment.

## Interview evaluator check (Mohler ASAG)

```bash
scripts/datasets/run_mohler_eval.sh --limit 80           # needs the local LLM (Huggingbay/start-llm.sh)
```

Runs `services/interview-service/evaluation/eval_mohler.py` in the interview-service container on a
sample stratified by human score, in two modes on the same answers: `no_reference` (question and answer
only) and `reference` (plus the instructor's answer). It reports Pearson, Spearman, quadratic weighted
kappa and MAE against the graders' average, and the two graders' agreement with each other as the
ceiling. Results go to `/Volumes/Dilmith Ext/datasets/results/`. About 17 s per grading with Gemma 4
E4B, so 80 answers x 2 modes takes about 45 minutes.
