import keyboard
import pyautogui as pg
from loguru import logger
import time
import math

from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser("auto-clicker")
    parser.add_argument(
        "-p", "--profile", action="store_true", help="print the profile information"
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=0, help="loop interval, defaul 0"
    )
    parser.add_argument(
        "-n", "--num", type=int, default=10, help="number of iterations, default 10"
    )
    return parser.parse_args()


T_DELTA = pow(10, 6)


def delayMsecond(t):
    start, end = time.perf_counter_ns(), time.perf_counter_ns()
    target_time = t * T_DELTA
    while end - start < target_time:
        end = time.perf_counter_ns()


class Points(object):
    def __init__(self, iterations: int, interval: float, pause: float):
        logger.info("waiting for the prog to be initialized ...")
        self.pts = []
        self.iterations = iterations
        self.interval = interval
        self.pause = pause
        self.freezed = False

    def add(self, pt: tuple):
        if not self.freezed:
            logger.info(f"Adding point {pt}")
            self.pts.append(pt)
        else:
            logger.warning("Points Freezed, skipping")

    def iter(self):
        for _ in range(self.iterations):
            for pt in self.pts:
                yield pt
                delayMsecond(self.interval)
            delayMsecond(self.pause)

    def freeze(self):
        self.freezed = True


class Clicker(object):
    def __init__(
        self,
        iterations: int = 10,
        interval: float = 500,
        pause: float = 500,
        profile: bool = True,
    ) -> None:
        self.pts = Points(iterations, interval, pause)
        self.preparing = True
        self.profile_ = profile

    def prepared(self):
        self.preparing = False

    def run(self) -> None:
        keyboard.add_hotkey("ctrl+a", lambda: self.pts.add(pg.position()))
        keyboard.add_hotkey("ctrl+s", self.prepared)

        logger.info(
            "prog ready, press ctrl+a to add points; press ctrl+s to freeze points and start click looping"
        )

        while self.preparing:
            pg.sleep(0.1)
        res = self.loop()
        if self.profile_:
            self.profile(res)

    def loop(self) -> None:
        self.pts.freeze()
        res = []
        for x, y in self.pts.iter():
            res.append(time.perf_counter_ns())
            pg.click(x, y)
        return res
    
    def cal_profile(self, res):
        mean_val = sum(res)/len(res)
        std_val = math.sqrt(sum([(x - mean_val)**2 for x in res]))/len(res)
        return mean_val, std_val

    def profile(self, data):
        data = [(data[i+1] - data[i]) / 1e9 for i in range(len(data)-1)]
        mean_val, std_val = self.cal_profile(data)

        logger.info(f"{'='*20} profile {'='*20}")
        logger.info(f" | interval mean | {mean_val:.4f} s|")
        logger.info(f" | interval std  | {std_val:.4f} s|")
        logger.info(f" | interval data | {data} ")


if __name__ == "__main__":
    args = parse_args()
    clicker = Clicker(
        iterations=args.num, interval=args.interval, pause=0, profile=args.profile,
    )
    clicker.run()
