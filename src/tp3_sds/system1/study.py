from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from tp3_sds.system1.analysis import (
    detect_stationary,
    linear_regression_slope,
    mean_std,
    median_value,
    resample_zero_order_hold,
)
from tp3_sds.system1.config import StudyConfig, build_run_config_from_study, validate_study_config
from tp3_sds.system1.observables import RadialProfileBin, aggregate_radial_profile_snapshots
from tp3_sds.system1.plotting import (
    plot_dual_errorbar_series,
    plot_errorbar_series,
    plot_near_shell_vs_n,
    plot_radial_profiles,
)
from tp3_sds.system1.simulation import SimulationEngine, run_simulation

NEAR_S_TARGET = 2.0


@dataclass(frozen=True)
class AnalysisRunResult:
    particle_count: int
    seed: int
    output_path: Path
    final_time: float
    processed_events: int
    snapshots_written: int
    stationary_time: float | None
    scanning_rate: float
    fest: float | None
    radial_profile: list[RadialProfileBin] | None
    near_shell: RadialProfileBin | None
    status: str


@dataclass(frozen=True)
class StudyResult:
    study_root: Path
    particle_counts: list[int]
    summary_path: Path
    generated_files: list[Path]


def run_study(study_config: StudyConfig, *, config_path: Path | None = None) -> StudyResult:
    validation = validate_study_config(study_config)
    if not validation.is_valid:
        raise ValueError("; ".join(validation.errors))

    study_root = study_config.output.artifacts_root / study_config.output.study_id
    runs_dir = study_root / "runs"
    raw_dir = study_root / "raw"
    aggregates_dir = study_root / "aggregates"
    figures_dir = study_root / "figures"
    for directory in (runs_dir, raw_dir, aggregates_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    runtime_rows: list[dict[str, object]] = []
    scanning_rows: list[dict[str, object]] = []
    used_rows: list[dict[str, object]] = []
    near_shell_rows: list[dict[str, object]] = []
    generated_files: list[Path] = []
    accepted_counts: list[int] = []
    analysis_outcomes_by_n: dict[int, list[AnalysisRunResult]] = {}

    for particle_count in study_config.planned_counts():
        accepted_counts.append(particle_count)
        seeds = study_config.seeds()

        runtime_samples: list[float] = []
        for repetition_index, seed in enumerate(seeds, start=1):
            runtime_output = runs_dir / f"runtime_n_{particle_count}_seed_{seed}.txt"
            runtime_config = build_run_config_from_study(
                study_config,
                count=particle_count,
                seed=seed,
                duration=study_config.runtime_duration,
                output_path=runtime_output,
            )
            runtime_start = perf_counter()
            run_simulation(runtime_config, config_path=config_path)
            runtime_elapsed = perf_counter() - runtime_start
            runtime_samples.append(runtime_elapsed)
            generated_files.append(runtime_output)
            _write_runtime_metadata(
                raw_dir / f"runtime_n_{particle_count}_seed_{seed}.csv",
                particle_count=particle_count,
                seed=seed,
                repetition_index=repetition_index,
                runtime_seconds=runtime_elapsed,
            )

        runtime_mean, runtime_std = mean_std(runtime_samples)
        runtime_rows.append(
            {
                "n": particle_count,
                "runtime_mean_seconds": runtime_mean,
                "runtime_std_seconds": runtime_std,
                "repetitions": len(runtime_samples),
                "runtime_median_seconds": median_value(runtime_samples),
            }
        )

        analysis_runs: list[AnalysisRunResult] = []
        for seed in seeds:
            outcome = _run_analysis_realization(
                study_config,
                particle_count=particle_count,
                seed=seed,
                runs_dir=runs_dir,
                raw_dir=raw_dir,
                config_path=config_path,
            )
            analysis_runs.append(outcome)
            generated_files.append(outcome.output_path)
        analysis_outcomes_by_n[particle_count] = analysis_runs

        scanning_values = [run.scanning_rate for run in analysis_runs]
        scanning_mean, scanning_std = mean_std(scanning_values)
        scanning_rows.append(
            {
                "n": particle_count,
                "j_mean": scanning_mean,
                "j_std": scanning_std,
                "repetitions": len(scanning_values),
            }
        )

        stationary_runs = [run for run in analysis_runs if run.status == "stationary" and run.fest is not None]
        stationary_times = [run.stationary_time for run in stationary_runs if run.stationary_time is not None]
        fest_values = [run.fest for run in stationary_runs if run.fest is not None]
        stationary_time_mean, stationary_time_std = mean_std([float(value) for value in stationary_times])
        fest_mean, fest_std = mean_std([float(value) for value in fest_values])
        used_rows.append(
            {
                "n": particle_count,
                "stationary_time_mean": stationary_time_mean,
                "stationary_time_std": stationary_time_std,
                "fest_mean": fest_mean,
                "fest_std": fest_std,
                "stationary_realizations": len(stationary_runs),
                "total_realizations": len(analysis_runs),
            }
        )

        if stationary_runs:
            radial_profile_output = aggregates_dir / f"radial_profile_n_{particle_count}.csv"
            radial_profile_summary = _write_aggregated_radial_profile(radial_profile_output, stationary_runs)
            generated_files.append(radial_profile_output)
            near_shell_rows.append(
                {
                    "n": particle_count,
                    "density_mean": radial_profile_summary["near_shell"]["density_mean"],
                    "density_std": radial_profile_summary["near_shell"]["density_std"],
                    "velocity_mean": radial_profile_summary["near_shell"]["velocity_mean"],
                    "velocity_std": radial_profile_summary["near_shell"]["velocity_std"],
                    "flux_mean": radial_profile_summary["near_shell"]["flux_mean"],
                    "flux_std": radial_profile_summary["near_shell"]["flux_std"],
                }
            )
            if study_config.output.generate_figures:
                figure_path = figures_dir / f"radial_profile_n_{particle_count}.png"
                plot_radial_profiles(
                    output_path=figure_path,
                    radial_profile=radial_profile_summary["mean_profile"],
                    particle_count=particle_count,
                )
                generated_files.append(figure_path)

        if study_config.counts_mode == "auto" and median_value(runtime_samples) > study_config.runtime_limit_seconds:
            break

    runtime_csv = aggregates_dir / "runtime_vs_n.csv"
    scanning_csv = aggregates_dir / "scanning_rate_vs_n.csv"
    used_csv = aggregates_dir / "used_fraction_vs_n.csv"
    near_shell_csv = aggregates_dir / "near_shell_s2_vs_n.csv"
    _write_csv(runtime_csv, runtime_rows)
    _write_csv(scanning_csv, scanning_rows)
    _write_csv(used_csv, used_rows)
    _write_csv(near_shell_csv, near_shell_rows)
    generated_files.extend([runtime_csv, scanning_csv, used_csv, near_shell_csv])

    if study_config.output.generate_figures and accepted_counts:
        runtime_figure = figures_dir / "runtime_vs_n.png"
        scanning_figure = figures_dir / "scanning_rate_vs_n.png"
        used_figure = figures_dir / "used_fraction_vs_n.png"
        near_shell_figure = figures_dir / "near_shell_s2_vs_n.png"
        plot_errorbar_series(
            output_path=runtime_figure,
            xs=[int(row["n"]) for row in runtime_rows],
            ys=[float(row["runtime_mean_seconds"]) for row in runtime_rows],
            yerr=[float(row["runtime_std_seconds"]) for row in runtime_rows],
            title="System 1 runtime versus N",
            xlabel="N",
            ylabel="Runtime (s)",
        )
        plot_errorbar_series(
            output_path=scanning_figure,
            xs=[int(row["n"]) for row in scanning_rows],
            ys=[float(row["j_mean"]) for row in scanning_rows],
            yerr=[float(row["j_std"]) for row in scanning_rows],
            title="System 1 scanning rate versus N",
            xlabel="N",
            ylabel="J",
        )
        plot_dual_errorbar_series(
            output_path=used_figure,
            xs=[int(row["n"]) for row in used_rows],
            left_values=[float(row["stationary_time_mean"]) for row in used_rows],
            left_errors=[float(row["stationary_time_std"]) for row in used_rows],
            right_values=[float(row["fest_mean"]) for row in used_rows],
            right_errors=[float(row["fest_std"]) for row in used_rows],
            left_label="t_stationary (s)",
            right_label="F_est",
            title="System 1 used-fraction metrics versus N",
        )
        plot_near_shell_vs_n(
            output_path=near_shell_figure,
            xs=[int(row["n"]) for row in near_shell_rows],
            density_values=[float(row["density_mean"]) for row in near_shell_rows],
            density_errors=[float(row["density_std"]) for row in near_shell_rows],
            velocity_values=[float(row["velocity_mean"]) for row in near_shell_rows],
            velocity_errors=[float(row["velocity_std"]) for row in near_shell_rows],
            flux_values=[float(row["flux_mean"]) for row in near_shell_rows],
            flux_errors=[float(row["flux_std"]) for row in near_shell_rows],
        )
        generated_files.extend([runtime_figure, scanning_figure, used_figure, near_shell_figure])

    summary_path = study_root / "summary.md"
    summary_path.write_text(
        _render_summary(
            study_config=study_config,
            particle_counts=accepted_counts,
            runtime_rows=runtime_rows,
            scanning_rows=scanning_rows,
            used_rows=used_rows,
            near_shell_rows=near_shell_rows,
            analysis_outcomes_by_n=analysis_outcomes_by_n,
        ),
        encoding="utf-8",
    )
    generated_files.append(summary_path)

    return StudyResult(
        study_root=study_root,
        particle_counts=accepted_counts,
        summary_path=summary_path,
        generated_files=generated_files,
    )


def _run_analysis_realization(
    study_config: StudyConfig,
    *,
    particle_count: int,
    seed: int,
    runs_dir: Path,
    raw_dir: Path,
    config_path: Path | None,
) -> AnalysisRunResult:
    run_output = runs_dir / f"analysis_n_{particle_count}_seed_{seed}.txt"
    run_output.parent.mkdir(parents=True, exist_ok=True)
    run_config = build_run_config_from_study(
        study_config,
        count=particle_count,
        seed=seed,
        duration=study_config.stationary.max_time,
        output_path=run_output,
    )

    with run_output.open("w", encoding="utf-8") as handle:
        engine = SimulationEngine(run_config, writer_handle=handle, config_path=config_path)
        next_check_time = max(
            study_config.stationary.window_seconds * 2.0,
            study_config.stationary.check_interval,
        )
        stationary_time: float | None = None

        while engine.current_time < study_config.stationary.max_time - 1e-9:
            if stationary_time is None:
                target_time = min(next_check_time, study_config.stationary.max_time)
            else:
                target_time = min(
                    stationary_time + study_config.stationary.settle_extension,
                    study_config.stationary.max_time,
                )

            engine.run_until(target_time)
            resampled = resample_zero_order_hold(
                engine.observables.used_fraction_history,
                dt=study_config.stationary.resample_dt,
                end_time=engine.current_time,
            )
            detection = detect_stationary(resampled, study_config.stationary)
            if stationary_time is None and detection.stationary_time is not None:
                stationary_time = detection.stationary_time
                continue
            if stationary_time is not None and engine.current_time >= min(
                stationary_time + study_config.stationary.settle_extension,
                study_config.stationary.max_time,
            ) - 1e-9:
                break
            if stationary_time is None:
                next_check_time += study_config.stationary.check_interval
                if next_check_time > study_config.stationary.max_time:
                    next_check_time = study_config.stationary.max_time
                if math.isclose(engine.current_time, study_config.stationary.max_time, rel_tol=0.0, abs_tol=1e-9):
                    break

        result = engine.finalize(force_final_snapshot=True)

    resampled = resample_zero_order_hold(
        result.used_fraction_history,
        dt=study_config.stationary.resample_dt,
        end_time=result.final_time,
    )
    detection = detect_stationary(resampled, study_config.stationary)
    stationary_time = detection.stationary_time
    scanning_rate = linear_regression_slope(result.center_contact_series)
    status = "no_stationary"
    fest: float | None = None
    radial_profile: list[RadialProfileBin] | None = None
    near_shell: RadialProfileBin | None = None
    if stationary_time is not None and result.final_time >= stationary_time + study_config.stationary.settle_extension - 1e-9:
        stationary_values = [value for time, value in resampled if time >= stationary_time]
        if stationary_values:
            fest = sum(stationary_values) / len(stationary_values)
            radial_profile = aggregate_radial_profile_snapshots(
                study_config.geometry,
                study_config.observables.radial_bin_width,
                result.radial_profile_samples,
                time_min=stationary_time,
            )
            near_shell = _select_near_shell(radial_profile)
            status = "stationary"

    run_raw_dir = raw_dir / f"n_{particle_count}" / f"seed_{seed}"
    run_raw_dir.mkdir(parents=True, exist_ok=True)
    _write_series_csv(run_raw_dir / "center_contacts.csv", ["time", "c_fc"], result.center_contact_series)
    _write_series_csv(run_raw_dir / "used_fraction_snapshots.csv", ["time", "used_fraction"], result.used_fraction_history)
    _write_series_csv(run_raw_dir / "used_fraction_resampled.csv", ["time", "used_fraction"], resampled)
    if radial_profile is not None:
        _write_radial_profile_csv(run_raw_dir / "radial_profile_post_stationary.csv", radial_profile)
    meta_path = run_raw_dir / "meta.csv"
    _write_csv(
        meta_path,
        [
            {
                "n": particle_count,
                "seed": seed,
                "processed_events": result.processed_events,
                "snapshots_written": result.snapshots_written,
                "final_time": result.final_time,
                "stationary_time": stationary_time if stationary_time is not None else "",
                "status": status,
                "scanning_rate": scanning_rate,
                "fest": fest if fest is not None else "",
            }
        ],
    )

    return AnalysisRunResult(
        particle_count=particle_count,
        seed=seed,
        output_path=run_output,
        final_time=result.final_time,
        processed_events=result.processed_events,
        snapshots_written=result.snapshots_written,
        stationary_time=stationary_time,
        scanning_rate=scanning_rate,
        fest=fest,
        radial_profile=radial_profile,
        near_shell=near_shell,
        status=status,
    )


def _write_runtime_metadata(
    output_path: Path,
    *,
    particle_count: int,
    seed: int,
    repetition_index: int,
    runtime_seconds: float,
) -> None:
    _write_csv(
        output_path,
        [
            {
                "n": particle_count,
                "seed": seed,
                "repetition_index": repetition_index,
                "runtime_seconds": runtime_seconds,
            }
        ],
    )


def _write_aggregated_radial_profile(output_path: Path, runs: list[AnalysisRunResult]) -> dict[str, object]:
    profiles = [run.radial_profile for run in runs if run.radial_profile is not None]
    if not profiles:
        _write_csv(output_path, [])
        return {
            "mean_profile": [],
            "near_shell": {
                "density_mean": 0.0,
                "density_std": 0.0,
                "velocity_mean": 0.0,
                "velocity_std": 0.0,
                "flux_mean": 0.0,
                "flux_std": 0.0,
            },
        }

    rows: list[dict[str, object]] = []
    mean_profile: list[RadialProfileBin] = []
    near_density_values: list[float] = []
    near_velocity_values: list[float] = []
    near_flux_values: list[float] = []

    for index in range(len(profiles[0])):
        density_values = [profile[index].density for profile in profiles]
        velocity_values = [profile[index].normal_velocity for profile in profiles]
        flux_values = [profile[index].inward_flux for profile in profiles]
        density_mean, density_std = mean_std(density_values)
        velocity_mean, velocity_std = mean_std(velocity_values)
        flux_mean, flux_std = mean_std(flux_values)
        first_profile = profiles[0][index]
        rows.append(
            {
                "radius_start": first_profile.radius_start,
                "radius_end": first_profile.radius_end,
                "density_mean": density_mean,
                "density_std": density_std,
                "velocity_mean": velocity_mean,
                "velocity_std": velocity_std,
                "flux_mean": flux_mean,
                "flux_std": flux_std,
            }
        )
        mean_profile.append(
            RadialProfileBin(
                radius_start=first_profile.radius_start,
                radius_end=first_profile.radius_end,
                density=density_mean,
                normal_velocity=velocity_mean,
                inward_flux=flux_mean,
                samples=len(profiles),
                particle_samples=sum(profile[index].particle_samples for profile in profiles),
            )
        )
        if first_profile.radius_start <= NEAR_S_TARGET < first_profile.radius_end:
            near_density_values = density_values
            near_velocity_values = velocity_values
            near_flux_values = flux_values

    _write_csv(output_path, rows)
    density_mean, density_std = mean_std(near_density_values)
    velocity_mean, velocity_std = mean_std(near_velocity_values)
    flux_mean, flux_std = mean_std(near_flux_values)
    return {
        "mean_profile": mean_profile,
        "near_shell": {
            "density_mean": density_mean,
            "density_std": density_std,
            "velocity_mean": velocity_mean,
            "velocity_std": velocity_std,
            "flux_mean": flux_mean,
            "flux_std": flux_std,
        },
    }


def _select_near_shell(profile: list[RadialProfileBin]) -> RadialProfileBin | None:
    for shell in profile:
        if shell.radius_start <= NEAR_S_TARGET < shell.radius_end:
            return shell
    return profile[0] if profile else None


def _write_series_csv(output_path: Path, headers: list[str], rows: list[tuple[float, float | int]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def _write_radial_profile_csv(output_path: Path, radial_profile: list[RadialProfileBin]) -> None:
    rows = [
        {
            "radius_start": shell.radius_start,
            "radius_end": shell.radius_end,
            "density": shell.density,
            "normal_velocity": shell.normal_velocity,
            "inward_flux": shell.inward_flux,
            "samples": shell.samples,
            "particle_samples": shell.particle_samples,
        }
        for shell in radial_profile
    ]
    _write_csv(output_path, rows)


def _write_csv(output_path: Path, rows: list[dict[str, object]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        if not rows:
            handle.write("")
            return
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_summary(
    *,
    study_config: StudyConfig,
    particle_counts: list[int],
    runtime_rows: list[dict[str, object]],
    scanning_rows: list[dict[str, object]],
    used_rows: list[dict[str, object]],
    near_shell_rows: list[dict[str, object]],
    analysis_outcomes_by_n: dict[int, list[AnalysisRunResult]],
) -> str:
    lines = [
        f"# System 1 study summary: {study_config.output.study_id}",
        "",
        "## Configuration",
        f"- Counts mode: `{study_config.counts_mode}`",
        f"- Particle counts used: `{particle_counts}`",
        f"- Repetitions per N: `{study_config.repetitions}`",
        f"- Seeds: `{study_config.seeds()}`",
        f"- Runtime duration for 1.1: `{study_config.runtime_duration}` s",
        f"- Stationary max time: `{study_config.stationary.max_time}` s",
        f"- Snapshot every: `{study_config.output.snapshot_every}` events",
        "",
        "## Runtime vs N",
    ]
    for row in runtime_rows:
        lines.append(
            f"- N={row['n']}: mean={float(row['runtime_mean_seconds']):.4f}s, std={float(row['runtime_std_seconds']):.4f}s, median={float(row['runtime_median_seconds']):.4f}s"
        )
    lines.extend(["", "## Scanning Rate"])
    for row in scanning_rows:
        lines.append(
            f"- N={row['n']}: ⟨J⟩={float(row['j_mean']):.6f}, std={float(row['j_std']):.6f}"
        )
    lines.extend(["", "## Used Fraction"])
    for row in used_rows:
        lines.append(
            f"- N={row['n']}: stationary_realizations={row['stationary_realizations']}/{row['total_realizations']}, t_stationary_mean={float(row['stationary_time_mean']):.4f}s, F_est_mean={float(row['fest_mean']):.6f}"
        )
    if near_shell_rows:
        lines.extend(["", "## Near-shell S≈2 metrics"])
        for row in near_shell_rows:
            lines.append(
                f"- N={row['n']}: density={float(row['density_mean']):.6f}, velocity={float(row['velocity_mean']):.6f}, flux={float(row['flux_mean']):.6f}"
            )
    lines.extend(["", "## Per-run status"])
    for particle_count in particle_counts:
        for outcome in analysis_outcomes_by_n.get(particle_count, []):
            lines.append(
                f"- N={particle_count}, seed={outcome.seed}: status={outcome.status}, events={outcome.processed_events}, final_time={outcome.final_time:.4f}s, scanning_rate={outcome.scanning_rate:.6f}"
            )
    lines.append("")
    return "\n".join(lines)
