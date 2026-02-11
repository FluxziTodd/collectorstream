#!/bin/bash
# Poll S3 for pipeline trigger and portfolio submissions
# Called by launchd every 2 minutes

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/../.venv"
BUCKET="collectorstream-site"
TRIGGER_KEY="private/pipeline-trigger.json"
STATUS_KEY="private/pipeline-status.json"
SUBMISSIONS_PREFIX="private/portfolio-submissions/"
PROFILE="fluxzi"

update_status() {
    local status="$1"
    local extra="$2"
    local now
    now=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
    local json="{\"status\":\"${status}\",\"updated_at\":\"${now}\"${extra}}"
    echo "$json" | aws s3 cp - "s3://${BUCKET}/${STATUS_KEY}" \
        --content-type application/json --profile "$PROFILE" 2>/dev/null
}

# --- Portfolio Submission Handling ---
# Check for new card submissions (runs every poll, independent of pipeline trigger)
SUBMISSIONS=$(aws s3 ls "s3://${BUCKET}/${SUBMISSIONS_PREFIX}" --profile "$PROFILE" 2>/dev/null | grep -c "\.json$")
if [ "$SUBMISSIONS" -gt 0 ] 2>/dev/null; then
    echo "$(date): Found $SUBMISSIONS portfolio submission(s), importing..."
    cd "$SCRIPT_DIR"
    source "$VENV_DIR/bin/activate"

    if [ -f "$SCRIPT_DIR/.env" ]; then
        export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
    fi

    python main.py portfolio --import-submissions 2>&1 || echo "Portfolio import failed"
    python main.py portfolio --export 2>&1 || echo "Portfolio export failed"

    deactivate 2>/dev/null
fi

# --- Pipeline Trigger Handling ---
# Check if trigger file exists
TRIGGER=$(aws s3 cp "s3://${BUCKET}/${TRIGGER_KEY}" - --profile "$PROFILE" 2>/dev/null)
if [ -z "$TRIGGER" ]; then
    exit 0
fi

# Parse status from trigger
STATUS=$(echo "$TRIGGER" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
if [ "$STATUS" != "queued" ]; then
    exit 0
fi

echo "$(date): Pipeline trigger detected, starting run..."

# Update status to running
REQUESTED_AT=$(echo "$TRIGGER" | python3 -c "import sys,json; print(json.load(sys.stdin).get('requested_at',''))" 2>/dev/null)
update_status "running" ",\"requested_at\":\"${REQUESTED_AT}\""

# Run the pipeline
cd "$SCRIPT_DIR"
if ./run_weekly.sh; then
    echo "$(date): Pipeline completed successfully"
    COMPLETED_AT=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
    update_status "completed" ",\"requested_at\":\"${REQUESTED_AT}\",\"completed_at\":\"${COMPLETED_AT}\""
else
    echo "$(date): Pipeline failed"
    FAILED_AT=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
    update_status "failed" ",\"requested_at\":\"${REQUESTED_AT}\",\"failed_at\":\"${FAILED_AT}\""
fi

# Remove trigger file
aws s3 rm "s3://${BUCKET}/${TRIGGER_KEY}" --profile "$PROFILE" 2>/dev/null

echo "$(date): Trigger processing complete"
