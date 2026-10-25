import numpy as np

def play_and_record(signal: np.ndarray, fs: int, record_duration: float) -> np.ndarray:
    """Reproduce una señal y graba simultáneamente.

    Parameters
    ----------
    signal : np.ndarray
        Senal a reproducir (1D mono o 2D estéreo).
    fs : int
        Frecuencia de muestreo en Hz.
    record_duration : float
        Duracion total de la grabacion en segundos (>= duracion de la señal).

    Returns
    -------
    np.ndarray
        La señal grabada, de largo int(record_duration * fs).

    Raises
    ------
    RuntimeError
        Si no hay dispositivo de audio disponible.
    """
    import sounddevice as sd

    total_frames = int(record_duration * fs)
    channels = 1 if signal.ndim == 1 else signal.shape[1]

    # Rellenar con ceros la señal si la duración de grabación es mayor
    if len(signal) < total_frames:
        pad_width = total_frames - len(signal)
        if signal.ndim == 1:
            signal_padded = np.pad(signal, (0, pad_width), mode='constant')
        else:
            signal_padded = np.pad(signal, ((0, pad_width), (0, 0)), mode='constant')
    else:
        signal_padded = signal[:total_frames]

    try:
        # playrec reproduce y graba de forma simultánea y bloqueante (blocking=True)
        recording = sd.playrec(signal_padded, samplerate=fs, channels=channels, blocking=True)
        return recording
    except Exception as e:
        raise RuntimeError("No hay dispositivo de audio disponible.") from e