from fastapi import APIRouter, File, HTTPException, UploadFile

from app.routers.audio_http import uploaded_file
from app.schemas.responses import BandAnalysisResponse
from app.services.acoustic_parameters import calculate_parameters_from_ir
from app.services.signal_utils import load_audio

router = APIRouter()


@router.post("/parameters", response_model=BandAnalysisResponse)   # POST /api/v1/acoustics/parameters
async def parameters(file: UploadFile = File(...)):
    with uploaded_file(file) as path:
        try:
            ir, fs = load_audio(path)
        except ValueError as e:                     # no es un audio: el pedido está mal
            raise HTTPException(status_code=422, detail=f"No es un audio válido: {e}")
    params = calculate_parameters_from_ir(ir, fs)   # todas las bandas, de una vez
    return BandAnalysisResponse(
        sample_rate=fs,
        duration=len(ir) / fs,
        center_frequencies=sorted(params["T30"]),
        parameters=params,
    )