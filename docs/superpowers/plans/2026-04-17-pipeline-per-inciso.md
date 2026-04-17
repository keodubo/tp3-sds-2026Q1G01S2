# Pipeline per-inciso (`generate_all.sh`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reescribir `generate_all.sh` para orquestar el estudio y distribuir sus artefactos en `output_1.X/` + `output_gifs/`, con el grid de N de producción `[10, 50, 100, 200, 400, 800]` y 5 GIFs reusando snapshots del estudio.

**Architecture:** Cambio puramente de orquestación + configuración. `study.py` sigue escribiendo a `artifacts/system1/studies/<id>/` sin cambios; el script nuevo lee ese directorio y copia los archivos relevantes a carpetas separadas por inciso. Los GIFs se generan corriendo `tp3 system1 animate` sobre los `runtime_n_<N>_seed_<seed_start>.txt` que el estudio ya produce. El wiki documenta el grid de N adoptado.

**Tech Stack:** bash 4+ (`mapfile`/`set -euo pipefail`), Python 3.11 (`tomllib` inline para resolver rutas del config), TOML, Markdown.

**Spec:** `docs/superpowers/specs/2026-04-17-pipeline-per-inciso-design.md`

---

## File Structure

**Modify:**
- `configs/system1.study.example.toml` — una línea: `counts = [10, 50, 100, 200, 400, 800]`.
- `generate_all.sh` — reescribir el flujo completo (file existente, NO crear archivo nuevo).
- `docs/wiki/system_1_experimental_protocol.md` — agregar bullet del production N grid, bumpear `last_updated`.

**No tocar:**
- `src/tp3_sds/system1/study.py`, `delivery.py`, `animation.py`, ni ningún `.py`.
- `configs/system1.example.toml` (single-run demo).
- Tests.

---

## Pre-flight check

- [ ] **Step 1: Working tree limpio, baseline verde**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git status
.venv/bin/pytest -q
.venv/bin/python3 -m tp3_sds wiki lint
```
Expected: "nothing to commit, working tree clean" con HEAD en `e685d9c` (el spec); 32 passed; "Wiki lint passed."

---

### Task 1: Actualizar el grid de N del study config

**Files:**
- Modify: `configs/system1.study.example.toml` (1 línea)

- [ ] **Step 1: Cambiar `counts`**

En `configs/system1.study.example.toml` buscar:
```toml
counts = [8, 12]
```
Reemplazar por:
```toml
counts = [10, 50, 100, 200, 400, 800]
```

- [ ] **Step 2: Validar el config con el CLI**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/python3 -m tp3_sds system1 validate-study --config configs/system1.study.example.toml
```
Expected: exit 0, `Study config validation passed.`

No se debe ejecutar el study completo (toma horas con N=800).

- [ ] **Step 3: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add configs/system1.study.example.toml
git commit -m "$(cat <<'EOF'
fix(configs): study grid pasa al production N [10,50,100,200,400,800]

El config de ejemplo pasa del grid de verificación [8, 12] al grid
de producción adoptado por el repositorio para los incisos 1.1-1.4.
Los incisos se organizan en output_1.X/ via generate_all.sh.

Ref: docs/superpowers/specs/2026-04-17-pipeline-per-inciso-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Reescribir `generate_all.sh`

**Files:**
- Modify: `generate_all.sh` (reescritura completa)

- [ ] **Step 1: Reemplazar el contenido completo de `generate_all.sh`**

Borrar el contenido actual (73 líneas) y reemplazar por:

```bash
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
```

- [ ] **Step 2: Verificar que el shebang + bit ejecutable están intactos**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
ls -l generate_all.sh
```
Expected: modo incluye `x` (ejecutable), ej. `-rwxr-xr-x`. Si no es ejecutable:
```bash
chmod +x generate_all.sh
```

- [ ] **Step 3: Syntax check del script (sin ejecutarlo)**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
bash -n generate_all.sh
```
Expected: exit 0, sin salida. Si hay error de sintaxis, corregir antes de seguir.

- [ ] **Step 4: Ejecutar `read_study_meta` standalone para confirmar que resuelve el STUDY_ROOT y el SEED_START**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/python3 - <<'PY' configs/system1.study.example.toml
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
```
Expected: **dos líneas** impresas. La primera debe terminar en `/artifacts/system1/studies/example-study`. La segunda debe ser `100` (valor actual de `seed_start` en el config).

Si la primera línea no matchea, el layout de `artifacts_root` relativo en el TOML cambió y hay que ajustar la resolución.

- [ ] **Step 5: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add generate_all.sh
git commit -m "$(cat <<'EOF'
feat(generate_all): orquestar pipeline per-inciso con 5 gifs

Nuevo flujo: validate-study → study → scatter a output_1.X/ con los
artefactos específicos de cada inciso (runtime 1.1, scanning 1.2,
used fraction 1.3, near-shell + radial profiles 1.4) → 5 gifs desde
runtime_n_<N>_seed_<seed_start>.txt para N ∈ {50,100,200,400,800} →
package-delivery. Se elimina el bloque de single-run + animate
(redundante: los gifs ahora salen del estudio).

Variables env de override: STUDY_CONFIG, OUTPUT_ROOT, DELIVERY_ZIP,
GIF_FPS, GIF_PLAYBACK_DURATION.

Ref: docs/superpowers/specs/2026-04-17-pipeline-per-inciso-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Documentar el production N grid en el wiki

**Files:**
- Modify: `docs/wiki/system_1_experimental_protocol.md`

- [ ] **Step 1: Bumpear `last_updated`**

Buscar en el frontmatter:
```yaml
last_updated: "2026-04-17"
```
Ya debería estar en 2026-04-17 (del cambio de errata). Si está, **dejarlo**. Si por alguna razón quedó con otra fecha, ponerlo en `"2026-04-17"`.

- [ ] **Step 2: Agregar bullet del production N grid en "Particle-Count Selection"**

Buscar la sección:
```markdown
## Particle-Count Selection
- If a study config provides an explicit list of `N`, use it as-is.
- If `counts_mode = auto`, use the default staircase from the study config.
- Stop extending the staircase after the median runtime for the current `N` exceeds `20 s` per realization.
```

Reemplazar por:
```markdown
## Particle-Count Selection
- If a study config provides an explicit list of `N`, use it as-is.
- If `counts_mode = auto`, use the default staircase from the study config.
- Stop extending the staircase after the median runtime for the current `N` exceeds `20 s` per realization.
- The production `N` grid adopted by this repository is `[10, 50, 100, 200, 400, 800]`. The file `configs/system1.study.example.toml` ships with this grid and `generate_all.sh` consumes it by default.
```

- [ ] **Step 3: Correr wiki lint**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/python3 -m tp3_sds wiki lint
```
Expected: "Wiki lint passed."

