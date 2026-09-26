#!/usr/bin/env bash
# Run every request in a batch directory live (generate -> evaluate -> rank), one at a time.
# Re-running skips requests whose log already shows a completed evaluation, so it resumes after
# interruptions without paying twice. A failed request is logged and the batch continues.
#
# Usage: scripts/run-batch.sh data/requests/batch-v1 [first-N]
set -u
BATCH_DIR=${1:?batch directory}
LIMIT=${2:-9999}
NAME=$(basename "$BATCH_DIR")
export ADGEN_STATE_DB=${ADGEN_STATE_DB:-runs/$NAME/state.db}
LOGS=runs/$NAME/logs
mkdir -p "$LOGS"
count=0
for request in "$BATCH_DIR"/*.json; do
  [ "$count" -ge "$LIMIT" ] && break
  count=$((count + 1))
  log="$LOGS/$(basename "$request")"
  if [ -f "$log" ] && grep -q '"evaluation_performed": true' "$log"; then
    echo "skip (done): $request"; continue
  fi
  echo "run: $request"
  adgen generate --request "$request" --mode live --allow-paid > "$log" 2> "$log.stderr"
  echo "  exit $? -> $(python3 -c "import json,sys; d=json.load(open('$log')); print(d.get('status'), 'winner', d.get('winner'), 'approved', d.get('approved'), d.get('error',''))" 2>/dev/null || echo 'see log')"
done
echo "state db: $ADGEN_STATE_DB"
