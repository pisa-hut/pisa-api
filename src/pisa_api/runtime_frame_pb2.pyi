from . import object_pb2 as _object_pb2
from . import collision_pb2 as _collision_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SimulatorObject(_message.Message):
    __slots__ = ("state", "entity_name")
    STATE_FIELD_NUMBER: _ClassVar[int]
    ENTITY_NAME_FIELD_NUMBER: _ClassVar[int]
    state: _object_pb2.ObjectState
    entity_name: str
    def __init__(self, state: _Optional[_Union[_object_pb2.ObjectState, _Mapping]] = ..., entity_name: _Optional[str] = ...) -> None: ...

class SimulatorEgo(_message.Message):
    __slots__ = ("tracking_id", "object")
    TRACKING_ID_FIELD_NUMBER: _ClassVar[int]
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    tracking_id: int
    object: SimulatorObject
    def __init__(self, tracking_id: _Optional[int] = ..., object: _Optional[_Union[SimulatorObject, _Mapping]] = ...) -> None: ...

class RuntimeFrame(_message.Message):
    __slots__ = ("sim_time_ns", "collision", "extras", "ego", "agents")
    class AgentsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: SimulatorObject
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[SimulatorObject, _Mapping]] = ...) -> None: ...
    SIM_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    COLLISION_FIELD_NUMBER: _ClassVar[int]
    EXTRAS_FIELD_NUMBER: _ClassVar[int]
    EGO_FIELD_NUMBER: _ClassVar[int]
    AGENTS_FIELD_NUMBER: _ClassVar[int]
    sim_time_ns: int
    collision: _containers.RepeatedCompositeFieldContainer[_collision_pb2.CollisionInfo]
    extras: _struct_pb2.Struct
    ego: SimulatorEgo
    agents: _containers.MessageMap[int, SimulatorObject]
    def __init__(self, sim_time_ns: _Optional[int] = ..., collision: _Optional[_Iterable[_Union[_collision_pb2.CollisionInfo, _Mapping]]] = ..., extras: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., ego: _Optional[_Union[SimulatorEgo, _Mapping]] = ..., agents: _Optional[_Mapping[int, SimulatorObject]] = ...) -> None: ...
