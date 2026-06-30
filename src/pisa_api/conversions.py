"""Shared protobuf/dataclass conversions for PISA payload messages."""

from pathlib import Path
from typing import Any, Dict, Optional

from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct

from pisa_api.av_server_pb2 import Observation, ObservedAgent
from pisa_api.collision_pb2 import ActorRef, CollisionInfo
from pisa_api.config_pb2 import Config
from pisa_api.control_pb2 import CtrlCmd
from pisa_api.object_pb2 import ObjectKinematic, ObjectState, Shape
from pisa_api.path_pb2 import Path as PathMessage
from pisa_api.position_pb2 import LanePosition, Position, WorldPosition
from pisa_api.runtime_frame_pb2 import RuntimeFrame, SimulatorEgo, SimulatorObject
from pisa_api.scenario_pb2 import EgoConfig, GoalConfig, Scenario, ScenarioPack, SpawnConfig
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
    SimulatorEgoData,
    SimulatorObjectData,
    SpawnConfigData,
    WorldPositionData,
)


def path_from_proto(path: PathMessage) -> Optional[Path]:
    if not path.path:
        return None
    return Path(path.path)


def path_to_proto(path: Optional[Path]) -> PathMessage:
    if path is None:
        return PathMessage()
    return PathMessage(path=str(path))


def config_from_proto(config: Config) -> Dict[str, Any]:
    return _dict_from_struct(config.config)


def config_to_proto(config: Dict[str, Any]) -> Config:
    return Config(config=_struct_from_dict(config))


def world_position_from_proto(position: WorldPosition) -> WorldPositionData:
    return WorldPositionData(
        x=position.x,
        y=position.y,
        z=position.z,
        h=position.h,
        p=position.p,
        r=position.r,
        h_relative=position.h_relative,
    )


def world_position_to_proto(position: WorldPositionData) -> WorldPosition:
    return WorldPosition(
        x=position.x,
        y=position.y,
        z=position.z,
        h=position.h,
        p=position.p,
        r=position.r,
        h_relative=position.h_relative,
    )


def lane_position_from_proto(position: LanePosition) -> LanePositionData:
    return LanePositionData(
        road_id=position.road_id,
        lane_id=position.lane_id,
        s=position.s,
        offset=position.offset,
        junction_id=position.junction_id if _has_field(position, "junction_id") else None,
    )


def lane_position_to_proto(position: LanePositionData) -> LanePosition:
    proto = LanePosition(
        road_id=position.road_id,
        lane_id=position.lane_id,
        s=position.s,
        offset=position.offset,
    )
    if position.junction_id is not None:
        proto.junction_id = position.junction_id
    return proto


def position_from_proto(position: Position) -> PositionData:
    return PositionData(
        lane=lane_position_from_proto(position.lane),
        world=world_position_from_proto(position.world),
    )


def position_to_proto(position: PositionData) -> Position:
    return Position(
        lane=lane_position_to_proto(position.lane),
        world=world_position_to_proto(position.world),
    )


def spawn_config_from_proto(config: SpawnConfig) -> SpawnConfigData:
    return SpawnConfigData(
        position=position_from_proto(config.position),
        speed=config.speed,
    )


def spawn_config_to_proto(config: SpawnConfigData) -> SpawnConfig:
    return SpawnConfig(
        position=position_to_proto(config.position),
        speed=config.speed,
    )


def goal_config_from_proto(config: GoalConfig) -> GoalConfigData:
    return GoalConfigData(position=position_from_proto(config.position))


def goal_config_to_proto(config: GoalConfigData) -> GoalConfig:
    return GoalConfig(position=position_to_proto(config.position))


def ego_config_from_proto(config: EgoConfig) -> EgoConfigData:
    return EgoConfigData(
        target_speed=config.target_speed,
        spawn_config=spawn_config_from_proto(config.spawn_config),
        goal_config=goal_config_from_proto(config.goal_config),
    )


