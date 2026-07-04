"""AV-system-specific dataclasses plus shared PISA payload types."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from pisa_api.types import (
    ActorRefData,
    ActorRole,
    CollisionInfoData,
    ControlCommand,
    ControlMode,
    EgoConfigData,
    GoalConfigData,
    LanePositionData,
    ObjectKinematicData,
    ObjectStateData,
    ObservationData,
    ObservedAgentData,
    PositionData,
    RoadObjectType,
    RuntimeFrameData,
    ScenarioData,
    ScenarioPackData,
    ShapeCenterPoseData,
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
    initial_observation: ObservationData = field(default_factory=ObservationData)


@dataclass(frozen=True)
class ResetResponse:
    ctrl_cmd: ControlCommand = field(default_factory=ControlCommand)


@dataclass(frozen=True)
class StepRequest:
    observation: ObservationData = field(default_factory=ObservationData)
    timestamp_ns: int = 0


@dataclass(frozen=True)
class StepResponse:
    ctrl_cmd: ControlCommand = field(default_factory=ControlCommand)


@dataclass(frozen=True)
class ShouldQuitResponse:
    should_quit: bool = False
    msg: str = ""


__all__ = [
    "ActorRefData",
    "ActorRole",
    "CollisionInfoData",
    "ControlCommand",
    "ControlMode",
    "EgoConfigData",
    "GoalConfigData",
    "InitRequest",
    "LanePositionData",
    "ObjectKinematicData",
    "ObjectStateData",
    "ObservationData",
    "ObservedAgentData",
    "PositionData",
    "ResetRequest",
    "ResetResponse",
    "RoadObjectType",
    "RuntimeFrameData",
    "ScenarioData",
    "ScenarioPackData",
    "ShapeData",
    "ShapeCenterPoseData",
    "ShapeDimensionData",
    "ShapeType",
    "ShapeVertexData",
    "ShouldQuitResponse",
    "SpawnConfigData",
    "StepRequest",
    "StepResponse",
    "WorldPositionData",
]
