from google.protobuf.descriptor import FieldDescriptor

from pisa_api import object_pb2
from pisa_api.av import (
    ObjectKinematicData,
    ObjectStateData,
    ObservationData,
    ObservedAgentData,
    RoadObjectType,
    object_kinematic_from_proto,
    object_kinematic_to_proto,
    observation_from_proto,
    observation_to_proto,
)
from pisa_api.simulator import (
    RuntimeFrameData,
    SimulatorEgoData,
    SimulatorObjectData,
    runtime_frame_from_proto,
    runtime_frame_to_proto,
)


def test_legacy_object_kinematic_round_trip_keeps_steering_absent() -> None:
    data = ObjectKinematicData()

    proto = object_kinematic_to_proto(data)
    decoded = object_kinematic_from_proto(proto)

    assert not proto.HasField("steering_tire_angle")
    assert decoded.steering_tire_angle is None
    assert decoded == data


def test_nonzero_steering_round_trip_preserves_presence_and_value() -> None:
    data = ObjectKinematicData(steering_tire_angle=0.25)

    proto = object_kinematic_to_proto(data)
    decoded = object_kinematic_from_proto(proto)

    assert proto.HasField("steering_tire_angle")
    assert proto.steering_tire_angle == 0.25
    assert decoded == data


def test_explicit_zero_steering_round_trip_preserves_presence() -> None:
    data = ObjectKinematicData(steering_tire_angle=0.0)

    proto = object_kinematic_to_proto(data)
    decoded = object_kinematic_from_proto(proto)

    assert proto.HasField("steering_tire_angle")
    assert decoded.steering_tire_angle == 0.0
    assert decoded.steering_tire_angle is not None


def test_observation_round_trip_preserves_ego_steering_and_agent_absence() -> None:
    observation = ObservationData(
        ego=ObjectStateData(
            type=RoadObjectType.CAR,
            kinematic=ObjectKinematicData(
                time_ns=100,
                steering_tire_angle=-0.15,
            ),
        ),
        agents=[
            ObservedAgentData(
                state=ObjectStateData(
                    type=RoadObjectType.CAR,
                    kinematic=ObjectKinematicData(time_ns=100),
                )
            )
        ],
    )

    proto = observation_to_proto(observation)
    decoded = observation_from_proto(proto)

    assert proto.ego.kinematic.HasField("steering_tire_angle")
    assert proto.ego.kinematic.steering_tire_angle == -0.15
    assert not proto.agents[0].state.kinematic.HasField("steering_tire_angle")
    assert decoded == observation
    assert decoded.agents[0].state.kinematic.steering_tire_angle is None


def test_runtime_frame_round_trip_preserves_ego_steering_feedback() -> None:
    frame = RuntimeFrameData(
        sim_time_ns=100,
        ego=SimulatorEgoData(
            tracking_id=1,
            object=SimulatorObjectData(
                state=ObjectStateData(
                    type=RoadObjectType.CAR,
                    kinematic=ObjectKinematicData(
                        time_ns=100,
                        steering_tire_angle=0.2,
                    ),
                )
            ),
        ),
    )

    proto = runtime_frame_to_proto(frame)
    decoded = runtime_frame_from_proto(proto)

    proto_kinematic = proto.ego.object.state.kinematic
    assert proto_kinematic.HasField("steering_tire_angle")
    assert proto_kinematic.steering_tire_angle == 0.2
    assert decoded == frame


def test_generated_steering_descriptor_and_existing_field_numbers() -> None:
    fields = object_pb2.ObjectKinematic.DESCRIPTOR.fields_by_name
    steering = fields["steering_tire_angle"]

    assert steering.number == 11
    assert steering.type == FieldDescriptor.TYPE_DOUBLE
    assert steering.has_presence
    assert fields["speed"].number == 6
    assert fields["linear_velocity"].number == 10
