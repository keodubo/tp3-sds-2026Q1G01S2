#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from tp3_sds.system1.animation import AnimationFrame, InterpolatedParticle, _load_pillow, _render_frame
from tp3_sds.system1.output import ParsedSnapshotOutput, parse_snapshot_output

BLUE = "#1A2E8A"
YELLOW = "#FFD700"
ORANGE = "#E67E22"
GREEN = "#2E8B57"
LIGHT = "#EEF1FA"
GRID = "#B8C2D6"

DEFAULT_STUDY_ROOT = REPO_ROOT / "artifacts/system1/studies/inciso-1.1"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "assets" / "generated"

plt.rcParams.update(
    {
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 12,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.edgecolor": "#303030",
        "axes.linewidth": 0.9,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)


@dataclass(frozen=True)
class FitLine:
    slope: float
    intercept: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Beamer presentation assets from an existing study root.")
    parser.add_argument(
        "--study-root",
        type=Path,
        default=DEFAULT_STUDY_ROOT,
        help="Study root containing aggregates/, raw/ and runs/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where generated PNG assets will be written.",
    )
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_xy_series(path: Path, x_key: str, y_key: str) -> list[tuple[float, float]]:
    return [(float(row[x_key]), float(row[y_key])) for row in read_csv_rows(path)]


def read_meta(path: Path) -> dict[str, str]:
    rows = read_csv_rows(path)
    if not rows:
        raise ValueError(f"Expected at least one row in {path}")
    return rows[0]


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def style_axis(axis, *, x_label: str, y_label: str) -> None:
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.grid(True, alpha=0.35, color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)


def save_figure(figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def fit_line(points: list[tuple[float, float]]) -> FitLine:
    if len(points) < 2:
        return FitLine(slope=0.0, intercept=0.0)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return FitLine(slope=0.0, intercept=y_mean)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in points) / denominator
    intercept = y_mean - slope * x_mean
    return FitLine(slope=slope, intercept=intercept)


def plot_errorbar_scatter(
    *,
    rows: list[dict[str, str]],
    x_key: str,
    y_key: str,
    err_key: str,
    y_label: str,
    output_path: Path,
    y_scale: str = "linear",
) -> None:
    xs = [int(row[x_key]) for row in rows]
    ys = [float(row[y_key]) for row in rows]
    errs = [float(row[err_key]) for row in rows]

    figure, axis = plt.subplots(figsize=(6.3, 4.0))
    axis.errorbar(
        xs,
        ys,
        yerr=errs,
        fmt="o",
        linestyle="none",
        color=BLUE,
        ecolor=BLUE,
        elinewidth=1.3,
        capsize=4,
        markersize=6.5,
    )
    axis.set_xticks(xs)
    axis.set_yscale(y_scale)
    style_axis(axis, x_label="N", y_label=y_label)
    save_figure(figure, output_path)


def plot_center_contacts_example(
    *,
    series_path: Path,
    output_path: Path,
) -> None:
    points = read_xy_series(series_path, "time", "c_fc")
    fit = fit_line(points)

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    fit_x = [xs[0], xs[-1]]
    fit_y = [fit.slope * x + fit.intercept for x in fit_x]

    figure, axis = plt.subplots(figsize=(4.4, 3.1))
    axis.step(xs, ys, where="post", color=BLUE, linewidth=1.8, label=r"$C_{fc}(t)$")
    axis.plot(fit_x, fit_y, color=ORANGE, linestyle="--", linewidth=1.6, label="Ajuste OLS")
    style_axis(axis, x_label="t (s)", y_label=r"$C_{fc}(t)$")
    axis.legend(loc="upper left")
    save_figure(figure, output_path)


def plot_used_fraction_example(
    *,
    resampled_series_path: Path,
    meta_path: Path,
    output_path: Path,
) -> None:
    points = read_xy_series(resampled_series_path, "time", "used_fraction")
    meta = read_meta(meta_path)
    stationary_time = float(meta["stationary_time"]) if meta.get("stationary_time") else math.nan
    fest = float(meta["fest"]) if meta.get("fest") else math.nan

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]

    figure, axis = plt.subplots(figsize=(4.4, 3.1))
    axis.plot(xs, ys, color=BLUE, linewidth=1.8, label=r"$F_u(t)$")
    if not math.isnan(stationary_time):
        axis.axvline(stationary_time, color=ORANGE, linestyle="--", linewidth=1.5, label=r"$t_{est}$")
    if not math.isnan(fest):
        axis.axhline(fest, color=GREEN, linestyle=":", linewidth=1.6, label=r"$F_{est}$")
    style_axis(axis, x_label="t (s)", y_label=r"$F_u(t)$")
    axis.set_ylim(bottom=0.0)
    axis.legend(loc="upper right")
    save_figure(figure, output_path)


