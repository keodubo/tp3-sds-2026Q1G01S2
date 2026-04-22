"""Render all System 1 plots for N={10,50,100,200,400,800} in the style of
the reference photos. All text in Spanish, Arial/Liberation Sans typeface.

Reads:
  - tools/cache/run_n_<N>_seed_<S>.npz (produced by compute_observables.py)
  - artifacts/system1/studies/example-study/aggregates/runtime_vs_n.csv

Writes:
  - output_1.1/runtime_vs_n.png                (inciso 1.1)
  - output_1.2/scanning_rate_vs_n.png          (inciso 1.2 - fig 7: ⟨J⟩ vs N)
  - output_1.2/cfc_fit_panel.png               (inciso 1.2 - fig 1: Cfc(t) + fits)
  - output_1.3/used_fraction_vs_n.png          (inciso 1.3 - fig 8: Fu(N))
  - output_1.3/used_fraction_time_panel.png    (inciso 1.3 - fig 2: Fu(t))
  - output_1.4/radial_density_panel.png        (inciso 1.4 - fig 3: ρ(S))
  - output_1.4/radial_velocity_panel.png       (inciso 1.4 - fig 4: |v|(S))
  - output_1.4/radial_flux_panel.png           (inciso 1.4 - fig 5: J(S))
  - output_1.4/radial_flux_multi_n.png         (inciso 1.4 - fig 6: J(S) multi-N zoom)
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from compute_observables import (
    BIN_COUNT,
    BIN_WIDTH,
    INNER_R,
    N_VALUES,
    OUTER_R,
    ROOT,
    SEEDS,
    STUDY,
    T_STEADY,
    compute_all,
)

# --- Style (Arial; fallback to Liberation Sans/DejaVu if Arial not installed) ---
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "Liberation Sans", "DejaVu Sans"]
plt.rcParams["mathtext.fontset"] = "dejavusans"
plt.rcParams["axes.labelsize"] = 12
plt.rcParams["axes.titlesize"] = 13
plt.rcParams["legend.fontsize"] = 10
plt.rcParams["xtick.labelsize"] = 10
plt.rcParams["ytick.labelsize"] = 10
plt.rcParams["figure.dpi"] = 120

OUT_1_1 = ROOT / "output_1.1"
OUT_1_2 = ROOT / "output_1.2"
OUT_1_3 = ROOT / "output_1.3"
OUT_1_4 = ROOT / "output_1.4"
for d in (OUT_1_1, OUT_1_2, OUT_1_3, OUT_1_4):
    d.mkdir(parents=True, exist_ok=True)

# Palette for multi-run panels (red/blue/green/purple/orange/yellow/brown/pink/grey/cyan ...)
RUN_COLORS = [
    "#d62728",  # red
    "#1f77b4",  # blue
    "#2ca02c",  # green
    "#9467bd",  # purple
    "#ff7f0e",  # orange
    "#e6c700",  # yellow-ish
    "#8c564b",  # brown
    "#7f7f7f",  # grey
]

N_COLORS = {
    10: "#1f77b4",
    50: "#ff7f0e",
    100: "#2ca02c",
    200: "#d62728",
    400: "#9467bd",
    800: "#8c564b",
}


def cumulative_cfc(n_used: np.ndarray) -> np.ndarray:
    """Reconstruct the monotone cumulative fresh→center contact counter Cfc(t).

    n_used is the *instantaneous* count of USED particles; USED reverts to FRESH
    on outer-wall collisions (simulation.py:426-427). Only positive increments
    of n_used count as new scanning events.
    """
    if n_used.size == 0:
        return n_used.astype(np.int64)
    diffs = np.diff(n_used.astype(np.int64))
    positive = np.maximum(diffs, 0)
    cfc = np.empty(n_used.size, dtype=np.int64)
    cfc[0] = int(n_used[0])
    cfc[1:] = int(n_used[0]) + np.cumsum(positive)
    return cfc


def scanning_rate_fit(times: np.ndarray, n_used: np.ndarray) -> tuple[float, float, float, np.ndarray]:
    """Linear fit of the reconstructed cumulative Cfc(t) vs t.

    Returns slope (= J, scanning rate in contacts/s), intercept, R^2, and the
    reconstructed Cfc series itself (for scatter plots).
    """
    cfc = cumulative_cfc(n_used).astype(float)
    if times.size < 2:
        return 0.0, 0.0, 0.0, cfc
    a, b = np.polyfit(times, cfc, 1)
    y_pred = a * times + b
    ss_res = np.sum((cfc - y_pred) ** 2)
    ss_tot = np.sum((cfc - cfc.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return float(a), float(b), float(r2), cfc


def fig_cfc_fit_panel(all_runs, target_ns=(100, 800), output_path: Path = None):
    """Foto 1: dos paneles Cfc(t) con fit lineal, una entrada por run."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, n in zip(axes, target_ns):
        entries = []
        for seed in SEEDS:
            run = all_runs[(n, seed)]
            slope, intercept, _, cfc = scanning_rate_fit(run.times, run.n_used)
            entries.append((seed, run, slope, intercept, cfc))

        # Plot scatter + dashed fit per seed (using monotone Cfc)
        for i, (seed, run, slope, intercept, cfc) in enumerate(entries):
            color = RUN_COLORS[i % len(RUN_COLORS)]
            j_rate = slope
            ax.scatter(run.times, cfc, s=8, color=color, alpha=0.5)
            t_line = np.array([run.times.min(), run.times.max()])
            ax.plot(t_line, slope * t_line + intercept, "--", color=color,
                    label=f"Run {i} (J={j_rate:.3f})", linewidth=1.4)
        ax.set_title(f"Cfc(t) y ajuste lineal para N = {n}")
        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel(r"$C_{fc}(t)$")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.85)

    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=160)
    plt.close(fig)


