from __future__ import annotations

import bisect
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tp3_sds.system1.output import ParsedSnapshotOutput, SnapshotHeader, parse_snapshot_output

DEFAULT_IMAGE_SIZE = 720
DEFAULT_MARGIN = 24
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
    particles: tuple[InterpolatedParticle, ...]


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
        interpolated = tuple(
            InterpolatedParticle(
                x=particle.x + dt * particle.vx,
                y=particle.y + dt * particle.vy,
                r=particle.r,
                g=particle.g,
                b=particle.b,
            )
            for particle in snap.particles
        )
        frames.append(AnimationFrame(t_frame=t_frame, n_used=snap.n_used, particles=interpolated))

    return frames


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


def _draw_circle(
    *,
    draw,
    center: float,
    radius: float,
    scale: float,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
    width: int,
    x: float = 0.0,
    y: float = 0.0,
) -> None:
    cx = center + x * scale
    cy = center - y * scale
    pixel_radius = radius * scale
    bounding_box = (
        cx - pixel_radius,
        cy - pixel_radius,
        cx + pixel_radius,
        cy + pixel_radius,
    )
    draw.ellipse(bounding_box, fill=fill, outline=outline, width=width)


def _load_pillow() -> dict[str, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Pillow is required for `tp3 system1 animate`. Install project dependencies first."
        ) from exc
    return {"Image": Image, "ImageDraw": ImageDraw, "ImageFont": ImageFont}
