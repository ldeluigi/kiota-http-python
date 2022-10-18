import httpx
import pytest
from asyncmock import AsyncMock
from kiota_abstractions.authentication import AnonymousAuthenticationProvider
from kiota_abstractions.method import Method
from kiota_abstractions.request_information import RequestInformation
from kiota_serialization_json.json_parse_node import JsonParseNode
from kiota_serialization_json.json_parse_node_factory import JsonParseNodeFactory
from kiota_serialization_json.json_serialization_writer_factory import (
    JsonSerializationWriterFactory,
)

from kiota_http import HttpxRequestAdapter

from .helpers import OfficeLocation, User

BASE_URL = "https://graph.microsoft.com"


@pytest.fixture
def auth_provider():
    return AnonymousAuthenticationProvider()


@pytest.fixture
def parse_node_factory():
    return JsonParseNodeFactory()


@pytest.fixture
def serialization_writer_factory():
    return JsonSerializationWriterFactory()


@pytest.fixture
def request_info():
    return RequestInformation()


@pytest.fixture
def request_info_mock():
    return RequestInformation()


@pytest.fixture
def simple_response():
    return httpx.Response(
        json={'error': 'not found'}, status_code=404, headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_user_response(mocker):
    return httpx.Response(
        200,
        headers={"Content-Type": "application/json"},
        json={
            "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users/$entity",
            "businessPhones": ["+1 205 555 0108"],
            "displayName": "Diego Siciliani",
            "mobilePhone": None,
            "officeLocation": "dunhill",
            "updatedAt": "2021 -07-29T03:07:25Z",
            "birthday": "2000-09-04",
            "isActive": True,
            "age": 21,
            "gpa": 3.2,
            "id": "8f841f30-e6e3-439a-a812-ebd369559c36"
        },
    )


@pytest.fixture
def mock_users_response(mocker):
    return httpx.Response(
        200,
        json=[
            {
                "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users/$entity",
                "businessPhones": ["+1 425 555 0109"],
                "displayName": "Adele Vance",
                "mobilePhone": None,
                "officeLocation": "dunhill",
                "updatedAt": "2017 -07-29T03:07:25Z",
                "birthday": "2000-09-04",
                "isActive": True,
                "age": 21,
                "gpa": 3.7,
                "id": "76cabd60-f9aa-4d23-8958-64f5539b826a"
            },
            {
                "businessPhones": ["425-555-0100"],
                "displayName": "MOD Administrator",
                "mobilePhone": None,
                "officeLocation": "oval",
                "updatedAt": "2020 -07-29T03:07:25Z",
                "birthday": "1990-09-04",
                "isActive": True,
                "age": 32,
                "gpa": 3.9,
                "id": "f58411c7-ae78-4d3c-bb0d-3f24d948de41"
            },
        ],
    )


@pytest.fixture
def mock_primitive_collection_response(mocker):
    return httpx.Response(
        200, json=[12.1, 12.2, 12.3, 12.4, 12.5], headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_primitive_response(mocker):
    return httpx.Response(200, json=22.3, headers={"Content-Type": "application/json"})


@pytest.fixture
def mock_no_content_response(mocker):
    return httpx.Response(204, json="Radom JSON", headers={"Content-Type": "application/json"})


def test_create_request_adapter(auth_provider, parse_node_factory, serialization_writer_factory):
    request_adapter = HttpxRequestAdapter(
        auth_provider, parse_node_factory, serialization_writer_factory
    )
    assert request_adapter._authentication_provider is auth_provider
    assert request_adapter._parse_node_factory is parse_node_factory
    assert request_adapter._serialization_writer_factory is serialization_writer_factory


@pytest.fixture
def request_adapter(auth_provider, parse_node_factory, serialization_writer_factory):
    return HttpxRequestAdapter(auth_provider, parse_node_factory, serialization_writer_factory)


def test_get_serialization_writer_factory(request_adapter, serialization_writer_factory):
    assert request_adapter.get_serialization_writer_factory() is serialization_writer_factory


def test_get_response_content_type(request_adapter, simple_response):
    content_type = request_adapter.get_response_content_type(simple_response)
    assert content_type == 'application/json'


def test_set_base_url_for_request_information(request_adapter, request_info):
    request_adapter.base_url = BASE_URL
    request_adapter.set_base_url_for_request_information(request_info)
    assert request_info.path_parameters["baseurl"] == BASE_URL


def test_get_request_from_request_information(request_adapter, request_info):
    request_info.http_method = Method.GET
    request_info.url = BASE_URL
    request_info.content = bytes('hello world', 'utf_8')
    req = request_adapter.get_request_from_request_information(request_info)
    assert isinstance(req, httpx.Request)


def test_enable_backing_store(request_adapter):
    request_adapter.enable_backing_store(None)
    assert request_adapter._parse_node_factory
    assert request_adapter._serialization_writer_factory


@pytest.mark.asyncio
async def test_get_root_parse_node(request_adapter, simple_response):
    assert simple_response.text == '{"error": "not found"}'
    assert simple_response.status_code == 404
    content_type = request_adapter.get_response_content_type(simple_response)
    assert content_type == 'application/json'

    root_node = await request_adapter.get_root_parse_node(simple_response)
    assert isinstance(root_node, JsonParseNode)


@pytest.mark.asyncio
async def test_send_async(request_adapter, request_info, mock_user_response):
    request_adapter.get_http_response_message = AsyncMock(return_value=mock_user_response)
    resp = await request_adapter.get_http_response_message(request_info)
    assert resp.headers.get("content-type") == 'application/json'
    final_result = await request_adapter.send_async(request_info, User, None, {})
    assert isinstance(final_result, User)
    assert final_result.display_name == "Diego Siciliani"
    assert final_result.office_location == OfficeLocation.Dunhill
    assert final_result.business_phones == ["+1 205 555 0108"]
    assert final_result.age == 21
    assert final_result.gpa == 3.2
    assert final_result.is_active is True
    assert final_result.mobile_phone is None
    assert "@odata.context" in final_result.additional_data


@pytest.mark.asyncio
async def test_send_collection_async(request_adapter, request_info, mock_users_response):
    request_adapter.get_http_response_message = AsyncMock(return_value=mock_users_response)
    resp = await request_adapter.get_http_response_message(request_info)
    assert resp.headers.get("content-type") == 'application/json'
    final_result = await request_adapter.send_collection_async(request_info, User, None, {})
    assert isinstance(final_result[0], User)
    assert final_result[0].display_name == "Adele Vance"
    assert final_result[0].office_location == OfficeLocation.Dunhill
    assert final_result[0].business_phones == ["+1 425 555 0109"]
    assert final_result[0].age == 21
    assert final_result[0].gpa == 3.7
    assert final_result[0].is_active is True
    assert final_result[0].mobile_phone is None
    assert "@odata.context" in final_result[0].additional_data


@pytest.mark.asyncio
async def test_send_collection_of_primitive_async(
    request_adapter, request_info, mock_primitive_collection_response
):
    request_adapter.get_http_response_message = AsyncMock(
        return_value=mock_primitive_collection_response
    )
    resp = await request_adapter.get_http_response_message(request_info)
    assert resp.headers.get("content-type") == 'application/json'
    final_result = await request_adapter.send_collection_of_primitive_async(
        request_info, int, None, {}
    )
    assert final_result == [12.1, 12.2, 12.3, 12.4, 12.5]


@pytest.mark.asyncio
async def test_send_primitive_async(request_adapter, request_info, mock_primitive_response):
    request_adapter.get_http_response_message = AsyncMock(return_value=mock_primitive_response)
    resp = await request_adapter.get_http_response_message(request_info)
    assert resp.headers.get("content-type") == 'application/json'
    final_result = await request_adapter.send_primitive_async(request_info, float, None, {})
    assert final_result == 22.3


@pytest.mark.asyncio
async def test_send_primitive_async_no_content(
    request_adapter, request_info, mock_no_content_response
):
    request_adapter.get_http_response_message = AsyncMock(return_value=mock_no_content_response)
    resp = await request_adapter.get_http_response_message(request_info)
    assert resp.headers.get("content-type") == 'application/json'
    final_result = await request_adapter.send_primitive_async(request_info, float, None, {})
    assert final_result is None
