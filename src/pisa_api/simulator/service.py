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
    RuntimeFrameData,
    StepRequest,
    StepResponse,
)

logger = logging.getLogger(__name__)


class Simulator(Protocol):
    def init(self, request: InitRequest) -> None: ...

    def reset(self, request: ResetRequest) -> RuntimeFrameData | ResetResponse: ...

    def step(self, request: StepRequest) -> RuntimeFrameData | StepResponse: ...

    def stop(self) -> None: ...

    def should_quit(self) -> bool: ...


class SimulatorError(Exception):
    """Base exception for expected simulator failures."""


class InvalidSimulatorRequest(SimulatorError):
    """Raised when a valid protobuf request is invalid for the simulator."""


class SimulatorNotReady(SimulatorError):
    """Raised when lifecycle ordering is invalid for the simulator."""


class GenericSimulatorService(BaseSimServer):
    """Adapter from generated gRPC service methods to dataclass simulator hooks."""

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
            init_request = init_request_from_proto(request)
            if (
                self._scenario_formats is not None
                and init_request.scenario.format not in self._scenario_formats
            ):
                supported_formats = ", ".join(sorted(self._scenario_formats))
                # Unsupported format is an INVALID_ARGUMENT — retrying the
                # same task with the same scenario format won't help.
                return self._invalid_argument(
                    context,
                    (
                        f"Unsupported scenario format: {init_request.scenario.format}. "
                        f"Supported formats: {supported_formats}"
                    ),
                    Empty(),
                )

            try:
                self._simulator.init(init_request)
            except InvalidSimulatorRequest as exc:
                self._initialized = False
                self._reset_done = False
                return self._invalid_argument(
                    context, f"Failed to initialize {self._name}: {exc}", Empty()
                )
            except SimulatorNotReady as exc:
                self._initialized = False
                self._reset_done = False
                return self._failed_precondition(
                    context, f"Failed to initialize {self._name}: {exc}", Empty()
                )
            except Exception as exc:
                logger.exception("Failed to initialize %s", self._name)
                self._initialized = False
                self._reset_done = False
                return self._internal_error(
                    context, f"Failed to initialize {self._name}: {exc}", Empty()
                )

            self._initialized = True
            self._reset_done = False
            return Empty()

    def Reset(self, request, context):  # noqa: N802
        logger.debug("Received Reset request from client: %s", _peer(context))
        with self._lock:
            if not self._initialized:
                return self._failed_precondition(
                    context,
                    "Simulator not initialized. Call Init first.",
                    sim_server_pb2.SimServerMessages.ResetResponse(),
                )

            reset_request = reset_request_from_proto(request)
            try:
                result = self._simulator.reset(reset_request)
                response = (
                    result if isinstance(result, ResetResponse) else ResetResponse(frame=result)
                )
            except (InvalidSimulatorRequest, SimulatorNotReady, RuntimeError) as exc:
                return self._failed_precondition(
                    context,
                    f"Failed to reset {self._name}: {exc}",
                    sim_server_pb2.SimServerMessages.ResetResponse(),
                )
            except Exception as exc:
                logger.exception("Failed to reset %s", self._name)
                return self._internal_error(
                    context,
                    f"Failed to reset {self._name}: {exc}",
                    sim_server_pb2.SimServerMessages.ResetResponse(),
                )

            self._reset_done = True
            return reset_response_to_proto(response)

    def Step(self, request, context):  # noqa: N802
        logger.debug("Received Step request with timestamp_ns=%s", request.timestamp_ns)
        with self._lock:
            if not self._initialized:
                return self._failed_precondition(
                    context,
                    "Simulator not initialized. Call Init first.",
                    sim_server_pb2.SimServerMessages.StepResponse(),
                )
            if not self._reset_done:
                return self._failed_precondition(
                    context,
                    "Simulator not reset. Call Reset before Step.",
                    sim_server_pb2.SimServerMessages.StepResponse(),
                )

            step_request = step_request_from_proto(request)
            try:
                result = self._simulator.step(step_request)
                response = (
                    result if isinstance(result, StepResponse) else StepResponse(frame=result)
                )
            except (InvalidSimulatorRequest, SimulatorNotReady, RuntimeError) as exc:
                return self._failed_precondition(
                    context,
                    f"Failed to step {self._name}: {exc}",
                    sim_server_pb2.SimServerMessages.StepResponse(),
                )
            except Exception as exc:
                logger.exception("Failed to step %s", self._name)
                return self._internal_error(
                    context,
                    f"Failed to step {self._name}: {exc}",
                    sim_server_pb2.SimServerMessages.StepResponse(),
                )

            return step_response_to_proto(response)

    def Stop(self, request, context):  # noqa: N802
        logger.debug("Received Stop request from client: %s", _peer(context))
        with self._lock:
            if not self._initialized:
                return self._failed_precondition(
                    context,
                    "Simulator not initialized. Call Init first.",
                    Empty(),
                )

            self._stop(context)
            return Empty()

    def Close(self, request, context):  # noqa: N802
        logger.debug("Received Close request from client: %s", _peer(context))
        with self._lock:
            if self._initialized:
                self._stop(context)
            return Empty()

    def ShouldQuit(self, request, context):  # noqa: N802
        logger.debug("Received ShouldQuit request from client: %s", _peer(context))
        with self._lock:
            if not self._initialized:
                return sim_server_pb2.SimServerMessages.ShouldQuitResponse(should_quit=False)

            return sim_server_pb2.SimServerMessages.ShouldQuitResponse(
                should_quit=self._simulator.should_quit()
            )

    def _stop(self, context: Any) -> None:
        try:
            self._simulator.stop()
        except Exception as exc:
            logger.exception("Failed to stop %s", self._name)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to stop {self._name}: {exc}")
        finally:
            self._initialized = False
            self._reset_done = False

    @staticmethod
    def _invalid_argument(context, details: str, response):
        """Used for InvalidSimulatorRequest / unsupported scenario format:
        the request is logically wrong, retrying with the same payload
        will fail the same way. Maps to gRPC INVALID_ARGUMENT."""
        logger.error(details)
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
        context.set_details(details)
        return response

    @staticmethod
    def _failed_precondition(context, details: str, response):
        logger.error(details)
        context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
        context.set_details(details)
        return response

    @staticmethod
    def _internal_error(context, details: str, response):
        logger.error(details)
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details(details)
        return response


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
    "SimulatorNotReady",
    "serve_simulator",
]
