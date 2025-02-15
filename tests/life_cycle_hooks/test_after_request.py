from typing import Optional

import pytest

from litestar import Controller, Response, Router, get
from litestar.status_codes import HTTP_200_OK
from litestar.testing import create_test_client
from litestar.types import AfterRequestHookHandler


def sync_after_request_handler(response: Response) -> Response:
    assert isinstance(response, Response)
    response.body = response.render({"hello": "moon"})
    return response


async def async_after_request_handler(response: Response) -> Response:
    assert isinstance(response, Response)
    response.body = response.render({"hello": "moon"})
    return response


async def async_after_request_handler_with_hello_world(response: Response) -> Response:
    assert isinstance(response, Response)
    response.body = response.render({"hello": "world"})
    return response


@pytest.mark.parametrize(
    "after_request, expected",
    [
        [None, {"hello": "world"}],
        [sync_after_request_handler, {"hello": "moon"}],
        [async_after_request_handler, {"hello": "moon"}],
    ],
)
def test_after_request_handler_called(after_request: Optional[AfterRequestHookHandler], expected: dict) -> None:
    @get(after_request=after_request)
    def handler() -> dict:
        return {"hello": "world"}

    with create_test_client(route_handlers=handler) as client:
        response = client.get("/")
        assert response.json() == expected


@pytest.mark.parametrize(
    "app_after_request_handler, router_after_request_handler, controller_after_request_handler, method_after_request_handler, expected",
    [
        [None, None, None, None, {"hello": "world"}],
        [sync_after_request_handler, None, None, None, {"hello": "moon"}],
        [None, sync_after_request_handler, None, None, {"hello": "moon"}],
        [None, None, sync_after_request_handler, None, {"hello": "moon"}],
        [None, None, None, sync_after_request_handler, {"hello": "moon"}],
        [sync_after_request_handler, async_after_request_handler_with_hello_world, None, None, {"hello": "world"}],
        [None, sync_after_request_handler, async_after_request_handler_with_hello_world, None, {"hello": "world"}],
        [None, None, sync_after_request_handler, async_after_request_handler_with_hello_world, {"hello": "world"}],
        [None, None, None, async_after_request_handler_with_hello_world, {"hello": "world"}],
    ],
)
def test_after_request_handler_resolution(
    app_after_request_handler: Optional[AfterRequestHookHandler],
    router_after_request_handler: Optional[AfterRequestHookHandler],
    controller_after_request_handler: Optional[AfterRequestHookHandler],
    method_after_request_handler: Optional[AfterRequestHookHandler],
    expected: dict,
) -> None:
    class MyController(Controller):
        path = "/hello"

        after_request = controller_after_request_handler

        @get(after_request=method_after_request_handler)
        def hello(self) -> dict:
            return {"hello": "world"}

    router = Router(path="/greetings", route_handlers=[MyController], after_request=router_after_request_handler)

    with create_test_client(route_handlers=router, after_request=app_after_request_handler) as client:
        response = client.get("/greetings/hello")
        assert response.json() == expected


def test_after_request_handles_handlers_that_return_responses() -> None:
    def after_request(response: Response) -> Response:
        response.headers["Custom-Header-Name"] = "Custom Header Value"
        return response

    @get("/")
    def handler() -> Response:
        return Response("test")

    with create_test_client(handler, after_request=after_request) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
        assert response.headers.get("Custom-Header-Name") == "Custom Header Value"
