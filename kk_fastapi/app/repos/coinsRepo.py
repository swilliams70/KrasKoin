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


Base = declarative_base()


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
    miner = Column(String(250), ForeignKey("beacons.mid"))
    kk = Column(String(250), nullable=False)


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
            self.session.add(Coins(miner=mid, kk=kk))
            self.session.commit()
            print(f"Coin received from {mid}")


# App init
db = dbMethods("sqlite:///app/data/kraskoins.db")
db.create()
