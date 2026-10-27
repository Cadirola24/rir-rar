from fastapi import APIRouter, HTTPException

from app.routers.audio_http import wav_response
from app.schemas.signals import PinkNoiseRequest, SineSweepRequest, SyntheticIRRequest
from app.services.pink_noise import generate_pink_noise
from app.services.sine_sweep import generate_sine_sweep_pair
from app.services.signal_utils import generate_synthetic_ir

router = APIRouter()


@router.post("/pink-noise")
async def pink_noise(req: PinkNoiseRequest):
    audio = generate_pink_noise(req.duration, req.sample_rate)
    return wav_response(audio, req.sample_rate, "pink_noise.wav")


@router.post("/sine-sweep")
async def sine_sweep(req: SineSweepRequest):
    if req.start_freq >= req.end_freq:
        raise HTTPException(
            status_code=400,
            detail="start_freq tiene que ser menor que end_freq",
        )

    sweep, inverse_filter = generate_sine_sweep_pair(
        req.duration, req.start_freq, req.end_freq, req.sample_rate
    )

    chosen_signal = inverse_filter if req.inverse else sweep
    filename = "sine_sweep_inverse.wav" if req.inverse else "sine_sweep.wav"

    return wav_response(chosen_signal, req.sample_rate, filename)


@router.post("/synthetic-ir")
async def synthetic_ir(req: SyntheticIRRequest):
    signal, fs = generate_synthetic_ir(req.duration, req.t60_values, req.sample_rate)
    return wav_response(signal, fs, "synthetic_ir.wav")