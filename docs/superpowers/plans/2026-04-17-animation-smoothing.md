# Animation Smoothing (Uniform-Time Interpolation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar los microcuts de la animación en colisiones resampleando uniformemente en tiempo físico con interpolación lineal exacta entre snapshots, bumpear fps default de 12 → 20 y agregar flag CLI `--playback-duration SECONDS` (default 30.0).

**Architecture:** Extraer un helper puro `build_animation_frames(parsed, fps, playback_duration) -> list[AnimationFrame]` que resamplea uniformemente en tiempo físico e interpola posiciones a partir del snapshot anclaje (exacto porque entre eventos las velocidades son constantes). `render_snapshot_animation` pasa a ser un orquestador: parsea → construye frames → renderiza uno por uno. CLI agrega el flag.

**Tech Stack:** Python 3.11, dataclasses, stdlib `bisect`, Pillow, pytest.

**Spec:** `docs/superpowers/specs/2026-04-17-animation-smoothing-design.md`

---

## File Structure

**Modify (code):**
- `src/tp3_sds/system1/animation.py` — agregar `InterpolatedParticle`, `AnimationFrame`, `build_animation_frames`, `DEFAULT_PLAYBACK_DURATION_SECONDS`. Reescribir `render_snapshot_animation` y `_render_frame`.
- `src/tp3_sds/cli.py` — agregar `--playback-duration` al parser de `animate`, cambiar default de `--fps` de 12 a 20, pasar el nuevo param a la función.

**Modify (tests):**
- `tests/test_system1_output_animation.py` — agregar 7 tests para `build_animation_frames` + actualizar el test CLI existente para pasar `--playback-duration 0.5`.

**No crear archivos nuevos.** No tocar el formato de snapshot, ni el simulador, ni los configs TOML.

---

## Pre-flight check

- [ ] **Step 1: Verificar working tree limpio**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git status
```
Expected: "On branch main ... nothing to commit, working tree clean" con HEAD en `dcb0e6b` (el spec).

- [ ] **Step 2: Baseline pytest**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/pytest -q
```
Expected: 25 passed. Si falla algo acá, detener y reportar.

---

### Task 1: Helper `build_animation_frames` con tests (TDD full cycle)

**Files:**
- Modify: `src/tp3_sds/system1/animation.py` (agregar dataclasses + helper)
- Modify: `tests/test_system1_output_animation.py` (agregar 7 tests al final)

- [ ] **Step 1: Escribir los 7 tests (fail por ahora porque el helper no existe)**

Agregar estos imports al top de `tests/test_system1_output_animation.py` (si no están):

```python
from tp3_sds.system1.animation import (
    AnimationFrame,
    InterpolatedParticle,
    build_animation_frames,
)
from tp3_sds.system1.output import ParsedParticle, ParsedSnapshotOutput, ParsedStep, SnapshotHeader
```

Agregar estos 7 tests al final del archivo:

