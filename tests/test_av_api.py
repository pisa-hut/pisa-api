from pathlib import Path

import grpc

from pisa_api import av_server_pb2
from pisa_api.av import (
    AvPreconditionFailed,
    AvUnavailable,
    ControlCommand,
    ControlMode,
    GenericAvService,
    InitRequest,
    InvalidAvRequest,
    ObjectKinematicData,
    ObjectStateData,
    ResetRequest,
    ResetResponse,
    RoadObjectType,
    ShapeData,
    ShapeDimensionData,
    ShapeType,
    StepRequest,
    StepResponse,
)
from pisa_api.av.conversions import (
    init_request_from_proto,
    init_request_to_proto,
    reset_request_from_proto,
    reset_request_to_proto,
    reset_response_from_proto,
    reset_response_to_proto,
    step_request_from_proto,
    step_request_to_proto,
    step_response_from_proto,
    step_response_to_proto,
)
from pisa_api.simulator import ControlCommand as SimulatorControlCommand


class FakeContext:
    def __init__(self):
        self.code = None
        self.details = None

    def peer(self):
        return "test-peer"

    def set_code(self, code):
        self.code = code

    def set_details(self, details):
        self.details = details


class FakeAvSystem:
    def __init__(self):
        self.init_request = None
        self.reset_request = None
        self.step_request = None
        self.stopped = False

    def init(self, request: InitRequest):
        self.init_request = request

    def reset(self, request: ResetRequest) -> ResetResponse:
        self.reset_request = request
        return ResetResponse(
            ctrl_cmd=ControlCommand(mode=ControlMode.ACKERMANN, payload={"speed": 1.0})
        )

    def step(self, request: StepRequest) -> StepResponse:
        self.step_request = request
        return StepResponse(
            ctrl_cmd=ControlCommand(mode=ControlMode.ACKERMANN, payload={"speed": 2.0})
        )

    def stop(self) -> None:
        self.stopped = True

    def should_quit(self) -> bool:
        return False


def test_av_and_simulator_reexport_same_shared_control_type() -> None:
    assert ControlCommand is SimulatorControlCommand


def test_av_init_and_observation_requests_round_trip() -> None:
    init_data = InitRequest(
        config={"autoware": {"headless": True}},
        output_dir=Path("/tmp/output"),
        map_name="town",
        dt=0.05,
    )

    init_round_trip = init_request_from_proto(init_request_to_proto(init_data))

    assert init_round_trip == init_data

    observation = [
        ObjectStateData(
            type=RoadObjectType.CAR,
            kinematic=ObjectKinematicData(time_ns=10, x=1.0, y=2.0),
            shape=ShapeData(
                type=ShapeType.BOUNDING_BOX,
                dimensions=ShapeDimensionData(x=4.0, y=2.0, z=1.5),
            ),
        )
    ]
    reset_proto = reset_request_to_proto(
        ResetRequest(output_dir=Path("run-1"), initial_observation=observation)
    )
    reset_round_trip = reset_request_from_proto(reset_proto)
    step_round_trip = step_request_from_proto(
        step_request_to_proto(StepRequest(observation=observation, timestamp_ns=123))
    )

    assert reset_round_trip.output_dir == Path("run-1")
    assert reset_round_trip.initial_observation == observation
    assert step_round_trip.observation == observation
    assert step_round_trip.timestamp_ns == 123


def test_av_control_responses_round_trip() -> None:
    ctrl_cmd = ControlCommand(
        mode=ControlMode.ACKERMANN,
        payload={"steer": 0.1, "speed": 12.5},
    )

    reset_round_trip = reset_response_from_proto(
        reset_response_to_proto(ResetResponse(ctrl_cmd=ctrl_cmd))
    )
    step_round_trip = step_response_from_proto(
        step_response_to_proto(StepResponse(ctrl_cmd=ctrl_cmd))
    )

    assert reset_round_trip.ctrl_cmd == ctrl_cmd
    assert step_round_trip.ctrl_cmd == ctrl_cmd


