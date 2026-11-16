from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class BandAnalysisResponse(BaseModel):
    sample_rate: int
    duration: float                                 # segundos
    center_frequencies: list[float]
    parameters: dict[str, dict[float, float | None]]
    # {"T30": {125.0: 1.52, 250.0: 1.31, ...}, "EDT": {...}, "D50": {...}, "C80": {...}}
