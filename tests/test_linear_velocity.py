from pisa_api import object_pb2
from pisa_api.av import (
    ObjectKinematicData,
    ObjectStateData,
    ObservationData,
    ObservedAgentData,
    RoadObjectType,
    Vector3Data,
    object_kinematic_from_proto,
    object_kinematic_to_proto,
    observation_from_proto,
    observation_to_proto,
)
from pisa_api.simulator import Vector3Data as SimulatorVector3Data


def test_scalar_only_object_kinematic_round_trip_keeps_linear_velocity_absent() -> None:
    data = ObjectKinematicData(speed=-4.5)

    proto = object_kinematic_to_proto(data)
    decoded = object_kinematic_from_proto(proto)

    assert not proto.HasField("linear_velocity")
    assert decoded.linear_velocity is None
    assert decoded == data


def test_nonzero_linear_velocity_round_trip_preserves_all_components() -> None:
    data = ObjectKinematicData(
        speed=8.4,
        linear_velocity=Vector3Data(x=8.4, y=-0.2, z=-1.96),
    )

    proto = object_kinematic_to_proto(data)
    decoded = object_kinematic_from_proto(proto)

    assert proto.HasField("linear_velocity")
    assert (proto.linear_velocity.x, proto.linear_velocity.y, proto.linear_velocity.z) == (
        8.4,
        -0.2,
        -1.96,
    )
    assert decoded == data


def test_explicit_zero_linear_velocity_is_present_after_round_trip() -> None:
    data = ObjectKinematicData(linear_velocity=Vector3Data())

    proto = object_kinematic_to_proto(data)
    decoded = object_kinematic_from_proto(proto)

    assert proto.HasField("linear_velocity")
    assert decoded.linear_velocity == Vector3Data(x=0.0, y=0.0, z=0.0)
    assert decoded.linear_velocity is not None


def test_observation_nested_round_trip_preserves_ego_and_agent_velocity_vectors() -> None:
    observation = ObservationData(
        ego=ObjectStateData(
            type=RoadObjectType.CAR,
            kinematic=ObjectKinematicData(
                time_ns=100,
                speed=8.4,
                linear_velocity=Vector3Data(x=8.4, y=-0.2, z=-1.96),
            ),
        ),
        agents=[
            ObservedAgentData(
                state=ObjectStateData(
                    type=RoadObjectType.CAR,
                    kinematic=ObjectKinematicData(
                        time_ns=100,
                        speed=-1.0,
                        linear_velocity=Vector3Data(x=-1.0, y=0.3, z=0.0),
                    ),
                )
            )
        ],
    )

    proto = observation_to_proto(observation)
    decoded = observation_from_proto(proto)

    assert proto.ego.kinematic.HasField("linear_velocity")
    assert proto.agents[0].state.kinematic.HasField("linear_velocity")
    assert decoded == observation


def test_generated_linear_velocity_descriptor_and_public_reexports() -> None:
    field = object_pb2.ObjectKinematic.DESCRIPTOR.fields_by_name["linear_velocity"]

    assert field.number == 10
    assert field.message_type.full_name == "pisa_api.Vector3"
    assert object_pb2.Vector3.DESCRIPTOR.full_name == "pisa_api.Vector3"
    assert SimulatorVector3Data is Vector3Data
