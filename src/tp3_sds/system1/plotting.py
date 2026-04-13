from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from tp3_sds.system1.observables import RadialProfileBin


def plot_errorbar_series(
    *,
    output_path: Path,
    xs: list[int],
    ys: list[float],
    yerr: list[float],
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    figure, axis = plt.subplots(figsize=(7, 4.5))
    axis.errorbar(xs, ys, yerr=yerr, marker="o", capsize=4)
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(True, alpha=0.25)
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def plot_dual_errorbar_series(
    *,
    output_path: Path,
    xs: list[int],
    left_values: list[float],
    left_errors: list[float],
    right_values: list[float],
    right_errors: list[float],
    left_label: str,
    right_label: str,
    title: str,
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for axis, values, errors, label in (
        (axes[0], left_values, left_errors, left_label),
        (axes[1], right_values, right_errors, right_label),
    ):
        axis.errorbar(xs, values, yerr=errors, marker="o", capsize=4)
        axis.set_xlabel("N")
        axis.set_ylabel(label)
        axis.grid(True, alpha=0.25)
    figure.suptitle(title)
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def plot_radial_profiles(
    *,
    output_path: Path,
    radial_profile: list[RadialProfileBin],
    particle_count: int,
) -> None:
    radii = [profile.radius_start for profile in radial_profile]
    densities = [profile.density for profile in radial_profile]
    normal_speeds = [abs(profile.normal_velocity) for profile in radial_profile]
    fluxes = [profile.inward_flux for profile in radial_profile]

    figure, axis = plt.subplots(figsize=(7.5, 4.5))
    axis.plot(radii, densities, marker="o", label="⟨ρ_in^f⟩(S)")
    axis.plot(radii, normal_speeds, marker="s", label="|⟨v_in^f⟩(S)|")
    axis.plot(radii, fluxes, marker="^", label="J_in(S)")
    axis.set_title(f"System 1 radial profiles for N={particle_count}")
    axis.set_xlabel("S (m)")
    axis.set_ylabel("Profile value")
    axis.grid(True, alpha=0.25)
    axis.legend()
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def plot_near_shell_vs_n(
    *,
    output_path: Path,
    xs: list[int],
    density_values: list[float],
    density_errors: list[float],
    velocity_values: list[float],
    velocity_errors: list[float],
    flux_values: list[float],
    flux_errors: list[float],
) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    chart_data = (
        (density_values, density_errors, "⟨ρ_in^f⟩ near S=2"),
        (velocity_values, velocity_errors, "⟨v_in^f⟩ near S=2"),
        (flux_values, flux_errors, "J_in near S=2"),
    )
    for axis, (values, errors, label) in zip(axes, chart_data, strict=True):
        axis.errorbar(xs, values, yerr=errors, marker="o", capsize=4)
        axis.set_xlabel("N")
        axis.set_ylabel(label)
        axis.grid(True, alpha=0.25)
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
