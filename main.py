import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
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
        name="root.html", context={"request": request}
    )


@app.post("/table")
async def clicked(request: Request):
    rows = make_fake()
    print(rows)
    return templates.TemplateResponse(
        name="main_table.html", context={"request": request,
                                         "rows": rows}
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
