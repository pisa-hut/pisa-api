from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CtrlMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[CtrlMode]
    TRAJECTORY: _ClassVar[CtrlMode]
    THROTTLE_STEER: _ClassVar[CtrlMode]
    WAYPOINTS: _ClassVar[CtrlMode]
    POSITION: _ClassVar[CtrlMode]
    ACKERMANN: _ClassVar[CtrlMode]
    THROTTLE_STEER_BREAK: _ClassVar[CtrlMode]
NONE: CtrlMode
TRAJECTORY: CtrlMode
THROTTLE_STEER: CtrlMode
WAYPOINTS: CtrlMode
POSITION: CtrlMode
ACKERMANN: CtrlMode
THROTTLE_STEER_BREAK: CtrlMode

class CtrlCmd(_message.Message):
    __slots__ = ("mode", "payload")
    MODE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    mode: CtrlMode
    payload: _struct_pb2.Struct
    def __init__(self, mode: _Optional[_Union[CtrlMode, str]] = ..., payload: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
