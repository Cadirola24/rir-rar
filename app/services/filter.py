"""Servicio de filtrado por bandas de octava.

Milestone 2: Procesamiento de la respuesta al impulso.
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt

STANDARD_OCTAVE_BANDS: tuple[float, ...] = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)


def filter_all_octave_bands(
    signal: np.ndarray,
    fs: int,
    order: int = 4,
) -> dict[float, np.ndarray]:
    """Filtra una señal en todas las bandas de octava estándar debajo de Nyquist."""
    x = np.asarray(signal, dtype=float)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if x.size == 0:
        raise ValueError("La señal no puede estar vacía.")
    if fs <= 0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")

    nyquist = fs / 2.0
    filtered_bands: dict[float, np.ndarray] = {}

    for center_freq in STANDARD_OCTAVE_BANDS:
        if center_freq * np.sqrt(2.0) >= nyquist:
            continue
        filtered_bands[center_freq] = filter_single_band(x, fs, center_freq, order)

    return filtered_bands


def filter_single_band(
    signal: np.ndarray, fs: int, center_freq: float, order: int = 4
) -> np.ndarray:
    """Aplica un filtro pasabanda de una octava centrado en ``center_freq`` (IEC 61260).

    Filtro Butterworth pasabanda (``scipy.signal.butter`` con ``output='sos'``)
    con frecuencias de corte:

    - inferior: ``center_freq / sqrt(2)``
    - superior: ``center_freq * sqrt(2)``

    Aplicarlo con ``scipy.signal.sosfiltfilt`` (fase cero), importante para no
    distorsionar EDT y T60. La forma ``(b, a)`` con ``filtfilt`` es inestable en
    las bandas graves.

    Parameters
    ----------
    signal : np.ndarray
        Senal de entrada (array 1D).
    fs : int
        Frecuencia de muestreo en Hz.
    center_freq : float
        Frecuencia central de la banda de octava en Hz.
    order : int, optional
        Orden del filtro Butterworth (por defecto 4).

    Returns
    -------
    np.ndarray
        Senal filtrada (array 1D, misma longitud que ``signal``).

        Raises
    ------
    ValueError
        Si la frecuencia superior de la banda excede o iguala el limite de Nyquist (fs / 2)
        o si las frecuencias son invalidas.
    """
    f_inf = center_freq / np.sqrt(2)
    f_sup = center_freq * np.sqrt(2)
    nyquist = fs / 2.0

    # Validacion del limite de Nyquist
    if f_sup >= nyquist:
        raise ValueError(
            f"La frecuencia superior de la banda ({f_sup:.1f} Hz) "
            f"excede el limite de Nyquist ({nyquist:.1f} Hz)."
        )

    if f_inf <= 0:
        raise ValueError(f"Frecuencia central o inferior invalida: {center_freq} Hz")

    # Diseno del filtro en formato SOS (secciones de segundo orden)
    sos = butter(N=order, Wn=[f_inf, f_sup], btype="bandpass", fs=fs, output="sos")

    # Filtrado en fase cero
    filtered_signal = sosfiltfilt(sos, signal)

    return filtered_signal