def test_generic_av_service_maps_lifecycle_requests_to_dataclass_av_system() -> None:
    av_system = FakeAvSystem()
    service = GenericAvService(av_system, name="FakeAV")

    init_request = av_server_pb2.AvServerMessages.InitRequest()
    init_request.config.config.update({"use_sim_time": True})
    init_request.output_dir.path = "/tmp/output"
    init_request.map_name = "town"
    init_request.dt = 0.05

    init_context = FakeContext()
    service.Init(init_request, init_context)

    assert init_context.code is None  # Init no longer signals via response payload
    assert av_system.init_request.config == {"use_sim_time": True}
    assert av_system.init_request.output_dir.as_posix() == "/tmp/output"
    assert av_system.init_request.map_name == "town"

    reset_request = av_server_pb2.AvServerMessages.ResetRequest()
    reset_request.output_dir.path = "run-1"
    reset_request.initial_observation.add(type=int(RoadObjectType.CAR))

    reset_response = service.Reset(reset_request, FakeContext())

    assert reset_response.ctrl_cmd.mode == int(ControlMode.ACKERMANN)
    assert av_system.reset_request.output_dir.as_posix() == "run-1"
    assert av_system.reset_request.initial_observation[0].type == RoadObjectType.CAR

    step_request = av_server_pb2.AvServerMessages.StepRequest(timestamp_ns=123)
    step_response = service.Step(step_request, FakeContext())

    assert step_response.ctrl_cmd.payload["speed"] == 2.0
    assert av_system.step_request.timestamp_ns == 123


def test_generic_av_service_rejects_step_before_reset() -> None:
    av_system = FakeAvSystem()
    service = GenericAvService(av_system, name="FakeAV")

    init_context = FakeContext()
    service.Init(av_server_pb2.AvServerMessages.InitRequest(), init_context)
    assert init_context.code is None

    context = FakeContext()
    response = service.Step(av_server_pb2.AvServerMessages.StepRequest(), context)

    assert response == av_server_pb2.AvServerMessages.StepResponse()
    assert context.code == grpc.StatusCode.FAILED_PRECONDITION
    assert "Reset" in context.details


class _RaisingAvSystem(FakeAvSystem):
    """FakeAvSystem variant that raises a configured exception from
    Reset/Step so the tests can assert on the gRPC status code routing."""

    def __init__(self, exc: BaseException) -> None:
        super().__init__()
        self._exc = exc

    def reset(self, request: ResetRequest) -> ControlCommand:
        raise self._exc

    def step(self, request: StepRequest) -> ControlCommand:
        raise self._exc


def _init_and_reset(service: GenericAvService) -> None:
    """Helper: drive the service to the post-reset state so Step is
    allowed (the early `not _reset_done` branch returns
    FAILED_PRECONDITION on its own)."""
    service.Init(av_server_pb2.AvServerMessages.InitRequest(), FakeContext())
    service.Reset(av_server_pb2.AvServerMessages.ResetRequest(), FakeContext())


def test_reset_invalid_av_request_returns_invalid_argument() -> None:
    service = GenericAvService(_RaisingAvSystem(InvalidAvRequest("bad logical")), name="FakeAV")
    service.Init(av_server_pb2.AvServerMessages.InitRequest(), FakeContext())
    context = FakeContext()
    service.Reset(av_server_pb2.AvServerMessages.ResetRequest(), context)
    assert context.code == grpc.StatusCode.INVALID_ARGUMENT


def test_reset_precondition_failed_returns_failed_precondition() -> None:
    service = GenericAvService(_RaisingAvSystem(AvPreconditionFailed("no route")), name="FakeAV")
    service.Init(av_server_pb2.AvServerMessages.InitRequest(), FakeContext())
    context = FakeContext()
    service.Reset(av_server_pb2.AvServerMessages.ResetRequest(), context)
    assert context.code == grpc.StatusCode.FAILED_PRECONDITION


