# Corrección `tf = 5s → 500s` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir el valor físico `tf` de 5s a 500s en todo el repo (errata de cátedra confirmada oralmente), escalando knobs dependientes y dejando trazabilidad en la página source del wiki.

**Architecture:** Cambio mecánico de valores en 3 capas — código (defaults y fallbacks en `config.py`), configs TOML (`system1.example.toml`, `system1.study.example.toml`), y wiki (enfoque A: errata trazable en `source_tp3_enunciado.md`, correcciones directas en 3 páginas derivadas). Sin nuevos tests de comportamiento — la validación se hace con los comandos `validate-config`, `validate-study`, `wiki lint` y `pytest -q` existentes.

**Tech Stack:** Python 3.11, tomllib, pytest, markdown con frontmatter YAML. Git (main branch, working tree limpio salvo el spec ya committed).

**Spec:** `docs/superpowers/specs/2026-04-17-sim-duration-500s-design.md`

---

## File Structure

**Modify (code):**
- `src/tp3_sds/system1/config.py` — 8 valores en dataclasses defaults y en los loaders `load_config` / `load_study_config`.

**Modify (configs):**
- `configs/system1.example.toml` — 2 valores (`duration`, `max_events`).
- `configs/system1.study.example.toml` — 4 valores (`runtime_duration`, `runtime_limit_seconds`, `max_events`, `[analysis].max_time`).

**Modify (wiki):**
- `docs/wiki/source_tp3_enunciado.md` — agregar subsección "Errata (cátedra)" y bumpear `last_updated`.
- `docs/wiki/system_1_experimental_protocol.md` — `tf = 5 s → 500 s`, `t_max = 200 s → 2000 s`, link a errata, `last_updated`.
- `docs/wiki/system_1_observables.md` — `tf = 5 s → 500 s`, `last_updated`.
- `docs/wiki/system_1_scanning_rate.md` — `tf = 5 s → 500 s`, `last_updated`.

**No crear ni borrar archivos.** No tocar tests.

---

## Pre-flight check

- [ ] **Step 1: Verificar working tree limpio**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git status
```
Expected output: "On branch main ... nothing to commit, working tree clean".

- [ ] **Step 2: Baseline — tests verdes antes de tocar nada**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src pytest -q
```
Expected: toda la suite pasa (baseline). Si falla algo aquí, **detener** y reportar al usuario antes de hacer cambios.

- [ ] **Step 3: Baseline — wiki lint limpio**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src python3 -m tp3_sds wiki lint
```
Expected: sin errores ni warnings nuevos. Anotar si hay warnings preexistentes para distinguirlos de los que el cambio pueda introducir.

---

### Task 1: Escalar defaults y fallbacks en `config.py`

**Files:**
- Modify: `src/tp3_sds/system1/config.py` (8 líneas: 43, 54, 76, 77, 79, 135, 177, 193)

- [ ] **Step 1: Actualizar `SimulationConfig.max_events` default (line 43)**

Buscar en `src/tp3_sds/system1/config.py`:
```python
    max_events: int = 100_000
```
Reemplazar por:
```python
    max_events: int = 10_000_000
```

- [ ] **Step 2: Actualizar `StationaryDetectionConfig.max_time` default (line 54)**

Buscar:
```python
    max_time: float = 200.0
```
Reemplazar por:
```python
    max_time: float = 2000.0
```

- [ ] **Step 3: Actualizar `StudyConfig.runtime_duration` default (line 76)**

Buscar:
```python
    runtime_duration: float = 5.0
```
Reemplazar por:
```python
    runtime_duration: float = 500.0
```

- [ ] **Step 4: Actualizar `StudyConfig.runtime_limit_seconds` default (line 77)**

Buscar:
```python
    runtime_limit_seconds: float = 20.0
```
Reemplazar por:
```python
    runtime_limit_seconds: float = 2000.0
```

- [ ] **Step 5: Actualizar `StudyConfig.max_events` default (line 79)**

Buscar:
```python
    max_events: int = 1_000_000
```
Reemplazar por:
```python
    max_events: int = 100_000_000
```

- [ ] **Step 6: Actualizar fallback de `duration` en `load_config` (line 135)**

Buscar:
```python
        duration=float(simulation.get("duration", 5.0)),
```
Reemplazar por:
```python
        duration=float(simulation.get("duration", 500.0)),
