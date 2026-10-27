from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.routers.audio_http import uploaded_file, wav_response
from app.services.filter import filter_single_band
from app.services.signal_utils import load_audio

router = APIRouter()


@router.post("/single-band")                        # POST /api/v1/filters/single-band
async def single_band(
    file: UploadFile = File(...),
    center_freq: float = Form(..., gt=0),
    order: int = Form(4, ge=1, le=8),
):
    with uploaded_file(file) as path:
        try:
            signal, fs = load_audio(path)
        except ValueError as e:                     # no es un audio: el pedido está mal
            raise HTTPException(status_code=422, detail=f"No es un audio válido: {e}")
    try:
        filtered = filter_single_band(signal, fs, center_freq, order)
    except ValueError as e:                         # la banda no entra en el archivo (ej. 16 kHz a 44,1 kHz)
        raise HTTPException(status_code=422, detail=f"Banda inválida para fs = {fs} Hz: {e}")
    return wav_response(filtered, fs, f"band_{center_freq:g}hz.wav")