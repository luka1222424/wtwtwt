#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Final optimized profile: one capture/inference per wake, then HALT.
export TEST_DURATION_SECONDS="${TEST_DURATION_SECONDS:-0}"
exec "$ROOT/run_test.sh" optimized --shutdown-after-initial-cycle "$@"
