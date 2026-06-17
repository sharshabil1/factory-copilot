from fastapi import FastAPI

from database import init_db

app = FastAPI()


@app.on_event("startup")
async def startup():

    await init_db()


@app.get("/")
async def root():
    return {"message": "Factory Copilot API"}