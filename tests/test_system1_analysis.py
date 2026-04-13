from __future__ import annotations

from tp3_sds.system1.analysis import detect_stationary, linear_regression_slope, resample_zero_order_hold
from tp3_sds.system1.config import StationaryDetectionConfig


def test_linear_regression_slope_matches_known_series() -> None:
    series = [(0.0, 0.0), (1.0, 2.0), (2.0, 4.0), (3.0, 6.0)]

    assert linear_regression_slope(series) == 2.0


def test_resample_zero_order_hold() -> None:
    history = [(0.0, 0.0), (0.8, 1.0), (1.6, 0.5)]

    resampled = resample_zero_order_hold(history, dt=0.5, end_time=2.0)

    assert resampled == [
        (0.0, 0.0),
        (0.5, 0.0),
        (1.0, 1.0),
        (1.5, 1.0),
        (2.0, 0.5),
    ]


def test_detect_stationary_positive_case() -> None:
    resampled = [(time, 0.49 + (0.01 if time >= 2.0 else 0.0)) for time in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]]
    config = StationaryDetectionConfig(
        resample_dt=0.5,
        window_seconds=1.0,
        check_interval=0.5,
        tolerance=0.05,
        consecutive_checks=1,
        settle_extension=1.0,
        max_time=4.0,
    )

    detection = detect_stationary(resampled, config)

    assert detection.stationary_time is not None


def test_detect_stationary_negative_case() -> None:
    resampled = [(0.0, 0.1), (0.5, 0.2), (1.0, 0.4), (1.5, 0.7), (2.0, 1.1), (2.5, 1.6)]
    config = StationaryDetectionConfig(
        resample_dt=0.5,
        window_seconds=1.0,
        check_interval=0.5,
        tolerance=0.01,
        consecutive_checks=2,
        settle_extension=1.0,
        max_time=3.0,
    )

    detection = detect_stationary(resampled, config)

    assert detection.stationary_time is None