```python
def _make_parsed(*, duration: float, steps: list[ParsedStep]) -> ParsedSnapshotOutput:
    header = SnapshotHeader(
        duration=duration,
        particle_count=len(steps[0].particles) if steps else 0,
        domain_diameter=80.0,
        obstacle_radius=1.0,
        particle_radius=1.0,
        snapshot_every=1,
        fresh_color=(0, 255, 0),
        used_color=(148, 0, 211),
    )
    return ParsedSnapshotOutput(header=header, steps=steps)


def _p(id_: int, x: float, y: float, vx: float, vy: float) -> ParsedParticle:
    return ParsedParticle(id=id_, x=x, y=y, vx=vx, vy=vy, state="fresh", r=0, g=255, b=0)


def test_build_animation_frames_linear_interpolation_exact() -> None:
    parsed = _make_parsed(
        duration=2.0,
        steps=[
            ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 1.0, 0.0)]),
            ParsedStep(event_id=1, time=2.0, n_used=0, particles=[_p(0, 2.0, 0.0, 1.0, 0.0)]),
        ],
    )
    frames = build_animation_frames(parsed=parsed, fps=1, playback_duration=2.0)
    assert len(frames) == 2
    assert frames[0].t_frame == 0.0
    assert frames[0].particles[0].x == 0.0
    assert frames[1].t_frame == 1.0
    assert frames[1].particles[0].x == 1.0
    assert frames[1].particles[0].y == 0.0


def test_build_animation_frames_snapshot_boundary_uses_right_anchor() -> None:
    parsed = _make_parsed(
        duration=2.0,
        steps=[
            ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 1.0, 0.0)]),
            ParsedStep(event_id=1, time=1.0, n_used=0, particles=[_p(0, 1.0, 0.0, 0.0, 1.0)]),
            ParsedStep(event_id=2, time=2.0, n_used=0, particles=[_p(0, 1.0, 1.0, 0.0, 1.0)]),
        ],
    )
    frames = build_animation_frames(parsed=parsed, fps=1, playback_duration=2.0)
    assert frames[1].t_frame == 1.0
    assert frames[1].particles[0].x == 1.0
    assert frames[1].particles[0].y == 0.0


def test_build_animation_frames_count_equals_fps_times_duration() -> None:
    parsed = _make_parsed(
        duration=5.0,
        steps=[ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 0.0, 0.0)])],
    )
    frames = build_animation_frames(parsed=parsed, fps=10, playback_duration=2.0)
    assert len(frames) == 20


def test_build_animation_frames_clamps_past_last_snapshot() -> None:
    parsed = _make_parsed(
        duration=5.0,
        steps=[
            ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 1.0, 0.0)]),
            ParsedStep(event_id=1, time=3.0, n_used=0, particles=[_p(0, 3.0, 0.0, 1.0, 0.0)]),
        ],
    )
    frames = build_animation_frames(parsed=parsed, fps=1, playback_duration=5.0)
    assert len(frames) == 5
    assert frames[-1].t_frame == 3.0
    assert frames[-1].particles[0].x == 3.0


def test_build_animation_frames_preserves_colors_and_n_used() -> None:
    used_particle = ParsedParticle(id=0, x=0.0, y=0.0, vx=0.0, vy=0.0, state="used", r=148, g=0, b=211)
    parsed = _make_parsed(
        duration=1.0,
        steps=[ParsedStep(event_id=0, time=0.0, n_used=1, particles=[used_particle])],
    )
    frames = build_animation_frames(parsed=parsed, fps=2, playback_duration=1.0)
    assert frames[0].n_used == 1
    assert (frames[0].particles[0].r, frames[0].particles[0].g, frames[0].particles[0].b) == (148, 0, 211)


def test_build_animation_frames_rejects_non_positive_fps() -> None:
    parsed = _make_parsed(
        duration=1.0,
        steps=[ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 0.0, 0.0)])],
    )
    with pytest.raises(ValueError, match="fps"):
        build_animation_frames(parsed=parsed, fps=0, playback_duration=1.0)


def test_build_animation_frames_rejects_non_positive_playback_duration() -> None:
    parsed = _make_parsed(
        duration=1.0,
        steps=[ParsedStep(event_id=0, time=0.0, n_used=0, particles=[_p(0, 0.0, 0.0, 0.0, 0.0)])],
    )
    with pytest.raises(ValueError, match="playback_duration"):
        build_animation_frames(parsed=parsed, fps=10, playback_duration=0.0)
```

- [ ] **Step 2: Correr los tests nuevos para confirmar que fallan**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/pytest tests/test_system1_output_animation.py -k "build_animation_frames" -q
```
Expected: FAIL — `ImportError: cannot import name 'AnimationFrame' from 'tp3_sds.system1.animation'` o similar.

- [ ] **Step 3: Implementar el helper en `animation.py`**

En `src/tp3_sds/system1/animation.py`, agregar estos imports al top (después del `from __future__`):

```python
import bisect
from dataclasses import dataclass
```

Agregar la constante y dataclasses después de `DEFAULT_MARGIN = 24`:

```python
DEFAULT_PLAYBACK_DURATION_SECONDS = 30.0


@dataclass(frozen=True)
class InterpolatedParticle:
    x: float
    y: float
    r: int
    g: int
    b: int


@dataclass(frozen=True)
class AnimationFrame:
    t_frame: float
    n_used: int
    particles: list[InterpolatedParticle]