```

- [ ] **Step 7: Actualizar fallback de `max_time` en `load_study_config` (line 177)**

Buscar:
```python
        max_time=float(analysis_data.get("max_time", 200.0)),
```
Reemplazar por:
```python
        max_time=float(analysis_data.get("max_time", 2000.0)),
```

- [ ] **Step 8: Actualizar fallback de `runtime_duration` en `load_study_config` (line 193)**

Buscar:
```python
        runtime_duration=float(study_data.get("runtime_duration", 5.0)),
```
Reemplazar por:
```python
        runtime_duration=float(study_data.get("runtime_duration", 500.0)),
```

- [ ] **Step 9: Correr la suite — no regresiones**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src pytest -q
```
Expected: toda la suite sigue verde. Si algo falla: investigar (probablemente es un test que asume un default viejo, aunque el grep previo descartó esto — si aparece, reportar al usuario antes de "corregir" el test).

- [ ] **Step 10: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add src/tp3_sds/system1/config.py
git commit -m "$(cat <<'EOF'
fix(system1): escalar defaults de duration/max_events a tf=500s

Escala proporcionalmente los valores que dependen del horizonte
físico (runtime_duration, runtime_limit_seconds, max_events,
max_time). Actualiza tanto los dataclass defaults como los fallbacks
de los loaders TOML.

Ref: docs/superpowers/specs/2026-04-17-sim-duration-500s-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Actualizar `configs/system1.example.toml`

**Files:**
- Modify: `configs/system1.example.toml` (2 valores en el bloque `[simulation]`)

- [ ] **Step 1: Actualizar `duration` y `max_events`**

Buscar en `configs/system1.example.toml`:
```toml
[simulation]
duration = 5.0
seed = 42
max_events = 20000
```
Reemplazar por:
```toml
[simulation]
duration = 500.0
seed = 42
max_events = 2000000
```

- [ ] **Step 2: Validar el config**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src python3 -m tp3_sds system1 validate-config --config configs/system1.example.toml
```
Expected: exit 0, "Configuration is valid." (o equivalente del CLI) sin errores.

- [ ] **Step 3: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add configs/system1.example.toml
git commit -m "$(cat <<'EOF'
fix(configs): single-run example pasa a tf=500s

Actualiza duration y max_events en el config de single-run para
reflejar la errata de cátedra (tf=500s). El GIF resultante del
animate va a durar ~500s a fps=12 — intencional.

Ref: docs/superpowers/specs/2026-04-17-sim-duration-500s-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Actualizar `configs/system1.study.example.toml`

**Files:**
- Modify: `configs/system1.study.example.toml` (4 valores: `runtime_duration`, `runtime_limit_seconds`, `max_events`, `[analysis].max_time`)

- [ ] **Step 1: Actualizar `runtime_duration`**

Buscar:
```toml
runtime_duration = 5.0
```
Reemplazar por:
```toml
runtime_duration = 500.0
```

- [ ] **Step 2: Actualizar `runtime_limit_seconds`**

Buscar:
```toml
runtime_limit_seconds = 20.0
```
Reemplazar por:
```toml
runtime_limit_seconds = 2000.0
```

- [ ] **Step 3: Actualizar `max_events`**

Buscar:
```toml
max_events = 500000
```
Reemplazar por:
```toml
max_events = 50000000
```

- [ ] **Step 4: Actualizar `[analysis].max_time`**

Buscar:
```toml
max_time = 60.0
```
Reemplazar por:
```toml
max_time = 2000.0
```

- [ ] **Step 5: Validar el config**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src python3 -m tp3_sds system1 validate-study --config configs/system1.study.example.toml
```
Expected: exit 0 sin errores. Puede haber un warning si `check_interval > window_seconds` pero en este config `check_interval=5` y `window_seconds=10` → no debería aparecer.

- [ ] **Step 6: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add configs/system1.study.example.toml
git commit -m "$(cat <<'EOF'
fix(configs): study example pasa a tf=500s

Escala runtime_duration (5→500s), runtime_limit_seconds (20→2000s),
max_events (500k→50M) y [analysis].max_time (60→2000s) para que la
configuración de estudio ejemplo sea coherente con tf=500s.

Nota: la verificación rápida que antes tomaba segundos ahora puede
tomar varios minutos de wall-clock — esperado.

Ref: docs/superpowers/specs/2026-04-17-sim-duration-500s-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Agregar errata en `docs/wiki/source_tp3_enunciado.md`

