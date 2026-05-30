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
                self._av_system.init(init_request)
            except InvalidAvRequest as exc:
                self._initialized = False
                self._reset_done = False
                return self._invalid_argument(
                    context, f"Failed to initialize {self._name}: {exc}", Empty()
                )
            except AvPreconditionFailed as exc:
                self._initialized = False
                self._reset_done = False
                return self._failed_precondition(
                    context, f"Failed to initialize {self._name}: {exc}", Empty()
                )
            except AvUnavailable as exc:
                self._initialized = False
                self._reset_done = False
                return self._unavailable(
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
                    "AV system not initialized. Call Init first.",
                    av_server_pb2.AvServerMessages.ResetResponse(),
                )

            reset_request = reset_request_from_proto(request)
            try:
                response = self._av_system.reset(reset_request)
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
                # Symmetric with Step(): a bare RuntimeError from the
                # wrapper is treated as a per-concrete precondition
                # failure rather than INTERNAL, so simcore can skip and
                # try the next sample instead of failing the run.
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

            if not isinstance(response, ResetResponse):
                # Wrapper contract bug — surfaces as INTERNAL so the
                # client knows it's not their fault. Includes the
                # offending type to make the wrapper test easy.
                return self._internal_error(
                    context,
                    (
                        f"{self._name}.reset() must return ResetResponse, "
                        f"got {type(response).__name__}"
                    ),
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
                response = self._av_system.step(step_request)
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

            if not isinstance(response, StepResponse):
                return self._internal_error(
                    context,
                    (
                        f"{self._name}.step() must return StepResponse, "
                        f"got {type(response).__name__}"
                    ),
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
        # Stop / Close were previously a flat `except Exception → INTERNAL`,
        # which lost the three-way error semantics the rest of the
        # handlers preserve. Dispatch by exception type so the client can
        # tell a transient teardown failure (UNAVAILABLE) from a wrapper
        # bug (INTERNAL). The `finally` keeps the invariant that a
        # half-failed teardown still resets `_initialized` so the next
        # Init can proceed.
        try:
            self._av_system.stop()
        except AvUnavailable as exc:
            logger.error("Failed to stop %s: %s", self._name, exc)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(f"Failed to stop {self._name}: {exc}")
        except AvPreconditionFailed as exc:
            logger.error("Failed to stop %s: %s", self._name, exc)
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details(f"Failed to stop {self._name}: {exc}")
        except Exception as exc:
            # Includes InvalidAvRequest: stop() takes no request payload,
            # so a wrapper raising that here is a bug — surface as
            # INTERNAL alongside any other unexpected exception.
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
