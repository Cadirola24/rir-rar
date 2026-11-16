"""Servicio de calculo de parametros acusticos segun ISO 3382.

Milestone 3: Producto final.
"""

import numpy as np
from scipy import signal as sp_signal


def apply_smoothing(
    signal: np.ndarray, fs: int, method: str = "hilbert", window_ms: float = 10
) -> np.ndarray:
    """Suaviza una señal y devuelve su envolvente en amplitud.

    - ``method='hilbert'`` (recomendado): envolvente de Hilbert,
      ``np.abs(scipy.signal.hilbert(signal))``. Ignora ``window_ms``.
    - ``method='moving_average'``: envolvente RMS calculada como la raíz de la
      media móvil causal de ``signal**2`` con ventana de ``window_ms`` ms
      (``max(1, int(window_ms * fs / 1000))`` muestras).
    """
    if method not in ("hilbert", "moving_average"):
        raise ValueError(f"Método inválido: '{method}'. Debe ser 'hilbert' o 'moving_average'.")
    if window_ms <= 0:
        raise ValueError("window_ms debe ser un valor positivo.")

    x = np.asarray(signal, dtype=float)
    if x.size == 0:
        return x.copy()

    if method == "hilbert":
        return np.abs(sp_signal.hilbert(x))

    m = max(1, int(window_ms * fs / 1000))
    kernel = np.ones(m, dtype=float) / m
    mean_square = np.convolve(x**2, kernel, mode="full")[: len(x)]
    return np.sqrt(np.maximum(mean_square, 0.0))


def apply_schroeder_integral(ir: np.ndarray) -> np.ndarray:
    """Calcula la integral de Schroeder (Energy Decay Curve) en dB.

    ``E[n] = sum_{k=n}^{N-1} h[k]**2`` (integracion inversa, por ejemplo con
    ``np.cumsum`` sobre la senal invertida) y ``L[n] = 10*log10(E[n] / E[0])``.

    Parameters
    ----------
    ir : np.ndarray
        Respuesta al impulso (o RI filtrada por banda, array 1D).

    Returns
    -------
    np.ndarray
        Curva de decaimiento en dB, normalizada a 0 dB en la primera muestra,
        de la misma longitud que ``ir``.

    References
    ----------
    .. [1] Schroeder, M. R. (1965). "New method of measuring reverberation
       time." JASA 37(3), 409-412.
    """
    h = np.asarray(ir, dtype=float)
    if h.size == 0:
        return h.copy()

    energy = h**2
    edc_linear = np.cumsum(energy[::-1])[::-1]
    total_energy = edc_linear[0]

    eps = np.finfo(float).eps
    edc_db = 10.0 * np.log10((edc_linear + eps) / (total_energy + eps))
    return np.maximum(edc_db, -150.0)


def linear_regression(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Calcula la regresion lineal por minimos cuadrados.

    Se recomienda implementarla a mano (formulas de minimos cuadrados) en lugar
    de ``np.polyfit``, para demostrar comprension del metodo.

    Parameters
    ----------
    x : np.ndarray
        Variable independiente (tipicamente tiempo en segundos).
    y : np.ndarray
        Variable dependiente (tipicamente curva de Schroeder en dB).

    Returns
    -------
    slope : float
        Pendiente de la recta ajustada ``m`` (dB/s en el contexto acustico).
    intercept : float
        Ordenada al origen ``b`` (dB).
    r2 : float
        Coeficiente de determinacion R^2.
    """
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)

    if x_arr.shape != y_arr.shape:
        raise ValueError("x e y deben tener la misma longitud.")
    if x_arr.size < 2:
        raise ValueError("Se necesitan al menos 2 puntos para la regresión lineal.")

    x_mean = np.mean(x_arr)
    y_mean = np.mean(y_arr)

    dx = x_arr - x_mean
    dy = y_arr - y_mean

    ss_xx = np.sum(dx**2)
    if ss_xx == 0.0:
        raise ValueError("Todos los valores de x son iguales; pendiente indefinida.")

    ss_xy = np.sum(dx * dy)
    slope = float(ss_xy / ss_xx)
    intercept = float(y_mean - slope * x_mean)

    y_hat = slope * x_arr + intercept
    ss_res = np.sum((y_arr - y_hat) ** 2)
    ss_tot = np.sum(dy**2)
    r2 = 1.0 if ss_tot == 0.0 else float(1.0 - (ss_res / ss_tot))

    return slope, intercept, r2


def calculate_parameters_from_ir(ir: np.ndarray, fs: int) -> dict[str, dict[float, float]]:
    """Calcula los parametros acusticos ISO 3382 por banda de octava.

    Parametros: EDT (0 a -10 dB), T10 (-5 a -15 dB), T20 (-5 a -25 dB),
    T30 (-5 a -35 dB), D50 (%) y C80 (dB).

    Parameters
    ----------
    ir : np.ndarray
        Respuesta al impulso (array 1D).
    fs : int
        Frecuencia de muestreo en Hz.

    Returns
    -------
    dict[str, dict[float, float]]
        ``{parametro: {frecuencia_central: valor}}``.
        Ejemplo: ``{'T30': {125: 1.5, 250: 1.3, ...}, 'EDT': {...}, 'D50': {...},
        'C80': {...}}``.

    References
    ----------
    .. [1] ISO 3382-1:2009. "Acoustics -- Measurement of room acoustic
       parameters -- Part 1: Performance spaces."
    """
    raise NotImplementedError("Implementar en Milestone 3")


def apply_lundeby(ir: np.ndarray, fs: int) -> tuple[int, float]:
    """Estima el punto de truncamiento de la RI (metodo de Lundeby).

    Parameters
    ----------
    ir : np.ndarray
        Respuesta al impulso (array 1D).
    fs : int
        Frecuencia de muestreo en Hz.

    Returns
    -------
    index : int
        Indice de la muestra donde la RI se cruza con el ruido de fondo.
    noise_level_db : float
        Nivel estimado del ruido de fondo en dB.

    Notes
    -----
    Esta funcion es **opcional** (extra).

    References
    ----------
    .. [1] Lundeby, A. et al. (1995). "Uncertainties of measurements in
       room acoustics." Acustica 81(4), 344-355.
    """
    raise NotImplementedError("Implementar en Milestone 3 (opcional)")
