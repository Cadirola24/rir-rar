"""Servicio de calculo de parametros acusticos segun ISO 3382.

Milestone 3: Producto final.
"""

import numpy as np
from scipy import signal as sp_signal

from app.services.filter import filter_single_band

OCTAVE_BANDS: tuple[float, ...] = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)

# (nombre_parametro, inicio_db, fin_db, rango_dinamico_minimo_db)
RT_SPECS: tuple[tuple[str, float, float, float], ...] = (
    ("EDT", 0.0, -10.0, 20.0),
    ("T10", -5.0, -15.0, 25.0),
    ("T20", -5.0, -25.0, 35.0),
    ("T30", -5.0, -35.0, 45.0),
)


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
    if x.ndim > 1:
        x = x.mean(axis=1)
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
    if h.ndim > 1:
        h = h.mean(axis=1)
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


def calculate_parameters_from_ir(
    ir: np.ndarray,
    fs: int,
) -> dict[str, dict[float, float | None]]:
    """Calcula los parametros acusticos ISO 3382 por banda de octava.

    Parametros calculados por banda (125 Hz a 4000 Hz, omitiendo bandas por
    encima de Nyquist): EDT (0 a -10 dB), T10 (-5 a -15 dB), T20 (-5 a -25 dB),
    T30 (-5 a -35 dB), D50 (%) y C80 (dB).

    Parameters
    ----------
    ir : np.ndarray
        Respuesta al impulso de banda ancha (array 1D).
    fs : int
        Frecuencia de muestreo en Hz.

    Returns
    -------
    dict[str, dict[float, float | None]]
        Diccionario anidado ``{parametro: {frecuencia_central: valor}}``.
        Si una banda no cuenta con rango dinamico suficiente para el tramo de
        regresion de un tiempo de reverberacion, su valor sera ``None``.

    Raises
    ------
    ValueError
        Si ``ir`` esta vacia o ``fs`` no es positiva.

    References
    ----------
    .. [1] ISO 3382-1:2009. "Acoustics -- Measurement of room acoustic
       parameters -- Part 1: Performance spaces."
    """
    signal = np.asarray(ir, dtype=float)
    if signal.ndim > 1:
        signal = signal.mean(axis=1)
    if signal.size == 0:
        raise ValueError("La respuesta al impulso no puede estar vacia.")
    if fs <= 0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")

    results: dict[str, dict[float, float | None]] = {
        "EDT": {},
        "T10": {},
        "T20": {},
        "T30": {},
        "D50": {},
        "C80": {},
    }

    # 5 ms de silencio inicial para evitar distorsion de borde de sosfiltfilt
    # cuando la RI arranca directamente en el sonido directo
    pre_pad = np.zeros(int(0.005 * fs), dtype=float)
    ir_padded = np.concatenate([pre_pad, signal])
    nyquist = fs / 2.0
    eps = np.finfo(float).eps

    for center_freq in OCTAVE_BANDS:
        # Omitir bandas cuya frecuencia de corte superior alcance o supere Nyquist
        if center_freq * np.sqrt(2.0) >= nyquist:
            continue

        try:
            band = filter_single_band(ir_padded, fs, center_freq)
        except ValueError:
            continue

        # Alinear al pico del sonido directo de la banda filtrada
        n0 = int(np.argmax(np.abs(band)))
        band_decay = band[n0:]
        energy = band_decay**2
        total_energy = float(np.sum(energy))

        if total_energy <= 0.0:
            for key in results:
                results[key][center_freq] = None
            continue

        # --- D50 (%) y C80 (dB) sobre la energia lineal ---
        n50 = int(np.floor(0.050 * fs))
        e50 = float(np.sum(energy[:n50]))
        results["D50"][center_freq] = float((e50 / total_energy) * 100.0)

        n80 = int(np.floor(0.080 * fs))
        e80_early = float(np.sum(energy[:n80]))
        e80_late = float(np.sum(energy[n80:]))
        results["C80"][center_freq] = float(
            10.0 * np.log10(max(e80_early, eps) / max(e80_late, eps))
        )

        # --- Rango dinamico (pico en ventana de 10 ms vs. ruido en ultimo 10%) ---
        win_10ms = max(1, int(0.010 * fs))
        if len(energy) >= win_10ms:
            kernel = np.ones(win_10ms, dtype=float) / win_10ms
            peak_power = float(np.max(np.convolve(energy, kernel, mode="valid")))
        else:
            peak_power = float(np.max(energy))

        tail_idx = int(0.9 * len(energy))
        noise_tail = energy[tail_idx:] if tail_idx < len(energy) else energy[-1:]
        noise_power = float(np.mean(noise_tail))
        dynamic_range_db = 10.0 * np.log10(max(peak_power, eps) / max(noise_power, eps))

        # --- Integral de Schroeder y regresion lineal por tramo ---
        edc = apply_schroeder_integral(band_decay)
        t = np.arange(len(edc), dtype=float) / fs

        for param_name, start_db, end_db, min_dr in RT_SPECS:
            if dynamic_range_db < min_dr:
                results[param_name][center_freq] = None
                continue

            mask = (edc <= start_db) & (edc >= end_db)
            if np.sum(mask) < 2:
                results[param_name][center_freq] = None
                continue

            slope, _intercept, _r2 = linear_regression(t[mask], edc[mask])
            if slope >= 0.0:
                results[param_name][center_freq] = None
            else:
                results[param_name][center_freq] = float(-60.0 / slope)

    return results


