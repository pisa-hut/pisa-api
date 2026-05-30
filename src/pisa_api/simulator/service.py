"""Generic SimServer implementation for dataclass-based simulators."""

from __future__ import annotations

import logging
import threading
from collections.abc import Collection
from typing import Any, Protocol

import grpc

from pisa_api import sim_server_pb2
from pisa_api.empty_pb2 import Empty
from pisa_api.wrapper import BaseSimServer, serve_sim

from .conversions import (
    init_request_from_proto,
    reset_request_from_proto,
    reset_response_to_proto,
    step_request_from_proto,
    step_response_to_proto,
)
from .types import (
    InitRequest,
    ResetRequest,
    ResetResponse,
    StepRequest,
    StepResponse,
)

logger = logging.getLogger(__name__)


class Simulator(Protocol):
    # Reset and Step MUST return the matching response dataclass — no
    # `None`, no bare `RuntimeFrameData` shortcut. Anything else surfaces
    # as gRPC INTERNAL since it's a wrapper-side contract bug.

    def init(self, request: InitRequest) -> None: ...

    def reset(self, request: ResetRequest) -> ResetResponse: ...

    def step(self, request: StepRequest) -> StepResponse: ...

    def stop(self) -> None: ...

    def should_quit(self) -> bool: ...


class SimulatorError(Exception):
    """Base exception for expected simulator failures."""


class InvalidSimulatorRequest(SimulatorError):
    """Logical request is invalid; do not retry this logical scenario."""


class SimulatorPreconditionFailed(SimulatorError):
    """Concrete execution precondition failed; abandon this concrete case.
    (Includes the old `SimulatorNotReady` lifecycle-ordering meaning.)"""


class SimulatorUnavailable(SimulatorError):
    """Transient simulator/runtime failure; requeue or retry."""


class SimulatorTimeout(SimulatorError):
    """Simulator did not produce a result within the expected deadline.
    Distinct from `SimulatorUnavailable` — the simulator is up, it
    just took too long."""


