from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RoadObjectType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[RoadObjectType]
    CAR: _ClassVar[RoadObjectType]
    TRUCK: _ClassVar[RoadObjectType]
    BUS: _ClassVar[RoadObjectType]
    SEMITRAILER: _ClassVar[RoadObjectType]
    TRAILER: _ClassVar[RoadObjectType]
    MOTORCYCLE: _ClassVar[RoadObjectType]
    BICYCLE: _ClassVar[RoadObjectType]
    PEDESTRIAN: _ClassVar[RoadObjectType]
    VAN: _ClassVar[RoadObjectType]
    TRAIN: _ClassVar[RoadObjectType]
    TRAM: _ClassVar[RoadObjectType]
    WHEEL_CHAIR: _ClassVar[RoadObjectType]
    ANIMAL: _ClassVar[RoadObjectType]

class ShapeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BOUNDING_BOX: _ClassVar[ShapeType]
    CYLINDER: _ClassVar[ShapeType]
    POLYGON: _ClassVar[ShapeType]
UNKNOWN: RoadObjectType
CAR: RoadObjectType
TRUCK: RoadObjectType
BUS: RoadObjectType
SEMITRAILER: RoadObjectType
TRAILER: RoadObjectType
MOTORCYCLE: RoadObjectType
BICYCLE: RoadObjectType
PEDESTRIAN: RoadObjectType
VAN: RoadObjectType
TRAIN: RoadObjectType
TRAM: RoadObjectType
WHEEL_CHAIR: RoadObjectType
ANIMAL: RoadObjectType
BOUNDING_BOX: ShapeType
CYLINDER: ShapeType
POLYGON: ShapeType

class ObjectKinematic(_message.Message):
    __slots__ = ("time_ns", "x", "y", "z", "yaw", "speed", "acceleration", "yaw_rate", "yaw_acceleration")
    TIME_NS_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    YAW_RATE_FIELD_NUMBER: _ClassVar[int]
    YAW_ACCELERATION_FIELD_NUMBER: _ClassVar[int]
    time_ns: int
    x: float
    y: float
    z: float
    yaw: float
    speed: float
    acceleration: float
    yaw_rate: float
    yaw_acceleration: float
    def __init__(self, time_ns: _Optional[int] = ..., x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ..., yaw: _Optional[float] = ..., speed: _Optional[float] = ..., acceleration: _Optional[float] = ..., yaw_rate: _Optional[float] = ..., yaw_acceleration: _Optional[float] = ...) -> None: ...

class Shape(_message.Message):
    __slots__ = ("type", "dimensions", "vertices", "center", "reference_point")
    class Dimension(_message.Message):
        __slots__ = ("x", "y", "z")
        X_FIELD_NUMBER: _ClassVar[int]
        Y_FIELD_NUMBER: _ClassVar[int]
        Z_FIELD_NUMBER: _ClassVar[int]
        x: float
        y: float
        z: float
        def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...
    class Vertex(_message.Message):
        __slots__ = ("x", "y", "z")
        X_FIELD_NUMBER: _ClassVar[int]
        Y_FIELD_NUMBER: _ClassVar[int]
        Z_FIELD_NUMBER: _ClassVar[int]
        x: float
        y: float
        z: float
        def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...
    class CenterPose(_message.Message):
        __slots__ = ("x", "y", "z", "roll", "pitch", "yaw")
        X_FIELD_NUMBER: _ClassVar[int]
        Y_FIELD_NUMBER: _ClassVar[int]
        Z_FIELD_NUMBER: _ClassVar[int]
        ROLL_FIELD_NUMBER: _ClassVar[int]
        PITCH_FIELD_NUMBER: _ClassVar[int]
        YAW_FIELD_NUMBER: _ClassVar[int]
        x: float
        y: float
        z: float
        roll: float
        pitch: float
        yaw: float
        def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ..., roll: _Optional[float] = ..., pitch: _Optional[float] = ..., yaw: _Optional[float] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DIMENSIONS_FIELD_NUMBER: _ClassVar[int]
    VERTICES_FIELD_NUMBER: _ClassVar[int]
    CENTER_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_POINT_FIELD_NUMBER: _ClassVar[int]
    type: ShapeType
    dimensions: Shape.Dimension
    vertices: _containers.RepeatedCompositeFieldContainer[Shape.Vertex]
    center: Shape.CenterPose
    reference_point: str
    def __init__(self, type: _Optional[_Union[ShapeType, str]] = ..., dimensions: _Optional[_Union[Shape.Dimension, _Mapping]] = ..., vertices: _Optional[_Iterable[_Union[Shape.Vertex, _Mapping]]] = ..., center: _Optional[_Union[Shape.CenterPose, _Mapping]] = ..., reference_point: _Optional[str] = ...) -> None: ...

class ObjectState(_message.Message):
    __slots__ = ("type", "kinematic", "shape")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    KINEMATIC_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    type: RoadObjectType
    kinematic: ObjectKinematic
    shape: Shape
    def __init__(self, type: _Optional[_Union[RoadObjectType, str]] = ..., kinematic: _Optional[_Union[ObjectKinematic, _Mapping]] = ..., shape: _Optional[_Union[Shape, _Mapping]] = ...) -> None: ...