def fig_scanning_rate_vs_n(all_runs, output_path: Path):
    """Foto 7: ⟨J⟩ vs N con errorbar + banda shaded."""
    ns = np.array(N_VALUES)
    means = []
    stds = []
    for n in N_VALUES:
        js = []
        for seed in SEEDS:
            run = all_runs[(n, seed)]
            slope, _, _, _ = scanning_rate_fit(run.times, run.n_used)
            js.append(slope)
        means.append(np.mean(js))
        stds.append(np.std(js, ddof=0))
    means = np.array(means)
    stds = np.array(stds)

    fig, ax = plt.subplots(figsize=(9, 5))
    # shaded band
    ax.fill_between(ns, means - stds, means + stds, color="#1f77b4", alpha=0.18, linewidth=0)
    ax.errorbar(ns, means, yerr=stds, fmt="-o", color="#1f77b4", markersize=7,
                capsize=5, linewidth=1.8)
    ax.set_title(r"Tasa de scanning promedio $\langle J \rangle$ en función de $N$")
    ax.set_xlabel(r"$N$")
    ax.set_ylabel(r"$\langle J \rangle$")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def fig_fu_time_panel(all_runs, target_ns=(100, 800), output_path: Path = None, tolerance=0.02):
    """Foto 2: panel Fu(t) con banda de tolerancia y media horizontal dashed.

    Para imitar el estilo multi-color, coloreamos segmentos consecutivos con
    colores cíclicos (aporte visual) y mostramos la media + banda [mean ± tol].
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    segment_colors = ["#d62728", "#1f77b4", "#2ca02c", "#ff7f0e", "#e6c700"]

    for ax, n in zip(axes, target_ns):
        # Combine both seeds into one long series (concatenate)
        series = []
        for seed in SEEDS:
            run = all_runs[(n, seed)]
            times = run.times
            fu = run.n_used.astype(float) / n
            # Keep only steady portion for mean estimation
            mask = times >= T_STEADY
            series.append((times, fu, mask))

        # For visualization, use just seed=100 (single run) to match photo aesthetic
        times0, fu0, mask0 = series[0]
        # Plot in segments for multi-color effect
        steady_fu = fu0[mask0]
        mean_val = float(np.mean(steady_fu)) if steady_fu.size else 0.0

        # Split times into ~5 segments and color each differently with markers
        n_segments = 10
        idx_splits = np.array_split(np.arange(times0.size), n_segments)
        for i, idx in enumerate(idx_splits):
            if idx.size == 0:
                continue
            c = segment_colors[i % len(segment_colors)]
            ax.plot(times0[idx], fu0[idx], "-o", color=c, markersize=2.5, linewidth=0.8,
                    alpha=0.9)

        # Shaded tolerance band around mean
        ax.axhspan(mean_val - tolerance, mean_val + tolerance, color="grey", alpha=0.18, linewidth=0)
        ax.axhline(mean_val, color="black", linestyle="--", linewidth=1.0, alpha=0.7)

        ax.set_title(f"Fracción de partículas usadas en función del tiempo para N = {n}")
        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel(r"$F_u(t)$")
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=160)
    plt.close(fig)


def fig_fu_vs_n(all_runs, output_path: Path):
    """Foto 8: Fu(N) vs N con errorbar rojo."""
    ns = np.array(N_VALUES)
    means = []
    stds = []
    for n in N_VALUES:
        vals = []
        for seed in SEEDS:
            run = all_runs[(n, seed)]
            mask = run.times >= T_STEADY
            if not np.any(mask):
                continue
            fu = run.n_used[mask].astype(float) / n
            vals.append(float(np.mean(fu)))
        if not vals:
            means.append(0.0)
            stds.append(0.0)
            continue
        means.append(np.mean(vals))
        stds.append(np.std(vals, ddof=0))
    means = np.array(means)
    stds = np.array(stds)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(ns, means, yerr=stds, fmt="-o", color="#1f77b4", ecolor="#d62728",
                markersize=7, capsize=5, linewidth=1.8, elinewidth=1.4)
    ax.set_title("Fracción de partículas usadas en función de N")
    ax.set_xlabel(r"$N$ (número de partículas)")
    ax.set_ylabel(r"$F_u(N)$")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _smooth(y: np.ndarray, window: int = 3) -> np.ndarray:
    if window <= 1:
        return y
    kernel = np.ones(window) / window
    return np.convolve(y, kernel, mode="same")


def _avg_profile_over_seeds(all_runs, n: int, smooth_window: int = 1):
    densities = []
    velocities = []
    fluxes = []
    for seed in SEEDS:
        run = all_runs[(n, seed)]
        densities.append(run.density_mean)
        velocities.append(np.abs(run.normal_v_mean))
        fluxes.append(run.flux_mean)
    density = np.mean(np.stack(densities), axis=0)
    velocity = np.mean(np.stack(velocities), axis=0)
    flux = np.mean(np.stack(fluxes), axis=0)
    bin_edges = all_runs[(n, SEEDS[0])].bin_edges
    centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    if smooth_window > 1:
        density = _smooth(density, smooth_window)
        velocity = _smooth(velocity, smooth_window)
        flux = _smooth(flux, smooth_window)
    return centers, density, velocity, flux


def fig_radial_density_panel(all_runs, target_ns=(200, 800), output_path: Path = None):
    """Foto 3: ⟨ρ_f^in⟩(S) panel azul."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, n in zip(axes, target_ns):
        centers, density, _, _ = _avg_profile_over_seeds(all_runs, n, smooth_window=3)
        ax.plot(centers, density, color="#1f77b4", linewidth=1.4)
        ax.set_title(f"N = {n}")
        ax.set_xlabel("S (distancia al centro)")
        ax.set_ylabel(r"$\langle \rho_f^{in} \rangle (S)$")
        ax.grid(True, alpha=0.25)
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=160)
    plt.close(fig)


