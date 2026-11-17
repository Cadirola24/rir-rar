from typing import Annotated

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.routers.audio_http import uploaded_file, wav_response
from app.schemas.responses import FrequenciesResponse, MultiBandFilterResponse
from app.services.filter import filter_all_octave_bands, filter_single_band
from app.services.signal_utils import load_audio

router = APIRouter()


OCTAVE_BANDS: tuple[float, ...] = (
    31.5,
    63.0,
    125.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    4000.0,
    8000.0,
    16000.0,
)

THIRD_OCTAVE_BANDS: tuple[float, ...] = (
    25.0,
    31.5,
    40.0,
    50.0,
    63.0,
    80.0,
    100.0,
    125.0,
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
    6300.0,
    8000.0,
    10000.0,
    12500.0,
    16000.0,
    20000.0,
)


# POST /api/v1/filters/frequencies
@router.get("/frequencies", response_model=FrequenciesResponse)
async def get_frequencies(
    sample_rate: int | None = Query(
        default=None,
        gt=0,
        description=(
            "Frecuencia de muestreo opcional (Hz) para filtrar bandas por debajo de Nyquist."
        ),
    ),
):
    """Devuelve las frecuencias centrales estándar de octava y tercio de octava."""
    if sample_rate is None:
        return FrequenciesResponse(
            sample_rate=None,
            octave_bands=list(OCTAVE_BANDS),
            third_octave_bands=list(THIRD_OCTAVE_BANDS),
        )

    nyquist = sample_rate / 2.0
    valid_octave = [f for f in OCTAVE_BANDS if f * np.sqrt(2.0) < nyquist]
    valid_third = [f for f in THIRD_OCTAVE_BANDS if f * (2.0 ** (1.0 / 6.0)) < nyquist]

    return FrequenciesResponse(
        sample_rate=sample_rate,
        octave_bands=valid_octave,
        third_octave_bands=valid_third,
    )


# POST /api/v1/filters/band
@router.post("/band", response_model=MultiBandFilterResponse)
async def all_bands(
    file: Annotated[UploadFile, File(...)],
    order: Annotated[int, Form(ge=1, le=8)] = 4,
):
    """Filtra el archivo de audio en todas las bandas de octava válidas."""
    with uploaded_file(file) as path:
        try:
            signal, fs = load_audio(path)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"No es un audio válido: {e}") from e

    try:
        bands_full = filter_all_octave_bands(signal, fs, order=order)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    num_samples = signal.shape[0]
    step = max(1, num_samples // 1000)
    bands_decimated = {fc: arr[::step].tolist() for fc, arr in bands_full.items()}

    return MultiBandFilterResponse(
        sample_rate=fs,
        order=order,
        center_frequencies=sorted(bands_decimated.keys()),
        time_step=step / fs,
        bands=bands_decimated,
    )


# POST /api/v1/filters/single-band
@router.post("/single-band")
async def single_band(
    file: UploadFile = File(...),  # noqa: B008
    center_freq: float = Form(..., gt=0),
    order: int = Form(4, ge=1, le=8),
):
    with uploaded_file(file) as path:
        try:
            signal, fs = load_audio(path)
        except ValueError as e:  # no es un audio: el pedido está mal
            raise HTTPException(status_code=422, detail=f"No es un audio válido: {e}") from e
    try:
        filtered = filter_single_band(signal, fs, center_freq, order)
    # la banda no entra en el archivo (ej. 16 kHz a 44,1 kHz)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Banda inválida para fs = {fs} Hz: {e}") from e
    return wav_response(filtered, fs, f"band_{center_freq:g}hz.wav")