- [ ] **Step 4: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add docs/wiki/system_1_experimental_protocol.md
git commit -m "$(cat <<'EOF'
docs(wiki): registrar production N grid [10,50,100,200,400,800]

Agrega un bullet en Particle-Count Selection documentando el grid
que el repositorio adopta por default (configs/system1.study.example.toml
y generate_all.sh). Esto cierra la ambigüedad del enunciado, que
sólo dice "valor máximo tal que las simulaciones se completen en
tiempo razonable".

Ref: docs/superpowers/specs/2026-04-17-pipeline-per-inciso-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Verificación final (sin correr el pipeline completo)

**Files:** ninguno.

**Contexto:** correr `./generate_all.sh` entero con N=800 toma horas. Esta verificación se limita a checks de forma y smoke del entorno.

- [ ] **Step 1: pytest verde**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/pytest -q
```
Expected: 32 passed (sin cambios — no se tocó código).

- [ ] **Step 2: Wiki lint verde**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/python3 -m tp3_sds wiki lint
```
Expected: "Wiki lint passed."

- [ ] **Step 3: validate-study pasa con el grid nuevo**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/python3 -m tp3_sds system1 validate-study --config configs/system1.study.example.toml
```
Expected: exit 0, "Study config validation passed."

- [ ] **Step 4: `bash -n` del generate_all.sh**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
bash -n generate_all.sh
```
Expected: exit 0, sin output.

- [ ] **Step 5: Confirmar que el zip de delivery (construido desde el estado actual del repo, sin correr el estudio) no incluye `output_*/`**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
rm -rf /tmp/delivery-check
.venv/bin/python3 -m tp3_sds system1 package-delivery --output /tmp/delivery-check/system1-motor.zip
unzip -l /tmp/delivery-check/system1-motor.zip
```

Expected: la salida de `unzip -l` muestra únicamente:
- `pyproject.toml`
- `README.md`
- `src/tp3_sds/__main__.py`
- `src/tp3_sds/cli.py`
- `src/tp3_sds/__init__.py`
- `src/tp3_sds/system1/__init__.py`
- `src/tp3_sds/system1/{analysis,config,events,model,observables,output,simulation}.py`
- `configs/system1.example.toml`

**Ningún** archivo con prefijo `output_`, `artifacts/`, `docs/`, `tests/`. El zip debe pesar < 100 KB. Si alguna entrada inesperada aparece → reportar, NO commitear cambios al packager en este plan.

- [ ] **Step 6: git log resumido**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git log --oneline -6
```
Expected: los 3 commits nuevos (Tasks 1-3) encima del commit del spec `e685d9c`, en orden. No hay commit para Task 4 (verificación sin cambios).

---

## Self-Review

**1. Spec coverage:**
- Spec §Alcance punto 1 (reescribir generate_all.sh): Task 2 ✓
- Spec §Alcance punto 2 (actualizar config): Task 1 ✓
- Spec §Alcance punto 3 (documentar grid): Task 3 ✓
- Spec §Alcance punto 4 (reusar snapshots): implementado en Task 2 Step 1, el loop de `GIF_COUNTS` lee `runtime_n_<N>_seed_<SEED_START>.txt` ✓
- Spec §Fuera de alcance: no se tocan study.py/animation.py/delivery.py/example.toml/tests ✓
- Spec §Layout de outputs: Task 2 Step 1 crea los 5 directorios y copia exactamente los archivos listados ✓
- Spec §Verificación: Task 4 cubre pytest, wiki lint, validate-study, `bash -n`, zip inspection ✓
- Spec §Riesgos: documentados, no requieren tareas ✓

**2. Placeholder scan:** todos los comandos son literales, no hay "TBD" ni "add validation". Los mensajes de commit son HEREDOC verbatim.

**3. Type consistency:** las variables bash son coherentes (`STUDY_ROOT`, `SEED_START`, `OUTPUT_ROOT`, `STUDY_CONFIG`, `GIF_COUNTS`, `GIF_FPS`, `GIF_PLAYBACK_DURATION` usadas consistentemente). Nombres de archivos del estudio matchean los de `study.py` (runtime_vs_n.csv, scanning_rate_vs_n.csv, used_fraction_vs_n.csv, near_shell_s2_vs_n.csv, radial_profile_n_<N>.csv). `SEED_START` se resuelve por el resolver de Task 2 Step 1 y se usa en Task 2 Step 1 en el loop de GIFs — mismo nombre.

**4. Granularidad:** 3 tareas con commit (Task 1: 1 línea de TOML; Task 2: reescritura del script; Task 3: 1 bullet de wiki). Task 4: 6 verificaciones sin commit.
