import uvicorn
import os
from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

database = {
    "users": {

    },
}

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    if email not in database["users"]:
        database["users"][email] = {"password": password, "guess": -1}
        return RedirectResponse(f"/?email={email}&guess=-1")
    else:
        if database["users"][email]["password"] == password:
            return RedirectResponse(f"/?email={email}&guess={database['users'][email]['guess']}")
    return RedirectResponse("/")

templates = Jinja2Templates(directory="templates")


@app.post("/guess")
async def guess(request: Request, guess: str = Form(...)):
    email = "abc"
    database["users"][email]["guess"] = guess
    return RedirectResponse(f"/?email={email}&guess={guess}")


@app.get("/")
@app.post("/")
async def homepage(request: Request):
    not_logged_in_message = "Please login"
    email = request.query_params.get("email") or not_logged_in_message
    return templates.TemplateResponse("index.html", {
        "request": request,
        "name": email,
        "logged_in": email != not_logged_in_message,
        "guess": request.query_params.get("guess"),
    })

if __name__ == "__main__":
    print("Starting webserver...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)))