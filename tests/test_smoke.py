"""Phase-2 smoke tests for the gRPC contract package.

Catches the cheap kinds of breakage that happen on every protoc
regeneration: missing module, broken import chain, renamed symbols
that downstream wrappers depend on.
"""

from typing import Set

from google.protobuf.descriptor_pb2 import DescriptorProto, FileDescriptorProto


def test_package_imports() -> None:
    import pisa_api  # noqa: F401


def test_core_pb2_modules_import() -> None:
    """Each downstream wrapper expects these modules. Renaming or
    accidentally removing any of them silently breaks four repos."""
    from pisa_api import (  # noqa: F401
        av_server_pb2,
        av_server_pb2_grpc,
        collision_pb2,
        config_pb2,
        control_pb2,
        empty_pb2,
        object_pb2,
        path_pb2,
        pong_pb2,
        position_pb2,
        runtime_frame_pb2,
        scenario_pb2,
        scenario_pb2_grpc,
        sim_server_pb2,
        sim_server_pb2_grpc,
    )


def test_sim_server_grpc_stub_exists() -> None:
    """Wrappers instantiate `SimServerStub`; runner instantiates the
    Servicer base class. If protoc generation skips the *_grpc stub
    these go missing entirely, so assert both are present."""
    from pisa_api import sim_server_pb2_grpc

    assert hasattr(sim_server_pb2_grpc, "SimServerStub")
    assert hasattr(sim_server_pb2_grpc, "SimServerServicer")


def _message_descriptor(file_descriptor, *path: str) -> DescriptorProto:
    descriptor = FileDescriptorProto.FromString(file_descriptor.serialized_pb)
    messages = descriptor.message_type
    message = None
    for name in path:
        message = next(candidate for candidate in messages if candidate.name == name)
        messages = message.nested_type
    assert message is not None
    return message


def _reserved_numbers(message: DescriptorProto) -> Set[int]:
    return {
        number
        for reserved_range in message.reserved_range
        for number in range(reserved_range.start, reserved_range.end)
    }


def test_generated_descriptors_reserve_obsolete_identity_fields() -> None:
    from pisa_api import av_server_pb2, collision_pb2, runtime_frame_pb2

    runtime_frame = _message_descriptor(runtime_frame_pb2.DESCRIPTOR, "RuntimeFrame")
    collision = _message_descriptor(collision_pb2.DESCRIPTOR, "CollisionInfo")
    reset_request = _message_descriptor(
        av_server_pb2.DESCRIPTOR, "AvServerMessages", "ResetRequest"
    )
    step_request = _message_descriptor(av_server_pb2.DESCRIPTOR, "AvServerMessages", "StepRequest")

    assert _reserved_numbers(runtime_frame) == {2}
    assert set(runtime_frame.reserved_name) == {"objects"}
    assert _reserved_numbers(collision) == {2, 3}
    assert _reserved_numbers(reset_request) == {3}
    assert _reserved_numbers(step_request) == {1}
