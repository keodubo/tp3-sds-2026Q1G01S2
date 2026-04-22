"""Extract observables from runtime snapshots of 500s each.

Two passes per file:
  1) Fast scan of `step` lines -> (time, n_used) series.
  2) Parse particle lines only for sub-sampled snapshots with t >= t_steady,
     compute per-snapshot radial profile bins (density + mean inward normal
     velocity weighted by particle count).

Cached results are stored in tools/cache/<run_id>.npz to avoid re-parsing
the large files (N=800 is 7.3 GB each).
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "artifacts" / "system1" / "studies" / "example-study"
RUNS_DIR = STUDY / "runs"
CACHE_DIR = ROOT / "tools" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

N_VALUES = [10, 50, 100, 200, 400, 800]
SEEDS = [100, 101]

DIAMETER = 80.0
OBSTACLE_R = 1.0
PARTICLE_R = 1.0
INNER_R = OBSTACLE_R + PARTICLE_R
OUTER_R = DIAMETER / 2.0 - PARTICLE_R
BIN_WIDTH = 0.2
BIN_COUNT = max(1, math.ceil((OUTER_R - INNER_R) / BIN_WIDTH))

T_STEADY = 50.0
TARGET_SAMPLES = 300


@dataclass
class RunData:
    n: int
    seed: int
    times: np.ndarray
    n_used: np.ndarray
    bin_edges: np.ndarray
    density_mean: np.ndarray
    normal_v_mean: np.ndarray
    flux_mean: np.ndarray
    sample_count: int


def run_path(n: int, seed: int) -> Path:
    return RUNS_DIR / f"runtime_n_{n}_seed_{seed}.txt"


def cache_path(n: int, seed: int) -> Path:
    return CACHE_DIR / f"run_n_{n}_seed_{seed}.npz"


def _extract_steps(path: Path) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Pass 1: scan only step lines. Return times, n_used, and line offsets
    of step lines (as line numbers, 1-indexed, for pass 2 targeting)."""
    times: list[float] = []
    n_used: list[int] = []
    line_numbers: list[int] = []
    with path.open("r", buffering=1 << 20) as f:
        for idx, line in enumerate(f):
            if line.startswith("step "):
                # Format: step event_id=<int> time=<float> n_used=<int>
                parts = line.split()
                t = float(parts[2].split("=", 1)[1])
                nu = int(parts[3].split("=", 1)[1])
                times.append(t)
                n_used.append(nu)
                line_numbers.append(idx)
    return np.asarray(times), np.asarray(n_used, dtype=np.int64), line_numbers


def _select_sample_indices(times: np.ndarray, t_min: float, target: int) -> np.ndarray:
    """Choose ~`target` snapshot indices uniformly spaced, limited to t>=t_min."""
    mask = times >= t_min
    eligible = np.nonzero(mask)[0]
    if eligible.size == 0:
        return eligible
    if eligible.size <= target:
        return eligible
    # Uniformly space within eligible indices
    positions = np.linspace(0, eligible.size - 1, target).round().astype(int)
    positions = np.unique(positions)
    return eligible[positions]


