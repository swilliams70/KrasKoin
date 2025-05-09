from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.repos.coinsRepo import db
from app.models import StatusResponse


templates = Jinja2Templates(directory="app/templates")


router = APIRouter()

@router.get("/status", response_class=HTMLResponse)
async def status_portal(request: Request):
    beacons = db.ListBeacons()
    return templates.TemplateResponse(
        "status.html", {"request": request, "beacons": beacons}
    )

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
    print(f"Updating {uuid} with heartbeat {h} and jitter {j}")
    db.UpdateBeacon(uuid, h, j)
    return {"status": f"Updated {uuid}"}



@router.get("/beacon/list")
def list_beacons():
    beacons = db.ListBeacons()
    return beacons
