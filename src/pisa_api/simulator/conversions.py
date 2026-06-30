"""Conversions between generated protobuf messages and simulator dataclasses."""

from pathlib import Path

from pisa_api import sim_server_pb2
from pisa_api.conversions import (
    actor_ref_from_proto,
    actor_ref_to_proto,
    collision_info_from_proto,
    collision_info_to_proto,
    config_from_proto,
    config_to_proto,
    control_command_from_proto,
    control_command_to_proto,
    ego_config_from_proto,
    ego_config_to_proto,
    goal_config_from_proto,
    goal_config_to_proto,
    lane_position_from_proto,
    lane_position_to_proto,
    object_kinematic_from_proto,
    object_kinematic_to_proto,
    object_state_from_proto,
    object_state_to_proto,
    path_from_proto,
    path_to_proto,
    position_from_proto,
    position_to_proto,
    runtime_frame_from_proto,
    runtime_frame_to_proto,
    scenario_from_proto,
    scenario_pack_from_proto,
    scenario_pack_to_proto,
    scenario_to_proto,
    shape_from_proto,
    shape_to_proto,
    simulator_ego_from_proto,
    simulator_ego_to_proto,
    simulator_object_from_proto,
    simulator_object_to_proto,
    spawn_config_from_proto,
    spawn_config_to_proto,
    world_position_from_proto,
    world_position_to_proto,
)

from .types import (
    InitRequest,
    ResetRequest,
    ResetResponse,
    ShouldQuitResponse,
    StepRequest,
    StepResponse,
)

SimServerMessages = sim_server_pb2.SimServerMessages


def init_request_from_proto(request: SimServerMessages.InitRequest) -> InitRequest:
    return InitRequest(
        config=config_from_proto(request.config),
        output_dir=Path(request.output_dir.path),
        scenario=scenario_from_proto(request.scenario),
        dt=request.dt,
    )


def init_request_to_proto(request: InitRequest) -> SimServerMessages.InitRequest:
    return SimServerMessages.InitRequest(
        config=config_to_proto(request.config),
        output_dir=path_to_proto(request.output_dir),
        dt=request.dt,
        scenario=scenario_to_proto(request.scenario),
    )


def reset_request_from_proto(request: SimServerMessages.ResetRequest) -> ResetRequest:
    return ResetRequest(
        output_dir=Path(request.output_dir.path),
        scenario_pack=scenario_pack_from_proto(request.scenario_pack),
        params=dict(request.params),
    )


def reset_request_to_proto(request: ResetRequest) -> SimServerMessages.ResetRequest:
    return SimServerMessages.ResetRequest(
        output_dir=path_to_proto(request.output_dir),
        scenario_pack=scenario_pack_to_proto(request.scenario_pack),
        params=request.params,
    )


def reset_response_from_proto(response: SimServerMessages.ResetResponse) -> ResetResponse:
    return ResetResponse(frame=runtime_frame_from_proto(response.frame))


def reset_response_to_proto(response: ResetResponse) -> SimServerMessages.ResetResponse:
    return SimServerMessages.ResetResponse(frame=runtime_frame_to_proto(response.frame))


def step_request_from_proto(request: SimServerMessages.StepRequest) -> StepRequest:
    return StepRequest(
        ctrl_cmd=control_command_from_proto(request.ctrl_cmd),
        timestamp_ns=request.timestamp_ns,
    )


def step_request_to_proto(request: StepRequest) -> SimServerMessages.StepRequest:
    return SimServerMessages.StepRequest(
        ctrl_cmd=control_command_to_proto(request.ctrl_cmd),
        timestamp_ns=request.timestamp_ns,
    )


def step_response_from_proto(response: SimServerMessages.StepResponse) -> StepResponse:
    return StepResponse(frame=runtime_frame_from_proto(response.frame))


def step_response_to_proto(response: StepResponse) -> SimServerMessages.StepResponse:
    return SimServerMessages.StepResponse(frame=runtime_frame_to_proto(response.frame))


def should_quit_response_from_proto(
    response: SimServerMessages.ShouldQuitResponse,
) -> ShouldQuitResponse:
    return ShouldQuitResponse(should_quit=response.should_quit, msg=response.msg)


def should_quit_response_to_proto(
    response: ShouldQuitResponse,
) -> SimServerMessages.ShouldQuitResponse:
    return SimServerMessages.ShouldQuitResponse(
        should_quit=response.should_quit,
        msg=response.msg,
    )


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
    "init_request_from_proto",
    "init_request_to_proto",
    "lane_position_from_proto",
    "lane_position_to_proto",
    "object_kinematic_from_proto",
    "object_kinematic_to_proto",
    "object_state_from_proto",
    "object_state_to_proto",
    "path_from_proto",
    "path_to_proto",
    "position_from_proto",
    "position_to_proto",
    "reset_request_from_proto",
    "reset_request_to_proto",
    "reset_response_from_proto",
    "reset_response_to_proto",
    "runtime_frame_from_proto",
    "runtime_frame_to_proto",
    "scenario_from_proto",
    "scenario_pack_from_proto",
    "scenario_pack_to_proto",
    "scenario_to_proto",
    "shape_from_proto",
    "shape_to_proto",
    "should_quit_response_from_proto",
    "should_quit_response_to_proto",
    "simulator_ego_from_proto",
    "simulator_ego_to_proto",
    "simulator_object_from_proto",
    "simulator_object_to_proto",
    "spawn_config_from_proto",
    "spawn_config_to_proto",
    "step_request_from_proto",
    "step_request_to_proto",
    "step_response_from_proto",
    "step_response_to_proto",
    "world_position_from_proto",
    "world_position_to_proto",
]