def ego_config_to_proto(config: EgoConfigData) -> EgoConfig:
    return EgoConfig(
        target_speed=config.target_speed,
        spawn_config=spawn_config_to_proto(config.spawn_config),
        goal_config=goal_config_to_proto(config.goal_config),
    )


def scenario_from_proto(scenario: Scenario) -> ScenarioData:
    return ScenarioData(
        format=scenario.format,
        name=scenario.name,
        path=path_from_proto(scenario.path),
    )


def scenario_to_proto(scenario: ScenarioData) -> Scenario:
    return Scenario(
        format=scenario.format,
        name=scenario.name,
        path=path_to_proto(scenario.path),
    )


def scenario_pack_from_proto(scenario_pack: ScenarioPack) -> ScenarioPackData:
    return ScenarioPackData(
        name=scenario_pack.name,
        map_name=scenario_pack.map_name,
        scenarios={name: Path(path.path) for name, path in scenario_pack.scenarios.items()},
        param_range_file=(
            path_from_proto(scenario_pack.param_range_file)
            if _has_field(scenario_pack, "param_range_file")
            else None
        ),
        ego=ego_config_from_proto(scenario_pack.ego),
        timeout_ns=scenario_pack.timeout_ns,
    )


def scenario_pack_to_proto(scenario_pack: ScenarioPackData) -> ScenarioPack:
    proto = ScenarioPack(
        name=scenario_pack.name,
        map_name=scenario_pack.map_name,
        ego=ego_config_to_proto(scenario_pack.ego),
        timeout_ns=scenario_pack.timeout_ns,
    )
    for name, path in scenario_pack.scenarios.items():
        proto.scenarios[name].path = str(path)
    if scenario_pack.param_range_file is not None:
        proto.param_range_file.CopyFrom(path_to_proto(scenario_pack.param_range_file))
    return proto


def control_command_from_proto(ctrl_cmd: CtrlCmd) -> ControlCommand:
    return ControlCommand(
        mode=ControlMode(ctrl_cmd.mode),
        payload=_dict_from_struct(ctrl_cmd.payload),
    )


def control_command_to_proto(ctrl_cmd: ControlCommand) -> CtrlCmd:
    return CtrlCmd(
        mode=int(ctrl_cmd.mode),
        payload=_struct_from_dict(ctrl_cmd.payload),
    )


def object_kinematic_from_proto(kinematic: ObjectKinematic) -> ObjectKinematicData:
    return ObjectKinematicData(
        time_ns=kinematic.time_ns,
        x=kinematic.x,
        y=kinematic.y,
        z=kinematic.z,
        yaw=kinematic.yaw,
        speed=kinematic.speed,
        acceleration=kinematic.acceleration,
        yaw_rate=kinematic.yaw_rate,
        yaw_acceleration=kinematic.yaw_acceleration,
    )


def object_kinematic_to_proto(kinematic: ObjectKinematicData) -> ObjectKinematic:
    return ObjectKinematic(
        time_ns=kinematic.time_ns,
        x=kinematic.x,
        y=kinematic.y,
        z=kinematic.z,
        yaw=kinematic.yaw,
        speed=kinematic.speed,
        acceleration=kinematic.acceleration,
        yaw_rate=kinematic.yaw_rate,
        yaw_acceleration=kinematic.yaw_acceleration,
    )


def shape_from_proto(shape: Shape) -> ShapeData:
    return ShapeData(
        type=ShapeType(shape.type),
        dimensions=ShapeDimensionData(
            x=shape.dimensions.x,
            y=shape.dimensions.y,
            z=shape.dimensions.z,
        ),
        vertices=[ShapeVertexData(x=vertex.x, y=vertex.y, z=vertex.z) for vertex in shape.vertices],
        center=ShapeCenterPoseData(
            x=shape.center.x,
            y=shape.center.y,
            z=shape.center.z,
            roll=shape.center.roll,
            pitch=shape.center.pitch,
            yaw=shape.center.yaw,
        ),
        reference_point=shape.reference_point,
    )


