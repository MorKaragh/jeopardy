import dataclasses
import datetime
import json
import logging
from pathlib import Path
from typing import Optional, Annotated

import uvicorn
from fastapi import FastAPI, Form
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocket

from ui.quiz.quiz import make_fake_game

app = FastAPI()

app.mount("/ui/static", StaticFiles(directory="ui/static"), name="static")

templates = Jinja2Templates(directory="ui/templates")

games = {}

connections = {}


@app.get("/")
async def root_page(request: Request):
    return templates.TemplateResponse(
        name="root.html", context={"request": request}
    )


@app.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse(
        name="login.html", context={"request": request}
    )


@app.post("/rooms")
async def create_room(request: Request,
                      response: Response,
                      room_name: Annotated[str, Form()]):
    if room_name not in games:
        games[room_name] = make_fake_game(room_name)
    return templates.TemplateResponse(
        name="game_room.html",
        context={
            "request": request,
            "game": games[room_name]
        }
    )


@app.get("/table/{room_name}")
async def open_game_table(request: Request,
                          room_name: str):
    return templates.TemplateResponse(
        name="main_table.html",
        context={
            "request": request,
            "game": games[room_name],
        }
    )


@app.get("/questions/{question_id}")
async def open_question(request: Request,
                        question_id: str,
                        room_name: str):
    return templates.TemplateResponse(
        name="question.html", context={
            "request": request,
            "room_name": room_name,
            "question": games[room_name].find_question_by_id(question_id),
            "showman": True,
        }
    )


@app.websocket("/game-ws")
async def websocket_endpoint(websocket: WebSocket):
    connections[websocket] = {}
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await process_received_message(json.loads(data), websocket)


async def process_received_message(message: dict, websocket: WebSocket):
    print(f"received {message}")
    match message["msg_type"]:
        case "room_hello":
            connections[websocket]["user_name"] = message["user_name"]
            connections[websocket]["room_name"] = message["room_name"]
        case "question_answer":
            room = message["room_name"]
            answer = message["answer"]
            question_id = message["question_id"]
            question = games[room].find_question_by_id(question_id)
            question.was_asked = True
            result = templates.get_template("close_question_signal.html").render()
            await send_game_updates(room, result)
            await send_game_updates(room, templates.get_template("main_table.html").render({
                "game": games[room],
            }))
        case _:
            pass


async def send_game_updates(room_name: str, html: str):
    sockets = all_room_sockets(room_name)
    for socket in sockets:
        print(f"sending {html} to {socket}")
        await socket.send_text(html)


def all_room_sockets(room_name) -> list[WebSocket]:
    result = []
    for connection in connections:
        if "room_name" in connections[connection] and connections[connection]["room_name"] == room_name:
            result.append(connection)
    return result


if __name__ == '__main__':
    path = Path(__file__)
    uvicorn.run(
        'main:app',
        host='localhost',
        port=8080,
        log_level=logging.DEBUG,
    )
