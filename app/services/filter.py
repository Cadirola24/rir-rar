"""Servicio de filtrado por bandas de octava.

Milestone 2: Procesamiento de la respuesta al impulso.
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt

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
            f"La frecuencia superior de la banda ({f_sup:.1f} Hz) excede el limite de Nyquist ({nyquist:.1f} Hz)."
        )

    if f_inf <= 0:
        raise ValueError(f"Frecuencia central o inferior invalida: {center_freq} Hz")

    # Diseno del filtro en formato SOS (secciones de segundo orden)
    sos = butter(N=order, Wn=[f_inf, f_sup], btype="bandpass", fs=fs, output="sos")

    # Filtrado en fase cero
    filtered_signal = sosfiltfilt(sos, signal)

    return filtered_signal