def shape_to_proto(shape: ShapeData) -> Shape:
    return Shape(
        type=int(shape.type),
        dimensions=Shape.Dimension(
            x=shape.dimensions.x,
            y=shape.dimensions.y,
            z=shape.dimensions.z,
        ),
        vertices=[Shape.Vertex(x=vertex.x, y=vertex.y, z=vertex.z) for vertex in shape.vertices],
        center=Shape.CenterPose(
            x=shape.center.x,
            y=shape.center.y,
            z=shape.center.z,
            roll=shape.center.roll,
            pitch=shape.center.pitch,
            yaw=shape.center.yaw,
        ),
        reference_point=shape.reference_point,
    )


def object_state_from_proto(obj: ObjectState) -> ObjectStateData:
    return ObjectStateData(
        type=RoadObjectType(obj.type),
        kinematic=object_kinematic_from_proto(obj.kinematic),
        shape=shape_from_proto(obj.shape) if _has_field(obj, "shape") else None,
    )


def object_state_to_proto(obj: ObjectStateData) -> ObjectState:
    proto = ObjectState(
        type=int(obj.type),
        kinematic=object_kinematic_to_proto(obj.kinematic),
    )
    if obj.shape is not None:
        proto.shape.CopyFrom(shape_to_proto(obj.shape))
    return proto


def collision_info_from_proto(collision: CollisionInfo) -> CollisionInfoData:
    return CollisionInfoData(
        occurred=collision.occurred,
        actor_a=actor_ref_from_proto(collision.actor_a)
        if _has_field(collision, "actor_a")
        else None,
        actor_b=actor_ref_from_proto(collision.actor_b)
        if _has_field(collision, "actor_b")
        else None,
        details=_dict_from_struct(collision.details),
    )


def collision_info_to_proto(collision: CollisionInfoData) -> CollisionInfo:
    proto = CollisionInfo(
        occurred=collision.occurred,
        details=_struct_from_dict(collision.details),
    )
    if collision.actor_a is not None:
        proto.actor_a.CopyFrom(actor_ref_to_proto(collision.actor_a))
    if collision.actor_b is not None:
        proto.actor_b.CopyFrom(actor_ref_to_proto(collision.actor_b))
    return proto


def actor_ref_from_proto(actor: ActorRef) -> ActorRefData:
    return ActorRefData(
        tracking_id=actor.tracking_id,
        entity_name=actor.entity_name if _has_field(actor, "entity_name") else None,
        role=ActorRole(actor.role),
    )


def actor_ref_to_proto(actor: ActorRefData) -> ActorRef:
    proto = ActorRef(tracking_id=actor.tracking_id, role=int(actor.role))
    if actor.entity_name is not None:
        proto.entity_name = actor.entity_name
    return proto


def simulator_object_from_proto(obj: SimulatorObject) -> SimulatorObjectData:
    return SimulatorObjectData(
        state=object_state_from_proto(obj.state),
        entity_name=obj.entity_name if _has_field(obj, "entity_name") else None,
    )


def simulator_object_to_proto(obj: SimulatorObjectData) -> SimulatorObject:
    proto = SimulatorObject(state=object_state_to_proto(obj.state))
    if obj.entity_name is not None:
        proto.entity_name = obj.entity_name
    return proto


def simulator_ego_from_proto(ego: SimulatorEgo) -> SimulatorEgoData:
    return SimulatorEgoData(
        tracking_id=ego.tracking_id,
        object=simulator_object_from_proto(ego.object),
    )


def simulator_ego_to_proto(ego: SimulatorEgoData) -> SimulatorEgo:
    return SimulatorEgo(
        tracking_id=ego.tracking_id,
        object=simulator_object_to_proto(ego.object),
    )


