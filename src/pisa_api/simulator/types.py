"""Simulator-specific dataclasses plus shared PISA payload types."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from pisa_api.types import (
    CollisionInfoData,
    ControlCommand,
    ControlMode,
    EgoConfigData,
    GoalConfigData,
    LanePositionData,
    ObjectKinematicData,
    ObjectStateData,
    PositionData,
    RoadObjectType,
    RuntimeFrameData,
    ScenarioData,
    ScenarioPackData,
    ShapeData,
    ShapeDimensionData,
    ShapeType,
    ShapeVertexData,
    SpawnConfigData,
    WorldPositionData,
)


@dataclass(frozen=True)
class InitRequest:
    config: Dict[str, Any] = field(default_factory=dict)
    output_dir: Path = field(default_factory=Path)
    scenario: ScenarioData = field(default_factory=ScenarioData)
    dt: float = 0.0


@dataclass(frozen=True)
class ResetRequest:
    output_dir: Path = field(default_factory=Path)
    scenario_pack: ScenarioPackData = field(default_factory=ScenarioPackData)
    params: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ResetResponse:
    frame: RuntimeFrameData = field(default_factory=RuntimeFrameData)


@dataclass(frozen=True)
class StepRequest:
    ctrl_cmd: ControlCommand = field(default_factory=ControlCommand)
    timestamp_ns: int = 0


@dataclass(frozen=True)
class StepResponse:
    frame: RuntimeFrameData = field(default_factory=RuntimeFrameData)


@dataclass(frozen=True)
class ShouldQuitResponse:
    should_quit: bool = False


__all__ = [
    "CollisionInfoData",
    "ControlCommand",
    "ControlMode",
    "EgoConfigData",
    "GoalConfigData",
    "InitRequest",
    "LanePositionData",
    "ObjectKinematicData",
    "ObjectStateData",
    "PositionData",
    "ResetRequest",
    "ResetResponse",
    "RoadObjectType",
    "RuntimeFrameData",
    "ScenarioData",
    "ScenarioPackData",
    "ShapeData",
    "ShapeDimensionData",
    "ShapeType",
    "ShapeVertexData",
    "ShouldQuitResponse",
    "SpawnConfigData",
    "StepRequest",
    "StepResponse",
    "WorldPositionData",
]
