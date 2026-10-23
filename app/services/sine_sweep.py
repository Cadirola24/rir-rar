"""Servicio de generacion de sine sweep logaritmico.

Milestone 1: Generacion de senales.
"""

import numpy as np


def generate_sine_sweep_pair(
    duration: float,
    f1: float = 20.0,
    f2: float = 20000.0,
    fs: int = 44100,
) -> tuple[np.ndarray, np.ndarray]:
    """Genera un barrido senoidal logaritmico y su filtro inverso.

    El sweep es ``x(t) = sin[2*pi*f1*T / ln(f2/f1) * (exp(t*ln(f2/f1)/T) - 1)]``
    y el filtro inverso es el sweep invertido en el tiempo con correccion de
    amplitud ``A(t) = exp(-t*ln(f2/f1)/T)`` (tecnica de Farina, 2000). La
    convolucion ``sweep * inverse_filter`` debe aproximar un impulso.

    Parameters
    ----------
    duration : float
        Duracion del barrido en segundos.
    f1 : float
        Frecuencia inicial del barrido en Hz (tipicamente 20 Hz).
    f2 : float
        Frecuencia final del barrido en Hz (tipicamente 20000 Hz).
    fs : int
        Frecuencia de muestreo en Hz.

    Returns
    -------
    sweep : np.ndarray
        Senal del barrido senoidal, normalizada, de longitud ``int(duration * fs)``.
    inverse_filter : np.ndarray
        Filtro inverso correspondiente, normalizado, de la misma longitud.

    References
    ----------
    .. [1] Farina, A. (2000). "Simultaneous measurement of impulse response
       and distortion with a swept-sine technique." 108th AES Convention.
    """
    # Vector de tiempo (t) desde 0 hasta T
    num_samples = int(duration * fs)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    # Constantes de la función
    t_tot = duration
    log_ratio = np.log(f2 / f1)
    k_const = (2 * np.pi * f1 * t_tot) / log_ratio

    # Generación del Sine Sweep: x(t)
    sweep = np.sin(k_const * (np.exp(t * log_ratio / t_tot) - 1))

    # Generación del Filtro Inverso: x(T - t) * A(t)
    sweep_reversed = sweep[::-1]  # Sweep invertido en el tiempo
    env = np.exp(-t * log_ratio / t_tot)  # Envolvente de atenuación
    inverse_filter = sweep_reversed * env  # Multiplicacion por A para evitar refuerzo en graves

    return sweep, inverse_filter
