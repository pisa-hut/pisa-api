# pisa-api

Shared gRPC contract between the PISA simulation orchestrator and the AV / simulator wrappers. Ships the Protocol Buffer definitions, generated Python stubs, dataclass wrappers around those stubs, and a generic gRPC server (`GenericAvService` / `GenericSimulatorService`) that wrappers subclass-by-composition.

## Install

Not published to PyPI — install directly from GitHub. With `uv`:

```bash
uv add --git https://github.com/pisa-hut/pisa-api.git pisa-api
```

Or pin in `pyproject.toml` the way every downstream consumer already does:

```toml
[project]
dependencies = [
    "pisa-api>=0.2.0",
]

[tool.uv.sources]
pisa-api = { git = "https://github.com/pisa-hut/pisa-api.git" }
```

Add `rev = "<sha>"` / `tag = "..."` / `branch = "..."` to pin a specific revision. Without it `uv` resolves to the current `main` tip and writes the resolved sha into `uv.lock`.

With plain `pip`:

```bash
pip install "pisa-api @ git+https://github.com/pisa-hut/pisa-api.git"
```

## Two shapes that matter

- **`pisa_api.av`** — `AvServer` contract: `Init`, `Reset`, `Step`, `ShouldQuit` (`Stop` / `Close` are declared in the proto but the generic server intentionally returns `UNIMPLEMENTED`; teardown happens via container lifecycle).
- **`pisa_api.simulator`** — `SimServer` contract with the same four methods.

Both expose:
- A `Protocol` (`AvSystem` / `Simulator`) describing the four methods a wrapper must implement.
- A `GenericAvService` / `GenericSimulatorService` that adapts the proto layer onto that Protocol.
- A `serve_av_system()` / `serve_simulator()` convenience entry point.

## Implementing a wrapper

```python
from pisa_api.av import (
    AvPreconditionFailed,
    AvTimeout,
    AvUnavailable,
    InvalidAvRequest,
    ResetRequest, ResetResponse,
    StepRequest, StepResponse,
    serve_av_system,
)
from pisa_api.types import ControlCommand, ControlMode


class MyAv:
    def init(self, request) -> None:
        # Raise InvalidAvRequest / AvUnavailable / AvTimeout on failure.
        # Returning None on success is the contract.
        ...

    def reset(self, request: ResetRequest) -> ResetResponse:
        cmd = ControlCommand(mode=ControlMode.ACKERMANN, payload={"speed": 0.0})
        return ResetResponse(ctrl_cmd=cmd)

    def step(self, request: StepRequest) -> StepResponse:
        cmd = ControlCommand(mode=ControlMode.ACKERMANN, payload={"speed": 5.0})
        return StepResponse(ctrl_cmd=cmd)

    def should_quit(self) -> bool:
        return False


if __name__ == "__main__":
    serve_av_system(MyAv(), name="my-av", port=50051)
```

The simulator side is symmetric (`Simulator` / `serve_simulator` / `StepResponse(frame=...)` etc.).

## Wrapper exception → gRPC status

Failure is signalled exclusively via raised exceptions; the generic server translates them to gRPC status codes through a single dispatch table per server type. The four typed errors mirror across AV and Sim:

| Exception                                | gRPC status           | Semantic                                       |
|------------------------------------------|-----------------------|------------------------------------------------|
| `Invalid{Av,Simulator}Request`           | `INVALID_ARGUMENT`    | Logical request invalid — don't retry          |
| `{Av,Simulator}PreconditionFailed`       | `FAILED_PRECONDITION` | Concrete unrunnable — skip and try next sample |
| `{Av,Simulator}Unavailable`              | `UNAVAILABLE`         | Transient — retry                              |
| `{Av,Simulator}Timeout`                  | `DEADLINE_EXCEEDED`   | Service is up but missed the deadline          |
| anything else (incl. bare `RuntimeError`) | `INTERNAL`            | Wrapper bug — investigate, don't paper over    |

Adding a fifth error kind is a one-line edit in `_AV_ERROR_TO_STATUS` / `_SIMULATOR_ERROR_TO_STATUS` inside the generic service.

## Wrapper return contract

`reset()` must return `ResetResponse`; `step()` must return `StepResponse`; `init()` must return `None`. Anything else (including `None` from `reset()` / `step()`, or a bare `ControlCommand` / `RuntimeFrameData`) surfaces as gRPC `INTERNAL` with a `must return X, got Y` detail. The previous "wrap a bare type for you" convenience is gone — wrappers wrap explicitly.

## Layout

```
proto/                  # .proto definitions
src/pisa_api/
  __init__.py
  *_pb2.py, *_pb2_grpc.py   # generated; not maintained by hand
  av/                       # AvSystem Protocol, dataclasses, conversions, GenericAvService
  simulator/                # mirror for Simulator
  types.py, conversions.py  # shared payload types (ControlCommand, ObjectState, …)
  wrapper/                  # BaseAvServer / BaseSimServer + serve helpers
tests/                  # pytest
justfile                # `just proto` regenerates pb2 + pb2_grpc
```

## Development

```bash
uv sync                              # install dev deps
uv run pytest                        # full test suite
uv run pytest tests/test_av_api.py -q::test_reset_av_timeout_returns_deadline_exceeded
uv run ruff check                    # lint (generated pb2 stubs are excluded)
uv run ruff format                   # format
just proto                           # regenerate Python stubs after editing .proto files
```

When a `.proto` changes, **regenerate the stubs in the same commit** as the proto edit; downstream consumers diff on the generated `*_pb2.py` so a bare proto change is invisible to them.

## Breaking-change history

Recent revisions are deliberately incompatible with older wrappers:

- **InitResponse removed.** `Init` returns `Empty`; success/failure is gRPC status only. Old `return InitResponse(success=False, msg=...)` → must `raise` a typed exception instead.
- **Bare return types rejected.** `return cmd` from `reset()` / `step()` → must be `return ResetResponse(ctrl_cmd=cmd)` / `return StepResponse(...)`.
- **`SimulatorNotReady` renamed** to `SimulatorPreconditionFailed` for AV/Sim parity.
- **`RuntimeError` no longer free-passes.** Used to bundle with `*PreconditionFailed` → `FAILED_PRECONDITION`; now goes to `INTERNAL`. Wrappers must raise the typed exception explicitly.
- **`Stop` / `Close` not implemented.** Generic servers return `UNIMPLEMENTED`; teardown is the container's responsibility.

Any wrapper or client (`simcore`, `runner/`, the four AV/Sim wrappers under `wrappers/`) needs updating before it can pull a new `pisa-api` revision.
