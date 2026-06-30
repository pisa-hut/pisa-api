from . import position_pb2 as _position_pb2
from . import path_pb2 as _path_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ScenarioPack(_message.Message):
    __slots__ = ("name", "map_name", "scenarios", "param_range_file", "ego", "timeout_ns")
    class ScenariosEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _path_pb2.Path
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_path_pb2.Path, _Mapping]] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    MAP_NAME_FIELD_NUMBER: _ClassVar[int]
    SCENARIOS_FIELD_NUMBER: _ClassVar[int]
    PARAM_RANGE_FILE_FIELD_NUMBER: _ClassVar[int]
    EGO_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_NS_FIELD_NUMBER: _ClassVar[int]
    name: str
    map_name: str
    scenarios: _containers.MessageMap[str, _path_pb2.Path]
    param_range_file: _path_pb2.Path
    ego: EgoConfig
    timeout_ns: int
    def __init__(self, name: _Optional[str] = ..., map_name: _Optional[str] = ..., scenarios: _Optional[_Mapping[str, _path_pb2.Path]] = ..., param_range_file: _Optional[_Union[_path_pb2.Path, _Mapping]] = ..., ego: _Optional[_Union[EgoConfig, _Mapping]] = ..., timeout_ns: _Optional[int] = ...) -> None: ...

class Scenario(_message.Message):
    __slots__ = ("format", "name", "path")
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    format: str
    name: str
    path: _path_pb2.Path
    def __init__(self, format: _Optional[str] = ..., name: _Optional[str] = ..., path: _Optional[_Union[_path_pb2.Path, _Mapping]] = ...) -> None: ...

class EgoConfig(_message.Message):
    __slots__ = ("target_speed", "spawn_config", "goal_config")
    TARGET_SPEED_FIELD_NUMBER: _ClassVar[int]
    SPAWN_CONFIG_FIELD_NUMBER: _ClassVar[int]
    GOAL_CONFIG_FIELD_NUMBER: _ClassVar[int]
    target_speed: float
    spawn_config: SpawnConfig
    goal_config: GoalConfig
    def __init__(self, target_speed: _Optional[float] = ..., spawn_config: _Optional[_Union[SpawnConfig, _Mapping]] = ..., goal_config: _Optional[_Union[GoalConfig, _Mapping]] = ...) -> None: ...

class SpawnConfig(_message.Message):
    __slots__ = ("position", "speed")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    position: _position_pb2.Position
    speed: float
    def __init__(self, position: _Optional[_Union[_position_pb2.Position, _Mapping]] = ..., speed: _Optional[float] = ...) -> None: ...

class GoalConfig(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: _position_pb2.Position
    def __init__(self, position: _Optional[_Union[_position_pb2.Position, _Mapping]] = ...) -> None: ...
