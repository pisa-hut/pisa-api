import pytest

from pisa_api.av import InitResponse as AvInitResponse
from pisa_api.conversions import init_response_from_proto, init_response_to_proto
from pisa_api.initialization_pb2 import InitResponse as InitResponseMessage
from pisa_api.simulator import InitResponse as SimulatorInitResponse
from pisa_api.types import InitResponse


def test_role_packages_reexport_the_shared_init_response() -> None:
    assert AvInitResponse is InitResponse
    assert SimulatorInitResponse is InitResponse


@pytest.mark.parametrize(
    "metadata",
    [
        {},
        {"nested": {"items": [None, True, 1.5, "value"]}},
        {"null": None, "bool": False, "number": 42, "string": "text"},
    ],
)
def test_init_response_round_trip(metadata) -> None:
    response = InitResponse(name="component", metadata=metadata)
    assert init_response_from_proto(init_response_to_proto(response)) == response


@pytest.mark.parametrize("name", ["", " ", "\t\n"])
def test_init_response_rejects_blank_name(name) -> None:
    with pytest.raises(ValueError):
        init_response_to_proto(InitResponse(name=name))
    with pytest.raises(ValueError):
        init_response_from_proto(InitResponseMessage(name=name))


def test_init_response_rejects_non_dict_metadata() -> None:
    with pytest.raises(TypeError):
        init_response_to_proto(InitResponse(name="component", metadata=[]))  # type: ignore[arg-type]


def test_init_response_rejects_unrepresentable_metadata_value() -> None:
    with pytest.raises((TypeError, ValueError)):
        init_response_to_proto(InitResponse(name="component", metadata={"bad": object()}))


def test_init_response_rejects_non_string_metadata_key() -> None:
    with pytest.raises((TypeError, ValueError)):
        init_response_to_proto(InitResponse(name="component", metadata={1: "bad"}))  # type: ignore[dict-item]
