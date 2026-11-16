from pydantic import BaseModel, Field


class LundebySummary(BaseModel):
    cutoff_index: int = Field(..., ge=0, description="Índice de muestra del cruce con ruido.")
    cutoff_time: float = Field(..., ge=0.0, description="Tiempo de corte en segundos.")
    noise_level_db: float = Field(..., description="Nivel del piso de ruido estimado (dB).")


class SchroederSummary(BaseModel):
    time_step: float = Field(..., gt=0, description="Paso temporal entre muestras diezmadas (s).")
    decay_curve: list[float] = Field(
        ...,
        description="Curva de decaimiento energético de Schroeder (dB), diezmada.",
    )


class ImpulseResponseAnalysisResponse(BaseModel):
    sample_rate: int = Field(..., gt=0, description="Frecuencia de muestreo en Hz.")
    duration: float = Field(..., gt=0, description="Duración total de la señal en segundos.")
    lundeby: LundebySummary = Field(..., description="Detección de corte por ruido de Lundeby.")
    schroeder: SchroederSummary = Field(
        ...,
        description="Curva de decaimiento global de Schroeder.",
    )
    acoustic_parameters: dict[str, dict[float, float | None]] = Field(
        ...,
        description="Parámetros acústicos ISO 3382-1 por banda de octava.",
    )