def plot_radial_profile(*, rows: list[dict[str, str]], output_path: Path) -> None:
    radii = [float(row["radius_start"]) for row in rows]
    density_key = "density_mean" if "density_mean" in rows[0] else "density"
    velocity_key = "velocity_mean" if "velocity_mean" in rows[0] else "normal_velocity"
    flux_key = "flux_mean" if "flux_mean" in rows[0] else "inward_flux"
    densities = [float(row[density_key]) for row in rows]
    speeds = [abs(float(row[velocity_key])) for row in rows]
    fluxes = [float(row[flux_key]) for row in rows]

    figure, axis = plt.subplots(figsize=(6.3, 4.0))
    axis.plot(radii, densities, color=BLUE, marker="o", markersize=4.5, linewidth=1.6, label=r"$\langle \rho_f^{in}\rangle(S)$")
    axis.plot(radii, speeds, color=ORANGE, marker="s", markersize=4.2, linewidth=1.6, label=r"$|\langle v_f^{in}\rangle(S)|$")
    axis.plot(radii, fluxes, color=GREEN, marker="^", markersize=4.5, linewidth=1.6, label=r"$J_{in}(S)$")
    style_axis(axis, x_label="S (m)", y_label="Valor del perfil")
    axis.legend(loc="upper right")
    save_figure(figure, output_path)


def plot_near_shell_combined(*, rows: list[dict[str, str]], output_path: Path) -> None:
    xs = [int(row["n"]) for row in rows]
    panels = (
        ("density_mean", "density_std", r"$\langle \rho_f^{in}\rangle$"),
        ("velocity_mean", "velocity_std", r"$\langle v_f^{in}\rangle$"),
        ("flux_mean", "flux_std", r"$J_{in}$"),
    )

    figure, axes = plt.subplots(1, 3, figsize=(11.6, 4.0), sharex=True)
    for axis, (value_key, err_key, label) in zip(axes, panels, strict=True):
        ys = [float(row[value_key]) for row in rows]
        errs = [float(row[err_key]) for row in rows]
        axis.errorbar(
            xs,
            ys,
            yerr=errs,
            fmt="o",
            linestyle="none",
            color=BLUE,
            ecolor=BLUE,
            elinewidth=1.2,
            capsize=4,
            markersize=6.0,
        )
        axis.set_xticks(xs)
        style_axis(axis, x_label="N", y_label=label)
        axis.tick_params(axis="both", labelsize=11)
    figure.subplots_adjust(wspace=0.34)
    save_figure(figure, output_path)


def pick_representative_step(parsed: ParsedSnapshotOutput):
    if not parsed.steps:
        raise ValueError("Expected parsed output to contain at least one step.")
    return max(parsed.steps, key=lambda step: (step.n_used, step.time))


