from pathlib import Path

import grpc

from pisa_api import sim_server_pb2
from pisa_api.simulator import (
    CollisionInfoData,
    ControlCommand,
    ControlMode,
    GenericSimulatorService,
    InitRequest,
    ObjectKinematicData,
    ObjectStateData,
    ResetRequest,
    RoadObjectType,
    RuntimeFrameData,
    ScenarioData,
    ScenarioPackData,
    ShapeData,
    ShapeDimensionData,
    ShapeType,
    StepRequest,
)
from pisa_api.simulator.conversions import (
    init_request_from_proto,
    init_request_to_proto,
    runtime_frame_from_proto,
    runtime_frame_to_proto,
    scenario_pack_from_proto,
    scenario_pack_to_proto,
    step_request_from_proto,
    step_request_to_proto,
)


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


class FakeSimulator:
    def __init__(self):
        self.init_request = None
        self.reset_request = None
        self.step_request = None
        self.stopped = False

    def init(self, request: InitRequest):
        self.init_request = request

    def reset(self, request: ResetRequest) -> RuntimeFrameData:
        self.reset_request = request
        return RuntimeFrameData(sim_time_ns=0)

    def step(self, request: StepRequest) -> RuntimeFrameData:
        self.step_request = request
        return RuntimeFrameData(sim_time_ns=request.timestamp_ns)

    def stop(self) -> None:
        self.stopped = True

    def should_quit(self) -> bool:
        return False


def make_init_request(scenario_format: str) -> sim_server_pb2.SimServerMessages.InitRequest:
    request = sim_server_pb2.SimServerMessages.InitRequest()
    request.scenario.format = scenario_format
    return request


def test_init_and_step_requests_round_trip_between_dataclasses_and_protobuf() -> None:
    init_data = InitRequest(
        config={"use_viewer": False, "backend": "fake"},
        output_dir=Path("/tmp/output"),
        scenario=ScenarioData(format="open_scenario1", name="cut-in", path=Path("case.xosc")),
        dt=0.05,
    )
    init_proto = init_request_to_proto(init_data)
    init_round_trip = init_request_from_proto(init_proto)

    assert init_round_trip == init_data

    step_data = StepRequest(
        ctrl_cmd=ControlCommand(
            mode=ControlMode.ACKERMANN,
            payload={"steer": 0.1, "speed": 12.5},
        ),
        timestamp_ns=123,
    )
    step_proto = step_request_to_proto(step_data)
    step_round_trip = step_request_from_proto(step_proto)

    assert step_round_trip == step_data


def test_scenario_pack_conversion_preserves_optional_fields() -> None:
    pack = ScenarioPackData(
        name="pack",
        map_name="town",
        scenarios={"case-a": Path("case-a.xosc")},
        param_range_file=Path("params.json"),
        timeout_ns=99,
    )

    proto = scenario_pack_to_proto(pack)
    round_trip = scenario_pack_from_proto(proto)

    assert proto.HasField("param_range_file")
    assert round_trip == pack


def test_runtime_frame_conversion_preserves_objects_collision_and_extras() -> None:
    frame = RuntimeFrameData(
        sim_time_ns=10,
        objects=[
            ObjectStateData(
                type=RoadObjectType.CAR,
                kinematic=ObjectKinematicData(time_ns=10, x=1.0, y=2.0, speed=3.0),
                shape=ShapeData(
                    type=ShapeType.BOUNDING_BOX,
                    dimensions=ShapeDimensionData(x=4.0, y=2.0, z=1.5),
                ),
            )
        ],
        collision=[
            CollisionInfoData(
                occurred=True,
                actor_a=0,
                actor_b=2,
                details={"source": "test"},
            )
        ],
        extras={"backend": "fake"},
    )

    proto = runtime_frame_to_proto(frame)
    round_trip = runtime_frame_from_proto(proto)

    assert proto.objects[0].HasField("shape")
    assert proto.collision[0].HasField("actor_a")
    assert round_trip == frame


