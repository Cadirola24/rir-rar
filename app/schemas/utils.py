from enum import Enum

from pydantic import BaseModel


class SmoothingMethod(str, Enum):
    HILBERT = "hilbert"
    MOVING_AVERAGE = "moving_average"


class SmoothingResponse(BaseModel):
    method: SmoothingMethod
    window_ms: float
    sample_rate: int                                # la del archivo
    time_step: float                                # segundos entre dos valores de envelope
    envelope: list[float]                           # la envolvente, decimada

class SchroederResponse(BaseModel):
    sample_rate: int                                # la del archivo
    num_samples: int                                # largo de la RI original
    lundeby_applied: bool = False                   # True si truncaron con apply_lundeby
    time_step: float                                # segundos entre dos valores de edc_db
    edc_db: list[float]                             # la curva en dB, decimada y sin -inf

class LundebyResponse(BaseModel):
    cutoff_index: int                               # muestra del cruce (lo que devuelve apply_lundeby)
    cutoff_time: float                              # segundos
    noise_level_db: float