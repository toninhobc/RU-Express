from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from db import init_db, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"Hello": "World!"}


@app.get("/db")
def db(db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")

    result = cursor.fetchall()

    cursor.close()

    return result
