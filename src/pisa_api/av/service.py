"""Generic AvServer implementation for dataclass-based AV systems."""

from __future__ import annotations

import logging
import threading
from typing import Any, Protocol

import grpc

from pisa_api import av_server_pb2
from pisa_api.empty_pb2 import Empty
from pisa_api.wrapper import BaseAvServer, serve_av

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


class AvSystem(Protocol):
    """Contract a wrapper must satisfy.

    Reset and Step MUST return the matching response dataclass — no
    `None`, no bare `ControlCommand` shortcut. Anything else surfaces
    as gRPC INTERNAL since it's a wrapper-side contract bug, not a
    runtime failure the client can recover from.
    """

    def init(self, request: InitRequest) -> None: ...

    def reset(self, request: ResetRequest) -> ResetResponse: ...

    def step(self, request: StepRequest) -> StepResponse: ...

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

    # Single source of truth for "wrapper exception → gRPC status code".
    # Adding a new AvError subclass is a one-line edit here, not a fan-out
    # across every handler's try/except chain.
    _AV_ERROR_TO_STATUS: dict[type[AvError], grpc.StatusCode] = {
        InvalidAvRequest: grpc.StatusCode.INVALID_ARGUMENT,
        AvPreconditionFailed: grpc.StatusCode.FAILED_PRECONDITION,
        AvUnavailable: grpc.StatusCode.UNAVAILABLE,
    }

    def __init__(self, av_system: AvSystem, *, name: str) -> None:
        self._name = name
        self._av_system = av_system
        self._lock = threading.RLock()
        self._initialized = False
        self._reset_done = False

    def Init(self, request, context):  # noqa: N802
        logger.debug("Received Init request from client: %s", _peer(context))
        with self._lock:
            # Pessimistic state reset up-front: any failure path below
            # returns leaving `_initialized = False`. Only the happy path
            # at the bottom flips it back to True.
            self._initialized = False
            self._reset_done = False
            init_request = init_request_from_proto(request)
            try:
                self._av_system.init(init_request)
            except Exception as exc:
                return self._dispatch_exception(
                    context, "initialize", exc, Empty()
                )

            self._initialized = True
            return Empty()

    def Reset(self, request, context):  # noqa: N802
        logger.debug("Received Reset request from client: %s", _peer(context))
        with self._lock:
            if not self._initialized:
                return self._status(
                    context,
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "AV system not initialized. Call Init first.",
                    av_server_pb2.AvServerMessages.ResetResponse(),
                )

            reset_request = reset_request_from_proto(request)
            empty_response = av_server_pb2.AvServerMessages.ResetResponse()
            try:
                response = self._av_system.reset(reset_request)
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
            empty_response = av_server_pb2.AvServerMessages.StepResponse()
            if not self._initialized:
                return self._status(
                    context,
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "AV system not initialized. Call Init first.",
                    empty_response,
                )
            if not self._reset_done:
                return self._status(
                    context,
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "AV system not reset. Call Reset before Step.",
                    empty_response,
                )

            step_request = step_request_from_proto(request)
            try:
                response = self._av_system.step(step_request)
            except Exception as exc:
                return self._dispatch_exception(context, "step", exc, empty_response)

            if not isinstance(response, StepResponse):
                return self._wrong_response_type(
                    context, "step", "StepResponse", response, empty_response
                )
            return step_response_to_proto(response)

    def ShouldQuit(self, request, context):  # noqa: N802
        logger.debug("Received ShouldQuit request from client: %s", _peer(context))
        with self._lock:
            if not self._initialized:
                return av_server_pb2.AvServerMessages.ShouldQuitResponse(should_quit=False)

            return av_server_pb2.AvServerMessages.ShouldQuitResponse(
                should_quit=self._av_system.should_quit()
            )

    # --- Status-code helpers ---
    #
    # `_status` is the primitive: set code + details, return response.
    # `_dispatch_exception` maps a raised exception to one of those
    # codes via the dispatch table; everything not in the table falls
    # back to INTERNAL.
    # `_wrong_response_type` is the contract-violation path used when
    # the wrapper returns something other than the expected dataclass.

    @staticmethod
    def _status(context, code: grpc.StatusCode, details: str, response):
        logger.error(details)
        context.set_code(code)
        context.set_details(details)
        return response

    def _dispatch_exception(self, context, action: str, exc: BaseException, response):
        details = f"Failed to {action} {self._name}: {exc}"
        for cls, code in self._AV_ERROR_TO_STATUS.items():
            if isinstance(exc, cls):
                return self._status(context, code, details, response)
        # Untyped wrapper bug — keep the full traceback in the log.
        logger.exception("Failed to %s %s", action, self._name)
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details(details)
        return response

    def _wrong_response_type(
        self, context, action: str, expected: str, actual: object, response
    ):
        return self._status(
            context,
            grpc.StatusCode.INTERNAL,
            f"{self._name}.{action}() must return {expected}, got {type(actual).__name__}",
            response,
        )


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