def apply_lundeby(ir: np.ndarray, fs: int) -> tuple[int, float]:
    """Estima el punto de truncamiento de la RI (metodo de Lundeby).

    Divide la energia de la respuesta al impulso en bloques cortos (20 ms),
    estima el piso de ruido de fondo y ajusta iterativamente una recta sobre
    el decaimiento principal para hallar la interseccion con el ruido.

    Parameters
    ----------
    ir : np.ndarray
        Respuesta al impulso (o RI filtrada por banda, array 1D).
    fs : int
        Frecuencia de muestreo en Hz.

    Returns
    -------
    index : int
        Indice de la muestra donde la caida de la RI se cruza con el ruido
        de fondo.
    noise_level_db : float
        Nivel estimado del ruido de fondo en dB respecto de la potencia pico
        en bloques de 20 ms.

    Raises
    ------
    ValueError
        Si ``ir`` esta vacia o ``fs`` no es positiva.

    References
    ----------
    .. [1] Lundeby, A., Vigran, T. E., Bietz, H. y Vorlander, M. (1995).
       "Uncertainties of measurements in room acoustics." Acustica, 81(4),
       344-355.
    """
    signal = np.asarray(ir, dtype=float)
    if signal.ndim > 1:
        signal = signal.mean(axis=1)
    if signal.size == 0:
        raise ValueError("La respuesta al impulso no puede estar vacia.")
    if fs <= 0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")

    energy = signal**2
    eps = np.finfo(float).eps
    n_samples = len(energy)

    # 1. Promediar la energia en intervalos cortos de 20 ms (rango 10-30 ms)
    win_samples = max(1, int(round(0.020 * fs)))
    num_blocks = n_samples // win_samples

    if num_blocks < 4:
        tail_power = float(np.mean(energy[int(0.9 * n_samples) :]))
        peak_power = max(float(np.max(energy)), eps)
        noise_db = float(10.0 * np.log10(max(tail_power, eps) / peak_power))
        return n_samples - 1, noise_db

    trimmed = energy[: num_blocks * win_samples]
    block_power = np.mean(trimmed.reshape(num_blocks, win_samples), axis=1)
    block_times = ((np.arange(num_blocks, dtype=float) + 0.5) * win_samples) / fs

    peak_block = int(np.argmax(block_power))
    ref_power = max(float(block_power[peak_block]), eps)
    block_db = 10.0 * np.log10(np.maximum(block_power, eps) / ref_power)

    # 2. Estimar el ruido de fondo inicial con el ultimo 10% de la RI en lineal
    tail_start = int(0.9 * n_samples)
    noise_power = float(np.mean(energy[tail_start:]))
    noise_level_db = float(10.0 * np.log10(max(noise_power, eps) / ref_power))

    # Si el rango dinamico es menor a 10 dB no hay tramo valido para ajustar recta
    if noise_level_db >= -10.0:
        return n_samples - 1, noise_level_db

    cross_sample = n_samples - 1
    max_iterations = 10

    for _ in range(max_iterations):
        # 3. Ajustar recta desde el maximo hasta 10 dB por encima del ruido
        decay_blocks = block_db[peak_block:]
        below_thresh = np.where(decay_blocks < noise_level_db + 10.0)[0]
        end_rel = int(below_thresh[0]) if below_thresh.size > 0 else len(decay_blocks)

        if end_rel >= 2:
            x_fit = block_times[peak_block : peak_block + end_rel]
            y_fit = block_db[peak_block : peak_block + end_rel]
        else:
            mask = (np.arange(num_blocks) >= peak_block) & (block_db >= noise_level_db + 10.0)
            if np.sum(mask) < 2:
                break
            x_fit = block_times[mask]
            y_fit = block_db[mask]

        slope, intercept, _r2 = linear_regression(x_fit, y_fit)
        if slope >= 0.0:
            break

        # 4. Calcular donde cruza esa recta el nivel del ruido
        cross_time = (noise_level_db - intercept) / slope
        new_cross_sample = int(np.clip(round(cross_time * fs), 0, n_samples - 1))

        # 5. Reestimar el ruido a partir de un margen posterior al cruce e iterar
        margin_samples = max(win_samples, int(round(abs(5.0 / slope) * fs)))
        noise_start = new_cross_sample + margin_samples
        min_tail = max(win_samples, int(0.05 * n_samples))
        if noise_start > n_samples - min_tail:
            noise_start = max(0, n_samples - min_tail)

        noise_power = float(np.mean(energy[noise_start:]))
        noise_level_db = float(10.0 * np.log10(max(noise_power, eps) / ref_power))

        if abs(new_cross_sample - cross_sample) <= win_samples:
            cross_sample = new_cross_sample
            break

        cross_sample = new_cross_sample

    return int(cross_sample), float(noise_level_db)
