"""AV-system-specific dataclasses plus shared PISA payload types."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

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
    map_name: str = ""
    dt: float = 0.0


@dataclass(frozen=True)
class ResetRequest:
    output_dir: Path = field(default_factory=Path)
    scenario_pack: ScenarioPackData = field(default_factory=ScenarioPackData)
    initial_observation: List[ObjectStateData] = field(default_factory=list)


@dataclass(frozen=True)
class ResetResponse:
    ctrl_cmd: ControlCommand = field(default_factory=ControlCommand)


@dataclass(frozen=True)
class StepRequest:
    observation: List[ObjectStateData] = field(default_factory=list)
    timestamp_ns: int = 0


@dataclass(frozen=True)
class StepResponse:
    ctrl_cmd: ControlCommand = field(default_factory=ControlCommand)


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
