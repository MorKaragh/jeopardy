import datetime
import json
import logging
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocket

from ui.quiz.quiz import make_fake

app = FastAPI()

app.mount("/ui/static", StaticFiles(directory="ui/static"), name="static")

templates = Jinja2Templates(directory="ui/templates")


@app.get("/")
async def root_page(request: Request):
    return templates.TemplateResponse(
        name="root.html", context={"request": request, "room_name": "rname", "user_name": "uname"}
    )


@app.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse(
        name="login.html", context={"request": request}
    )

@app.post("/rooms")
async def create_room(request: Request, response: Response):
    print(request)
    return templates.TemplateResponse(
        name="game_room.html", context={"request": request}
    )

@app.get("/table")
async def open_game_table(request: Request):
    rows = make_fake()
    return templates.TemplateResponse(
        name="main_table.html", context={
            "request": request,
            "rows": rows,
        }
    )


@app.get("/questions/{question_id}")
async def open_question(request: Request,
                        question_id: str):
    return templates.TemplateResponse(
        name="question.html", context={
            "request": request,
            "question": {
                "text": f"ID {question_id} {str(datetime.datetime.now())}",
                "id": question_id
            },
            "showman": True,
        }
    )


@app.post("/questions/{question_id}/answers/{answer}")
async def give_answer(request: Request,
                      question_id: str,
                      answer: str):
    print(question_id)
    return templates.TemplateResponse(
        name="answer.html", context={
            "request": request,
            "question": {
                "id": question_id
            },
            "answer": answer,
        }
    )


connections = {}


@app.websocket("/game")
async def websocket_endpoint(websocket: WebSocket):
    connections[websocket] = {}
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        message = json.loads(data)
        if message["msg_type"] == "room_hello":
            connections[websocket]["user_name"] = message["user_name"]
            connections[websocket]["room_name"] = message["room_name"]


async def send_game_updates(user_name: str, room_name: str, event: dict):
    websocket = find_socket(user_name, room_name)
    await websocket.send_text(templates.get_template("game_control.html").render({"data": "data"}))


def find_socket(user_name, room_name) -> Optional[WebSocket]:
    for connection in connections:
        if connections[connection]["user_name"] == user_name and connections[connection]["room_name"] == room_name:
            return connection
    return None


if __name__ == '__main__':
    path = Path(__file__)
    uvicorn.run(
        'main:app',
        host='localhost',
        port=8080,
        log_level=logging.DEBUG,
    )
