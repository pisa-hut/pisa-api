"""Pure-Python dataclasses for PISA wire message payloads.

These shared types intentionally do not import generated protobuf modules.
Role-specific APIs such as ``pisa_api.simulator`` and ``pisa_api.av`` re-export
the relevant names so wrapper authors can stay out of ``*_pb2``.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ControlMode(IntEnum):
    NONE = 0
    TRAJECTORY = 1
    THROTTLE_STEER = 2
    WAYPOINTS = 3
    POSITION = 4
    ACKERMANN = 5
    THROTTLE_STEER_BREAK = 6


@dataclass(frozen=True)
class InitResponse:
    """Result of a successful wrapper initialization."""

    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class RoadObjectType(IntEnum):
    UNKNOWN = 0
    CAR = 1
    TRUCK = 2
    BUS = 3
    SEMITRAILER = 4
    TRAILER = 5
    MOTORCYCLE = 6
    BICYCLE = 7
    PEDESTRIAN = 8
    VAN = 9
    TRAIN = 10
    TRAM = 11
    WHEEL_CHAIR = 12
    WHEELCHAIR = 12
    ANIMAL = 13


class ShapeType(IntEnum):
    BOUNDING_BOX = 0
    CYLINDER = 1
    POLYGON = 2


class ActorRole(IntEnum):
    ACTOR_ROLE_UNSPECIFIED = 0
    EGO = 1
    AGENT = 2


@dataclass(frozen=True)
class WorldPositionData:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    h: float = 0.0
    p: float = 0.0
    r: float = 0.0
    h_relative: float = 0.0


@dataclass(frozen=True)
class LanePositionData:
    road_id: int = 0
    lane_id: int = 0
    s: float = 0.0
    offset: float = 0.0
    junction_id: Optional[int] = None


@dataclass(frozen=True)
class PositionData:
    lane: LanePositionData = field(default_factory=LanePositionData)
    world: WorldPositionData = field(default_factory=WorldPositionData)


@dataclass(frozen=True)
class SpawnConfigData:
    position: PositionData = field(default_factory=PositionData)
    speed: float = 0.0


@dataclass(frozen=True)
class GoalConfigData:
    position: PositionData = field(default_factory=PositionData)


@dataclass(frozen=True)
class EgoConfigData:
    target_speed: float = 0.0
    spawn_config: SpawnConfigData = field(default_factory=SpawnConfigData)
    goal_config: GoalConfigData = field(default_factory=GoalConfigData)


@dataclass(frozen=True)
class ScenarioData:
    format: str = ""
    name: str = ""
    path: Optional[Path] = None


@dataclass(frozen=True)
class ScenarioPackData:
    name: str = ""
    map_name: str = ""
    scenarios: Dict[str, Path] = field(default_factory=dict)
    param_range_file: Optional[Path] = None
    ego: EgoConfigData = field(default_factory=EgoConfigData)
    timeout_ns: int = 0


@dataclass(frozen=True)
class ControlCommand:
    mode: ControlMode = ControlMode.NONE
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Vector3Data:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass(frozen=True)
class ObjectKinematicData:
    time_ns: int = 0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    speed: float = 0.0
    acceleration: float = 0.0
    yaw_rate: float = 0.0
    yaw_acceleration: float = 0.0
    linear_velocity: Optional[Vector3Data] = None


@dataclass(frozen=True)
class ShapeDimensionData:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass(frozen=True)
class ShapeVertexData:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass(frozen=True)
class ShapeCenterPoseData:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


@dataclass(frozen=True)
class ShapeData:
    type: ShapeType = ShapeType.BOUNDING_BOX
    dimensions: ShapeDimensionData = field(default_factory=ShapeDimensionData)
    vertices: List[ShapeVertexData] = field(default_factory=list)
    center: ShapeCenterPoseData = field(default_factory=ShapeCenterPoseData)
    reference_point: str = ""


@dataclass(frozen=True)
class ObjectStateData:
    type: RoadObjectType = RoadObjectType.UNKNOWN
    kinematic: ObjectKinematicData = field(default_factory=ObjectKinematicData)
    shape: Optional[ShapeData] = None


@dataclass(frozen=True)
class ActorRefData:
    tracking_id: int = 0
    entity_name: Optional[str] = None
    role: ActorRole = ActorRole.ACTOR_ROLE_UNSPECIFIED


@dataclass(frozen=True)
class CollisionInfoData:
    occurred: bool = False
    actor_a: Optional[ActorRefData] = None
    actor_b: Optional[ActorRefData] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulatorObjectData:
    state: ObjectStateData = field(default_factory=ObjectStateData)
    entity_name: Optional[str] = None


@dataclass(frozen=True)
class SimulatorEgoData:
    tracking_id: int = 0
    object: SimulatorObjectData = field(default_factory=SimulatorObjectData)


@dataclass(frozen=True)
class RuntimeFrameData:
    sim_time_ns: int = 0
    ego: SimulatorEgoData = field(default_factory=SimulatorEgoData)
    agents: Dict[int, SimulatorObjectData] = field(default_factory=dict)
    collision: List[CollisionInfoData] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ObservedAgentData:
    state: ObjectStateData = field(default_factory=ObjectStateData)
    tracking_id: Optional[int] = None
    entity_name: Optional[str] = None


@dataclass(frozen=True)
class ObservationData:
    ego: ObjectStateData = field(default_factory=ObjectStateData)
    # Sequence order is deliberately non-identity-bearing.
    agents: List[ObservedAgentData] = field(default_factory=list)


__all__ = [
    "ActorRefData",
    "ActorRole",
    "CollisionInfoData",
    "ControlCommand",
    "ControlMode",
    "EgoConfigData",
    "GoalConfigData",
    "InitResponse",
    "LanePositionData",
    "ObjectKinematicData",
    "ObjectStateData",
    "ObservationData",
    "ObservedAgentData",
    "PositionData",
    "RoadObjectType",
    "RuntimeFrameData",
    "ScenarioData",
    "ScenarioPackData",
    "ShapeData",
    "ShapeCenterPoseData",
    "ShapeDimensionData",
    "ShapeType",
    "ShapeVertexData",
    "SimulatorEgoData",
    "SimulatorObjectData",
    "SpawnConfigData",
    "Vector3Data",
    "WorldPositionData",
]