class GenericSimulatorService(BaseSimServer):
    """Adapter from generated gRPC service methods to dataclass simulator hooks."""

    # Same shape as GenericAvService's table — single source of truth for
    # "wrapper exception → gRPC status code". RuntimeError is no longer
    # bundled into FAILED_PRECONDITION; wrappers that want that routing
    # must raise `SimulatorPreconditionFailed` explicitly.
    _SIMULATOR_ERROR_TO_STATUS: dict[type[SimulatorError], grpc.StatusCode] = {
        InvalidSimulatorRequest: grpc.StatusCode.INVALID_ARGUMENT,
        SimulatorPreconditionFailed: grpc.StatusCode.FAILED_PRECONDITION,
        SimulatorUnavailable: grpc.StatusCode.UNAVAILABLE,
        SimulatorTimeout: grpc.StatusCode.DEADLINE_EXCEEDED,
    }

    def __init__(
        self,
        simulator: Simulator,
        *,
        name: str,
        scenario_format: str | None = None,
        scenario_formats: Collection[str] | None = None,
    ) -> None:
        self._name = name
        self._simulator = simulator
        self._scenario_formats = _normalize_scenario_formats(
            scenario_format=scenario_format,
            scenario_formats=scenario_formats,
        )
        self._lock = threading.RLock()
        self._initialized = False
        self._reset_done = False

    def Init(self, request, context):  # noqa: N802
        logger.debug("Received Init request from client: %s", _peer(context))
        with self._lock:
            self._initialized = False
            self._reset_done = False
            init_request = init_request_from_proto(request)
            if (
                self._scenario_formats is not None
                and init_request.scenario.format not in self._scenario_formats
            ):
                supported_formats = ", ".join(sorted(self._scenario_formats))
                return self._status(
                    context,
                    grpc.StatusCode.INVALID_ARGUMENT,
                    (
                        f"Unsupported scenario format: {init_request.scenario.format}. "
                        f"Supported formats: {supported_formats}"
                    ),
                    Empty(),
                )

            try:
                self._simulator.init(init_request)
            except Exception as exc:
                return self._dispatch_exception(context, "initialize", exc, Empty())

            self._initialized = True
            return Empty()

    def Reset(self, request, context):  # noqa: N802
        logger.debug("Received Reset request from client: %s", _peer(context))
        with self._lock:
            empty_response = sim_server_pb2.SimServerMessages.ResetResponse()
            if not self._initialized:
                return self._status(
                    context,
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "Simulator not initialized. Call Init first.",
                    empty_response,
                )

            reset_request = reset_request_from_proto(request)
            try:
                response = self._simulator.reset(reset_request)
            except Exception as exc:
                return self._dispatch_exception(context, "reset", exc, empty_response)

            if not isinstance(response, ResetResponse):
                return self._wrong_response_type(
                    context, "reset", "ResetResponse", response, empty_response
                )
            self._reset_done = True
            return reset_response_to_proto(response)

    def Step(self, request, context):  # noqa: N802
        logger.debug("Received Step request with timestamp_ns=%s", request.timestamp_ns)
        with self._lock:
            empty_response = sim_server_pb2.SimServerMessages.StepResponse()
            if not self._initialized:
                return self._status(
                    context,
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "Simulator not initialized. Call Init first.",
                    empty_response,
                )
            if not self._reset_done:
                return self._status(
                    context,
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "Simulator not reset. Call Reset before Step.",
                    empty_response,
                )

            step_request = step_request_from_proto(request)
            try:
                response = self._simulator.step(step_request)
            except Exception as exc:
                return self._dispatch_exception(context, "step", exc, empty_response)

            if not isinstance(response, StepResponse):
                return self._wrong_response_type(
                    context, "step", "StepResponse", response, empty_response
                )
            return step_response_to_proto(response)

    def Stop(self, request, context):  # noqa: N802
        # `Close` is intentionally NOT implemented — see the AV-side
        # comment. Stop is exposed so clients can release the simulator
        # between scenarios without rebuilding the wrapper container.
        logger.debug("Received Stop request from client: %s", _peer(context))
        with self._lock:
            if not self._initialized:
                return self._status(
                    context,
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "Simulator not initialized. Call Init first.",
                    Empty(),
                )
            try:
                self._simulator.stop()
            except Exception as exc:
                return self._dispatch_exception(context, "stop", exc, Empty())
            finally:
                self._initialized = False
                self._reset_done = False
            return Empty()

    def ShouldQuit(self, request, context):  # noqa: N802
        logger.debug("Received ShouldQuit request from client: %s", _peer(context))
        with self._lock:
            if not self._initialized:
                return sim_server_pb2.SimServerMessages.ShouldQuitResponse(should_quit=False)

            return sim_server_pb2.SimServerMessages.ShouldQuitResponse(
                should_quit=self._simulator.should_quit()
            )

    # --- Status-code helpers ---
    # See `GenericAvService` for the dispatch-table rationale.

    @staticmethod
    def _status(context, code: grpc.StatusCode, details: str, response):
        logger.error(details)
        context.set_code(code)
        context.set_details(details)
        return response

    def _dispatch_exception(self, context, action: str, exc: BaseException, response):
        details = f"Failed to {action} {self._name}: {exc}"
        for cls, code in self._SIMULATOR_ERROR_TO_STATUS.items():
            if isinstance(exc, cls):
                return self._status(context, code, details, response)
        logger.exception("Failed to %s %s", action, self._name)
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details(details)
        return response

    def _wrong_response_type(self, context, action: str, expected: str, actual: object, response):
        return self._status(
            context,
            grpc.StatusCode.INTERNAL,
            f"{self._name}.{action}() must return {expected}, got {type(actual).__name__}",
            response,
        )


def serve_simulator(
    simulator: Simulator,
    *,
    name: str,
    scenario_format: str | None = None,
    scenario_formats: Collection[str] | None = None,
    port: Any | None = None,
    max_workers: int = 10,
) -> None:
    service = GenericSimulatorService(
        simulator,
        name=name,
        scenario_format=scenario_format,
        scenario_formats=scenario_formats,
    )
    serve_sim(service, name=name, port=port, max_workers=max_workers)


def _peer(context: Any) -> str:
    try:
        return context.peer()
    except Exception:
        return "unknown"


def _normalize_scenario_formats(
    *,
    scenario_format: str | None,
    scenario_formats: Collection[str] | None,
) -> frozenset[str] | None:
    if scenario_format is not None and scenario_formats is not None:
        raise ValueError("Pass either scenario_format or scenario_formats, not both.")
    if scenario_formats is not None:
        return frozenset(scenario_formats)
    if scenario_format is not None:
        return frozenset({scenario_format})
    return None


__all__ = [
    "GenericSimulatorService",
    "InvalidSimulatorRequest",
    "Simulator",
    "SimulatorError",
    "SimulatorPreconditionFailed",
    "SimulatorTimeout",
    "SimulatorUnavailable",
    "serve_simulator",
]
