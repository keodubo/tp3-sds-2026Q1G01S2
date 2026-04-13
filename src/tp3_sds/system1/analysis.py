from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median, stdev

from tp3_sds.system1.config import StationaryDetectionConfig


@dataclass(frozen=True)
class StationaryDetectionResult:
    stationary_time: float | None
    recent_mean: float | None
    previous_mean: float | None
    checks_passed: int


def mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], 0.0
    return mean(values), stdev(values)


def median_value(values: list[float]) -> float:
    return median(values) if values else 0.0


def linear_regression_slope(points: list[tuple[float, float]]) -> float:
    if len(points) < 2:
        return 0.0
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x_mean = mean(xs)
    y_mean = mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=True))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def resample_zero_order_hold(
    history: list[tuple[float, float]],
    *,
    dt: float,
    end_time: float | None = None,
) -> list[tuple[float, float]]:
    if not history:
        return []
    if dt <= 0:
        raise ValueError("dt must be positive.")

    sorted_history = sorted(history, key=lambda item: item[0])
    if end_time is None:
        end_time = sorted_history[-1][0]

    result: list[tuple[float, float]] = []
    history_index = 0
    current_value = sorted_history[0][1]
    current_time = 0.0
    epsilon = dt / 1000.0

    while current_time <= end_time + epsilon:
        while history_index + 1 < len(sorted_history) and sorted_history[history_index + 1][0] <= current_time + epsilon:
            history_index += 1
            current_value = sorted_history[history_index][1]
        result.append((round(current_time, 10), current_value))
        current_time += dt

    if result[-1][0] < end_time:
        result.append((end_time, current_value))
    return result


def detect_stationary(
    resampled_history: list[tuple[float, float]],
    config: StationaryDetectionConfig,
) -> StationaryDetectionResult:
    if not resampled_history:
        return StationaryDetectionResult(None, None, None, 0)

    dt = config.resample_dt
    window_points = max(1, round(config.window_seconds / dt))
    check_points = max(1, round(config.check_interval / dt))
    values = [value for _, value in resampled_history]
    times = [time for time, _ in resampled_history]

    consecutive = 0
    recent_mean_value: float | None = None
    previous_mean_value: float | None = None
    for end_index in range(2 * window_points, len(values) + 1, check_points):
        previous_window = values[end_index - 2 * window_points : end_index - window_points]
        recent_window = values[end_index - window_points : end_index]
        previous_mean_value = mean(previous_window)
        recent_mean_value = mean(recent_window)
        if abs(recent_mean_value - previous_mean_value) <= config.tolerance:
            consecutive += 1
            if consecutive >= config.consecutive_checks:
                return StationaryDetectionResult(
                    stationary_time=times[end_index - 1],
                    recent_mean=recent_mean_value,
                    previous_mean=previous_mean_value,
                    checks_passed=consecutive,
                )
        else:
            consecutive = 0

    return StationaryDetectionResult(None, recent_mean_value, previous_mean_value, consecutive)
