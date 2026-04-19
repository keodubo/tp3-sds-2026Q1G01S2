#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DECK_DIR="${ROOT_DIR}/presentation/system1-beamer"
PYTHON_BIN="${PYTHON_BIN:-python3}"
STUDY_ROOT="${STUDY_ROOT:-${ROOT_DIR}/artifacts/system1/studies/inciso-1.1}"
OUTPUT_DIR="${OUTPUT_DIR:-${DECK_DIR}/assets/generated}"
BUILD_DIR="${BUILD_DIR:-${DECK_DIR}/build}"
PDF_NAME="${PDF_NAME:-system1-beamer.pdf}"
GUIDE_PDF_NAME="${GUIDE_PDF_NAME:-guion-defensa.pdf}"

build_latex_document() {
  local source_tex="$1"
  local jobname="$2"

  if command -v latexmk >/dev/null 2>&1; then
    latexmk -pdf -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD_DIR}" \
      -jobname="${jobname}" \
      "${source_tex}"
  elif command -v pdflatex >/dev/null 2>&1; then
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD_DIR}" \
      -jobname="${jobname}" \
      "${source_tex}"
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="${BUILD_DIR}" \
      -jobname="${jobname}" \
      "${source_tex}"
  else
    echo "ERROR: neither latexmk nor pdflatex is available." >&2
    exit 1
  fi
}

echo "==> Generating presentation assets"
PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "${PYTHON_BIN}" "${DECK_DIR}/generate_assets.py" \
  --study-root "${STUDY_ROOT}" \
  --output-dir "${OUTPUT_DIR}"

echo
echo "==> Building Beamer deck"
mkdir -p "${BUILD_DIR}"
cd "${DECK_DIR}"

build_latex_document deck.tex deck

cp "${BUILD_DIR}/deck.pdf" "${DECK_DIR}/${PDF_NAME}"

echo
echo "==> Building defense guide"
build_latex_document guion-defensa.tex guion-defensa

cp "${BUILD_DIR}/guion-defensa.pdf" "${DECK_DIR}/${GUIDE_PDF_NAME}"

echo
echo "Deck ready: ${DECK_DIR}/${PDF_NAME}"
echo "Guide ready: ${DECK_DIR}/${GUIDE_PDF_NAME}"
