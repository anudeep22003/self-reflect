from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.api.routers import router
from core.config import load_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_config()
    yield


app = FastAPI(title="Browsy Recording Server", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[""],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
