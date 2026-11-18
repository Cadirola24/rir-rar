from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.routers.audio_http import uploaded_file
from app.schemas.utils import (
    LogScaleResponse,
    LundebyResponse,
    SchroederResponse,
    SmoothingMethod,
    SmoothingResponse,
)
from app.services.acoustic_parameters import (
    apply_lundeby,
    apply_schroeder_integral,
    apply_smoothing,
)
from app.services.signal_utils import load_audio, logarithmic_scale_conversion

router = APIRouter()


# POST /api/v1/utils/smoothing
@router.post("/smoothing", response_model=SmoothingResponse)
async def smoothing(
    file: Annotated[UploadFile, File(...)],
    method: Annotated[SmoothingMethod, Form()] = SmoothingMethod.HILBERT,
    window_ms: Annotated[float, Form(gt=0, le=100)] = 10,
):
    with uploaded_file(file) as path:
        try:
            ir, fs = load_audio(path)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"No es un audio válido: {e}") from e

    env = apply_smoothing(ir, fs, method=method.value, window_ms=window_ms)
    step = max(1, len(env) // 1000)
    env_decimated = env[::step]

    return SmoothingResponse(
        method=method,
        window_ms=window_ms,
        sample_rate=fs,
        time_step=step / fs,
        envelope=env_decimated.tolist(),
    )


# POST /api/v1/utils/schroeder
@router.post("/schroeder", response_model=SchroederResponse)
async def schroeder(file: Annotated[UploadFile, File(...)]):
    with uploaded_file(file) as path:
        try:
            ir, fs = load_audio(path)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"No es un audio válido: {e}") from e

    edc = apply_schroeder_integral(ir)
    step = max(1, len(edc) // 1000)
    edc_decimated = edc[::step]

    return SchroederResponse(
        sample_rate=fs,
        num_samples=len(ir),
        lundeby_applied=False,
        time_step=step / fs,
        edc_db=edc_decimated.tolist(),
    )


# POST /api/v1/utils/lundeby
@router.post("/lundeby", response_model=LundebyResponse)
async def lundeby(file: UploadFile = File(...)) -> LundebyResponse:  # noqa: B008
    with uploaded_file(file) as path:
        try:
            ir, fs = load_audio(path)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"No es un audio válido: {e}") from e

    try:
        index, noise_level_db = apply_lundeby(ir, fs)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return LundebyResponse(
        cutoff_index=index,
        cutoff_time=round(index / fs, 6),
        noise_level_db=noise_level_db,
    )


# POST /api/v1/utils/log-scale
@router.post("/log-scale", response_model=LogScaleResponse)
async def log_scale(
    file: Annotated[UploadFile, File(...)],
    floor_db: Annotated[float, Form(lt=0, ge=-200)] = -120.0,
):
    with uploaded_file(file) as path:
        try:
            ir, fs = load_audio(path)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"No es un audio válido: {e}") from e

    signal_db = logarithmic_scale_conversion(ir, floor_db=floor_db)

    step = max(1, len(signal_db) // 1000)
    signal_decimated = signal_db[::step]

    return LogScaleResponse(
        sample_rate=fs,
        floor_db=floor_db,
        time_step=step / fs,
        signal_db=signal_decimated.tolist(),
    )
