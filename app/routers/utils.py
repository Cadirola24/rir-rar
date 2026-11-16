from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.routers.audio_http import uploaded_file
from app.schemas.utils import SchroederResponse, SmoothingMethod, SmoothingResponse, LundebyResponse
from app.services.acoustic_parameters import apply_schroeder_integral, apply_smoothing
from app.services.signal_utils import load_audio

router = APIRouter()

@router.post("/smoothing", response_model=SmoothingResponse)   # POST /api/v1/utils/smoothing
async def smoothing(
    file: UploadFile = File(...),
    method: SmoothingMethod = Form(SmoothingMethod.HILBERT),
    window_ms: float = Form(10, gt=0, le=100),
):
    ...  # load_audio (422 si no es audio), apply_smoothing y responder el JSON

@router.post("/schroeder", response_model=SchroederResponse)   # POST /api/v1/utils/schroeder
async def schroeder(file: UploadFile = File(...)):
    ...  # load_audio (422 si no es audio), apply_schroeder_integral y responder el JSON

@router.post("/lundeby", response_model=LundebyResponse)
async def lundeby(file: UploadFile) -> LundebyResponse:
    ...