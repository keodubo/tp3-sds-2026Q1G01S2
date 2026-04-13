#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TP3_MODULE=("${PYTHON_BIN}" -m tp3_sds)

RUN_CONFIG="${RUN_CONFIG:-${ROOT_DIR}/configs/system1.example.toml}"
STUDY_CONFIG="${STUDY_CONFIG:-${ROOT_DIR}/configs/system1.study.example.toml}"
DELIVERY_ZIP="${DELIVERY_ZIP:-${ROOT_DIR}/artifacts/system1/delivery/system1-motor.zip}"

read_run_output_path() {
  "${PYTHON_BIN}" - <<'PY' "${RUN_CONFIG}"
from pathlib import Path
import tomllib
import sys

config_path = Path(sys.argv[1]).resolve()
data = tomllib.loads(config_path.read_text(encoding="utf-8"))
relative = data["output"]["path"]
print((config_path.parent / relative).resolve())
PY
}

read_study_summary_path() {
  "${PYTHON_BIN}" - <<'PY' "${STUDY_CONFIG}"
from pathlib import Path
import tomllib
import sys

config_path = Path(sys.argv[1]).resolve()
data = tomllib.loads(config_path.read_text(encoding="utf-8"))
study = data["study"]
artifacts_root = (config_path.parent / study["artifacts_root"]).resolve()
study_id = study["study_id"]
print(artifacts_root / study_id / "summary.md")
PY
}

run_tp3() {
  echo
  echo "==> $*"
  PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" "${TP3_MODULE[@]}" "$@"
}

mkdir -p "$(dirname "${DELIVERY_ZIP}")"
cd "${ROOT_DIR}"

RUN_OUTPUT_PATH="$(read_run_output_path)"
RUN_ANIMATION_PATH="${RUN_OUTPUT_PATH%.*}.gif"
STUDY_SUMMARY_PATH="$(read_study_summary_path)"

echo "Running all System 1 tasks from ${ROOT_DIR}"
echo "Python: ${PYTHON_BIN}"
echo "Run config: ${RUN_CONFIG}"
echo "Study config: ${STUDY_CONFIG}"
echo "Delivery zip: ${DELIVERY_ZIP}"

run_tp3 system1 validate-config --config "${RUN_CONFIG}"
run_tp3 system1 run --config "${RUN_CONFIG}"
run_tp3 system1 animate --input "${RUN_OUTPUT_PATH}" --output "${RUN_ANIMATION_PATH}"
run_tp3 system1 validate-study --config "${STUDY_CONFIG}"
run_tp3 system1 study --config "${STUDY_CONFIG}"
run_tp3 system1 package-delivery --output "${DELIVERY_ZIP}"

echo
echo "System 1 generation completed."
echo "Single-run output: ${RUN_OUTPUT_PATH}"
echo "Animation output: ${RUN_ANIMATION_PATH}"
echo "Study summary: ${STUDY_SUMMARY_PATH}"
echo "Delivery package: ${DELIVERY_ZIP}"
