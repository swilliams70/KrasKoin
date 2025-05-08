from fastapi import FastAPI
import os
from .routes.beacon import router as beacon_router

app = FastAPI()
app.include_router(beacon_router, prefix="/healthcheck", tags=["healthcheck"])
