from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    exists,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()
Base = declarative_base()
templates = Jinja2Templates(directory=".")


# Models
class Beacons(Base):
    __tablename__ = "beacons"
    id = Column(Integer, primary_key=True)
    ip = Column(String(15))
    mid = Column(String(250), nullable=False)
    heartbeat = Column(Integer, nullable=False)
    jitter = Column(Integer, nullable=False)
    lastCheckIn = Column(DateTime)
    nextCheckIn = Column(DateTime)


class Coins(Base):
    __tablename__ = "coins"
    id = Column(Integer, primary_key=True)
    mid = Column(String(250), ForeignKey("beacons.mid"))
    kk = Column(Integer, nullable=False)


# DB methods
class dbMethods:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create(self):
        Base.metadata.create_all(self.engine)

    def ProcessBeacon(self, mid, ip):
        if self.session.query(exists().where(Beacons.mid == mid)).scalar():
            beacon = self.session.query(Beacons).filter_by(mid=mid).one()
            offset = beacon.heartbeat + beacon.jitter
            now = datetime.now()
            beacon.lastCheckIn = now
            beacon.nextCheckIn = now + timedelta(seconds=offset)
            beacon.ip = ip
            print(f"Beacon check-in, next: {beacon.nextCheckIn}")
        else:
            now = datetime.now()
            new_beacon = Beacons(
                mid=mid,
                ip=ip,
                heartbeat=30,
                jitter=15,
                lastCheckIn=now,
                nextCheckIn=now + timedelta(seconds=45),
            )
            self.session.add(new_beacon)
            print(f"New beacon registered, next: {new_beacon.nextCheckIn}")
        self.session.commit()

    def ListBeacons(self):
        return self.session.query(Beacons).all()

    def UpdateBeacon(self, mid, h, j):
        beacon = self.session.query(Beacons).filter_by(mid=mid).one()
        h, j = int(h), int(j)
        beacon.heartbeat = h if h >= j else h
        beacon.jitter = j if j <= h else beacon.jitter
        self.session.commit()

    def DeleteBeacon(self, mid):
        beacon = self.session.query(Beacons).filter_by(mid=mid).one()
        self.session.delete(beacon)
        self.session.commit()

    def newCoin(self, mid, kk):
        if not self.session.query(exists().where(Coins.kk == kk)).scalar():
            self.session.add(Coins(mid=mid, kk=kk))
            self.session.commit()
            print(f"Coin received from {mid}")


# App init
db = dbMethods("sqlite:///kraskoins.db")
db.create()


# Routes
@app.get("/kk")
async def coin_or_beacon(c: str, m: str, request: Request):
    ip = request.headers.get("x-real-ip") or request.client.host
    if c == "BCH":
        db.ProcessBeacon(m, ip)
        beacon = db.session.query(Beacons).filter_by(mid=m).one()
        return JSONResponse({"h": beacon.heartbeat, "j": beacon.jitter})
    elif c == "CCH":
        k = request.query_params.get("k")
        db.newCoin(m, int(k))
        return {"status": "coin received"}


@app.post("/status")
async def update_beacon(
    c: str = Form(...), uuid: str = Form(None), h: str = Form(None), j: str = Form(None)
):
    if c == "DBR":
        db.DeleteBeacon(uuid)
        return {"status": f"Deleted {uuid}"}
    elif c == "UBR":
        db.UpdateBeacon(uuid, h, j)
        return {"status": f"Updated {uuid}"}


@app.get("/status", response_class=HTMLResponse)
async def status_portal(request: Request):
    beacons = db.ListBeacons()
    return templates.TemplateResponse(
        "status.mako", {"request": request, "beacons": beacons}
    )


@app.post("/updateHeartbeat")
async def update_heartbeat(
    uuid: str = Form(...), h: str = Form(...), j: str = Form(...)
):
    db.UpdateBeacon(uuid, h, j)
    return {"status": f"Updated {uuid} with heartbeat {h} and jitter {j}"}