```

Necesitamos `ParsedSnapshotOutput` en el import; actualizar la línea existente:

```python
from tp3_sds.system1.output import ParsedSnapshotOutput, ParsedStep, SnapshotHeader, parse_snapshot_output
```

Agregar el helper (entre las dataclasses y `render_snapshot_animation`):

```python
def build_animation_frames(
    *,
    parsed: ParsedSnapshotOutput,
    fps: int,
    playback_duration: float,
) -> list[AnimationFrame]:
    """Resample snapshots uniformly in physical time with exact linear interpolation.

    Between two events no particle changes velocity, so `pos(t) = anchor.pos + (t - anchor.time) * anchor.vel` is exact.
    """
    if fps <= 0:
        raise ValueError("fps must be greater than zero.")
    if playback_duration <= 0:
        raise ValueError("playback_duration must be greater than zero.")
    if not parsed.steps:
        raise ValueError("parsed output must contain at least one step.")

    n_frames = max(1, int(round(fps * playback_duration)))
    tf = parsed.header.duration
    dt_physical = tf / n_frames
    snapshot_times = [step.time for step in parsed.steps]
    last_snapshot_time = parsed.steps[-1].time

    frames: list[AnimationFrame] = []
    for i in range(n_frames):
        t_frame_raw = i * dt_physical
        t_frame = min(t_frame_raw, last_snapshot_time)
        k = max(0, bisect.bisect_right(snapshot_times, t_frame) - 1)
        snap = parsed.steps[k]
        dt = t_frame - snap.time
        interpolated = [
            InterpolatedParticle(
                x=particle.x + dt * particle.vx,
                y=particle.y + dt * particle.vy,
                r=particle.r,
                g=particle.g,
                b=particle.b,
            )
            for particle in snap.particles
        ]
        frames.append(AnimationFrame(t_frame=t_frame, n_used=snap.n_used, particles=interpolated))

    return frames
```

- [ ] **Step 4: Correr los tests nuevos — deben pasar**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/pytest tests/test_system1_output_animation.py -k "build_animation_frames" -q
```
Expected: 7 passed.

- [ ] **Step 5: Correr la suite entera — nada más roto**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/pytest -q
```
Expected: 32 passed (25 previos + 7 nuevos). El test CLI `test_system1_animate_cli_writes_gif` **todavía** debe pasar (todavía usa la función vieja; recién se refactora en Task 2).

Si falla el test CLI antes de Task 2 → detener. Significa que el helper rompió algún import o signature. Investigar.

- [ ] **Step 6: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add src/tp3_sds/system1/animation.py tests/test_system1_output_animation.py
git commit -m "$(cat <<'EOF'
feat(animation): add build_animation_frames helper with uniform-time resampling

Introduces InterpolatedParticle, AnimationFrame, and build_animation_frames
to resample snapshots uniformly in physical time with exact linear
interpolation between events. Between two events particle velocity is
constant, so the interpolation is not an approximation. Helper comes with
7 tests covering linear interpolation, snapshot boundary selection, frame
count = fps * playback_duration, post-end clamping, color/n_used
preservation, and input validation.

Ref: docs/superpowers/specs/2026-04-17-animation-smoothing-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Conectar el helper con `render_snapshot_animation` + `_render_frame`

**Files:**
- Modify: `src/tp3_sds/system1/animation.py` (reescribir dos funciones)
- Modify: `tests/test_system1_output_animation.py` (agregar `--playback-duration 0.5` al test CLI)

- [ ] **Step 1: Actualizar el test CLI existente para pasar `--playback-duration 0.5`**

En `tests/test_system1_output_animation.py`, reemplazar el contenido actual de la lista de args en `test_system1_animate_cli_writes_gif`:

```python
    assert main(
        [
            "system1",
            "animate",
            "--input",
            str(snapshot_path),
            "--output",
            str(output_path),
            "--fps",
            "8",
            "--show-step-label",
        ]
    ) == 0
```
Por:
```python
    assert main(
        [
            "system1",
            "animate",
            "--input",
            str(snapshot_path),
            "--output",
            str(output_path),
            "--fps",
            "8",
            "--playback-duration",
            "0.5",
            "--show-step-label",
        ]
    ) == 0
