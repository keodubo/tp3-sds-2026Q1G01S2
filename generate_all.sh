#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TP3_MODULE=("${PYTHON_BIN}" -m tp3_sds)

STUDY_CONFIG="${STUDY_CONFIG:-${ROOT_DIR}/configs/system1.study.example.toml}"
DELIVERY_ZIP="${DELIVERY_ZIP:-${ROOT_DIR}/artifacts/system1/delivery/system1-motor.zip}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${ROOT_DIR}}"

GIF_FPS="${GIF_FPS:-20}"
GIF_PLAYBACK_DURATION="${GIF_PLAYBACK_DURATION:-30.0}"
GIF_COUNTS=(50 100 200 400 800)

read_study_meta() {
  "${PYTHON_BIN}" - <<'PY' "${STUDY_CONFIG}"
from pathlib import Path
import tomllib
import sys

config_path = Path(sys.argv[1]).resolve()
data = tomllib.loads(config_path.read_text(encoding="utf-8"))
study = data["study"]
artifacts_root = (config_path.parent / study["artifacts_root"]).resolve()
print(artifacts_root / study["study_id"])
print(int(study.get("seed_start", 1)))
PY
}

run_tp3() {
  echo
  echo "==> $*"
  PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" "${TP3_MODULE[@]}" "$@"
}

mkdir -p "$(dirname "${DELIVERY_ZIP}")"
cd "${ROOT_DIR}"

mapfile -t STUDY_META < <(read_study_meta)
STUDY_ROOT="${STUDY_META[0]}"
SEED_START="${STUDY_META[1]}"

echo "Running System 1 delivery pipeline from ${ROOT_DIR}"
echo "Python: ${PYTHON_BIN}"
echo "Study config: ${STUDY_CONFIG}"
echo "Study root: ${STUDY_ROOT}"
echo "Seed start: ${SEED_START}"
echo "Output root: ${OUTPUT_ROOT}"
echo "Delivery zip: ${DELIVERY_ZIP}"
echo "GIF fps/playback: ${GIF_FPS}/${GIF_PLAYBACK_DURATION}s"

# 1. Validar y correr el estudio (largo: varias horas con N=800)
run_tp3 system1 validate-study --config "${STUDY_CONFIG}"
run_tp3 system1 study --config "${STUDY_CONFIG}"

# 2. Scatter de artefactos a output_1.X/
echo
echo "==> Scattering study artifacts into output_1.X/"
mkdir -p "${OUTPUT_ROOT}/output_1.1" "${OUTPUT_ROOT}/output_1.2" "${OUTPUT_ROOT}/output_1.3" "${OUTPUT_ROOT}/output_1.4"

cp "${STUDY_ROOT}/aggregates/runtime_vs_n.csv" "${OUTPUT_ROOT}/output_1.1/"
cp "${STUDY_ROOT}/figures/runtime_vs_n.png" "${OUTPUT_ROOT}/output_1.1/"

cp "${STUDY_ROOT}/aggregates/scanning_rate_vs_n.csv" "${OUTPUT_ROOT}/output_1.2/"
cp "${STUDY_ROOT}/figures/scanning_rate_vs_n.png" "${OUTPUT_ROOT}/output_1.2/"

cp "${STUDY_ROOT}/aggregates/used_fraction_vs_n.csv" "${OUTPUT_ROOT}/output_1.3/"
cp "${STUDY_ROOT}/figures/used_fraction_vs_n.png" "${OUTPUT_ROOT}/output_1.3/"

cp "${STUDY_ROOT}/aggregates/near_shell_s2_vs_n.csv" "${OUTPUT_ROOT}/output_1.4/"
cp "${STUDY_ROOT}/figures/near_shell_s2_vs_n.png" "${OUTPUT_ROOT}/output_1.4/"
cp "${STUDY_ROOT}"/aggregates/radial_profile_n_*.csv "${OUTPUT_ROOT}/output_1.4/" 2>/dev/null || true
cp "${STUDY_ROOT}"/figures/radial_profile_n_*.png "${OUTPUT_ROOT}/output_1.4/" 2>/dev/null || true

# 3. Generar 5 GIFs reusando runtime snapshots del estudio
echo
echo "==> Rendering GIFs from study runtime snapshots"
mkdir -p "${OUTPUT_ROOT}/output_gifs"
for N in "${GIF_COUNTS[@]}"; do
  SNAPSHOT="${STUDY_ROOT}/runs/runtime_n_${N}_seed_${SEED_START}.txt"
  OUT="${OUTPUT_ROOT}/output_gifs/n_${N}.gif"
  run_tp3 system1 animate \
    --input "${SNAPSHOT}" \
    --output "${OUT}" \
    --fps "${GIF_FPS}" \
    --playback-duration "${GIF_PLAYBACK_DURATION}"
done

# 4. Empaquetar el motor
run_tp3 system1 package-delivery --output "${DELIVERY_ZIP}"

echo
echo "System 1 delivery pipeline completed."
echo "Inciso folders: ${OUTPUT_ROOT}/output_1.{1,2,3,4}/"
echo "Animations: ${OUTPUT_ROOT}/output_gifs/"
echo "Delivery zip: ${DELIVERY_ZIP}"