def fig_radial_velocity_panel(all_runs, target_ns=(200, 800), output_path: Path = None):
    """Foto 4: |⟨v_f^in⟩|(S) panel naranja."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, n in zip(axes, target_ns):
        centers, _, velocity, _ = _avg_profile_over_seeds(all_runs, n, smooth_window=3)
        ax.plot(centers, velocity, color="#ff7f0e", linewidth=1.4)
        ax.set_title(f"N = {n}")
        ax.set_xlabel("S (distancia al centro)")
        ax.set_ylabel(r"$|\langle v_f^{in} \rangle (S)|$")
        ax.grid(True, alpha=0.25)
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=160)
    plt.close(fig)


def fig_radial_flux_panel(all_runs, target_ns=(200, 800), output_path: Path = None):
    """Foto 5: J_in(S) panel verde."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, n in zip(axes, target_ns):
        centers, _, _, flux = _avg_profile_over_seeds(all_runs, n, smooth_window=3)
        ax.plot(centers, flux, color="#2ca02c", linewidth=1.4)
        ax.set_title(f"N = {n}")
        ax.set_xlabel("S (distancia al centro)")
        ax.set_ylabel(r"$J_{in}(S)$")
        ax.grid(True, alpha=0.25)
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=160)
    plt.close(fig)


def fig_radial_flux_multi_n(all_runs, zoom=(2.0, 5.0), output_path: Path = None):
    """Foto 6: J_in(S) overlay de múltiples N, zoom en [2, 5]."""
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for n in N_VALUES:
        centers, _, _, flux = _avg_profile_over_seeds(all_runs, n)
        mask = (centers >= zoom[0]) & (centers <= zoom[1])
        ax.plot(centers[mask], flux[mask], color=N_COLORS[n], linewidth=1.8,
                label=f"N = {n}")
    ax.set_xlabel("S (distancia al centro)")
    ax.set_ylabel(r"$J_{in}(S)$")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", framealpha=0.9)
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=160)
    plt.close(fig)


