from pydantic import BaseModel, Field, PositiveFloat

class PinkNoiseRequest(BaseModel):
    duration: float = Field(gt=0, le=60)            # segundos
    sample_rate: int = Field(default=44100, ge=8000, le=192000)

class SineSweepRequest(BaseModel):
    duration: float = Field(gt=0, le=60)
    start_freq: float = Field(default=20, ge=1, le=20000)
    end_freq: float = Field(default=20000, ge=1, le=22050)
    sample_rate: int = Field(default=44100, ge=8000, le=192000)
    inverse: bool = False                           # True: devuelve el filtro inverso

class SyntheticIRRequest(BaseModel):
    duration: float = Field(gt=0, le=10)
    t60_values: dict[PositiveFloat, PositiveFloat]  # {frecuencia_central: T60}, ej. {"1000": 0.8}
    sample_rate: int = Field(default=44100, ge=8000, le=192000)