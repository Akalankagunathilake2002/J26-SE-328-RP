#!/usr/bin/env bash
# Downloads the public datasets used by the learning assistant and the interview evaluator.
# Raw files go outside the repo (default: /Volumes/Dilmith Ext/datasets/raw); build_learning_corpus.py
# then turns the documentation into services/learning-service/data/external.
#
#   scripts/datasets/fetch_datasets.sh [RAW_DIR]
#
# Licences: see scripts/datasets/README.md. Git sources are shallow, sparse clones of the doc folders only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW="${1:-/Volumes/Dilmith Ext/datasets/raw}"
PG_VERSION=18
mkdir -p "$RAW"
cd "$RAW"

# Python tools (pyarrow etc.) live in a venv next to the raw data, not in the system Python
VENV="$(dirname "$RAW")/.venv"
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --disable-pip-version-check -r "$SCRIPT_DIR/requirements.txt"
PY="$VENV/bin/python"

clone() { # clone <dir> <url> <sparse paths...>
  local dir=$1 url=$2; shift 2
  [ -d "$dir" ] || git clone --quiet --depth 1 --filter=blob:none --sparse "$url" "$dir"
  git -C "$dir" sparse-checkout set --no-cone "$@"
  echo "$dir @ $(git -C "$dir" rev-parse --short HEAD)"
}

# Kubernetes docs (CC BY 4.0)
clone kubernetes-website https://github.com/kubernetes/website.git \
  '/content/en/docs/concepts/' '/LICENSE'

# Docker docs (Apache-2.0)
clone docker-docs https://github.com/docker/docs.git \
  '/content/manuals/build/' '/content/manuals/compose/' '/content/manuals/engine/' '/content/get-started/' '/LICENSE'

# MDN Web Docs (prose CC BY-SA 2.5, "Mozilla Contributors")
clone mdn-content https://github.com/mdn/content.git \
  '/files/en-us/web/http/' '/files/en-us/web/javascript/guide/' '/files/en-us/web/api/fetch_api/' \
  '/files/en-us/web/api/web_storage_api/' '/files/en-us/web/performance/' '/files/en-us/web/security/' '/LICENSE.md'

# Gap sources for the learning assistant
clone azure-architecture-center https://github.com/MicrosoftDocs/architecture-center.git \
  '/docs/patterns/' '/docs/guide/architecture-styles/' '/docs/best-practices/' '/docs/microservices/' '/LICENSE'  # CC BY 4.0
clone og-aws https://github.com/open-guides/og-aws.git '/README.md' '/LICENSE'                                     # CC BY 4.0
clone generative-ai-for-beginners https://github.com/microsoft/generative-ai-for-beginners.git \
  '/[0-2][0-9]-*/README.md' '/LICENSE'                                                                              # MIT
clone prometheus-docs https://github.com/prometheus/docs.git '/docs/' '/LICENSE'                                    # Apache-2.0
clone kubernetes-the-hard-way https://github.com/kelseyhightower/kubernetes-the-hard-way.git '/docs/' '/LICENSE'    # Apache-2.0
clone art-of-command-line https://github.com/jlevy/the-art-of-command-line.git '/README.md'                         # CC BY-SA 4.0
clone system-design-primer https://github.com/donnemartin/system-design-primer.git \
  '/README.md' '/solutions/system_design/' '/LICENSE.txt'                                                           # CC BY 4.0
clone github-docs https://github.com/github/docs.git '/content/get-started/using-git/' '/content/get-started/git-basics/' \
  '/content/pull-requests/' '/content/actions/' '/LICENSE'                                                           # CC BY 4.0

# Interview question sources (MIT)
clone sysadmin-skills https://github.com/trimstray/test-your-sysadmin-skills.git '/README.md' '/LICENSE.md'
clone reactjs-interview-questions https://github.com/sudheerj/reactjs-interview-questions.git '/README.md' '/LICENSE'
clone h5bp-fe-questions https://github.com/h5bp/Front-end-Developer-Interview-Questions.git '/src/questions/' '/LICENSE.md'

# SQLite docs (public domain)
SQLITE_PAGES=(
  queryplanner optoverview eqp isolation lang_transaction wal atomiccommit lockingv3 datatype3 foreignkeys
  partialindex expridx lang_createindex lang_with windowfunctions json1 whentouse quirks howtocorrupt
  lang_upsert lang_returning stricttables autoinc rowidtable withoutrowid
)
mkdir -p sqlite-docs
for page in "${SQLITE_PAGES[@]}"; do
  out="sqlite-docs/$page.html"
  [ -s "$out" ] || curl -sfL --retry 2 -o "$out" "https://www.sqlite.org/$page.html" || { echo "  missing: $page"; rm -f "$out"; }
done
echo "sqlite-docs: $(ls sqlite-docs | wc -l | tr -d ' ') pages"

# PostgreSQL docs (PostgreSQL Licence): the source is SGML, so fetch the published HTML chapters
PG_PAGES=(
  indexes-intro indexes-types indexes-multicolumn indexes-ordering indexes-bitmap-scans indexes-unique
  indexes-expressional indexes-partial indexes-index-only-scans indexes-examine
  mvcc-intro transaction-iso explicit-locking applevel-consistency locking-indexes
  using-explain planner-stats explicit-joins populate non-durability
  ddl-constraints ddl-partitioning ddl-schemas ddl-rowsecurity ddl-priv
  routine-vacuuming wal-intro wal-reliability wal-async-commit
  different-replication-solutions warm-standby hot-standby logical-replication
  backup-dump continuous-archiving
  tutorial-transactions tutorial-views tutorial-fk tutorial-window
  queries-with queries-table-expressions datatype-json textsearch-intro
  client-authentication auth-pg-hba-conf
)
mkdir -p "postgresql-docs-$PG_VERSION"
for page in "${PG_PAGES[@]}"; do
  out="postgresql-docs-$PG_VERSION/$page.html"
  [ -s "$out" ] || curl -sfL --retry 2 -o "$out" "https://www.postgresql.org/docs/$PG_VERSION/$page.html" \
    || { echo "  missing: $page"; rm -f "$out"; }
done
echo "postgresql-docs-$PG_VERSION: $(ls "postgresql-docs-$PG_VERSION" | wc -l | tr -d ' ') pages"

# Mohler ASAG (CC BY 4.0): CS short answers graded 0-5 by two humans ("cleaned" config, open-ended split)
mkdir -p mohler-asag
if [ ! -s mohler-asag/open_ended.jsonl ]; then
  curl -sfL --retry 2 -o mohler-asag/cleaned-oe.parquet \
    https://huggingface.co/datasets/nkazi/MohlerASAG/resolve/main/data/cleaned-oe-00001.parquet
  "$PY" - mohler-asag/cleaned-oe.parquet mohler-asag/open_ended.jsonl <<'EOF2'
import json, sys
import pyarrow.parquet as pq
rows = pq.read_table(sys.argv[1]).to_pylist()
with open(sys.argv[2], "w") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")
print(f"mohler-asag: {len(rows)} graded answers")
EOF2
fi
