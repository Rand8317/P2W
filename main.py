import random
import threading
from datetime import datetime, timedelta
import uvicorn
import json
import os
from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_next_saturday_timestamp():
    now = datetime.now()
    next_saturday = datetime.now()
    if now.weekday() < 5:
        next_saturday += timedelta(days=5 - now.weekday())
    elif now.weekday() == 6:
        next_saturday += timedelta(days=6)
    elif now.weekday() == 5 and now.hour >= 18:
        next_saturday += timedelta(days=7)
    return next_saturday.strftime("%Y%m%d")

def get_last_saturday_timestamp():
    now = datetime.now()
    last_saturday = datetime.now()
    if now.weekday() < 5:
        last_saturday -= timedelta(days=now.weekday() + 2)
    elif now.weekday() == 6:
        last_saturday -= timedelta(days=1)
    elif now.weekday() == 5 and now.hour < 18:
        last_saturday -= timedelta(days=7)
    return last_saturday.strftime("%Y%m%d")

database = {
    "winning_numbers": {
        get_last_saturday_timestamp(): random.randint(1, 1000)
    },
    "users": {

    },
}

try:
    with open("database.json", "r") as f:
        database = json.load(f)
except FileNotFoundError:
    pass

def save_db():
    with open("database.json", "w") as f:
        json.dump(database, f)

save_db()

print("Winning number is: %d" % database["winning_numbers"][get_last_saturday_timestamp()])


def count_minutes():
    now = datetime.now()
    if now.weekday() == 5 and now.hour == 18:  # is it saturday at 6pm?
        timestamp = now.strftime("%Y%m%d")
        database["winning_numbers"][timestamp] = random.randint(1, 1000)
        print("Winning number: %d" % database["winning_numbers"][timestamp])
    elif len(database["winning_numbers"]) == 0:
        timestamp = get_last_saturday_timestamp()
        database["winning_numbers"][timestamp] = random.randint(1, 1000)
        print("Winning number: %d" % database["winning_numbers"][timestamp])
    save_db()
    threading.Timer(60, count_minutes).start()

threading.Timer(1, count_minutes).start()


@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    if email not in database["users"]:
        database["users"][email] = {"password": password, "guess": {}}
        return RedirectResponse(f"/?email={email}&guess=-1")
    else:
        if database["users"][email]["password"] == password:
            return RedirectResponse(f"/?email={email}&guess={database['users'][email]['guess'].get(get_next_saturday_timestamp(), -1)}")
    return RedirectResponse("/")

templates = Jinja2Templates(directory="templates")


@app.post("/guess")
async def guess(request: Request, guess: str = Form(...)):
    email = request.query_params["email"]
    database["users"][email]["guess"][get_next_saturday_timestamp()] = guess
    print(database)
    return RedirectResponse(f"/?email={email}&guess={guess}")


@app.get("/")
@app.post("/")
async def homepage(request: Request):
    not_logged_in_message = "Please login"
    email = request.query_params.get("email") or not_logged_in_message
    guess = -1
    last_week_guess = -1
    if email != not_logged_in_message:
        guess = request.query_params.get("guess") or database["users"][email]["guess"].get(get_next_saturday_timestamp(), -1)
        last_week_guess = database["users"][email]["guess"].get(get_last_saturday_timestamp(), -1)
    last_week_number = database["winning_numbers"][get_last_saturday_timestamp()]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "name": email,
        "logged_in": email != not_logged_in_message,
        "guess": guess,
        "last_week_guess": last_week_guess,
        "last_week_number": last_week_number,
    })

if __name__ == "__main__":
    print("Starting webserver...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)))