**Files:**
- Modify: `docs/wiki/source_tp3_enunciado.md`

**Contexto:** esta página transcribe el PDF y debe preservar la cita original. Lo único que se agrega es una subsección de errata explicando la corrección de cátedra. La cita textual del PDF (`tf = 5 s`) queda intacta.

- [ ] **Step 1: Bumpear `last_updated` en frontmatter**

Buscar:
```yaml
last_updated: "2026-04-13"
```
Reemplazar por:
```yaml
last_updated: "2026-04-17"
```

- [ ] **Step 2: Agregar subsección de errata después del "Statement Requirement" del punto 1.1**

Buscar exactamente (líneas 71–80 aprox.):
```markdown
## System 1: Required Study 1.1
### Statement Requirement
- Simulate for fixed absolute time `tf = 5 s`.
- Vary `N`.
- Plot execution time as a function of `N`.

### Implementation Implication
```
Reemplazar por:
```markdown
## System 1: Required Study 1.1
### Statement Requirement
- Simulate for fixed absolute time `tf = 5 s`.
- Vary `N`.
- Plot execution time as a function of `N`.

### Errata (cátedra)
- La cátedra confirmó oralmente que `tf = 5 s` es una errata del PDF.
- El valor correcto usado en este repositorio y aplicado a las simulaciones 1.1 a 1.4 es `tf = 500 s`.
- Esta página conserva la cita literal del PDF como referencia histórica; las páginas derivadas ([protocol](system_1_experimental_protocol.md), [observables](system_1_observables.md), [scanning rate](system_1_scanning_rate.md)) trabajan con el valor corregido.

### Implementation Implication
```

