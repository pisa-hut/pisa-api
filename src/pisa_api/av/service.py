"""Generic AvServer implementation for dataclass-based AV systems."""

from __future__ import annotations

import logging
import threading
from typing import Any, Protocol

import grpc

from pisa_api import av_server_pb2
from pisa_api.empty_pb2 import Empty
from pisa_api.types import ControlCommand
from pisa_api.wrapper import BaseAvServer, serve_av

from .conversions import (
    init_request_from_proto,
    init_response_to_proto,
    reset_request_from_proto,
    reset_response_to_proto,
    step_request_from_proto,
    step_response_to_proto,
)
from .types import (
    InitRequest,
    InitResponse,
    ResetRequest,
    ResetResponse,
    StepRequest,
    StepResponse,
)

logger = logging.getLogger(__name__)


class AvSystem(Protocol):
    def init(self, request: InitRequest) -> InitResponse | None: ...

    def reset(self, request: ResetRequest) -> ControlCommand | ResetResponse: ...

    def step(self, request: StepRequest) -> ControlCommand | StepResponse: ...

    def stop(self) -> None: ...

    def should_quit(self) -> bool: ...


class AvError(Exception):
    """Base exception for expected AV-system failures."""


class InvalidAvRequest(AvError):
    """Logical request is invalid; do not retry this logical scenario."""


class AvPreconditionFailed(AvError):
    """Concrete execution precondition failed; abandon this concrete case."""


class AvUnavailable(AvError):
    """Transient AV/runtime failure; requeue or retry."""


