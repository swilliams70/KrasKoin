import uuid
import datetime
import hashlib
import string
import time
import requests
import json
import logging
from random import *

#below value should be 0 (CPU @ ~20%) or 1 (CPU quiet, slows payoff)
processingLevel = 0

#below value is too high? pays too often? probably should be set by server
target = 3000000000000000000000000000000000000000000000
#targetDigest = 00045a5623a9ad5c610e2c7dfb024fa8a798f52d

class phoneHome():
        heartbeat = 30
        jitter = 15
        
        def __init__(self):
                super().__init__()
                
        def callHome(self, checkpoint, minerID):
                r = requests.get('http://localhost:8888/beta?mid={}'.format(minerID))
                if r.status_code != 200: raise ValueError(r.text)
                p = json.loads(r.text)
                phoneHome.heartbeat = p["h"]
                phoneHome.jitter = p["j"]
                print('Heartbeat updated: {}, {}'.format(phoneHome.heartbeat, phoneHome.jitter))

        def callCoin(self, coinResult, minerID):
                payload = { 'kk' : coinResult, 'mid' : minerID }
                r = requests.post('http://localhost:8888/beta', data=payload)
                print(r.text)

        def newTime(self):
                current_time = datetime.datetime.now()
                #add or subtract jitter based on current time
                if current_time.microsecond % 2 == 0:   
                        offset = phoneHome.heartbeat - randint(0, phoneHome.jitter)
                else: 
                        offset = phoneHome.heartbeat + randint(0, phoneHome.jitter)
                #use offset to establish next check in
                return_time = (current_time + datetime.timedelta(seconds = offset))
                return (return_time)

class coin():
        def __init__(self):
                super().__init__()
                
        def mine(self):
                allchar = string.ascii_letters + string.punctuation + string.digits
                miningSeed = "".join(choice(allchar) for x in range(randint(1, 20)))
                miningDigest=hashlib.sha1((miningSeed).encode('utf-8'))
                time.sleep(processingLevel)
                return (miningDigest)

        def compare(self, target, miningDigest):
                coinTry=int(miningDigest.hexdigest(),miningDigest.digest_size)
                if coinTry < target:
                        result = 1
                else:
                        result = 0
                return (result)


def main():
        getNewParams = 1
        app=phoneHome()
        mine=coin()
        minerID = uuid.uuid4().hex
        
        while True:
                try:
                        checkpoint = datetime.datetime.now()

                        if getNewParams == 1:
                                check_in = app.newTime()
                                getNewParams = 0
                                app.callHome(checkpoint, minerID)
                                
                        if checkpoint > check_in:
                                getNewParams = 1
                        else:
                                coinResult = mine.mine()
                        
                                if mine.compare(target,coinResult) == 1:
                                    app.callCoin(coinResult.hexdigest(),minerID)
                        
                except (KeyboardInterrupt):                     #REMOVE IN FINAL
                        break                                   #REMOVE IN FINAL
                except Exception as e:
                        logging.exception(e)
                        print (e)                               #REMOVE IN FINAL
                        continue

if __name__ == "__main__":
        main()

