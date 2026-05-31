"""Conversions between AvServer protobuf messages and AV dataclasses."""

from pathlib import Path

from pisa_api import av_server_pb2
from pisa_api.conversions import (
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

AvServerMessages = av_server_pb2.AvServerMessages


def init_request_from_proto(request: AvServerMessages.InitRequest) -> InitRequest:
    return InitRequest(
        config=config_from_proto(request.config),
        output_dir=Path(request.output_dir.path),
        map_name=request.map_name,
        dt=request.dt,
    )


def init_request_to_proto(request: InitRequest) -> AvServerMessages.InitRequest:
    return AvServerMessages.InitRequest(
        config=config_to_proto(request.config),
        output_dir=path_to_proto(request.output_dir),
        map_name=request.map_name,
        dt=request.dt,
    )


def reset_request_from_proto(request: AvServerMessages.ResetRequest) -> ResetRequest:
    return ResetRequest(
        output_dir=Path(request.output_dir.path),
        scenario_pack=scenario_pack_from_proto(request.scenario_pack),
        initial_observation=[object_state_from_proto(obj) for obj in request.initial_observation],
    )


def reset_request_to_proto(request: ResetRequest) -> AvServerMessages.ResetRequest:
    return AvServerMessages.ResetRequest(
        output_dir=path_to_proto(request.output_dir),
        scenario_pack=scenario_pack_to_proto(request.scenario_pack),
        initial_observation=[object_state_to_proto(obj) for obj in request.initial_observation],
    )


def reset_response_from_proto(response: AvServerMessages.ResetResponse) -> ResetResponse:
    return ResetResponse(ctrl_cmd=control_command_from_proto(response.ctrl_cmd))


def reset_response_to_proto(response: ResetResponse) -> AvServerMessages.ResetResponse:
    return AvServerMessages.ResetResponse(ctrl_cmd=control_command_to_proto(response.ctrl_cmd))


def step_request_from_proto(request: AvServerMessages.StepRequest) -> StepRequest:
    return StepRequest(
        observation=[object_state_from_proto(obj) for obj in request.observation],
        timestamp_ns=request.timestamp_ns,
    )


def step_request_to_proto(request: StepRequest) -> AvServerMessages.StepRequest:
    return AvServerMessages.StepRequest(
        observation=[object_state_to_proto(obj) for obj in request.observation],
        timestamp_ns=request.timestamp_ns,
    )


def step_response_from_proto(response: AvServerMessages.StepResponse) -> StepResponse:
    return StepResponse(ctrl_cmd=control_command_from_proto(response.ctrl_cmd))


def step_response_to_proto(response: StepResponse) -> AvServerMessages.StepResponse:
    return AvServerMessages.StepResponse(ctrl_cmd=control_command_to_proto(response.ctrl_cmd))


def should_quit_response_from_proto(
    response: AvServerMessages.ShouldQuitResponse,
) -> ShouldQuitResponse:
    return ShouldQuitResponse(should_quit=response.should_quit, msg=response.msg)


def should_quit_response_to_proto(
    response: ShouldQuitResponse,
) -> AvServerMessages.ShouldQuitResponse:
    return AvServerMessages.ShouldQuitResponse(
        should_quit=response.should_quit,
        msg=response.msg,
    )


__all__ = [
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
    "spawn_config_from_proto",
    "spawn_config_to_proto",
    "step_request_from_proto",
    "step_request_to_proto",
    "step_response_from_proto",
    "step_response_to_proto",
    "world_position_from_proto",
    "world_position_to_proto",
]
