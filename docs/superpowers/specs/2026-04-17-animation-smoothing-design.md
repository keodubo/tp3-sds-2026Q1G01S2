# Design: Animación fluida con interpolación entre eventos

**Fecha:** 2026-04-17
**Autor:** Claude + Nico
**Estado:** Aprobado

## Motivación

Al simular event-driven, los snapshots se emiten en los tiempos físicos de los eventos, que están espaciados de manera irregular. Hoy `render_snapshot_animation` renderiza un frame por snapshot a fps constante, lo que produce microcuts/stutter cada vez que hay dos eventos cercanos en el tiempo (típicamente colisiones) y "saltos" cuando los eventos están separados. El usuario observó este artefacto en el GIF de Sistema 1 y pidió que la animación sea fluida siempre, además de subir el fps a 20.

## Alcance

- Reescribir el loop de frames de `src/tp3_sds/system1/animation.py` para muestreo uniforme en tiempo físico con interpolación lineal entre snapshots.
- Agregar CLI flag `--playback-duration SECONDS` (default 30.0) en el subcomando `animate`.
- Cambiar default de `--fps` de 12 a 20.
- Adaptar el label opcional `--show-step-label` para mostrar `t=X.XXX s  used=Z` (sin `event=`).
- Tests nuevos para la interpolación.

### Fuera de alcance

- No se toca el simulador ni el formato del archivo de snapshots (`output.py`).
- No se tocan los configs TOML (`animate` es CLI-only).
- No se agrega `--speed` ni otros flags de tiempo (YAGNI).
- No se persiste `playback_duration` en el header del snapshot.

## Algoritmo

La clave del fix es que, entre dos eventos consecutivos, ninguna partícula cambia de velocidad (por definición event-driven hard-sphere). Por lo tanto, la posición de cualquier partícula en un tiempo `t_frame ∈ [snap_k.time, snap_{k+1}.time)` es **exactamente** `snap_k.pos + (t_frame − snap_k.time) × snap_k.velocity`. La interpolación lineal no es una aproximación.

```
n_frames     = fps * playback_duration
dt_physical  = header.duration / n_frames
snapshot_times = [snap.time for snap in snapshots]   # pre-computed

for i in 0..n_frames-1:
    t_frame = i * dt_physical
    k       = bisect_right(snapshot_times, t_frame) - 1
    snap    = snapshots[k]
    dt      = t_frame - snap.time
    for particle in snap.particles:
        x_frame = particle.x + dt * particle.vx
        y_frame = particle.y + dt * particle.vy
        # color y state: los del snap (no interpolan)
    render_frame(t_frame, n_used=snap.n_used, particles_at_frame=...)
```

Entre snapshots, la interpolación sólo avanza posiciones; `state` (fresh/used) y `n_used` se toman del snapshot de anclaje porque los cambios de estado son eventos discretos.

## Cambios en código

### `src/tp3_sds/system1/animation.py`

- `render_snapshot_animation`:
  - Nuevo parámetro `playback_duration: float = 30.0`. Validar `playback_duration > 0`; ValueError si no.
  - Cambiar default `fps: int = 12` → `fps: int = 20`.
  - Reemplazar la lista comprehension que hace "1 frame por step" por el loop de muestreo uniforme descrito arriba.
  - Pre-computar `snapshot_times` y usar `bisect.bisect_right` (import módulo `bisect` del stdlib) para O(log n) por frame.
- `_render_frame`:
  - Cambiar la firma para recibir `t_frame: float`, `n_used: int`, y una lista de tuplas `(x, y, r, g, b)` ya interpoladas (o un dataclass interno chiquito), en lugar de `step: ParsedStep`.
  - Ajustar el label de `event=... t=... used=...` a `t=X.XXX s  used=Z`.

### `src/tp3_sds/cli.py`

- Parser del subcomando `animate`:
  - Agregar `--playback-duration` como `float`, default `30.0`, con help que explique "duración del GIF en segundos de reproducción".
  - Cambiar default de `--fps` de `12` a `20`.
- Pasar `playback_duration` al llamar `render_snapshot_animation`.

## Edge cases

- `playback_duration ≤ 0`: ValueError en `render_snapshot_animation`.
- `fps ≤ 0`: ya existe ValueError; mantener.
- `n_frames` resultante 0 después del cálculo: dibujar mínimo 1 frame (clamp a `max(1, n_frames)`).
- Simulación terminada antes de `header.duration` (ej. por `max_events`): `last_snapshot.time < header.duration`. Si `t_frame > last_snapshot.time`, clampear `t_frame` al último snapshot y usarlo directamente (no extrapolar).
- Único snapshot disponible: un solo frame sin interpolación.
- Snapshot con `time=0` al inicio: `bisect_right([0, ...], 0) - 1 = 0` (correcto).

## Tests

Agregar a `tests/test_system1_output_animation.py` (o archivo nuevo análogo):

1. **Interpolación básica**: dos snapshots, `t=0` con partícula en `(0,0)` con `vx=1, vy=0`, y `t=2.0` (velocidad constante). Con `playback_duration=2, fps=1` → `n_frames=2, dt=1.0, t_frames=[0, 1]`. Verificar que el frame 1 contiene partícula en `(1, 0)`.
2. **Snapshot boundary**: snapshots en `t=0, 1, 2` con velocidades distintas; verificar que en `t_frame=1.0` se usa el snapshot en `t=1.0` (bisect_right boundary).
3. **n_frames = fps × playback_duration**: con fps=10 y playback=2, el GIF resultante debe tener 20 frames.
4. **Clampeo post-final**: simulación que termina en `t=3` pero `header.duration=5`. Con `playback_duration=1, fps=1` → `t_frames=[0,1,2,3,4]` (en tiempo físico 0,1,2,3,4), el último debe usar el snapshot de `t=3` sin extrapolación loca.
5. **playback_duration ≤ 0** y **fps ≤ 0**: ValueError.

Modificar si corresponde los tests existentes que asumen "1 frame = 1 snapshot".

## Verificación

```bash
.venv/bin/pytest -q
.venv/bin/python3 -m tp3_sds system1 validate-config --config configs/system1.example.toml
.venv/bin/python3 -m tp3_sds system1 run --config configs/system1.example.toml
.venv/bin/python3 -m tp3_sds system1 animate --input artifacts/system1/example_run.txt --output artifacts/system1/example_run.gif
# Abrir el GIF y confirmar: fluido, ~30s de playback, fps visualmente cercano a 20.
```

## Riesgos

- **File size**: a fps=20, 30s playback → 600 frames. Con GIF de 720×720 optimizado, ~3–5MB. Aceptable.
- **Tests actuales**: si alguno assertea que `número_de_frames_gif == número_de_snapshots`, hay que reescribirlo como `número_de_frames_gif == fps × playback_duration`. Revisar `test_system1_output_animation.py` al implementar.
- **Backward compat**: el contrato del archivo de snapshots no cambia. Archivos viejos siguen siendo animables (mismo header/body).