- [ ] **Step 3: Correr wiki lint**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src python3 -m tp3_sds wiki lint
```
Expected: sin errores nuevos. Los links agregados (`system_1_experimental_protocol.md`, etc.) ya existen en `docs/wiki/` y no deben romper nada.

- [ ] **Step 4: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add docs/wiki/source_tp3_enunciado.md
git commit -m "$(cat <<'EOF'
docs(wiki): registrar errata de cátedra en source TP3

La cátedra corrigió oralmente tf=5s → tf=500s. La página source
preserva la cita literal del PDF y documenta la errata en una
subsección nueva bajo el punto 1.1, con referencias a las páginas
derivadas que ya aplican el valor corregido.

Ref: docs/superpowers/specs/2026-04-17-sim-duration-500s-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Actualizar páginas derivadas del wiki

**Files:**
- Modify: `docs/wiki/system_1_experimental_protocol.md`
- Modify: `docs/wiki/system_1_observables.md`
- Modify: `docs/wiki/system_1_scanning_rate.md`

- [ ] **Step 1: `system_1_experimental_protocol.md` — bumpear `last_updated`**

Buscar:
```yaml
last_updated: "2026-04-13"
```
Reemplazar por:
```yaml
last_updated: "2026-04-17"
```

- [ ] **Step 2: `system_1_experimental_protocol.md` — actualizar tf y agregar nota de errata**

Buscar:
```markdown
## Runtime Study (1.1)
- Use fixed physical horizon `tf = 5 s`.
- Repeat each `N` five times by default.
- Report mean and standard deviation of wall-clock runtime.
```
Reemplazar por:
```markdown
## Runtime Study (1.1)
- Use fixed physical horizon `tf = 500 s` (see [errata](source_tp3_enunciado.md#errata-cátedra)).
- Repeat each `N` five times by default.
- Report mean and standard deviation of wall-clock runtime.
```

- [ ] **Step 3: `system_1_experimental_protocol.md` — actualizar safety cutoff**

Buscar:
```markdown
- Safety cutoff:
  - terminate a realization at `t_max = 200 s`
  - if stationarity is not reached by then, mark the realization `no_stationary`
```
Reemplazar por:
```markdown
- Safety cutoff:
  - terminate a realization at `t_max = 2000 s`
  - if stationarity is not reached by then, mark the realization `no_stationary`
```

- [ ] **Step 4: `system_1_observables.md` — bumpear `last_updated`**

Buscar:
```yaml
last_updated: "2026-04-13"
```
Reemplazar por:
```yaml
last_updated: "2026-04-17"
```

- [ ] **Step 5: `system_1_observables.md` — actualizar tf**

Buscar:
```markdown
- Absolute simulation horizon fixed at `tf = 5 s`.
```
Reemplazar por:
```markdown
- Absolute simulation horizon fixed at `tf = 500 s` (see [errata](source_tp3_enunciado.md#errata-cátedra)).
```

- [ ] **Step 6: `system_1_scanning_rate.md` — bumpear `last_updated`**

Buscar:
```yaml
last_updated: "2026-04-13"
```
Reemplazar por:
```yaml
last_updated: "2026-04-17"
```

- [ ] **Step 7: `system_1_scanning_rate.md` — actualizar tf**

Buscar:
```markdown
- Runtime is measured separately at fixed `tf = 5 s`.
```
Reemplazar por:
```markdown
- Runtime is measured separately at fixed `tf = 500 s` (see [errata](source_tp3_enunciado.md#errata-cátedra)).
```

- [ ] **Step 8: Correr wiki lint**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src python3 -m tp3_sds wiki lint
```
Expected: sin errores nuevos. El anchor `#errata-cátedra` usa el slug generado por el H3 "Errata (cátedra)" — el lint del repo no valida anchors internos (solo `.md` existencia), así que si fallara aquí habría que investigar la config del lint, pero no debería.

- [ ] **Step 9: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add docs/wiki/system_1_experimental_protocol.md docs/wiki/system_1_observables.md docs/wiki/system_1_scanning_rate.md
git commit -m "$(cat <<'EOF'
docs(wiki): derivar tf=500s en protocol/observables/scanning_rate

Actualiza las páginas derivadas al valor corregido y linkea a la
errata registrada en source_tp3_enunciado.md. También sube el
safety cutoff de estacionariedad de 200s a 2000s, proporcional al
nuevo horizonte.

Ref: docs/superpowers/specs/2026-04-17-sim-duration-500s-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Verificación final end-to-end

**Files:** ninguno (solo comandos de verificación; sin commit si todo pasa).

- [ ] **Step 1: pytest limpio**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src pytest -q
```
Expected: toda la suite verde (igual que el baseline pre-flight).

- [ ] **Step 2: wiki lint limpio**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src python3 -m tp3_sds wiki lint
```
Expected: sin errores. Warnings preexistentes deben coincidir con los del baseline (ningún warning nuevo introducido).

- [ ] **Step 3: validate-config del single-run**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src python3 -m tp3_sds system1 validate-config --config configs/system1.example.toml
```
Expected: exit 0. Salida del CLI indicando que el config es válido.

- [ ] **Step 4: validate-study del estudio**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
PYTHONPATH=src python3 -m tp3_sds system1 validate-study --config configs/system1.study.example.toml
```
Expected: exit 0 sin errores.

- [ ] **Step 5: Grep final — ningún residuo de "5 s" o "5.0" como horizonte físico**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git grep -nE "tf = 5 s|tf=5s|tf = 5\.0|runtime_duration = 5\.0|duration = 5\.0" -- docs configs src
```
Expected: **un único match** en `docs/wiki/source_tp3_enunciado.md` (la cita textual preservada del PDF, línea "Simulate for fixed absolute time `tf = 5 s`"). Si aparece otro match fuera de esa línea, investigar — puede ser un lugar olvidado que también debía escalarse.

- [ ] **Step 6: Log de git**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git log --oneline -7
```
Expected: ver los 5 commits de este plan (Tasks 1–5) encima del commit del spec `196ddac`, en orden.

---

## Self-Review

**1. Spec coverage:**
- Code defaults (8 líneas): Task 1 ✓
- `system1.example.toml` (2 valores): Task 2 ✓
- `system1.study.example.toml` (4 valores): Task 3 ✓
- Wiki source con errata: Task 4 ✓
- Wiki derivadas (3 páginas): Task 5 ✓
- Verificación (pytest, wiki lint, validate-config, validate-study): Task 6 ✓
- "No run/study en verificación": respetado (solo validate-* + pytest).

**2. Placeholder scan:** sin TBD/TODO. Todos los valores numéricos son literales. Todos los commits traen mensaje completo. Todos los comandos traen expected output.

**3. Type consistency:** no aplica — no se declaran tipos nuevos. Valores escalados ×100 coherentes entre código y configs (código: `10_000_000`, `500.0`, `2000.0`, `100_000_000`; configs: `2000000`, `500.0`, `2000.0`, `50000000`). Los factores matchean el spec.

**4. Granularidad:** cada step es una edición o un comando individual (2–5 min). 5 commits atómicos + 1 verificación final sin commit.
