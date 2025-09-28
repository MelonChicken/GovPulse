import time
import asyncio
from collections import defaultdict
from typing import Dict

class RateState:
    def __init__(self, per_host_conc: int, global_conc: int):
        self.last_host_check: Dict[str, float] = defaultdict(float)
        self.last_ep_check: Dict[str, float] = defaultdict(float)
        self.global_sem = asyncio.Semaphore(global_conc)
        self.host_sems: Dict[str, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(per_host_conc)
        )

    def allowed_now(self, host: str, ep_key: str, host_interval: float, ep_interval: float) -> bool:
        now = time.monotonic()
        return (now - self.last_host_check[host] >= host_interval) and \
               (now - self.last_ep_check[ep_key] >= ep_interval)

    def mark(self, host: str, ep_key: str) -> None:
        now = time.monotonic()
        self.last_host_check[host] = now
        self.last_ep_check[ep_key] = now