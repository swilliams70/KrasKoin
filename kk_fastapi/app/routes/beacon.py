from ..repos.coinsRepo import db, Beacons
from fastapi import (
    Form,
    Request,
    APIRouter,
    File,
    UploadFile,
    Body,
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import json


templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


class BeaconResponse(BaseModel):
    miner_id: str


class CoinResponse(BaseModel):
    miner_id: str
    coin_result: str


class StatusResponse(BaseModel):
    uuid: str
    h: int
    j: int


# Routes
@router.post("/beacon")
async def coin_or_beacon(request: Request, beaconIn: BeaconResponse):
    ip = request.headers.get("x-real-ip") or request.client.host
    db.ProcessBeacon(beaconIn.miner_id, ip)
    beacon = db.session.query(Beacons).filter_by(mid=beaconIn.miner_id).one()
    return {"h": beacon.heartbeat, "j": beacon.jitter}


@router.post("/coin")
def coin_call_home(coin: CoinResponse):
    db.newCoin(mid=coin.miner_id, kk=coin.coin_result)
    return {"status": "coin received"}


@router.delete("/status/{uuid}/")
def delete_beacon(uuid: str):
    db.DeleteBeacon(uuid)
    return {"status": f"Deleted {uuid}"}


@router.put("/status/{uuid}/")
def update_beacon(statusIn: StatusResponse):
    uuid = statusIn.uuid
    h = statusIn.h
    j = statusIn.j
    # Check if h and j are valid integers
    try:
        h = int(h)
        j = int(j)
    except ValueError:
        return {"error": "Invalid heartbeat or jitter value"}
    db.UpdateBeacon(uuid, h, j)
    return {"status": f"Updated {uuid}"}


@router.get("/status", response_class=HTMLResponse)
async def status_portal(request: Request):
    beacons = db.ListBeacons()
    return templates.TemplateResponse(
        "status.html", {"request": request, "beacons": beacons}
    )


@router.get("/beacon/list")
def list_beacons():
    beacons = db.ListBeacons()
    return beacons


@router.post("/updateHeartbeat")
async def update_heartbeat(
    uuid: str = Form(...), h: str = Form(...), j: str = Form(...)
):
    db.UpdateBeacon(uuid, h, j)
    return {"status": f"Updated {uuid} with heartbeat {h} and jitter {j}"}


@router.post("/upload")
async def receive_archive(
    metadata: str = Form(...),
    upload: UploadFile = File(...),
):
    data = json.loads(metadata)
    uuid = str(data.get("uuid"))
    print(f"Received tarball: {upload.filename} for UUID: {uuid}")
    contents = await upload.read()
    os.makedirs(f"../tars/{uuid}", exist_ok=True)
    with open(f"../tars/{uuid}/{upload.filename}", "wb") as f:
        f.write(contents)
    return {"status": "received"}
