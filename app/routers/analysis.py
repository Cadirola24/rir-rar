from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.routers.audio_http import uploaded_file
from app.schemas.analysis import (
    ImpulseResponseAnalysisResponse,
    LundebySummary,
    SchroederSummary,
)
from app.services.acoustic_parameters import (
    apply_lundeby,
    apply_schroeder_integral,
    calculate_parameters_from_ir,
)
from app.services.signal_utils import load_audio

router = APIRouter()


# POST /api/v1/analysis/impulse-response
@router.post("/impulse-response", response_model=ImpulseResponseAnalysisResponse)
async def analyze_impulse_response(
    file: Annotated[UploadFile, File(...)],
):
    """Ejecuta el análisis acústico completo de una respuesta al impulso."""
    with uploaded_file(file) as path:
        try:
            ir, fs = load_audio(path)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"No es un audio válido: {e}") from e

    try:
        cutoff_idx, noise_db = apply_lundeby(ir, fs)
        edc = apply_schroeder_integral(ir)
        params = calculate_parameters_from_ir(ir, fs)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    step = max(1, len(edc) // 1000)
    edc_decimated = edc[::step]

    return ImpulseResponseAnalysisResponse(
        sample_rate=fs,
        duration=len(ir) / fs,
        lundeby=LundebySummary(
            cutoff_index=cutoff_idx,
            cutoff_time=cutoff_idx / fs,
            noise_level_db=noise_db,
        ),
        schroeder=SchroederSummary(
            time_step=step / fs,
            decay_curve=edc_decimated.tolist(),
        ),
        acoustic_parameters=params,
    )
