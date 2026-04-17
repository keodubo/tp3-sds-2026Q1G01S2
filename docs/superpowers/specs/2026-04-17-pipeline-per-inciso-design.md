# Design: Pipeline `generate_all.sh` con outputs por inciso

**Fecha:** 2026-04-17
**Autor:** Claude + Nico
**Estado:** Aprobado

## Motivación

Los incisos 1.1–1.4 del TP3 producen artefactos distintos (PNGs, CSVs) que hoy se mezclan dentro de `artifacts/system1/studies/<id>/{aggregates,figures}/`. Para el entregable conviene tener cada inciso en su propia carpeta y, adicionalmente, 5 GIFs (uno por cada N ∈ [50, 100, 200, 400, 800]) derivados de las simulaciones ya generadas por el estudio. El grid estándar de producción para los N pasa a ser `[10, 50, 100, 200, 400, 800]`. El TP3 no dicta la estructura de carpetas, así que la decisión es de presentación únicamente.

## Alcance

- Reescribir `generate_all.sh` para orquestar: validar → estudio → scatter a `output_1.X/` → 5 GIFs en `output_gifs/` → package-delivery.
- Actualizar `configs/system1.study.example.toml` con el grid de N de producción.
- Documentar el grid estándar de N en `docs/wiki/system_1_experimental_protocol.md`.
- Reusar los snapshots `runtime_n_<N>_seed_<seed_start>.txt` del estudio como fuente de GIF (para no duplicar simulaciones).

### Fuera de alcance

- No se toca `src/tp3_sds/system1/study.py` (sigue escribiendo a `artifacts/system1/studies/<id>/` igual que hoy).
- No se toca `src/tp3_sds/system1/animation.py`.
- No se toca `src/tp3_sds/system1/delivery.py` — ya usa un whitelist explícito (confirmado) que no incluye `output_*/` ni `artifacts/`, por lo que el zip entregable queda limpio automáticamente.
- No se toca `configs/system1.example.toml` (single-run demo queda para uso manual).
- No se agregan tests — el cambio es orquestación bash + un valor de config + texto de wiki.

## Layout de outputs (en la raíz del repo)

```
tp3-sds-2026Q1G01S2/
├── output_1.1/            # runtime vs N (inciso 1.1)
│   ├── runtime_vs_n.csv
│   └── runtime_vs_n.png
├── output_1.2/            # scanning rate J vs N (inciso 1.2)
│   ├── scanning_rate_vs_n.csv
│   └── scanning_rate_vs_n.png
├── output_1.3/            # F_est(N) y t_estacionario(N) (inciso 1.3)
│   ├── used_fraction_vs_n.csv
│   └── used_fraction_vs_n.png
├── output_1.4/            # perfiles radiales + near-shell (inciso 1.4)
│   ├── near_shell_s2_vs_n.csv
│   ├── near_shell_s2_vs_n.png
│   ├── radial_profile_n_10.csv   ...    radial_profile_n_800.csv
│   └── radial_profile_n_10.png   ...    radial_profile_n_800.png
└── output_gifs/           # 5 animaciones de dinámica
    ├── n_50.gif
    ├── n_100.gif
    ├── n_200.gif
    ├── n_400.gif
    └── n_800.gif
```

Los archivos internos del estudio siguen escribiéndose a `artifacts/system1/studies/<study_id>/{runs,raw,aggregates,figures}/ + summary.md` sin cambios. Las 5 carpetas `output_1.X/` y `output_gifs/` son **copias curadas** de los archivos relevantes.

El `summary.md` del estudio **no se copia** a ningún `output_*/`. Queda como referencia agregada en `artifacts/`.

## Cambios concretos

### `configs/system1.study.example.toml`

- `[study].counts: [8, 12]` → `[10, 50, 100, 200, 400, 800]`

Resto del archivo sin cambios (runtime_duration=500, runtime_limit_seconds=2000, max_events=50000000, analysis.max_time=2000 ya están post-corrección de tf).

### `generate_all.sh` — nuevo flujo

Pseudocódigo del script final:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=<directorio del script>
PYTHON_BIN=${PYTHON_BIN:-python3}
STUDY_CONFIG=${STUDY_CONFIG:-${ROOT_DIR}/configs/system1.study.example.toml}
DELIVERY_ZIP=${DELIVERY_ZIP:-${ROOT_DIR}/artifacts/system1/delivery/system1-motor.zip}
OUTPUT_ROOT=${OUTPUT_ROOT:-${ROOT_DIR}}

GIF_FPS=${GIF_FPS:-20}
GIF_PLAYBACK_DURATION=${GIF_PLAYBACK_DURATION:-30.0}
GIF_COUNTS=(50 100 200 400 800)

# ----- 1. Validar + correr el estudio -----
tp3 system1 validate-study --config "${STUDY_CONFIG}"
tp3 system1 study --config "${STUDY_CONFIG}"

# ----- 2. Resolver rutas del estudio a partir del TOML -----
# Via python inline: leer artifacts_root + study_id + seed_start del TOML
STUDY_ROOT=...       # <artifacts_root>/<study_id>
SEED_START=...       # para identificar qué runtime_*_seed_*.txt usar

# ----- 3. Scatter a output_1.X/ -----
mkdir -p "${OUTPUT_ROOT}"/output_1.{1,2,3,4}

# 1.1
cp "${STUDY_ROOT}/aggregates/runtime_vs_n.csv"   "${OUTPUT_ROOT}/output_1.1/"
cp "${STUDY_ROOT}/figures/runtime_vs_n.png"      "${OUTPUT_ROOT}/output_1.1/"

