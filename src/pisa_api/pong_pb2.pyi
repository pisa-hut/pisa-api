from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Pong(_message.Message):
    __slots__ = ("msg", "name", "version")
    MSG_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    msg: str
    name: str
    version: str
    def __init__(self, msg: _Optional[str] = ..., name: _Optional[str] = ..., version: _Optional[str] = ...) -> None: ...
