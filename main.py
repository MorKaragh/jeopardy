import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocket

app = FastAPI()

app.mount("/ui/static", StaticFiles(directory="ui/static"), name="static")

templates = Jinja2Templates(directory="ui/templates")


@app.get("/test")
async def hello_test(request: Request):
    return templates.TemplateResponse(
        name="test.html", context={"request": request}
    )

@app.post("/clicked")
async def clicked(request: Request):
    return templates.TemplateResponse(
        name="test2.html", context={"request": request}
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


if __name__ == '__main__':
    path = Path(__file__)
    uvicorn.run(
        'main:app',
        host='localhost',
        port=8080,
        log_level=logging.DEBUG,
    )
