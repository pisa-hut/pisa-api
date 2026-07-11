from . import config_pb2 as _config_pb2
from . import control_pb2 as _control_pb2
from . import empty_pb2 as _empty_pb2
from . import initialization_pb2 as _initialization_pb2
from . import object_pb2 as _object_pb2
from . import pong_pb2 as _pong_pb2
from . import path_pb2 as _path_pb2
from . import scenario_pb2 as _scenario_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ObservedAgent(_message.Message):
    __slots__ = ("state", "tracking_id", "entity_name")
    STATE_FIELD_NUMBER: _ClassVar[int]
    TRACKING_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_NAME_FIELD_NUMBER: _ClassVar[int]
    state: _object_pb2.ObjectState
    tracking_id: int
    entity_name: str
    def __init__(self, state: _Optional[_Union[_object_pb2.ObjectState, _Mapping]] = ..., tracking_id: _Optional[int] = ..., entity_name: _Optional[str] = ...) -> None: ...

class Observation(_message.Message):
    __slots__ = ("ego", "agents")
    EGO_FIELD_NUMBER: _ClassVar[int]
    AGENTS_FIELD_NUMBER: _ClassVar[int]
    ego: _object_pb2.ObjectState
    agents: _containers.RepeatedCompositeFieldContainer[ObservedAgent]
    def __init__(self, ego: _Optional[_Union[_object_pb2.ObjectState, _Mapping]] = ..., agents: _Optional[_Iterable[_Union[ObservedAgent, _Mapping]]] = ...) -> None: ...

class AvServerMessages(_message.Message):
    __slots__ = ()
    class InitRequest(_message.Message):
        __slots__ = ("config", "output_dir", "map_name", "dt")
        CONFIG_FIELD_NUMBER: _ClassVar[int]
        OUTPUT_DIR_FIELD_NUMBER: _ClassVar[int]
        MAP_NAME_FIELD_NUMBER: _ClassVar[int]
        DT_FIELD_NUMBER: _ClassVar[int]
        config: _config_pb2.Config
        output_dir: _path_pb2.Path
        map_name: str
        dt: float
        def __init__(self, config: _Optional[_Union[_config_pb2.Config, _Mapping]] = ..., output_dir: _Optional[_Union[_path_pb2.Path, _Mapping]] = ..., map_name: _Optional[str] = ..., dt: _Optional[float] = ...) -> None: ...
    class ResetRequest(_message.Message):
        __slots__ = ("output_dir", "scenario_pack", "initial_observation")
        OUTPUT_DIR_FIELD_NUMBER: _ClassVar[int]
        SCENARIO_PACK_FIELD_NUMBER: _ClassVar[int]
        INITIAL_OBSERVATION_FIELD_NUMBER: _ClassVar[int]
        output_dir: _path_pb2.Path
        scenario_pack: _scenario_pb2.ScenarioPack
        initial_observation: Observation
        def __init__(self, output_dir: _Optional[_Union[_path_pb2.Path, _Mapping]] = ..., scenario_pack: _Optional[_Union[_scenario_pb2.ScenarioPack, _Mapping]] = ..., initial_observation: _Optional[_Union[Observation, _Mapping]] = ...) -> None: ...
    class ResetResponse(_message.Message):
        __slots__ = ("ctrl_cmd",)
        CTRL_CMD_FIELD_NUMBER: _ClassVar[int]
        ctrl_cmd: _control_pb2.CtrlCmd
        def __init__(self, ctrl_cmd: _Optional[_Union[_control_pb2.CtrlCmd, _Mapping]] = ...) -> None: ...
    class StepRequest(_message.Message):
        __slots__ = ("observation", "timestamp_ns")
        OBSERVATION_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
        observation: Observation
        timestamp_ns: int
        def __init__(self, observation: _Optional[_Union[Observation, _Mapping]] = ..., timestamp_ns: _Optional[int] = ...) -> None: ...
    class StepResponse(_message.Message):
        __slots__ = ("ctrl_cmd",)
        CTRL_CMD_FIELD_NUMBER: _ClassVar[int]
        ctrl_cmd: _control_pb2.CtrlCmd
        def __init__(self, ctrl_cmd: _Optional[_Union[_control_pb2.CtrlCmd, _Mapping]] = ...) -> None: ...
    class ShouldQuitResponse(_message.Message):
        __slots__ = ("should_quit", "msg")
        SHOULD_QUIT_FIELD_NUMBER: _ClassVar[int]
        MSG_FIELD_NUMBER: _ClassVar[int]
        should_quit: bool
        msg: str
        def __init__(self, should_quit: bool = ..., msg: _Optional[str] = ...) -> None: ...
    def __init__(self) -> None: ...