def test_reset_runtime_error_still_failed_precondition() -> None:
    """Generic RuntimeError keeps the previous "skip this concrete"
    behaviour — only InvalidAvRequest gets promoted to INVALID_ARGUMENT."""
    service = GenericAvService(_RaisingAvSystem(RuntimeError("oops")), name="FakeAV")
    service.Init(av_server_pb2.AvServerMessages.InitRequest(), FakeContext())
    context = FakeContext()
    service.Reset(av_server_pb2.AvServerMessages.ResetRequest(), context)
    assert context.code == grpc.StatusCode.FAILED_PRECONDITION


def test_reset_av_unavailable_returns_unavailable() -> None:
    service = GenericAvService(_RaisingAvSystem(AvUnavailable("down")), name="FakeAV")
    service.Init(av_server_pb2.AvServerMessages.InitRequest(), FakeContext())
    context = FakeContext()
    service.Reset(av_server_pb2.AvServerMessages.ResetRequest(), context)
    assert context.code == grpc.StatusCode.UNAVAILABLE


def test_reset_returning_none_is_internal_error() -> None:
    """Wrapper contract: reset() must return ResetResponse. None
    surfaces as INTERNAL so the wrapper author can see the bug."""
    av_system = FakeAvSystem()
    av_system.reset = lambda _req: None  # contract violation
    service = GenericAvService(av_system, name="FakeAV")
    service.Init(av_server_pb2.AvServerMessages.InitRequest(), FakeContext())
    context = FakeContext()
    service.Reset(av_server_pb2.AvServerMessages.ResetRequest(), context)
    assert context.code == grpc.StatusCode.INTERNAL
    assert "must return ResetResponse" in context.details


def test_step_returning_bare_control_command_is_internal_error() -> None:
    """Old shortcut where step() returned a bare ControlCommand is gone;
    wrappers must wrap it in a StepResponse explicitly."""
    av_system = FakeAvSystem()
    service = GenericAvService(av_system, name="FakeAV")
    _init_and_reset(service)
    av_system.step = lambda _req: ControlCommand(mode=ControlMode.ACKERMANN)
    context = FakeContext()
    service.Step(av_server_pb2.AvServerMessages.StepRequest(), context)
    assert context.code == grpc.StatusCode.INTERNAL
    assert "must return StepResponse" in context.details


def test_step_invalid_av_request_returns_invalid_argument() -> None:
    # Use a clean FakeAvSystem so Init + Reset succeed, then monkey-patch
    # `step` to raise — otherwise Reset would fail and Step would short-
    # circuit on the "not reset" guard before reaching the step handler.
    av_system = FakeAvSystem()
    service = GenericAvService(av_system, name="FakeAV")
    _init_and_reset(service)

    def _raise(_req):
        raise InvalidAvRequest("step bad")

    av_system.step = _raise
    context = FakeContext()
    service.Step(av_server_pb2.AvServerMessages.StepRequest(), context)
    assert context.code == grpc.StatusCode.INVALID_ARGUMENT


def test_serve_av_system_wraps_existing_serve_av(monkeypatch) -> None:
    import pisa_api.av.service as service_module

    calls = {}

    def fake_serve_av(servicer, *, port, max_workers, name):
        calls["servicer"] = servicer
        calls["port"] = port
        calls["max_workers"] = max_workers
        calls["name"] = name

    monkeypatch.setattr(service_module, "serve_av", fake_serve_av)

    service_module.serve_av_system(FakeAvSystem(), name="FakeAV", port=1234, max_workers=2)

    assert isinstance(calls["servicer"], GenericAvService)
    assert calls["port"] == 1234
    assert calls["max_workers"] == 2
    assert calls["name"] == "FakeAV"
