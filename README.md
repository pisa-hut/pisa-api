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
    "pisa-api>=0.4.2",
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

- **`pisa_api.av`** — `AvServer` contract: `Init`, `Reset`, `Step`, `Stop`, `ShouldQuit`. (`Close` is declared in the proto but the generic server intentionally returns `UNIMPLEMENTED` — see *Breaking-change history* below.)
- **`pisa_api.simulator`** — `SimServer` contract with the same four methods.

Both expose:
- A `Protocol` (`AvSystem` / `Simulator`) describing the four methods a wrapper must implement.
- A `GenericAvService` / `GenericSimulatorService` that adapts the proto layer onto that Protocol.
- A `serve_av_system()` / `serve_simulator()` convenience entry point.

## Kinematic semantics

`ObjectKinematic.speed` remains a scalar in m/s: it is the signed longitudinal
speed along the object's forward direction. It is not the Euclidean magnitude
of the object's velocity and may be negative when the object moves backward.

`ObjectKinematic.linear_velocity` is an optional authoritative 3D vector in
m/s, expressed in the canonical world coordinate frame used by `x`, `y`, and
`z`, and sampled at the same `time_ns`. It contains longitudinal, lateral, and
vertical components. An absent field means that the producer does not provide
the full vector; a present `(0, 0, 0)` value explicitly reports zero velocity.

Therefore, `norm(linear_velocity)` does not necessarily equal `abs(speed)`,
for example during vertical motion, lateral slip, vehicle pitch or grade, or
simulator-specific dynamics.

## Implementing a wrapper

```python
from pisa_api.av import (
    AvPreconditionFailed,
    AvTimeout,
    AvUnavailable,
    InvalidAvRequest,
    InitRequest, InitResponse,
    ResetRequest, ResetResponse,
    StepRequest, StepResponse,
    serve_av_system,
)
from pisa_api.types import ControlCommand, ControlMode


class MyAv:
    def init(self, request: InitRequest) -> InitResponse:
        # Raise InvalidAvRequest / AvUnavailable / AvTimeout on failure.
        # initialize...
        self._agent_name = "plant2"
        self._server_version = "0.9.15"
        return InitResponse(
            name=self._agent_name,
            metadata={
                "profile": self._agent_name,
                "runtime": {
                    "carla_version": self._server_version or "unknown",
                },
            },
        )

    def reset(self, request: ResetRequest) -> ResetResponse:
        cmd = ControlCommand(mode=ControlMode.ACKERMANN, payload={"speed": 0.0})
        return ResetResponse(ctrl_cmd=cmd)

    def step(self, request: StepRequest) -> StepResponse:
        cmd = ControlCommand(mode=ControlMode.ACKERMANN, payload={"speed": 5.0})
        return StepResponse(ctrl_cmd=cmd)

    def should_quit(self) -> bool:
        return False


if __name__ == "__main__":
    serve_av_system(
        MyAv(),
        name="pcla-wrapper",
        version="0.3.1",
        port=50051,
    )
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

`init()` must return the shared `InitResponse`; `reset()` must return `ResetResponse`; `step()` must return `StepResponse`; `should_quit()` must return `ShouldQuitResponse`; and `stop()` returns `None`. Anything else (including `None` from `init()` / `reset()` / `step()`, a bare `ControlCommand` / `RuntimeFrameData`, or a bare `bool` from `should_quit()`) surfaces as gRPC `INTERNAL` with a `must return X, got Y` detail. The previous "wrap a bare type for you" convenience is gone — wrappers wrap explicitly.

## Wrapper and component identity

Ping and Init describe two deliberately different identities:

- `Pong.name` is the stable wrapper identity explicitly passed to the serve API, for example `pcla-wrapper`.
- `Pong.version` is that wrapper package or build version, for example `0.3.1`.
- `InitResponse.name` is the component actually selected and initialized for this request, for example `plant2`, `interfuser`, `lmdrive`, or `carla`.
- `InitResponse.metadata` contains effective configuration and runtime details after initialization.

Clients must use `Pong.name` and `Pong.version` directly rather than parsing the human-readable `Pong.msg`. Both identity arguments are required, must be strings, and cannot be empty or whitespace. The API does not inspect package metadata, project files, wrapper classes, modules, or source paths to infer them.

`InitResponse.metadata` is encoded as `google.protobuf.Struct`. Keys must be strings; values are limited to null, bool, number, string, list, and object. Arbitrary Python objects are unsupported. Protobuf numbers are doubles, so wrappers should encode large integers as strings when exact preservation matters. The runner writes this metadata into the execution manifest: wrappers must never include passwords, tokens, credentials, or other secrets.

## Layout

```
proto/                  # .proto definitions
src/pisa_api/
  __init__.py
  *_pb2.py, *_pb2.pyi, *_pb2_grpc.py  # generated; not maintained by hand
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
uv run pytest tests/test_av_api.py::test_reset_av_timeout_returns_deadline_exceeded -q
uv run ruff check                    # lint (generated pb2 stubs are excluded)
uv run ruff format                   # format
just proto                           # regenerate Python stubs after editing .proto files
```

When a `.proto` changes, **regenerate the stubs in the same commit** as the proto edit; downstream consumers diff on the generated `*_pb2.py` so a bare proto change is invisible to them.

## Breaking-change history

Recent revisions are deliberately incompatible with older wrappers:

- **Observation identity is explicit.** `RuntimeFrame` carries a dedicated ego and an
  episode-local tracking-ID map of agents; AV reset/step requests carry an `Observation` with an
  explicit ego and non-identity-bearing repeated agents. Tracking IDs must not be assumed stable
  across reset, and `entity_name` can be absent for dynamically created actors.
- **InitResponse is now shared and descriptive.** AV and simulator `Init` return the same `pisa_api.types.InitResponse` / protobuf `pisa_api.InitResponse`. It identifies the initialized component and metadata; failures remain gRPC statuses and must be raised as typed exceptions. Returning `None` is now a wrapper contract error.
- **Wrapper identity is explicit.** `serve_av_system()` and `serve_simulator()` now require keyword-only `name` and `version`; Ping returns both without package or source-path inference.
- **Bare return types rejected.** `return cmd` from `reset()` / `step()` → must be `return ResetResponse(ctrl_cmd=cmd)` / `return StepResponse(...)`.
- **`SimulatorNotReady` renamed** to `SimulatorPreconditionFailed` for AV/Sim parity.
- **`RuntimeError` no longer free-passes.** Used to bundle with `*PreconditionFailed` → `FAILED_PRECONDITION`; now goes to `INTERNAL`. Wrappers must raise the typed exception explicitly.
- **`Close` not implemented.** `Close` is declared in the proto but the generic server returns `UNIMPLEMENTED` — clients shouldn't rely on it; container-lifecycle teardown is the contract. `Stop` *is* implemented (it raises through the same dispatch table as Reset/Step), so clients can release the AV / simulator between scenarios without rebuilding the wrapper container.
- **`should_quit()` returns `ShouldQuitResponse`, not `bool`.** The proto's `ShouldQuitResponse.msg` field is now exposed end-to-end, so wrappers can surface *why* they're asking to quit. `return ShouldQuitResponse(should_quit=True, msg="ego stuck")` instead of `return True`. Pre-Init the handler still short-circuits to `should_quit=False, msg=""` without calling the wrapper.

Any wrapper or client (`simcore`, `runner/`, the four AV/Sim wrappers under `wrappers/`) needs updating before it can pull a new `pisa-api` revision.
