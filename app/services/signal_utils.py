"""Utilidades de procesamiento de senales.

Milestone 2: Procesamiento de la respuesta al impulso.
"""

from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve

from app.services.filter import filter_single_band


def load_audio(path: str | Path) -> tuple[np.ndarray, int]:
    """Carga un archivo de audio (al menos WAV y FLAC) y retorna senal y fs.

    La senal se devuelve **mono**: si el archivo es estereo (o multicanal) se
    promedian los canales. Se convierte a ``float64`` normalizada entre -1 y 1
    independientemente de la profundidad de bits original (16, 24 o 32 bits).
    Usar ``soundfile`` (o ``scipy.io.wavfile``).

    Parameters
    ----------
    path : str | Path
        Ruta al archivo de audio a cargar.

    Returns
    -------
    signal : np.ndarray
        Senal de audio mono como array 1D ``float64`` en [-1, 1].
    fs : int
        Frecuencia de muestreo del archivo en Hz.

    Raises
    ------
    FileNotFoundError
        Si el archivo especificado no existe.
    ValueError
        Si el archivo no es un audio valido o el formato no es soportado
        (con un mensaje claro que indique el archivo y el motivo).
    """
    path_obj = Path(path)

        # 1. Verificar si el archivo existe antes de intentar leerlo
    if not path_obj.exists():
            raise FileNotFoundError(f"El archivo especificado no existe: {path}")

        # 2. Intentar leer el audio con soundfile en float64
    try:
            signal, fs = sf.read(path_obj, dtype="float64")
    except Exception as e:
            raise ValueError(f"No se pudo leer el archivo de audio '{path_obj.name}': {e}") from e

        # 3. Promediar a mono si tiene mas de 1 canal (estereo/multicanal)
    if signal.ndim > 1:
            signal = signal.mean(axis=1)

    return signal, int(fs)


def generate_synthetic_ir(duration: float, t60_values: dict[float, float], fs: int) -> np.ndarray:
    """Sintetiza una respuesta al impulso con valores de T60 conocidos por banda.

    Modelo: ``h(t) = n(t) * exp(-alpha * t)`` con ``alpha = 3 * ln(10) / T60``,
    donde ``n(t)`` es ruido blanco filtrado en la banda de octava. Se suman las
    componentes de todas las bandas y se normaliza.

    Parameters
    ----------
    duration : float
        Duracion de la respuesta al impulso en segundos.
    t60_values : dict[float, float]
        Diccionario ``{frecuencia_central_Hz: T60_segundos}``.
        Ejemplo: ``{125: 2.0, 250: 1.8, 500: 1.5, 1000: 1.2, 2000: 1.0, 4000: 0.8}``.
    fs : int
        Frecuencia de muestreo en Hz.

    Returns
    -------
    np.ndarray
        Respuesta al impulso sintetizada (array 1D de ``int(duration * fs)`` muestras).
    """
    num_samples = int(duration * fs)
    t = np.arange(num_samples) / fs
    synthetic_ir = np.zeros(num_samples, dtype=np.float64)

    # Generar el vector de ruido blanco base
    rng = np.random.default_rng()
    white_noise = rng.normal(0.0, 1.0, num_samples)

    for center_freq, t60 in t60_values.items():
        center_freq_float = float(center_freq)
        t60_float = float(t60)

        if t60_float <= 0:
            continue

        # 1. Filtrar ruido blanco en la banda de octava correspondiente
        band_noise = filter_single_band(white_noise, fs, center_freq_float)

        # 2. Normalizar la banda por su valor RMS antes de la envolvente
        rms = np.sqrt(np.mean(band_noise**2))
        if rms > 0:
            band_noise = band_noise / rms

        # 3. Aplicar envolvente de decaimiento exponencial: exp(-alpha * t)
        alpha = (3.0 * np.log(10.0)) / t60_float
        envelope = np.exp(-alpha * t)

        # 4. Sumar el aporte de la banda a la RI total
        synthetic_ir += band_noise * envelope

    # 5. Normalizar al valor pico absoluto
    max_peak = np.max(np.abs(synthetic_ir))
    if max_peak > 0:
        synthetic_ir = synthetic_ir / max_peak

    return synthetic_ir


def get_impulse_response(
    recording: np.ndarray,
    inverse_filter: np.ndarray,
    fs: int = 44100,
) -> np.ndarray:
    """Obtiene la respuesta al impulso mediante deconvolucion de un sine sweep.

    ``h(t) = y(t) * x_inv(t)``, con ``y = recording`` y ``x_inv = inverse_filter``;
    usar ``scipy.signal.fftconvolve`` (``mode='full'``), recortar para que la RI
    comience en el pico (o ligeramente antes) y normalizar respecto del pico.

    Parameters
    ----------
    recording : np.ndarray
        Senal grabada que contiene la respuesta de la sala al sweep.
    inverse_filter : np.ndarray
        Filtro inverso del sweep utilizado.

    Returns
    -------
    np.ndarray
        Respuesta al impulso estimada, normalizada.
    """
    # 1. Convolucion por FFT entre la grabacion y el filtro inverso
    raw_ir = fftconvolve(recording, inverse_filter, mode="full")

    # 2. Ubicar el pico absoluto del sonido directo
    peak_idx = int(np.argmax(np.abs(raw_ir)))

    # 3. Recortar comenzando 5 ms antes del pico
    samples_pre = int(0.005 * fs)
    start_idx = max(0, peak_idx - samples_pre)
    trimmed_ir = raw_ir[start_idx:]

    # 4. Normalizar respecto al pico maximo absoluto
    peak_val = np.max(np.abs(trimmed_ir))
    if peak_val > 0:
        trimmed_ir = trimmed_ir / peak_val

    return trimmed_ir


def logarithmic_scale_conversion(signal: np.ndarray, floor_db: float | None = None,) -> np.ndarray:
    """Convierte una senal a escala logaritmica (dB) normalizada.

    ``L = 20 * log10(|x| / max(|x|))``. Evitar ``log(0)`` (usar un ``eps`` o
    un piso, por ejemplo -120 dB).

    Parameters
    ----------
    signal : np.ndarray
        Senal de entrada (valores lineales, array 1D).

    Returns
    -------
    np.ndarray
        Senal en dB, normalizada a 0 dB en el maximo.
    """
    abs_signal = np.abs(signal)
    max_val = np.max(abs_signal)

    # Manejo de senal completamente nula
    if max_val == 0:
        if floor_db is not None:
            return np.full_like(signal, floor_db, dtype=np.float64)
        eps = np.finfo(np.float64).eps
        return np.full_like(signal, 20.0 * np.log10(eps), dtype=np.float64)

    # Normalizar respecto al maximo absoluto
    norm_signal = abs_signal / max_val

    # Evitar log(0) usando el epsilon de float64 (~2.2e-16)
    eps = np.finfo(np.float64).eps
    norm_signal = np.maximum(norm_signal, eps)

    # Convertir a escala logaritmica (dB)
    db_signal = 20.0 * np.log10(norm_signal)

    # Aplicar piso opcional si fue especificado
    if floor_db is not None:
        db_signal = np.maximum(db_signal, floor_db)

    return db_signal
