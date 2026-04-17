# Design: Corregir `tf` de 5s a 500s en Sistema 1

**Fecha:** 2026-04-17
**Autor:** Claude + Nico
**Estado:** Aprobado

## Motivación

El enunciado TP3 (página 2, punto 1.1) dice textualmente:

> "Simular el sistema durante un tiempo absoluto fijo `tf = 5 s`"

La cátedra confirmó verbalmente que es una **errata del PDF**: el valor correcto es `tf = 500 s`. El repo quedó construido asumiendo 5s (configs, defaults de código y wiki), por lo que corre simulaciones 100× más cortas que las requeridas por el estudio real.

## Alcance

Corregir el valor `tf = 5 s → 500 s` en todo el repo, tratándolo como errata oficial confirmada por cátedra. Escalar knobs numéricos dependientes para que las corridas sean viables con 500s de tiempo físico. La página `source_tp3_enunciado.md` preserva la cita literal del PDF y adjunta la errata (enfoque A — corrección trazable).

### Fuera de alcance

- Cambios en tests (ninguno hardcodea 5s como requisito; usan duraciones cortas para velocidad).
- Ejecutar `system1 run` o `system1 study` con los valores nuevos — tiempos wall-clock altos; se delega al usuario.
- Regenerar `docs/wiki/index.md` (no hay alta/baja de páginas).

## Cambios

### Código — `src/tp3_sds/system1/config.py`

| Símbolo | Línea | Antes | Después |
|---|---|---|---|
| `SimulationConfig.max_events` default | 43 | `100_000` | `10_000_000` |
| `StationaryDetectionConfig.max_time` default | 54 | `200.0` | `2000.0` |
| `StudyConfig.runtime_duration` default | 76 | `5.0` | `500.0` |
| `StudyConfig.runtime_limit_seconds` default | 77 | `20.0` | `2000.0` |
| `StudyConfig.max_events` default | 79 | `1_000_000` | `100_000_000` |
| `load_config` fallback de `duration` | 135 | `5.0` | `500.0` |
| `load_study_config` fallback de `max_time` | 177 | `200.0` | `2000.0` |
| `load_study_config` fallback de `runtime_duration` | 193 | `5.0` | `500.0` |

### Configs

**`configs/system1.example.toml`:**
- `[simulation].duration`: `5.0 → 500.0`
- `[simulation].max_events`: `20000 → 2000000`

**`configs/system1.study.example.toml`:**
- `[study].runtime_duration`: `5.0 → 500.0`
- `[study].runtime_limit_seconds`: `20.0 → 2000.0`
- `[study].max_events`: `500000 → 50000000`
- `[analysis].max_time`: `60.0 → 2000.0`

### Wiki (enfoque A — corrección trazable)

**`docs/wiki/source_tp3_enunciado.md`:**
- En la sección "System 1: Required Study 1.1 → Statement Requirement", preservar la cita actual del PDF (`tf = 5 s`).
- Agregar subsección **"Errata (cátedra)"** debajo de "Statement Requirement" con texto aproximado:
  > La cátedra confirmó oralmente que el `tf = 5 s` publicado en el PDF es un error tipográfico y que el valor correcto a utilizar en las simulaciones 1.1 a 1.4 es `tf = 500 s`. Las páginas derivadas (protocolo experimental, scanning rate, observables) trabajan con el valor corregido. Esta página conserva la cita literal del PDF como referencia histórica.
- Bumpear `last_updated: "2026-04-17"`.

**`docs/wiki/system_1_experimental_protocol.md`:**
- "Use fixed physical horizon `tf = 5 s`" → "`tf = 500 s`"
- Safety cutoff: "terminate a realization at `t_max = 200 s`" → "`t_max = 2000 s`"
- Agregar nota: "Se usa `tf = 500 s` siguiendo la errata registrada en [Source: TP3 Enunciado](source_tp3_enunciado.md)."
- `last_updated: "2026-04-17"`.

**`docs/wiki/system_1_observables.md`:**
- "Absolute simulation horizon fixed at `tf = 5 s`" → "`tf = 500 s`"
- `last_updated: "2026-04-17"`.

**`docs/wiki/system_1_scanning_rate.md`:**
- "Runtime is measured separately at fixed `tf = 5 s`" → "`tf = 500 s`"
- `last_updated: "2026-04-17"`.

## No se toca

- `snapshot_every` en ambos configs: con 100× más eventos físicos, el GIF del single-run pasará a durar ~500s a `fps=12` — resultado deseado por el usuario.
- `resample_dt`, `window_seconds`, `check_interval`, `settle_extension`, `consecutive_checks`, `tolerance` en `StationaryDetectionConfig`: no dependen de `tf`, siguen representando física local (ventanas de 10s, check cada 5s, etc.).
- Tests: usan `duration = 0.5` / `1.0` / `1.5` como casos de prueba rápidos, no como espejo del valor físico real.

## Justificación de los escalados

- **`runtime_limit_seconds 20s → 2000s`**: presupuesto wall-clock por realización en el estudio 1.1. Si no escala, el barrido sobre N se corta en el primer N grande.
- **`max_events` ×100**: los eventos crecen aproximadamente linealmente con `tf` a densidad y velocidad fijas; ×100 mantiene el mismo margen que antes (factor ~10 sobre el uso típico).
- **`max_time 200s → 2000s`**: safety cutoff de estacionariedad. Escalarlo mantiene el mismo margen relativo sobre `tf`.

## Verificación post-cambio

Comandos que deben seguir pasando sin errores nuevos:

```bash
pytest -q
PYTHONPATH=src python3 -m tp3_sds wiki lint
PYTHONPATH=src python3 -m tp3_sds system1 validate-config --config configs/system1.example.toml
PYTHONPATH=src python3 -m tp3_sds system1 validate-study --config configs/system1.study.example.toml
```

No se correrán `system1 run` ni `system1 study` como parte de la verificación automática — con `tf = 500 s` el wall-clock puede ser alto y la decisión de ejecutarlos la toma el usuario manualmente.

## Riesgos

- Si el usuario corre el study completo con los defaults nuevos, el wall-clock puede extenderse varios minutos u horas dependiendo del `N` máximo. `runtime_limit_seconds = 2000s` hace que este límite ya no sirva como atajo rápido.
- El snapshot del single-run pasará de kilobytes a ~megabytes, y el GIF a ~10MB+. No bloqueante pero vale anticiparlo.
