"""Servicio de generacion de ruido rosa.

Milestone 1: Generacion de senales.
"""

import numpy as np


def generate_pink_noise(duration: float, fs: int) -> np.ndarray:
    """Genera una senal de ruido rosa de la duracion especificada.

    Parameters
    ----------
    duration : float
        Duracion de la senal en segundos.
    fs : int
        Frecuencia de muestreo en Hz.

    Returns
    -------
    np.ndarray
        Ruido rosa normalizado entre -1 y 1, de largo int(duration * fs).
    """
    N = int(duration * fs)
    n_gen = 16

    # 1. Salida y generadores de ruido blanco con distribución uniforme entre -1 y 1
    out = np.zeros(N)
    gens = np.random.uniform(-1.0, 1.0, n_gen)

    # Mantenemos la suma actual en una variable para no recalcular sum(gens) en cada iteración
    current_sum = np.sum(gens)

    # 2. Algoritmo de McCartney
    for n in range(1, N + 1):
        # Ruido blanco que se suma en cada muestra
        white_noise = np.random.randn()

        # Cada muestra es la suma de los generadores lentos y el ruido rápido
        out[n - 1] = current_sum + white_noise

        # 3. Encontrar el generador a renovar
        idx = (n & -n).bit_length() - 1

        # 4. Renovar el valor del generador si corresponde
        if idx < n_gen:
            current_sum -= gens[idx]  # Restar valor viejo
            new_val = np.random.randn()  # Nuevo ruido blanco
            gens[idx] = new_val  # Guardar en el arreglo
            current_sum += new_val  # Sumar nuevo valor

    # 5. Restar la media
    out = out - np.mean(out)

    # 6. Normalizar
    max_val = np.max(np.abs(out))
    if max_val > 0:
        out = out / max_val

    return out
