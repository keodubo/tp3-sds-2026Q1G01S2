"""System 1 event-driven hard-sphere simulation."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS: dict[str, tuple[str, str]] = {
    "SimulationConfig": ("tp3_sds.system1.config", "SimulationConfig"),
    "StudyConfig": ("tp3_sds.system1.config", "StudyConfig"),
    "load_config": ("tp3_sds.system1.config", "load_config"),
    "load_study_config": ("tp3_sds.system1.config", "load_study_config"),
    "validate_config": ("tp3_sds.system1.config", "validate_config"),
    "validate_study_config": ("tp3_sds.system1.config", "validate_study_config"),
    "build_delivery_package": ("tp3_sds.system1.delivery", "build_delivery_package"),
    "SimulationEngine": ("tp3_sds.system1.simulation", "SimulationEngine"),
    "SimulationResult": ("tp3_sds.system1.simulation", "SimulationResult"),
    "run_simulation": ("tp3_sds.system1.simulation", "run_simulation"),
    "StudyResult": ("tp3_sds.system1.study", "StudyResult"),
    "run_study": ("tp3_sds.system1.study", "run_study"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
