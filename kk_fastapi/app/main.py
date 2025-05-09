from fastapi import FastAPI
from app.routes.beacon import router as beacon_router
from app.routes.info import router as info_router

app = FastAPI()
app.include_router(beacon_router, prefix="/healthcheck", tags=["healthcheck"])
app.include_router(info_router, prefix="/info", tags=["info"])