```

(El test sigue verificando que el GIF existe y tiene tamaño > 0; el `--playback-duration 0.5` mantiene el test rápido — sólo 4 frames con fps=8.)

- [ ] **Step 2: Reescribir `render_snapshot_animation` para usar el helper**

En `src/tp3_sds/system1/animation.py`, reemplazar la función `render_snapshot_animation` completa (actualmente líneas ~12-54). La versión nueva:

```python
def render_snapshot_animation(
    *,
    input_path: Path,
    output_path: Path,
    fps: int = 20,
    playback_duration: float = DEFAULT_PLAYBACK_DURATION_SECONDS,
    show_step_label: bool = False,
    image_size: int = DEFAULT_IMAGE_SIZE,
    margin: int = DEFAULT_MARGIN,
) -> Path:
    if image_size <= 2 * margin:
        raise ValueError("image_size must be larger than twice the margin.")

    pillow = _load_pillow()
    snapshot_output = parse_snapshot_output(input_path)
    animation_frames = build_animation_frames(
        parsed=snapshot_output,
        fps=fps,
        playback_duration=playback_duration,
    )
    frames = [
        _render_frame(
            pillow=pillow,
            header=snapshot_output.header,
            animation_frame=animation_frame,
            image_size=image_size,
            margin=margin,
            show_step_label=show_step_label,
        )
        for animation_frame in animation_frames
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame_duration_ms = max(1, round(1000 / fps))
    first_frame, *remaining_frames = frames
    first_frame.save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=remaining_frames,
        duration=frame_duration_ms,
        loop=0,
        disposal=2,
    )
    return output_path
