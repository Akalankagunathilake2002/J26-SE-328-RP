#!/usr/bin/env bash
# Set up the shared Skillaro database on Neon (schemas, one login per service, and the v2 tables).
# Reads NEON_OWNER_URL from infrastructure/.env, creates any missing NEON_<SCHEMA>_PASSWORD values there,
# then runs setup.sql as the Neon owner. Safe to run again.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
env_file="${ENV_FILE:-$here/../.env}"
touch "$env_file"

get() { grep -E "^$1=" "$env_file" | tail -n 1 | cut -d= -f2- || true; }

owner_url="${NEON_OWNER_URL:-$(get NEON_OWNER_URL)}"
if [ -z "$owner_url" ]; then
  echo "Add NEON_OWNER_URL=<owner connection string of the skillaro database> to $env_file first." >&2
  exit 1
fi
command -v psql >/dev/null || { echo "psql is needed (brew install libpq, or postgresql)." >&2; exit 1; }

# Make sure the file ends with a newline before appending.
[ -s "$env_file" ] && [ -n "$(tail -c 1 "$env_file")" ] && echo >> "$env_file"

for schema in AUTH SSKS JOB_MARKET SKILL_PROFILE READINESS LEARNING INTERVIEW; do
  var="NEON_${schema}_PASSWORD"
  value="$(get "$var")"
  if [ -z "$value" ]; then
    value="$(openssl rand -hex 24)"
    echo "$var=$value" >> "$env_file"
    echo "Created $var in $env_file"
  fi
  export "$var=$value"
done

host="$(printf '%s' "$owner_url" | sed -E 's#^[^@]*@([^/:?]+).*#\1#')"
host="${host/-pooler/}"   # services use the direct host
current_host="$(get NEON_HOST)"
if [ -z "$current_host" ]; then
  echo "NEON_HOST=$host" >> "$env_file"
  echo "Created NEON_HOST in $env_file"
elif [ "$current_host" != "$host" ]; then   # e.g. the project moved to another region
  sed -i.bak "s#^NEON_HOST=.*#NEON_HOST=$host#" "$env_file" && rm -f "$env_file.bak"
  echo "Updated NEON_HOST in $env_file to the owner URL's host"
fi

psql "$owner_url" -X -v ON_ERROR_STOP=1 -f "$here/setup.sql"
echo "Done. Each service logs in as <schema>_svc with the password from $env_file."