def runtime_frame_from_proto(frame: RuntimeFrame) -> RuntimeFrameData:
    return RuntimeFrameData(
        sim_time_ns=frame.sim_time_ns,
        ego=simulator_ego_from_proto(frame.ego),
        agents={
            tracking_id: simulator_object_from_proto(obj)
            for tracking_id, obj in frame.agents.items()
        },
        collision=[collision_info_from_proto(collision) for collision in frame.collision],
        extras=_dict_from_struct(frame.extras),
    )


def runtime_frame_to_proto(frame: RuntimeFrameData) -> RuntimeFrame:
    return RuntimeFrame(
        sim_time_ns=frame.sim_time_ns,
        ego=simulator_ego_to_proto(frame.ego),
        agents={
            tracking_id: simulator_object_to_proto(obj) for tracking_id, obj in frame.agents.items()
        },
        collision=[collision_info_to_proto(collision) for collision in frame.collision],
        extras=_struct_from_dict(frame.extras),
    )


def observed_agent_from_proto(agent: ObservedAgent) -> ObservedAgentData:
    return ObservedAgentData(
        state=object_state_from_proto(agent.state),
        tracking_id=agent.tracking_id if _has_field(agent, "tracking_id") else None,
        entity_name=agent.entity_name if _has_field(agent, "entity_name") else None,
    )


def observed_agent_to_proto(agent: ObservedAgentData) -> ObservedAgent:
    proto = ObservedAgent(state=object_state_to_proto(agent.state))
    if agent.tracking_id is not None:
        proto.tracking_id = agent.tracking_id
    if agent.entity_name is not None:
        proto.entity_name = agent.entity_name
    return proto


def observation_from_proto(observation: Observation) -> ObservationData:
    return ObservationData(
        ego=object_state_from_proto(observation.ego),
        agents=[observed_agent_from_proto(agent) for agent in observation.agents],
    )


def observation_to_proto(observation: ObservationData) -> Observation:
    return Observation(
        ego=object_state_to_proto(observation.ego),
        agents=[observed_agent_to_proto(agent) for agent in observation.agents],
    )


def _dict_from_struct(struct: Struct) -> Dict[str, Any]:
    return MessageToDict(struct, preserving_proto_field_name=True)


def _struct_from_dict(values: Dict[str, Any]) -> Struct:
    struct = Struct()
    struct.update(values or {})
    return struct


def _has_field(message: Any, field_name: str) -> bool:
    try:
        return message.HasField(field_name)
    except ValueError:
        return False


__all__ = [
    "actor_ref_from_proto",
    "actor_ref_to_proto",
    "collision_info_from_proto",
    "collision_info_to_proto",
    "config_from_proto",
    "config_to_proto",
    "control_command_from_proto",
    "control_command_to_proto",
    "ego_config_from_proto",
    "ego_config_to_proto",
    "goal_config_from_proto",
    "goal_config_to_proto",
    "lane_position_from_proto",
    "lane_position_to_proto",
    "object_kinematic_from_proto",
    "object_kinematic_to_proto",
    "object_state_from_proto",
    "object_state_to_proto",
    "observation_from_proto",
    "observation_to_proto",
    "observed_agent_from_proto",
    "observed_agent_to_proto",
    "path_from_proto",
    "path_to_proto",
    "position_from_proto",
    "position_to_proto",
    "runtime_frame_from_proto",
    "runtime_frame_to_proto",
    "scenario_from_proto",
    "scenario_pack_from_proto",
    "scenario_pack_to_proto",
    "scenario_to_proto",
    "shape_from_proto",
    "shape_to_proto",
    "simulator_ego_from_proto",
    "simulator_ego_to_proto",
    "simulator_object_from_proto",
    "simulator_object_to_proto",
    "spawn_config_from_proto",
    "spawn_config_to_proto",
    "world_position_from_proto",
    "world_position_to_proto",
]