def render_still(*, snapshot_path: Path, output_path: Path) -> None:
    if not snapshot_path.exists():
        create_placeholder_still(
            output_path=output_path,
            title="Snapshot no disponible",
            lines=(
                "No existe el archivo fuente",
                snapshot_path.name,
                "",
                "Completar este still cuando",
                "el snapshot este en runs/.",
            ),
        )
        return

    parsed = parse_snapshot_output(snapshot_path)
    step = pick_representative_step(parsed)
    frame = AnimationFrame(
        t_frame=step.time,
        n_used=step.n_used,
        particles=tuple(
            InterpolatedParticle(
                x=particle.x,
                y=particle.y,
                r=particle.r,
                g=particle.g,
                b=particle.b,
            )
            for particle in step.particles
        ),
    )

    pillow = _load_pillow()
    image = _render_frame(
        pillow=pillow,
        header=parsed.header,
        animation_frame=frame,
        image_size=760,
        margin=24,
        show_step_label=False,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def create_placeholder_still(*, output_path: Path, title: str, lines: tuple[str, ...]) -> None:
    pillow = _load_pillow()
    image = pillow["Image"].new("RGB", (760, 760), color=(250, 250, 250))
    draw = pillow["ImageDraw"].Draw(image)
    font = pillow["ImageFont"].load_default()

    draw.rectangle((40, 40, 720, 720), outline=(26, 46, 138), width=4, fill=(255, 255, 255))
    draw.rectangle((40, 40, 720, 120), outline=(26, 46, 138), width=0, fill=(238, 241, 250))
    draw.text((60, 72), title, fill=(26, 46, 138), font=font)

    text = "\n".join(lines)
    draw.multiline_text((70, 180), text, fill=(40, 40, 40), font=font, spacing=8)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def extract_gif_poster(*, gif_path: Path, output_path: Path) -> None:
    pillow = _load_pillow()
    if not gif_path.exists():
        create_placeholder_still(
            output_path=output_path,
            title="GIF no disponible",
            lines=(
                "No existe el archivo fuente",
                gif_path.name,
                "",
                "Completar este poster cuando",
                "el GIF este disponible.",
            ),
        )
        return

    image = pillow["Image"].open(gif_path)
    frame_count = getattr(image, "n_frames", 1)
    frame_index = max(0, frame_count // 2)
    image.seek(frame_index)
    poster = image.convert("RGB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    poster.save(output_path)


def generate_assets(study_root: Path, output_dir: Path) -> list[Path]:
    ensure_output_dir(output_dir)

    aggregates_dir = study_root / "aggregates"
    raw_dir = study_root / "raw"
    runs_dir = study_root / "runs"

    runtime_rows = read_csv_rows(aggregates_dir / "runtime_vs_n.csv")
    scanning_rows = read_csv_rows(aggregates_dir / "scanning_rate_vs_n.csv")
    used_rows = read_csv_rows(aggregates_dir / "used_fraction_vs_n.csv")
    near_shell_rows = read_csv_rows(aggregates_dir / "near_shell_s2_vs_n.csv")
    radial_rows_500 = read_csv_rows(aggregates_dir / "radial_profile_n_500.csv")

    outputs = [
        output_dir / "runtime_vs_n.png",
        output_dir / "scanning_rate_vs_n.png",
        output_dir / "stationary_time_vs_n.png",
        output_dir / "fest_vs_n.png",
        output_dir / "near_shell_vs_n.png",
        output_dir / "center_contacts_n_50_seed_100.png",
        output_dir / "center_contacts_n_1000_seed_100.png",
        output_dir / "used_fraction_n_50_seed_100.png",
        output_dir / "used_fraction_n_1000_seed_100.png",
        output_dir / "radial_profile_n_500.png",
        output_dir / "still_n_50_seed_100.png",
        output_dir / "still_n_1000_seed_100.png",
        output_dir / "gif_poster_example_run.png",
        output_dir / "gif_poster_runtime_n_400.png",
        output_dir / "gif_poster_runtime_n_800_short.png",
    ]

    plot_errorbar_scatter(
        rows=runtime_rows,
        x_key="n",
        y_key="runtime_mean_seconds",
        err_key="runtime_std_seconds",
        y_label="Tiempo de ejecucion (s)",
        output_path=output_dir / "runtime_vs_n.png",
        y_scale="log",
    )
    plot_errorbar_scatter(
        rows=scanning_rows,
        x_key="n",
        y_key="j_mean",
        err_key="j_std",
        y_label=r"$J$ (s$^{-1}$)",
        output_path=output_dir / "scanning_rate_vs_n.png",
    )
    plot_errorbar_scatter(
        rows=used_rows,
        x_key="n",
        y_key="stationary_time_mean",
        err_key="stationary_time_std",
        y_label=r"$t_{stationary}$ (s)",
        output_path=output_dir / "stationary_time_vs_n.png",
    )
    plot_errorbar_scatter(
        rows=used_rows,
        x_key="n",
        y_key="fest_mean",
        err_key="fest_std",
        y_label=r"$F_{est}$",
        output_path=output_dir / "fest_vs_n.png",
    )
    plot_near_shell_combined(rows=near_shell_rows, output_path=output_dir / "near_shell_vs_n.png")
    plot_center_contacts_example(
        series_path=raw_dir / "n_50" / "seed_100" / "center_contacts.csv",
        output_path=output_dir / "center_contacts_n_50_seed_100.png",
    )
    plot_center_contacts_example(
        series_path=raw_dir / "n_1000" / "seed_100" / "center_contacts.csv",
        output_path=output_dir / "center_contacts_n_1000_seed_100.png",
    )
    plot_used_fraction_example(
        resampled_series_path=raw_dir / "n_50" / "seed_100" / "used_fraction_resampled.csv",
        meta_path=raw_dir / "n_50" / "seed_100" / "meta.csv",
        output_path=output_dir / "used_fraction_n_50_seed_100.png",
    )
    plot_used_fraction_example(
        resampled_series_path=raw_dir / "n_1000" / "seed_100" / "used_fraction_resampled.csv",
        meta_path=raw_dir / "n_1000" / "seed_100" / "meta.csv",
        output_path=output_dir / "used_fraction_n_1000_seed_100.png",
    )
    plot_radial_profile(rows=radial_rows_500, output_path=output_dir / "radial_profile_n_500.png")
    render_still(
        snapshot_path=runs_dir / "runtime_n_50_seed_100.txt",
        output_path=output_dir / "still_n_50_seed_100.png",
    )
    render_still(
        snapshot_path=runs_dir / "runtime_n_1000_seed_100.txt",
        output_path=output_dir / "still_n_1000_seed_100.png",
    )
    extract_gif_poster(
        gif_path=REPO_ROOT / "artifacts/system1/example_run.gif",
        output_path=output_dir / "gif_poster_example_run.png",
    )
    extract_gif_poster(
        gif_path=REPO_ROOT / "artifacts/system1/bench/runs/runtime_n_400.gif",
        output_path=output_dir / "gif_poster_runtime_n_400.png",
    )
    extract_gif_poster(
        gif_path=REPO_ROOT / "artifacts/system1/bench800/runs/runtime_n_800_short.gif",
        output_path=output_dir / "gif_poster_runtime_n_800_short.png",
    )

    return outputs


def main() -> int:
    args = parse_args()
    outputs = generate_assets(args.study_root.resolve(), args.output_dir.resolve())
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
