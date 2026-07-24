from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from models import complaints

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html")


@app.get("/complaints")
async def complaints_board(request: Request):
    return templates.TemplateResponse(
        request, "complaints.html", {"complaints": complaints}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", reload=True)
