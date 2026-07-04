from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Position(_message.Message):
    __slots__ = ("lane", "world")
    LANE_FIELD_NUMBER: _ClassVar[int]
    WORLD_FIELD_NUMBER: _ClassVar[int]
    lane: LanePosition
    world: WorldPosition
    def __init__(self, lane: _Optional[_Union[LanePosition, _Mapping]] = ..., world: _Optional[_Union[WorldPosition, _Mapping]] = ...) -> None: ...

class WorldPosition(_message.Message):
    __slots__ = ("x", "y", "z", "h", "p", "r", "h_relative")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    H_FIELD_NUMBER: _ClassVar[int]
    P_FIELD_NUMBER: _ClassVar[int]
    R_FIELD_NUMBER: _ClassVar[int]
    H_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    h: float
    p: float
    r: float
    h_relative: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ..., h: _Optional[float] = ..., p: _Optional[float] = ..., r: _Optional[float] = ..., h_relative: _Optional[float] = ...) -> None: ...

class LanePosition(_message.Message):
    __slots__ = ("road_id", "lane_id", "s", "offset", "junction_id")
    ROAD_ID_FIELD_NUMBER: _ClassVar[int]
    LANE_ID_FIELD_NUMBER: _ClassVar[int]
    S_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    JUNCTION_ID_FIELD_NUMBER: _ClassVar[int]
    road_id: int
    lane_id: int
    s: float
    offset: float
    junction_id: int
    def __init__(self, road_id: _Optional[int] = ..., lane_id: _Optional[int] = ..., s: _Optional[float] = ..., offset: _Optional[float] = ..., junction_id: _Optional[int] = ...) -> None: ...
