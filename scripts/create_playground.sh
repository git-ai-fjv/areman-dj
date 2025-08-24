#!/usr/bin/env bash
set -euo pipefail

MAIN_BRANCH="main"
BRANCH="${1:-playground}"                 # z.B. ./scripts/create_playground.sh debug/playground
DB_NAME="${2:-playground_datenbank}"      # optional 2. Arg: DB-Name, default: playground_datenbank
ENV_DEFAULTS=".env.${BRANCH}.defaults"    # z.B. .env.playground.defaults

echo ">> ensure git repo"
git rev-parse --is-inside-work-tree >/dev/null

echo ">> switch to $MAIN_BRANCH"
git switch "$MAIN_BRANCH"

echo ">> snapshot commit if needed"
if ! git diff-index --quiet HEAD --; then
  git add -A
  git commit -m "chore: snapshot before ${BRANCH}"
else
  echo "   no changes to commit"
fi

echo ">> fast-forward pull (optional)"
if ! git pull --ff-only; then
  echo "   (warn) could not fast-forward; continuing anyway"
fi

echo ">> create fresh database: ${DB_NAME}"
if command -v dropdb >/dev/null; then
  dropdb --if-exists "${DB_NAME}"
fi
createdb "${DB_NAME}"

echo ">> write ${ENV_DEFAULTS} (DB only, no secrets)"
cat > "${ENV_DEFAULTS}" <<EOF
DB_NAME=${DB_NAME}
DB_HOST=localhost
DB_PORT=5432
EOF

echo ">> point .env.defaults -> ${ENV_DEFAULTS}"
ln -sf "${ENV_DEFAULTS}" .env.defaults

echo ">> create/switch branch: ${BRANCH}"
if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  git switch "${BRANCH}"
else
  git switch -c "${BRANCH}"
fi

echo ">> done."
echo "   DB: ${DB_NAME}"
echo "   env defaults: ${ENV_DEFAULTS} (symlinked as .env.defaults)"
echo "   branch: ${BRANCH}"
echo "   (optional) run: python manage.py migrate && seed_*"


