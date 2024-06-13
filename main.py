import json
import logging
from pathlib import Path
from typing import Annotated, Callable

import uvicorn
from fastapi import FastAPI, Form
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocket

from models import Player, Game
from quiz import make_fake_game

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
            "game": games[room_name],
            "player_name": "showman",
        }
    )


@app.post("/join")
async def join_room(request: Request,
                    response: Response,
                    room_name: Annotated[str, Form()],
                    player_name: Annotated[str, Form()]):
    if room_name in games:
        game = games[room_name]
        player = game.find_player(player_name)
        if not player:
            player = Player(name=player_name, score=0)
            game.players.append(player)
        return templates.TemplateResponse(
            name="game_room.html",
            context={
                "request": request,
                "game": games[room_name],
                "player_name": player_name,
            }
        )


@app.get("/table/{room_name}")
async def open_game_table(request: Request,
                          room_name: str,
                          player_name: str):
    return templates.TemplateResponse(
        name="main_table.html",
        context={
            "request": request,
            "game": games[room_name],
            "player_name": player_name,
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
            room = message["room_name"]
            connections[websocket]["player_name"] = message["player_name"]
            connections[websocket]["room_name"] = room
            await send_game_updates(room, templates.get_template("players.html").render({"game": games[room]}))
        case "question_answer":
            room = message["room_name"]
            answer = message["answer"]
            question_id = message["question_id"]
            question = games[room].find_question_by_id(question_id)
            question.was_asked = True
            await send_game_updates(room, templates.get_template("close_question_signal.html").render())
            await send_to_all(room, main_table_renderer)
        case "open_question":
            room = message["room_name"]
            question_id = message["question_id"]
            await send_game_updates(room, templates.get_template("question.html").render({
                "room_name": room,
                "question": games[room].find_question_by_id(question_id),
                "showman": True,
            }))
        case _:
            pass


def main_table_renderer(game: Game, player_name: str):
    return templates.get_template("main_table.html").render({
        "game": game,
        "player_name": player_name
    })


async def send_to_all(room: str, render_fun: Callable):
    sockets = all_room_sockets(room)
    for socket in sockets:
        socket_metadata = connections[socket]
        player_name = socket_metadata.get("player_name")
        if player_name:
            try:
                await socket.send_text(render_fun(games[room], player_name))
            except RuntimeError:
                pass


async def send_game_updates(room_name: str, html: str):
    sockets = all_room_sockets(room_name)
    for socket in sockets:
        print(f"sending {html} to {socket}")
        try:
            await socket.send_text(html)
        except RuntimeError:
            pass


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