def _aggregate_sampled_profiles(
    path: Path,
    step_line_numbers: list[int],
    sample_indices: np.ndarray,
    particles_per_snapshot: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Pass 2: for each selected sample, parse the N particle lines after the
    step line and aggregate into radial bins.

    Returns per-bin:
      density_mean (particles per unit area, averaged over sampled snapshots),
      normal_v_mean (mass-weighted avg over particles contributing to bin),
      flux_mean (density_mean * |normal_v_mean|),
      number of snapshots used.

    Only fresh particles moving inward (radial_dot < 0) are counted.
    """
    bin_density_sum = np.zeros(BIN_COUNT, dtype=np.float64)
    bin_v_weighted_sum = np.zeros(BIN_COUNT, dtype=np.float64)
    bin_particle_count = np.zeros(BIN_COUNT, dtype=np.int64)

    # Compute areas per bin once
    starts = INNER_R + np.arange(BIN_COUNT) * BIN_WIDTH
    ends = np.minimum(OUTER_R, starts + BIN_WIDTH)
    areas = np.pi * (ends**2 - starts**2)

    target_set = set(sample_indices.tolist())
    step_to_lineno = {idx: ln for idx, ln in enumerate(step_line_numbers)}

    # Build a sorted list of (line_number, sample_idx) to scan sequentially
    targets = sorted((step_to_lineno[i], i) for i in target_set)

    sample_count = 0
    with path.open("r", buffering=1 << 20) as f:
        line_iter = enumerate(f)
        target_ptr = 0
        try:
            while target_ptr < len(targets):
                target_line, _ = targets[target_ptr]
                # Advance to the target step line
                while True:
                    idx, line = next(line_iter)
                    if idx == target_line:
                        break
                # Parse the following `particles_per_snapshot` lines
                bin_counts_snapshot = np.zeros(BIN_COUNT, dtype=np.int64)
                v_sums_snapshot = np.zeros(BIN_COUNT, dtype=np.float64)
                parsed = 0
                while parsed < particles_per_snapshot:
                    idx, line = next(line_iter)
                    if not line.startswith("particle "):
                        # defensive: could be blank or another step if snapshot_every yielded fewer lines
                        if line.startswith("step "):
                            break
                        continue
                    # Format: particle id=i x=.. y=.. vx=.. vy=.. state=.. r=.. g=.. b=..
                    # Only count fresh particles moving inward
                    parts = line.split()
                    # state is parts[6] -> "state=fresh" or "state=used"
                    state = parts[6].split("=", 1)[1]
                    parsed += 1
                    if state != "fresh":
                        continue
                    x = float(parts[2].split("=", 1)[1])
                    y = float(parts[3].split("=", 1)[1])
                    vx = float(parts[4].split("=", 1)[1])
                    vy = float(parts[5].split("=", 1)[1])
                    r = math.hypot(x, y)
                    if r < INNER_R or r > OUTER_R or r == 0.0:
                        continue
                    radial_dot = (x * vx + y * vy) / r
                    if radial_dot >= 0.0:
                        continue
                    bin_idx = min(BIN_COUNT - 1, int((r - INNER_R) / BIN_WIDTH))
                    bin_counts_snapshot[bin_idx] += 1
                    v_sums_snapshot[bin_idx] += radial_dot

                # Fold into aggregate
                with np.errstate(divide="ignore", invalid="ignore"):
                    density = np.where(areas > 0, bin_counts_snapshot / areas, 0.0)
                bin_density_sum += density
                bin_v_weighted_sum += v_sums_snapshot
                bin_particle_count += bin_counts_snapshot
                sample_count += 1
                target_ptr += 1
        except StopIteration:
            pass

    density_mean = bin_density_sum / max(sample_count, 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        normal_v_mean = np.where(
            bin_particle_count > 0,
            bin_v_weighted_sum / bin_particle_count,
            0.0,
        )
    flux_mean = density_mean * np.abs(normal_v_mean)
    return density_mean, normal_v_mean, flux_mean, sample_count


def compute_run(n: int, seed: int, *, use_cache: bool = True) -> RunData:
    cache = cache_path(n, seed)
    if use_cache and cache.exists():
        data = np.load(cache)
        return RunData(
            n=n,
            seed=seed,
            times=data["times"],
            n_used=data["n_used"],
            bin_edges=data["bin_edges"],
            density_mean=data["density_mean"],
            normal_v_mean=data["normal_v_mean"],
            flux_mean=data["flux_mean"],
            sample_count=int(data["sample_count"]),
        )

    path = run_path(n, seed)
    if not path.exists():
        raise FileNotFoundError(path)

    print(f"[pass 1] N={n} seed={seed}: scanning steps from {path.name} ({path.stat().st_size/1e6:.1f} MB)", flush=True)
    times, n_used_arr, step_lines = _extract_steps(path)
    print(f"  steps={len(times)}, tmax={times[-1]:.3f}", flush=True)

    sample_idx = _select_sample_indices(times, T_STEADY, TARGET_SAMPLES)
    print(f"[pass 2] N={n} seed={seed}: aggregating {sample_idx.size} radial samples (t>={T_STEADY})", flush=True)
    density_mean, normal_v_mean, flux_mean, sample_count = _aggregate_sampled_profiles(
        path, step_lines, sample_idx, particles_per_snapshot=n
    )
    print(f"  used {sample_count} samples", flush=True)

    bin_edges = INNER_R + np.arange(BIN_COUNT + 1) * BIN_WIDTH
    bin_edges = np.minimum(bin_edges, OUTER_R)

    np.savez_compressed(
        cache,
        times=times,
        n_used=n_used_arr,
        bin_edges=bin_edges,
        density_mean=density_mean,
        normal_v_mean=normal_v_mean,
        flux_mean=flux_mean,
        sample_count=np.asarray(sample_count),
    )
    return RunData(
        n=n,
        seed=seed,
        times=times,
        n_used=n_used_arr,
        bin_edges=bin_edges,
        density_mean=density_mean,
        normal_v_mean=normal_v_mean,
        flux_mean=flux_mean,
        sample_count=sample_count,
    )


def compute_all(*, use_cache: bool = True) -> dict[tuple[int, int], RunData]:
    out: dict[tuple[int, int], RunData] = {}
    for n in N_VALUES:
        for seed in SEEDS:
            out[(n, seed)] = compute_run(n, seed, use_cache=use_cache)
    return out


if __name__ == "__main__":
    subset = sys.argv[1:]
    if subset:
        for token in subset:
            n = int(token)
            for seed in SEEDS:
                compute_run(n, seed)
    else:
        compute_all()