def fig_runtime_vs_n(output_path: Path):
    """Inciso 1.1: runtime vs N (reuse existing CSV)."""
    csv_path = STUDY / "aggregates" / "runtime_vs_n.csv"
    ns: list[int] = []
    means: list[float] = []
    stds: list[float] = []
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            ns.append(int(row["n"]))
            means.append(float(row["runtime_mean_seconds"]))
            stds.append(float(row["runtime_std_seconds"]))
    ns = np.array(ns)
    means = np.array(means)
    stds = np.array(stds)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(ns, means, yerr=stds, fmt="-o", color="#1f77b4", markersize=7,
                capsize=5, linewidth=1.8)
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.set_title("Tiempo de ejecución vs N (simulación de 500 s)")
    ax.set_xlabel(r"$N$ (número de partículas)")
    ax.set_ylabel("Tiempo de ejecución (s)")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_aggregate_csvs(all_runs):
    """Write updated aggregate CSVs derived from 500s runtime data."""
    # scanning rate
    with (OUT_1_2 / "scanning_rate_vs_n.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "j_mean", "j_std", "repetitions"])
        for n in N_VALUES:
            js = []
            for seed in SEEDS:
                run = all_runs[(n, seed)]
                slope, _, _, _ = scanning_rate_fit(run.times, run.n_used)
                js.append(slope)
            w.writerow([n, float(np.mean(js)), float(np.std(js, ddof=0)), len(js)])

    # used fraction
    with (OUT_1_3 / "used_fraction_vs_n.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "fu_mean", "fu_std", "repetitions"])
        for n in N_VALUES:
            vals = []
            for seed in SEEDS:
                run = all_runs[(n, seed)]
                mask = run.times >= T_STEADY
                if not np.any(mask):
                    continue
                fu = run.n_used[mask].astype(float) / n
                vals.append(float(np.mean(fu)))
            if vals:
                w.writerow([n, float(np.mean(vals)), float(np.std(vals, ddof=0)), len(vals)])
            else:
                w.writerow([n, 0.0, 0.0, 0])

    # radial profile per N
    for n in N_VALUES:
        centers, density, velocity, flux = _avg_profile_over_seeds({(n, s): all_runs[(n, s)] for s in SEEDS}, n)
        with (OUT_1_4 / f"radial_profile_n_{n}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["S_center", "density_mean", "velocity_mean_abs", "flux_mean"])
            for s, d, v, j in zip(centers, density, velocity, flux):
                w.writerow([float(s), float(d), float(v), float(j)])


def main():
    print("Loading run data from cache...", flush=True)
    all_runs = compute_all(use_cache=True)

    print("Rendering inciso 1.1 (runtime vs N)...", flush=True)
    fig_runtime_vs_n(OUT_1_1 / "runtime_vs_n.png")

    print("Rendering inciso 1.2 (scanning rate)...", flush=True)
    fig_scanning_rate_vs_n(all_runs, OUT_1_2 / "scanning_rate_vs_n.png")
    fig_cfc_fit_panel(all_runs, target_ns=(100, 800), output_path=OUT_1_2 / "cfc_fit_panel.png")

    print("Rendering inciso 1.3 (used fraction)...", flush=True)
    fig_fu_vs_n(all_runs, OUT_1_3 / "used_fraction_vs_n.png")
    fig_fu_time_panel(all_runs, target_ns=(100, 800), output_path=OUT_1_3 / "used_fraction_time_panel.png")

    print("Rendering inciso 1.4 (radial profiles)...", flush=True)
    fig_radial_density_panel(all_runs, target_ns=(200, 800), output_path=OUT_1_4 / "radial_density_panel.png")
    fig_radial_velocity_panel(all_runs, target_ns=(200, 800), output_path=OUT_1_4 / "radial_velocity_panel.png")
    fig_radial_flux_panel(all_runs, target_ns=(200, 800), output_path=OUT_1_4 / "radial_flux_panel.png")
    fig_radial_flux_multi_n(all_runs, zoom=(2.0, 5.0), output_path=OUT_1_4 / "radial_flux_multi_n.png")

    print("Writing aggregate CSVs derived from 500 s runtime data...", flush=True)
    write_aggregate_csvs(all_runs)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
