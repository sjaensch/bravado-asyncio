import argparse
import asyncio
import multiprocessing
import os.path
import sys

import umsgpack
from aiohttp import web


INTEGRATION_SERVER_HOST = "127.0.0.1"

shm_request_received = None


async def swagger_spec(request):
    with open(os.path.join(os.path.dirname(__file__), "swagger.yaml")) as f:
        spec = f.read()
    return web.Response(text=spec, content_type="text/vnd.yaml")


async def store_inventory(request):
    await asyncio.sleep(1)
    return web.json_response({})


async def login(request):
    if not (
        request.query.get("username") == "asyncio"
        and request.query.get("password") == "p%s&wörd?"
        and request.query.get("invalidate_sessions") in ("True", "true")
    ):
        return web.HTTPBadRequest()

    return web.json_response(
        "success",
        headers={"X-Rate-Limit": "4711", "X-Expires-After": "Expiration date"},
    )


async def get_pet(request):
    check_content_type(request.headers, expected_content_type=None)

    pet_id = request.match_info["petId"]
    if pet_id == "5":
        return web.HTTPNotFound()

    return web.json_response({"id": int(pet_id), "name": "Lili", "photoUrls": []})


async def search_pets(request):
    pet_name = request.query["petName"]
    if pet_name == "lili":
        response = [{"id": 42, "name": "Lili", "photoUrls": []}]
    else:
        response = []

    return web.Response(
        body=umsgpack.packb(response), content_type="application/msgpack"
    )


async def update_pet_formdata(request):
    check_content_type(
        request.headers, expected_content_type="application/x-www-form-urlencoded"
    )

    post_data = await request.post()
    if not (
        request.match_info["petId"] == "12"
        and post_data.get("name") == "Vivi"
        and post_data.get("status") == "sold"
        and request.headers.get("userId") == "42"
        and post_data.getall("photoUrls")
        == ["http://first.url?param1=value1&param2=ß%$", "http://second.url"]
    ):
        return web.HTTPNotFound()

    return web.json_response({})


async def upload_pet_image(request):
    check_content_type(request.headers, expected_content_type="multipart/form-data")

    with open(os.path.join(os.path.dirname(__file__), "sample.jpg"), "rb") as f:
        data = await request.post()
        file_data = data.get("file")
        content = file_data.file.read()
        expected_content = f.read()

    if content != expected_content:
        return web.HTTPBadRequest()

    if not (request.match_info["petId"] == "42" and data.get("userId") == "12"):
        return web.HTTPBadRequest()

    return web.json_response({})


async def update_pet(request):
    check_content_type(request.headers, expected_content_type="application/json")

    body = await request.json()
    success = body == {
        "id": 42,
        "category": {"name": "extracute"},
        "name": "Lili",
        "photoUrls": [],
        "status": "sold",
    }

    if success:
        return web.json_response({})

    return web.HTTPBadRequest()


async def delete_pet(request):
    check_content_type(request.headers, expected_content_type=None)

    if request.query.get("petId") == "42":
        return web.HTTPInternalServerError()

    return web.json_response({})


async def get_pets(request):
    pet_ids = request.query.getall("petIds")
    if pet_ids != ["23", "42"]:
        return web.HTTPNotFound()

    pets = [
        {"id": 23, "name": "Takamoto", "photoUrls": []},
        {"id": 42, "name": "Lili", "photoUrls": []},
    ]
    return web.json_response(pets)


async def ping(request):
    shm_request_received.value = 1
    return web.json_response({})


def check_content_type(headers, expected_content_type):
    content_type = headers.get("Content-Type")
    if content_type != expected_content_type:
        if not (
            isinstance(expected_content_type, str)
            and str(content_type).startswith(expected_content_type)
        ):
            print("Invalid content type {}".format(content_type), file=sys.stderr)
            raise web.HTTPBadRequest()


def setup_routes(app):
    app.router.add_get("/swagger.yaml", swagger_spec)
    app.router.add_get("/store/inventory", store_inventory)
    app.router.add_get("/user/login", login)
    app.router.add_get("/pet/search", search_pets)
    app.router.add_get("/pet/{petId}", get_pet)
    app.router.add_post("/pet/{petId}", update_pet_formdata)
    app.router.add_post("/pet/{petId}/uploadImage", upload_pet_image)
    app.router.add_put("/pet", update_pet)
    app.router.add_delete("/pet", delete_pet)
    app.router.add_get("/pets", get_pets)
    app.router.add_get("/ping", ping)


def start_integration_server(port, shm_request_received_var):
    global shm_request_received, INTEGRATION_SERVER_HOST
    shm_request_received = shm_request_received_var
    app = web.Application()
    setup_routes(app)
    web.run_app(app, host=INTEGRATION_SERVER_HOST, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        default=8080,
        help="The port the webserver should listen on (default: %(default)s)",
    )
    args = parser.parse_args()

    start_integration_server(args.port, multiprocessing.Value("i", 0))
