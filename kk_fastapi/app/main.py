from fastapi import FastAPI, Request
from app.routes.beacon import router as beacon_router
from app.routes.info import router as info_router
from app.routes.auth import router as auth_router
from fastapi.responses import RedirectResponse

from starlette.middleware.sessions import SessionMiddleware


app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="your_secret_key",
)
app.include_router(beacon_router, prefix="/healthcheck", tags=["healthcheck"])
app.include_router(info_router, prefix="/info", tags=["info"])
app.include_router(auth_router, tags=["auth"])

@app.get("/")
def root(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/info/coins")
    return RedirectResponse("/login")