```

Nota: la validación `if fps <= 0` se eliminó porque `build_animation_frames` ya la hace (y dispara más temprano). La validación `if not frames` también se saca porque `build_animation_frames` garantiza ≥ 1 frame.

- [ ] **Step 3: Reescribir `_render_frame` para consumir `AnimationFrame`**

En `src/tp3_sds/system1/animation.py`, reemplazar la función `_render_frame` completa. La nueva versión:

```python
def _render_frame(
    *,
    pillow: dict[str, Any],
    header: SnapshotHeader,
    animation_frame: AnimationFrame,
    image_size: int,
    margin: int,
    show_step_label: bool,
):
    image = pillow["Image"].new("RGB", (image_size, image_size), color=(250, 250, 250))
    draw = pillow["ImageDraw"].Draw(image)
    outer_radius = header.domain_diameter / 2.0
    scale = (image_size - 2 * margin) / (2.0 * outer_radius)
    center = image_size / 2.0
    line_width = max(2, image_size // 180)

    _draw_circle(
        draw=draw,
        center=center,
        radius=outer_radius,
        scale=scale,
        fill=(255, 255, 255),
        outline=(20, 20, 20),
        width=line_width,
    )
    _draw_circle(
        draw=draw,
        center=center,
        radius=header.obstacle_radius,
        scale=scale,
        fill=(210, 210, 210),
        outline=(90, 90, 90),
        width=line_width,
    )

    particle_outline = (30, 30, 30)
    particle_width = max(1, line_width - 1)
    for particle in animation_frame.particles:
        _draw_circle(
            draw=draw,
            center=center,
            radius=header.particle_radius,
            scale=scale,
            fill=(particle.r, particle.g, particle.b),
            outline=particle_outline,
            width=particle_width,
            x=particle.x,
            y=particle.y,
        )

    if show_step_label:
        font = pillow["ImageFont"].load_default()
        label = f"t={animation_frame.t_frame:.3f} s  used={animation_frame.n_used}"
        text_box = draw.textbbox((0, 0), label, font=font)
        padding = 6
        box = (
            margin,
            margin,
            margin + (text_box[2] - text_box[0]) + 2 * padding,
            margin + (text_box[3] - text_box[1]) + 2 * padding,
        )
        draw.rounded_rectangle(box, radius=6, fill=(255, 255, 255), outline=(120, 120, 120), width=1)
        draw.text((box[0] + padding, box[1] + padding), label, fill=(20, 20, 20), font=font)

    return image
```

Cambios respecto a la versión previa:
- Parámetro `step: ParsedStep` → `animation_frame: AnimationFrame`.
- El loop de partículas ahora itera `animation_frame.particles` (instancias de `InterpolatedParticle` con `x, y, r, g, b` ya computados).
- Label cambia de `f"event={step.event_id}  t={step.time:.3f} s  used={step.n_used}"` a `f"t={animation_frame.t_frame:.3f} s  used={animation_frame.n_used}"`.

Remover el import de `ParsedStep` si ya no se usa en ninguna función de este archivo (verificar con búsqueda). Si no hay más referencias, sacarlo del import al top.

- [ ] **Step 4: Correr tests — la suite entera debe pasar**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/pytest -q
```
Expected: 32 passed. El test CLI pasa ahora con la nueva firma (porque le pasamos `--playback-duration 0.5` en Step 1).

**Si falla `test_system1_animate_cli_writes_gif`**: revisar que el CLI todavía acepta `--playback-duration` — si no, la Task 3 debe ejecutarse antes. En el flujo normal Task 3 sigue a Task 2, pero el CLI no acepta el flag hasta Task 3. Por eso hay que ejecutar Task 3 **inmediatamente** después.

Nota importante: Step 1 de Task 2 modifica el test CLI para pasar `--playback-duration 0.5`. Pero el CLI parser todavía no reconoce ese flag hasta Task 3 Step 1. Por lo tanto, **el test CLI va a fallar entre Task 2 y Task 3**. Esto es un red state aceptable de breve duración. La alternativa sería ejecutar Task 3 antes que este step, pero entonces la CLI pasaría un kwarg desconocido. El camino cuidadoso:

- Temporalmente, Task 2 Step 4 puede saltarse el test CLI: `.venv/bin/pytest -q --deselect tests/test_system1_output_animation.py::test_system1_animate_cli_writes_gif` → expected 31 passed.
- Task 3 Step 4 corre la suite entera y ahí sí debe volver a 32 passed.

Ajustar Step 4 a:

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/pytest -q --deselect tests/test_system1_output_animation.py::test_system1_animate_cli_writes_gif
```
Expected: 31 passed. El CLI test se re-habilita al final de Task 3.

- [ ] **Step 5: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add src/tp3_sds/system1/animation.py tests/test_system1_output_animation.py
git commit -m "$(cat <<'EOF'
refactor(animation): render_snapshot_animation consume AnimationFrame

Reescribe render_snapshot_animation para orquestar parse →
build_animation_frames → render, y adapta _render_frame a recibir
AnimationFrame con partículas ya interpoladas. Cambia el label
opcional de "event=X t=Y used=Z" a "t=X.XXX s used=Z". Default de
fps pasa de 12 a 20; nuevo parámetro playback_duration con default
DEFAULT_PLAYBACK_DURATION_SECONDS (30s).

El test CLI pasa ahora --playback-duration 0.5 para mantenerse rápido;
el test falla temporalmente hasta que el CLI parser agregue el flag
en la Task 3 de este plan.

Ref: docs/superpowers/specs/2026-04-17-animation-smoothing-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: CLI — flag `--playback-duration` + default fps

**Files:**
- Modify: `src/tp3_sds/cli.py` (parser del subcomando `animate` + invocación)

- [ ] **Step 1: Agregar el flag y cambiar el default de `--fps`**

En `src/tp3_sds/cli.py`, localizar el bloque del subparser `animate` (actualmente líneas ~52-56):

```python
    animate_parser = system1_subparsers.add_parser("animate", help="Render a GIF animation from a System 1 snapshot file.")
    animate_parser.add_argument("--input", required=True, type=Path)
    animate_parser.add_argument("--output", required=True, type=Path)
    animate_parser.add_argument("--fps", type=int, default=12)
    animate_parser.add_argument("--show-step-label", action="store_true")
```

Reemplazarlo por:

```python
    animate_parser = system1_subparsers.add_parser("animate", help="Render a GIF animation from a System 1 snapshot file.")
    animate_parser.add_argument("--input", required=True, type=Path)
    animate_parser.add_argument("--output", required=True, type=Path)
    animate_parser.add_argument("--fps", type=int, default=20)
    animate_parser.add_argument(
        "--playback-duration",
        type=float,
        default=30.0,
        help="Playback duration of the GIF in seconds (controls total frame count together with --fps).",
    )
    animate_parser.add_argument("--show-step-label", action="store_true")
```

- [ ] **Step 2: Pasar `playback_duration` al invocar la función**

En `src/tp3_sds/cli.py`, localizar la invocación actual de `render_snapshot_animation` (alrededor de la línea 189):

```python
            render_snapshot_animation(
                input_path=input_path,
                output_path=output_path,
                fps=args.fps,
                show_step_label=args.show_step_label,
            )
```

Reemplazarlo por:

```python
            render_snapshot_animation(
                input_path=input_path,
                output_path=output_path,
                fps=args.fps,
                playback_duration=args.playback_duration,
                show_step_label=args.show_step_label,
            )
```

- [ ] **Step 3: Correr la suite entera — todo verde**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/pytest -q
```
Expected: **32 passed**. El test CLI `test_system1_animate_cli_writes_gif` ahora pasa porque el flag `--playback-duration` existe.

- [ ] **Step 4: Smoke manual del help del CLI**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/python3 -m tp3_sds system1 animate --help
```
Expected: la salida muestra `--fps` con default 20 y `--playback-duration` con default 30.0 y el help text "Playback duration of the GIF in seconds...".

- [ ] **Step 5: Commit**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
git add src/tp3_sds/cli.py
git commit -m "$(cat <<'EOF'
feat(cli): add --playback-duration and bump --fps default to 20

El subcomando system1 animate acepta --playback-duration SECONDS
(default 30.0) y el default de --fps pasa de 12 a 20. Ambos se
propagan a render_snapshot_animation.

Ref: docs/superpowers/specs/2026-04-17-animation-smoothing-design.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Verificación end-to-end (sin commit)

**Files:** ninguno.

- [ ] **Step 1: pytest limpio**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/pytest -q
```
Expected: 32 passed.

- [ ] **Step 2: Generar un GIF real y confirmar que funciona**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/python3 -m tp3_sds system1 run --config configs/system1.example.toml
.venv/bin/python3 -m tp3_sds system1 animate --input artifacts/system1/example_run.txt --output artifacts/system1/example_run.gif
```
Expected: comandos exit 0. Mensaje "Wrote animation to ...". `artifacts/system1/example_run.gif` existe.

- [ ] **Step 3: Verificar tamaño y cantidad de frames aprox**

Run:
```bash
cd /home/nico/Desktop/simu/tp3-sds-2026Q1G01S2
.venv/bin/python3 -c "from PIL import Image; im = Image.open('artifacts/system1/example_run.gif'); print(f'n_frames={im.n_frames}, size={im.size}')"
ls -lh artifacts/system1/example_run.gif
```
Expected: `n_frames=600` (= 20 fps × 30 s default), `size=(720, 720)`. Tamaño del GIF en el orden de 1–10 MB.

Si `n_frames` ≠ 600, el cálculo del helper está mal — investigar.

- [ ] **Step 4: (Opcional) Abrir el GIF y confirmar visualmente que la animación es fluida y no tiene microcuts durante las colisiones.**

El spec especifica que el fix debe eliminar los microcuts. Esto es un check visual — no automatizable en este plan. El usuario puede abrir el GIF en un navegador o visor de imágenes.

---

## Self-Review

**1. Spec coverage:**
- §1 Scope: "reescribir loop de frames + nuevo flag + default fps 20 + adaptar label" → Tasks 1–3 ✓
- §2 Algoritmo: pseudocódigo matchea exactamente `build_animation_frames` en Task 1 Step 3 ✓
- §3.1 Cambios en animation.py (new params, dataclasses, helper, _render_frame adaptation) → Tasks 1 y 2 ✓
- §3.2 Cambios en cli.py (flag + default fps + pass-through) → Task 3 ✓
- §4 Edge cases: fps ≤ 0 (test), playback_duration ≤ 0 (test), n_frames=0 clamp (`max(1, ...)`), past-last-snapshot clamp (test), único snapshot (cubre el test de count) → Task 1 ✓
- §5 Tests (7 nuevos + update CLI test) → Task 1 Step 1 y Task 2 Step 1 ✓
- §6 Verificación → Task 4 ✓

Gap: el test "único snapshot disponible" no está explícito. La cobertura indirecta viene de `test_build_animation_frames_count_equals_fps_times_duration` que usa un solo step. Queda cubierto funcionalmente — no agrego test adicional para no inflar.

**2. Placeholder scan:** todos los steps tienen código concreto, comandos exactos, expected outputs. Ningún "TBD / TODO / implement later".

**3. Type consistency:**
- `AnimationFrame.t_frame: float`, `n_used: int`, `particles: list[InterpolatedParticle]` — usado así en `_render_frame` ✓
- `InterpolatedParticle(x, y, r, g, b)` — creado con estos 5 campos en `build_animation_frames` y consumido con estos mismos 5 campos en `_render_frame` ✓
- `render_snapshot_animation(..., fps=20, playback_duration=DEFAULT_PLAYBACK_DURATION_SECONDS, ...)` — kwargs coinciden entre la definición (Task 2 Step 2) y el call site del CLI (Task 3 Step 2) ✓
- `build_animation_frames(parsed=..., fps=..., playback_duration=...)` — kwargs only; usados consistentes en tests (Task 1 Step 1) y en `render_snapshot_animation` (Task 2 Step 2) ✓

**4. Granularidad:** cada step es una edición o un comando individual (2–5 min). 3 commits atómicos + 1 task de verificación sin commit. TDD respetado en Task 1 (test → fail → implement → pass → commit).