# 1.2
cp "${STUDY_ROOT}/aggregates/scanning_rate_vs_n.csv" "${OUTPUT_ROOT}/output_1.2/"
cp "${STUDY_ROOT}/figures/scanning_rate_vs_n.png"    "${OUTPUT_ROOT}/output_1.2/"

# 1.3
cp "${STUDY_ROOT}/aggregates/used_fraction_vs_n.csv" "${OUTPUT_ROOT}/output_1.3/"
cp "${STUDY_ROOT}/figures/used_fraction_vs_n.png"    "${OUTPUT_ROOT}/output_1.3/"

# 1.4 (aggregates + figures + todos los radial_profile_n_*.{csv,png})
cp "${STUDY_ROOT}/aggregates/near_shell_s2_vs_n.csv" "${OUTPUT_ROOT}/output_1.4/"
cp "${STUDY_ROOT}/figures/near_shell_s2_vs_n.png"    "${OUTPUT_ROOT}/output_1.4/"
cp "${STUDY_ROOT}"/aggregates/radial_profile_n_*.csv "${OUTPUT_ROOT}/output_1.4/" 2>/dev/null || true
cp "${STUDY_ROOT}"/figures/radial_profile_n_*.png    "${OUTPUT_ROOT}/output_1.4/" 2>/dev/null || true

# ----- 4. Generar 5 GIFs desde runtime snapshots -----
mkdir -p "${OUTPUT_ROOT}/output_gifs"
for N in "${GIF_COUNTS[@]}"; do
  SNAPSHOT="${STUDY_ROOT}/runs/runtime_n_${N}_seed_${SEED_START}.txt"
  OUT="${OUTPUT_ROOT}/output_gifs/n_${N}.gif"
  tp3 system1 animate --input "${SNAPSHOT}" --output "${OUT}" \
                      --fps "${GIF_FPS}" --playback-duration "${GIF_PLAYBACK_DURATION}"
done

# ----- 5. Delivery zip -----
tp3 system1 package-delivery --output "${DELIVERY_ZIP}"

echo "Done. Incisos en output_1.X/, gifs en output_gifs/, zip en ${DELIVERY_ZIP}"
```

**Cambios respecto al script viejo:**
- Se elimina el bloque de `validate-config` + `run` + `animate` del single-run (redundante: los GIFs ahora salen del estudio).
- Se agrega el resolver de `STUDY_ROOT` y `SEED_START` vía python inline leyendo el TOML.
- Se agrega el scatter a `output_1.X/`.
- Se agrega el loop de animación por N.

### Override via env vars

- `STUDY_CONFIG` — ruta al TOML del estudio (default: `configs/system1.study.example.toml`)
- `DELIVERY_ZIP` — ruta del zip
- `OUTPUT_ROOT` — dónde se crean `output_1.X/` y `output_gifs/` (default: root del repo)
- `GIF_FPS` — default 20
- `GIF_PLAYBACK_DURATION` — default 30.0

### `docs/wiki/system_1_experimental_protocol.md`

En la sección "Particle-Count Selection", agregar un bullet:

```markdown
- The production `N` grid adopted by this repository is `[10, 50, 100, 200, 400, 800]`. The `configs/system1.study.example.toml` ships with this grid and it is what `generate_all.sh` consumes by default.
```

Bumpear `last_updated` a `2026-04-17`.

## Edge cases

- **Si `study` aborta antes de generar `runtime_n_<N>_seed_<seed_start>.txt`** (ej. OOM o error en N grande): el loop de animación va a fallar en el primer N faltante. El script corta por `set -euo pipefail`, lo que es correcto — se ve el error explícito.
- **Si un radial_profile_n_<N>.png no existe** (caso improbable, ocurre cuando ninguna realization alcanzó estacionariedad para ese N): el glob `*` lo saltea y el `|| true` evita que `cp` con 0 matches rompa el script.
- **Si `OUTPUT_ROOT` ya tiene `output_1.X/` de una corrida previa**: los archivos se sobrescriben (intencional).

## Verificación

```bash
.venv/bin/pytest -q                                           # sigue verde (32 passed, sin cambios)
.venv/bin/python3 -m tp3_sds wiki lint                        # sin nuevos issues
.venv/bin/python3 -m tp3_sds system1 validate-study --config configs/system1.study.example.toml
./generate_all.sh                                             # corrida completa (horas)
ls -la output_1.1 output_1.2 output_1.3 output_1.4 output_gifs  # confirmar layout
unzip -l artifacts/system1/delivery/system1-motor.zip         # confirmar que NO hay output_*/
```

## Riesgos

- **Wall-clock**: `N=[10, 50, 100, 200, 400, 800]` con 5 realizations cada uno, tf=500s event-driven: varias horas de runtime total, dominado por N=800. El usuario acepta este costo.
- **File size de los snapshots grandes**: para N=800, tf=500s con `snapshot_every=5`, los `runtime_n_800_seed_<s>.txt` pueden llegar a cientos de MB. El animator carga en memoria. Si se vuelve inviable, la salida es bumpear `snapshot_every` en el config (no forma parte de este scope).
- **File size de GIFs grandes**: el GIF de N=800 podría pesar ~20–50 MB (600 frames × 800 círculos). Si es demasiado, el usuario puede reducir `GIF_PLAYBACK_DURATION` o `GIF_FPS` via env vars.
- **`.gitignore`**: `output_*/` y `output_gifs/` no están ignorados actualmente. No es un riesgo per se (son artefactos locales), pero se podría agregar al `.gitignore` si se quiere evitar commits accidentales.
