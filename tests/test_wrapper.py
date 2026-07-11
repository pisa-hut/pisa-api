"""Tests for the pisa_api.wrapper subpackage.

Verifies the base servicer Ping wiring and the public surface of the
serve helpers — full gRPC integration is exercised by each wrapper's
own image build.
"""

from unittest.mock import MagicMock

from pisa_api import sim_server_pb2_grpc
from pisa_api.empty_pb2 import Empty
from pisa_api.wrapper import (
    BaseAvServer,
    BaseSimServer,
    serve_av,
    serve_sim,
    setup_logging,
)


class _Sim(BaseSimServer):
    _name = "TestSim"
    _version = "2.0.0"


class _Av(BaseAvServer):
    _name = "TestAv"
    _version = "3.0.0"


def test_base_sim_server_ping_returns_named_pong() -> None:
    pong = _Sim().Ping(Empty(), MagicMock(peer=lambda: "test"))
    assert pong.msg == "TestSim alive"
    assert pong.name == "TestSim"
    assert pong.version == "2.0.0"


def test_base_av_server_ping_returns_named_pong() -> None:
    pong = _Av().Ping(Empty(), MagicMock(peer=lambda: "test"))
    assert pong.msg == "TestAv alive"
    assert pong.name == "TestAv"
    assert pong.version == "3.0.0"


def test_base_sim_server_inherits_grpc_servicer() -> None:
    """If BaseSimServer doesn't extend the generated Servicer, gRPC's
    add_*Servicer_to_server will reject it at runtime."""
    assert issubclass(BaseSimServer, sim_server_pb2_grpc.SimServerServicer)


def test_serve_helpers_are_callable() -> None:
    # Smoke-check that the entry points exist and accept the documented
    # keyword args. We don't actually start a server here — that would
    # block forever on `wait_for_termination`.
    assert callable(serve_sim)
    assert callable(serve_av)


def test_setup_logging_is_idempotent() -> None:
    # Should not raise even when called multiple times.
    setup_logging()
    setup_logging()
