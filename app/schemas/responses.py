from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class BandAnalysisResponse(BaseModel):
    sample_rate: int
    duration: float  # segundos
    center_frequencies: list[float]
    parameters: dict[str, dict[float, float | None]]
    # {"T30": {125.0: 1.52, 250.0: 1.31, ...}, "EDT": {...}, "D50": {...}, "C80": {...}}


class FrequenciesResponse(BaseModel):
    sample_rate: int | None = Field(
        default=None,
        description="Frecuencia de muestreo de referencia en Hz, si se especificó.",
    )
    octave_bands: list[float] = Field(
        ...,
        description="Frecuencias centrales estándar de bandas de octava en Hz.",
    )
    third_octave_bands: list[float] = Field(
        ...,
        description="Frecuencias centrales estándar de bandas de tercio de octava en Hz.",
    )
