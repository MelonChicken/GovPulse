import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    UA: str = os.getenv("PP_UA", "GovPublicStatusMonitor/1.0 (+contact@example.com)")
    CONNECT_TIMEOUT_S: float = float(os.getenv("PP_CONNECT_TIMEOUT_S", "5"))
    READ_TIMEOUT_S: float = float(os.getenv("PP_READ_TIMEOUT_S", "8"))
    TOTAL_TIMEOUT_S: float = float(os.getenv("PP_TOTAL_TIMEOUT_S", "12"))
    TTFB_SLA_S: float = float(os.getenv("PP_TTFB_SLA_S", "8"))
    HOST_MIN_INTERVAL_S: float = float(os.getenv("PP_HOST_MIN_INTERVAL_S", "60"))
    EP_MIN_INTERVAL_S: float = float(os.getenv("PP_EP_MIN_INTERVAL_S", "600"))
    GLOBAL_MAX_CONCURRENCY: int = int(os.getenv("PP_GLOBAL_MAX_CONCURRENCY", "3"))
    PER_HOST_CONCURRENCY: int = int(os.getenv("PP_PER_HOST_CONCURRENCY", "1"))

settings = Settings()