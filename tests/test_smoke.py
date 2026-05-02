"""Phase-2 smoke tests for the gRPC contract package.

Catches the cheap kinds of breakage that happen on every protoc
regeneration: missing module, broken import chain, renamed symbols
that downstream wrappers depend on.
"""


def test_package_imports() -> None:
    import pisa_api  # noqa: F401


def test_core_pb2_modules_import() -> None:
    """Each downstream wrapper expects these modules. Renaming or
    accidentally removing any of them silently breaks four repos."""
    from pisa_api import (  # noqa: F401
        av_server_pb2,
        av_server_pb2_grpc,
        config_pb2,
        control_pb2,
        empty_pb2,
        object_pb2,
        path_pb2,
        pong_pb2,
        position_pb2,
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
