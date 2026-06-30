from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ActorRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ACTOR_ROLE_UNSPECIFIED: _ClassVar[ActorRole]
    EGO: _ClassVar[ActorRole]
    AGENT: _ClassVar[ActorRole]
ACTOR_ROLE_UNSPECIFIED: ActorRole
EGO: ActorRole
AGENT: ActorRole

class ActorRef(_message.Message):
    __slots__ = ("tracking_id", "entity_name", "role")
    TRACKING_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_NAME_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    tracking_id: int
    entity_name: str
    role: ActorRole
    def __init__(self, tracking_id: _Optional[int] = ..., entity_name: _Optional[str] = ..., role: _Optional[_Union[ActorRole, str]] = ...) -> None: ...

class CollisionInfo(_message.Message):
    __slots__ = ("occurred", "details", "actor_a", "actor_b")
    OCCURRED_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    ACTOR_A_FIELD_NUMBER: _ClassVar[int]
    ACTOR_B_FIELD_NUMBER: _ClassVar[int]
    occurred: bool
    details: _struct_pb2.Struct
    actor_a: ActorRef
    actor_b: ActorRef
    def __init__(self, occurred: bool = ..., details: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., actor_a: _Optional[_Union[ActorRef, _Mapping]] = ..., actor_b: _Optional[_Union[ActorRef, _Mapping]] = ...) -> None: ...