def test_generic_service_maps_lifecycle_requests_to_dataclass_simulator() -> None:
    simulator = FakeSimulator()
    service = GenericSimulatorService(
        simulator,
        name="Fake",
        scenario_format="open_scenario1",
    )

    init_request = sim_server_pb2.SimServerMessages.InitRequest()
    init_request.config.config.update({"use_viewer": False})
    init_request.output_dir.path = "/tmp/output"
    init_request.scenario.format = "open_scenario1"
    init_request.dt = 0.05

    init_context = FakeContext()
    service.Init(init_request, init_context)

    assert init_context.code is None
    assert simulator.init_request.config == {"use_viewer": False}
    assert simulator.init_request.output_dir.as_posix() == "/tmp/output"
    assert simulator.init_request.dt == 0.05

    reset_request = sim_server_pb2.SimServerMessages.ResetRequest()
    reset_request.output_dir.path = "run-1"
    reset_request.scenario_pack.name = "scenario"
    reset_request.params["speed"] = "10"

    reset_response = service.Reset(reset_request, FakeContext())

    assert reset_response.frame.sim_time_ns == 0
    assert simulator.reset_request.output_dir.as_posix() == "run-1"
    assert simulator.reset_request.params == {"speed": "10"}

    step_request = sim_server_pb2.SimServerMessages.StepRequest(timestamp_ns=123)
    step_response = service.Step(step_request, FakeContext())

    assert step_response.frame.sim_time_ns == 123
    assert simulator.step_request.timestamp_ns == 123


def test_generic_service_accepts_legacy_scenario_format_parameter() -> None:
    simulator = FakeSimulator()
    service = GenericSimulatorService(
        simulator,
        name="Fake",
        scenario_format="open_scenario1",
    )

    context = FakeContext()
    service.Init(make_init_request("open_scenario1"), context)

    assert context.code is None
    assert simulator.init_request.scenario.format == "open_scenario1"


def test_generic_service_accepts_multiple_scenario_formats() -> None:
    simulator = FakeSimulator()
    service = GenericSimulatorService(
        simulator,
        name="Fake",
        scenario_formats={"open_scenario1", "open_scenario2"},
    )

    context = FakeContext()
    service.Init(make_init_request("open_scenario2"), context)

    assert context.code is None
    assert simulator.init_request.scenario.format == "open_scenario2"


def test_generic_service_rejects_unsupported_scenario_format_with_supported_list() -> None:
    simulator = FakeSimulator()
    service = GenericSimulatorService(
        simulator,
        name="Fake",
        scenario_formats={"open_scenario2", "open_scenario1"},
    )

    context = FakeContext()
    service.Init(make_init_request("foo"), context)

    # Unsupported scenario format now surfaces as INVALID_ARGUMENT instead
    # of the old InitResponse(success=False) protocol-level signal.
    assert context.code == grpc.StatusCode.INVALID_ARGUMENT
    assert "Unsupported scenario format: foo" in context.details
    assert "Supported formats: open_scenario1, open_scenario2" in context.details
    assert simulator.init_request is None


def test_generic_service_rejects_ambiguous_scenario_format_arguments() -> None:
    try:
        GenericSimulatorService(
            FakeSimulator(),
            name="Fake",
            scenario_format="open_scenario1",
            scenario_formats={"open_scenario2"},
        )
    except ValueError as exc:
        assert "scenario_format" in str(exc)
        assert "scenario_formats" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_generic_service_skips_format_validation_when_no_formats_are_configured() -> None:
    simulator = FakeSimulator()
    service = GenericSimulatorService(simulator, name="Fake")

    context = FakeContext()
    service.Init(make_init_request("custom_format"), context)

    assert context.code is None
    assert simulator.init_request.scenario.format == "custom_format"


def test_generic_service_rejects_step_before_reset() -> None:
    simulator = FakeSimulator()
    service = GenericSimulatorService(simulator, name="Fake")

    init_context = FakeContext()
    service.Init(sim_server_pb2.SimServerMessages.InitRequest(), init_context)
    assert init_context.code is None

    context = FakeContext()
    response = service.Step(sim_server_pb2.SimServerMessages.StepRequest(), context)

    assert response == sim_server_pb2.SimServerMessages.StepResponse()
    assert context.code == grpc.StatusCode.FAILED_PRECONDITION
    assert "Reset" in context.details


def test_serve_simulator_wraps_existing_serve_sim(monkeypatch) -> None:
    import pisa_api.simulator.service as service_module

    calls = {}

    def fake_serve_sim(servicer, *, port, max_workers, name):
        calls["servicer"] = servicer
        calls["port"] = port
        calls["max_workers"] = max_workers
        calls["name"] = name

    monkeypatch.setattr(service_module, "serve_sim", fake_serve_sim)

    service_module.serve_simulator(
        FakeSimulator(),
        name="Fake",
        scenario_formats={"open_scenario1", "open_scenario2"},
        port=1234,
        max_workers=2,
    )

    assert isinstance(calls["servicer"], GenericSimulatorService)
    assert calls["servicer"]._scenario_formats == frozenset({"open_scenario1", "open_scenario2"})
    assert calls["port"] == 1234
    assert calls["max_workers"] == 2
    assert calls["name"] == "Fake"
