#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-}"
[[ "$MODE" == baseline || "$MODE" == optimized ]] || { echo 'Usage: run_test.sh {baseline|optimized}' >&2; exit 2; }
shift
# All optimized launches use the production HALT path.
if [[ "$MODE" == optimized ]]; then set -- --shutdown-after-initial-cycle "$@"; fi
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT/smart_plant_test.pid"
# Serialize launcher PID-file checks; the Python runner independently locks execution.
exec 9>"$ROOT/.smartplant-launch.lock"
flock -n 9 || { echo "Another launcher is starting." >&2; exit 1; }
SERVICE=smartplant-optimized.service
if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet "$SERVICE"; then
        echo "Stop $SERVICE before a direct run." >&2; exit 1
    fi
    if [[ "$MODE" == baseline ]] && systemctl is-enabled --quiet "$SERVICE"; then
        echo "Disable $SERVICE before BASELINE (sudo systemctl disable --now $SERVICE)." >&2; exit 1
    fi
fi
if [[ -f "$PID_FILE" ]]; then
    OLD_PID="$(cat "$PID_FILE")"
    if [[ "$OLD_PID" =~ ^[1-9][0-9]*$ ]] && [[ -r "/proc/$OLD_PID/cmdline" ]] &&
       tr '\0' ' ' < "/proc/$OLD_PID/cmdline" | grep -Fq "smartplant_pi.experiment_runner" &&
       [[ "$(readlink -f "/proc/$OLD_PID/cwd")" == "$(realpath "$ROOT")" ]]; then
        echo "Already running (PID $OLD_PID)" >&2; exit 1
    fi
    rm -f -- "$PID_FILE"
fi
[[ -x "$ROOT/.venv-camera/bin/python" && -x "$ROOT/.venv-onnx/bin/python" ]] || {
    echo 'Run ./prepare_raspberry_pi.sh first.' >&2; exit 1;
}
[[ -f "$ROOT/leaf_classifier/model.onnx" ]] || { echo 'ONNX model missing; run ./prepare_raspberry_pi.sh.' >&2; exit 1; }
cd "$ROOT"
nohup "$ROOT/.venv-camera/bin/python" -m smartplant_pi.experiment_runner \
    --mode "$MODE" --serial-device "${SERIAL_DEVICE:-/dev/serial0}" \
    --events-log "$ROOT/events_log.txt" --measurements-csv "$ROOT/test_events.csv" \
    --image-dir "$ROOT/images" --onnx-python "$ROOT/.venv-onnx/bin/python" \
    --leaf-worker "$ROOT/leaf_classifier/worker.py" \
    --camera-interval-seconds "${CAMERA_INTERVAL_SECONDS:-1800}" \
    --duration-seconds "${TEST_DURATION_SECONDS:-0}" "$@" \
    >> "$ROOT/runtime_${MODE}.log" 2>&1 9>&- &
PID=$!
echo "$PID" > "$PID_FILE"
sleep 1
if ! kill -0 "$PID" 2>/dev/null; then
    rm -f -- "$PID_FILE"
    echo "Runner exited during startup; see runtime_${MODE}.log" >&2
    tail -n 20 "$ROOT/runtime_${MODE}.log" >&2 || true
    exit 1
fi
echo "Started $MODE (PID $PID); verify RUN_MARKER in runtime_${MODE}.log; stop with ./stop_test.sh"