class GenericAvService(BaseAvServer):
    """Adapter from generated gRPC service methods to dataclass AV hooks."""

    def __init__(self, av_system: AvSystem, *, name: str) -> None:
        self._name = name
        self._av_system = av_system
        self._lock = threading.RLock()
        self._initialized = False
        self._reset_done = False

    def Init(self, request, context):  # noqa: N802
        logger.debug("Received Init request from client: %s", _peer(context))
        with self._lock:
            init_request = init_request_from_proto(request)
            try:
                result = self._av_system.init(init_request)
            except InvalidAvRequest as exc:
                logger.error("Invalid init request: %s", exc)
                return av_server_pb2.AvServerMessages.InitResponse(success=False, msg=str(exc))
            except AvUnavailable as exc:
                logger.error("AV system unavailable during init: %s", exc)
                return av_server_pb2.AvServerMessages.InitResponse(success=False, msg=str(exc))
            except Exception:
                logger.exception("Failed to initialize %s", self._name)
                return av_server_pb2.AvServerMessages.InitResponse(
                    success=False,
                    msg=f"Failed to initialize {self._name}",
                )

            response = result if isinstance(result, InitResponse) else None
            if response is not None and not response.success:
                self._initialized = False
                self._reset_done = False
                return init_response_to_proto(response)

            self._initialized = True
            self._reset_done = False
            return av_server_pb2.AvServerMessages.InitResponse(
                success=True,
                msg=(response.msg if response is not None else f"{self._name} initialized"),
            )

    def Reset(self, request, context):  # noqa: N802
        logger.debug("Received Reset request from client: %s", _peer(context))
        with self._lock:
            if not self._initialized:
                return self._failed_precondition(
                    context,
                    "AV system not initialized. Call Init first.",
                    av_server_pb2.AvServerMessages.ResetResponse(),
                )

            reset_request = reset_request_from_proto(request)
            try:
                result = self._av_system.reset(reset_request)
                response = (
                    result if isinstance(result, ResetResponse) else ResetResponse(ctrl_cmd=result)
                )
            except AvUnavailable as exc:
                return self._unavailable(
                    context,
                    f"Failed to reset {self._name}: {exc}",
                    av_server_pb2.AvServerMessages.ResetResponse(),
                )
            except InvalidAvRequest as exc:
                return self._invalid_argument(
                    context,
                    f"Failed to reset {self._name}: {exc}",
                    av_server_pb2.AvServerMessages.ResetResponse(),
                )
            except (AvPreconditionFailed, RuntimeError) as exc:
                return self._failed_precondition(
                    context,
                    f"Failed to reset {self._name}: {exc}",
                    av_server_pb2.AvServerMessages.ResetResponse(),
                )
            except Exception as exc:
                logger.exception("Failed to reset %s", self._name)
                return self._internal_error(
                    context,
                    f"Failed to reset {self._name}: {exc}",
                    av_server_pb2.AvServerMessages.ResetResponse(),
                )

            self._reset_done = True
            return reset_response_to_proto(response)

    def Step(self, request, context):  # noqa: N802
        logger.debug("Received Step request with timestamp_ns=%s", request.timestamp_ns)
        with self._lock:
            if not self._initialized:
                return self._failed_precondition(
                    context,
                    "AV system not initialized. Call Init first.",
                    av_server_pb2.AvServerMessages.StepResponse(),
                )
            if not self._reset_done:
                return self._failed_precondition(
                    context,
                    "AV system not reset. Call Reset before Step.",
                    av_server_pb2.AvServerMessages.StepResponse(),
                )

            step_request = step_request_from_proto(request)
            try:
                result = self._av_system.step(step_request)
                response = (
                    result if isinstance(result, StepResponse) else StepResponse(ctrl_cmd=result)
                )
            except AvUnavailable as exc:
                return self._unavailable(
                    context,
                    f"Failed to step {self._name}: {exc}",
                    av_server_pb2.AvServerMessages.StepResponse(),
                )
            except InvalidAvRequest as exc:
                return self._invalid_argument(
                    context,
                    f"Failed to step {self._name}: {exc}",
                    av_server_pb2.AvServerMessages.StepResponse(),
                )
            except (AvPreconditionFailed, RuntimeError) as exc:
                return self._failed_precondition(
                    context,
                    f"Failed to step {self._name}: {exc}",
                    av_server_pb2.AvServerMessages.StepResponse(),
                )
            except Exception as exc:
                logger.exception("Failed to step %s", self._name)
                return self._internal_error(
                    context,
                    f"Failed to step {self._name}: {exc}",
                    av_server_pb2.AvServerMessages.StepResponse(),
                )

            return step_response_to_proto(response)

    def Stop(self, request, context):  # noqa: N802
        logger.debug("Received Stop request from client: %s", _peer(context))
        with self._lock:
            if not self._initialized:
                return self._failed_precondition(
                    context,
                    "AV system not initialized. Call Init first.",
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
                return av_server_pb2.AvServerMessages.ShouldQuitResponse(should_quit=False)

            return av_server_pb2.AvServerMessages.ShouldQuitResponse(
                should_quit=self._av_system.should_quit()
            )

    def _stop(self, context: Any) -> None:
        try:
            self._av_system.stop()
        except Exception as exc:
            logger.exception("Failed to stop %s", self._name)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to stop {self._name}: {exc}")
        finally:
            self._initialized = False
            self._reset_done = False

    @staticmethod
    def _invalid_argument(context, details: str, response):
        """Used for InvalidAvRequest: the logical scenario itself is wrong,
        retrying the same task will fail the same way. Maps to gRPC
        INVALID_ARGUMENT so simcore can short-circuit instead of looping."""
        logger.error(details)
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
        context.set_details(details)
        return response

    @staticmethod
    def _failed_precondition(context, details: str, response):
        """Used for AvPreconditionFailed (and generic RuntimeError from the
        wrapper). This concrete is unrunnable but the logical scenario is
        fine — simcore should skip to the next sampled concrete."""
        logger.error(details)
        context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
        context.set_details(details)
        return response

    @staticmethod
    def _unavailable(context, details: str, response):
        logger.error(details)
        context.set_code(grpc.StatusCode.UNAVAILABLE)
        context.set_details(details)
        return response

    @staticmethod
    def _internal_error(context, details: str, response):
        logger.error(details)
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details(details)
        return response


def serve_av_system(
    av_system: AvSystem,
    *,
    name: str,
    port: Any | None = None,
    max_workers: int = 10,
) -> None:
    service = GenericAvService(av_system, name=name)
    serve_av(service, name=name, port=port, max_workers=max_workers)


def _peer(context: Any) -> str:
    try:
        return context.peer()
    except Exception:
        return "unknown"


__all__ = [
    "AvError",
    "AvPreconditionFailed",
    "AvSystem",
    "AvUnavailable",
    "GenericAvService",
    "InvalidAvRequest",
    "serve_av_system",
]
