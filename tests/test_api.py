"""Tests para los endpoints de la API.

Cada milestone expone lo que construye:

- M0: ``/`` y ``/health`` (pasan desde el principio).
- M1: ``/api/v1/signals/pink-noise`` y ``/api/v1/signals/sine-sweep``.
- M2: ``/api/v1/signals/synthetic-ir`` y ``/api/v1/filters/single-band``.
- M3: ``/api/v1/acoustics/parameters``, ``/api/v1/utils/schroeder`` y ``/api/v1/utils/smoothing``.

Mientras un endpoint no existe responde 404, por eso sus tests estan marcados
``xfail`` sin ``raises``: fallan por assert, no por ``NotImplementedError``.
Cuando lo implementen, borren la marca de ese test.
"""

import io

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from app.main import app
from app.routers.audio_http import wav_response

client = TestClient(app)

xfail_m1 = pytest.mark.xfail(strict=False, reason="se implementa en M1")
xfail_m2 = pytest.mark.xfail(strict=False, reason="se implementa en M2")
xfail_m3 = pytest.mark.xfail(strict=False, reason="se implementa en M3")


def _wav_en_memoria(signal: np.ndarray, fs: int) -> bytes:
    buffer = io.BytesIO()
    sf.write(buffer, signal, fs, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def _ri_sintetica(fs: int = 44100, t60: float = 0.5) -> np.ndarray:
    t = np.arange(fs) / fs
    rng = np.random.default_rng(0)
    ir = rng.standard_normal(fs) * np.exp(-3 * np.log(10) / t60 * t)
    return ir / np.max(np.abs(ir)) * 0.9


# ── M0 ───────────────────────────────────────────────────────────────────────


class TestHealthEndpoint:
    """Tests para el endpoint /health."""

    def test_health_endpoint(self):
        """/health responde 200 con status 'healthy' y version."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestRootEndpoint:
    """Tests para el endpoint raiz /."""

    def test_root_returns_200(self):
        """/ responde con status 200."""
        assert client.get("/").status_code == 200

    def test_root_returns_api_info(self):
        """La raiz devuelve informacion de la API."""
        data = client.get("/").json()
        assert data["name"] == "RIR-API"
        assert "docs" in data


def test_wav_response_roundtrip():
    """wav_response (ya resuelta en el template) devuelve un WAV que se puede leer."""
    senal = np.linspace(-0.5, 0.5, 1000)
    response = wav_response(senal, 8000)
    assert response.media_type == "audio/wav"
    leida, fs = sf.read(io.BytesIO(response.body))
    assert fs == 8000
    assert np.allclose(leida, senal, atol=1e-6)


# ── M1 ───────────────────────────────────────────────────────────────────────


def test_signals_pink_noise_endpoint():
    """/api/v1/signals/pink-noise genera y devuelve un WAV valido."""
    response = client.post(
        "/api/v1/signals/pink-noise", json={"duration": 1.0, "sample_rate": 44100}
    )
    assert response.status_code == 200
    senal, fs = sf.read(io.BytesIO(response.content))
    assert fs == 44100
    assert len(senal) == 44100


def test_signals_sine_sweep_endpoint():
    """/api/v1/signals/sine-sweep devuelve el sweep o, con inverse=True, su filtro inverso."""
    pedido = {"duration": 1.0, "start_freq": 20, "end_freq": 20000, "sample_rate": 44100}
    sweep = client.post("/api/v1/signals/sine-sweep", json=pedido)
    inverso = client.post("/api/v1/signals/sine-sweep", json={**pedido, "inverse": True})
    assert sweep.status_code == 200 and inverso.status_code == 200
    s, fs = sf.read(io.BytesIO(sweep.content))
    k, _ = sf.read(io.BytesIO(inverso.content))
    assert fs == 44100
    assert len(s) == 44100
    assert not np.allclose(s[: len(k)], k[: len(s)])


def test_invalid_duration_returns_422():
    """Una duracion negativa la rechaza el schema (Pydantic) con 422."""
    response = client.post(
        "/api/v1/signals/pink-noise", json={"duration": -1.0, "sample_rate": 44100}
    )
    assert response.status_code == 422


# ── M2 ───────────────────────────────────────────────────────────────────────


def test_signals_synthetic_ir_endpoint():
    """/api/v1/signals/synthetic-ir devuelve una RI en WAV con la duracion pedida."""
    pedido = {"duration": 1.0, "t60_values": {"1000": 0.8}, "sample_rate": 44100}
    response = client.post("/api/v1/signals/synthetic-ir", json=pedido)
    assert response.status_code == 200
    senal, fs = sf.read(io.BytesIO(response.content))
    assert fs == 44100
    assert len(senal) == 44100


def test_synthetic_ir_band_above_nyquist_returns_422():
    """Si se pide una banda por encima de fs/2, devuelve 422 Unprocessable Entity."""
    response = client.post(
        "/api/v1/signals/synthetic-ir",
        json={
            "duration": 1.0,
            "t60_values": {"16000": 1.0},
            "sample_rate": 44100,
        },
    )
    assert response.status_code == 422


def test_filters_single_band_endpoint():
    """/api/v1/filters/single-band recibe un WAV y devuelve la banda filtrada."""
    fs = 44100
    ruido = np.random.default_rng(1).standard_normal(fs) * 0.5
    archivos = {"file": ("ruido.wav", _wav_en_memoria(ruido, fs), "audio/wav")}
    response = client.post(
        "/api/v1/filters/single-band", files=archivos, data={"center_freq": 1000}
    )
    assert response.status_code == 200
    filtrada, fs_out = sf.read(io.BytesIO(response.content))
    assert fs_out == fs
    assert len(filtrada) == fs


def test_invalid_file_returns_422():
    """Un archivo que no es audio devuelve 422 Unprocessable Entity."""
    archivos = {"file": ("no_es_audio.wav", b"esto no es audio", "audio/wav")}
    response = client.post(
        "/api/v1/filters/single-band", files=archivos, data={"center_freq": 1000}
    )
    assert response.status_code == 422


# ── M3 ───────────────────────────────────────────────────────────────────────


def test_acoustics_parameters_endpoint():
    """Enviar una RI a /api/v1/acoustics/parameters devuelve los parametros por banda."""
    fs = 44100
    archivos = {"file": ("ir.wav", _wav_en_memoria(_ri_sintetica(fs), fs), "audio/wav")}
    response = client.post("/api/v1/acoustics/parameters", files=archivos)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_utils_schroeder_endpoint():
    """/api/v1/utils/schroeder devuelve la curva de caida (en dB, decreciente)."""
    fs = 44100
    archivos = {"file": ("ir.wav", _wav_en_memoria(_ri_sintetica(fs), fs), "audio/wav")}
    response = client.post("/api/v1/utils/schroeder", files=archivos)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_utils_smoothing_endpoint():
    """/api/v1/utils/smoothing devuelve la envolvente de la senal."""
    fs = 44100
    archivos = {"file": ("ir.wav", _wav_en_memoria(_ri_sintetica(fs), fs), "audio/wav")}
    response = client.post("/api/v1/utils/smoothing", files=archivos)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_utils_lundeby_endpoint():
    fs = 16000
    t = np.arange(fs) / fs
    rng = np.random.default_rng(42)
    ir = np.exp(-6.9078 * t) * rng.standard_normal(fs) + 1e-4 * rng.standard_normal(fs)

    buf = io.BytesIO()
    sf.write(buf, ir, fs, format="WAV")
    buf.seek(0)

    response = client.post(
        "/api/v1/utils/lundeby",
        files={"file": ("ir_test.wav", buf, "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["cutoff_index"] < fs
    assert 0.0 <= data["cutoff_time"] < 1.0
    assert data["noise_level_db"] < 0.0


def test_utils_lundeby_invalid_file_returns_422():
    response = client.post(
        "/api/v1/utils/lundeby",
        files={"file": ("not_audio.txt", b"contenido invalido", "text/plain")},
    )
    assert response.status_code == 422


def test_filters_frequencies_endpoint():
    """/api/v1/filters/frequencies devuelve bandas estandar y filtra por Nyquist."""
    res_all = client.get("/api/v1/filters/frequencies")
    assert res_all.status_code == 200
    assert 16000.0 in res_all.json()["octave_bands"]

    res_nyquist = client.get("/api/v1/filters/frequencies?sample_rate=8000")
    assert res_nyquist.status_code == 200
    assert 4000.0 not in res_nyquist.json()["octave_bands"]

    res_invalid = client.get("/api/v1/filters/frequencies?sample_rate=0")
    assert res_invalid.status_code == 422


def test_utils_log_scale_endpoint():
    """/api/v1/utils/log-scale devuelve la amplitud normalizada en dB."""
    fs = 44100
    archivos = {"file": ("ir.wav", _wav_en_memoria(_ri_sintetica(fs), fs), "audio/wav")}
    res_ok = client.post("/api/v1/utils/log-scale", files=archivos, data={"floor_db": -100.0})
    assert res_ok.status_code == 200
    body = res_ok.json()
    assert max(body["signal_db"]) <= 0.0
    assert min(body["signal_db"]) >= -100.0

    res_bad = client.post(
        "/api/v1/utils/log-scale",
        files={"file": ("not_audio.txt", b"contenido invalido", "text/plain")},
    )
    assert res_bad.status_code == 422


def test_filters_all_bands_endpoint():
    """/api/v1/filters/band filtra todas las bandas de octava validas."""
    fs = 44100
    archivos = {"file": ("ir.wav", _wav_en_memoria(_ri_sintetica(fs), fs), "audio/wav")}
    res_ok = client.post("/api/v1/filters/band", files=archivos, data={"order": 4})
    assert res_ok.status_code == 200
    body = res_ok.json()
    assert len(body["center_frequencies"]) > 0
    assert set(body["bands"].keys()) == {str(f) for f in body["center_frequencies"]}

    res_bad = client.post(
        "/api/v1/filters/band",
        files={"file": ("not_audio.txt", b"contenido invalido", "text/plain")},
    )
    assert res_bad.status_code == 422
