from enum import StrEnum

from pydantic import BaseModel, Field


class SmoothingMethod(StrEnum):
    HILBERT = "hilbert"
    MOVING_AVERAGE = "moving_average"


class SmoothingResponse(BaseModel):
    method: SmoothingMethod
    window_ms: float
    sample_rate: int  # la del archivo
    time_step: float  # segundos entre dos valores de envelope
    envelope: list[float]  # la envolvente, decimada


class SchroederResponse(BaseModel):
    sample_rate: int  # la del archivo
    num_samples: int  # largo de la RI original
    lundeby_applied: bool = False  # True si truncaron con apply_lundeby
    time_step: float  # segundos entre dos valores de edc_db
    edc_db: list[float]  # la curva en dB, decimada y sin -inf


class LundebyResponse(BaseModel):
    cutoff_index: int  # muestra del cruce (lo que devuelve apply_lundeby)
    cutoff_time: float  # segundos
    noise_level_db: float


class LogScaleResponse(BaseModel):
    sample_rate: int = Field(..., gt=0, description="Frecuencia de muestreo en Hz.")
    floor_db: float = Field(..., description="Piso mínimo en dB aplicado al recorte.")
    time_step: float = Field(..., gt=0, description="Paso temporal entre muestras diezmadas (s).")
    signal_db: list[float] = Field(
        ...,
        description="Amplitud normalizada en escala logarítmica (dB), diezmada.",
    )
