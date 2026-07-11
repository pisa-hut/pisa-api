from . import config_pb2 as _config_pb2
from . import control_pb2 as _control_pb2
from . import empty_pb2 as _empty_pb2
from . import initialization_pb2 as _initialization_pb2
from . import path_pb2 as _path_pb2
from . import pong_pb2 as _pong_pb2
from . import scenario_pb2 as _scenario_pb2
from . import runtime_frame_pb2 as _runtime_frame_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SimServerMessages(_message.Message):
    __slots__ = ()
    class InitRequest(_message.Message):
        __slots__ = ("config", "output_dir", "dt", "scenario")
        CONFIG_FIELD_NUMBER: _ClassVar[int]
        OUTPUT_DIR_FIELD_NUMBER: _ClassVar[int]
        DT_FIELD_NUMBER: _ClassVar[int]
        SCENARIO_FIELD_NUMBER: _ClassVar[int]
        config: _config_pb2.Config
        output_dir: _path_pb2.Path
        dt: float
        scenario: _scenario_pb2.Scenario
        def __init__(self, config: _Optional[_Union[_config_pb2.Config, _Mapping]] = ..., output_dir: _Optional[_Union[_path_pb2.Path, _Mapping]] = ..., dt: _Optional[float] = ..., scenario: _Optional[_Union[_scenario_pb2.Scenario, _Mapping]] = ...) -> None: ...
    class ResetRequest(_message.Message):
        __slots__ = ("output_dir", "scenario_pack", "params")
        class ParamsEntry(_message.Message):
            __slots__ = ("key", "value")
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: str
            def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
        OUTPUT_DIR_FIELD_NUMBER: _ClassVar[int]
        SCENARIO_PACK_FIELD_NUMBER: _ClassVar[int]
        PARAMS_FIELD_NUMBER: _ClassVar[int]
        output_dir: _path_pb2.Path
        scenario_pack: _scenario_pb2.ScenarioPack
        params: _containers.ScalarMap[str, str]
        def __init__(self, output_dir: _Optional[_Union[_path_pb2.Path, _Mapping]] = ..., scenario_pack: _Optional[_Union[_scenario_pb2.ScenarioPack, _Mapping]] = ..., params: _Optional[_Mapping[str, str]] = ...) -> None: ...
    class ResetResponse(_message.Message):
        __slots__ = ("frame",)
        FRAME_FIELD_NUMBER: _ClassVar[int]
        frame: _runtime_frame_pb2.RuntimeFrame
        def __init__(self, frame: _Optional[_Union[_runtime_frame_pb2.RuntimeFrame, _Mapping]] = ...) -> None: ...
    class StepRequest(_message.Message):
        __slots__ = ("ctrl_cmd", "timestamp_ns")
        CTRL_CMD_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
        ctrl_cmd: _control_pb2.CtrlCmd
        timestamp_ns: int
        def __init__(self, ctrl_cmd: _Optional[_Union[_control_pb2.CtrlCmd, _Mapping]] = ..., timestamp_ns: _Optional[int] = ...) -> None: ...
    class StepResponse(_message.Message):
        __slots__ = ("frame",)
        FRAME_FIELD_NUMBER: _ClassVar[int]
        frame: _runtime_frame_pb2.RuntimeFrame
        def __init__(self, frame: _Optional[_Union[_runtime_frame_pb2.RuntimeFrame, _Mapping]] = ...) -> None: ...
    class ShouldQuitResponse(_message.Message):
        __slots__ = ("should_quit", "msg")
        SHOULD_QUIT_FIELD_NUMBER: _ClassVar[int]
        MSG_FIELD_NUMBER: _ClassVar[int]
        should_quit: bool
        msg: str
        def __init__(self, should_quit: bool = ..., msg: _Optional[str] = ...) -> None: ...
    def __init__(self) -> None: ...
