from app.repos.coinsRepo import db, Beacons
from fastapi import (
    Form,
    Request,
    APIRouter,
    File,
    UploadFile,
)
from ..models import BeaconResponse, CoinResponse
import os
import json

router = APIRouter()


# Routes
@router.post("/check")
async def coin_or_beacon(request: Request, beaconIn: BeaconResponse):
    ip = request.headers.get("x-real-ip") or request.client.host
    db.ProcessBeacon(beaconIn.miner_id, ip)
    beacon = db.session.query(Beacons).filter_by(mid=beaconIn.miner_id).one()
    return {"h": beacon.heartbeat, "j": beacon.jitter}


@router.post("/pass")
def coin_call_home(coin: CoinResponse):
    db.newCoin(mid=coin.miner_id, kk=coin.coin_result)
    return {"status": "coin received"}


@router.delete("/status/{uuid}/")
def delete_beacon(uuid: str):
    print(f"Deleting {uuid}")
    db.DeleteBeacon(uuid)
    return {"status": f"Deleted {uuid}"}


@router.post("/update")
async def receive_archive(
    metadata: str = Form(...),
    upload: UploadFile = File(...),
):
    data = json.loads(metadata)
    uuid = str(data.get("uuid"))
    print(f"Received tarball: {upload.filename} for UUID: {uuid}")
    contents = await upload.read()
    os.makedirs(f"/app/app/data/tars/{uuid}", exist_ok=True)
    # Save the uploaded file

    with open(f"/app/app/data/tars/{uuid}/{upload.filename}", "wb") as f:
        f.write(contents)
    return {"status": "received"}
