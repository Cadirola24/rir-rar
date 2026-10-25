import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import fftconvolve, spectrogram

from app.services.audio_io import play_and_record
from app.services.sine_sweep import generate_sine_sweep_pair


def main() -> None:
    # Crear la carpeta docs/m1 si no existe
    os.makedirs("docs/m1", exist_ok=True)

    fs = 44100
    duration = 5.0
    f1, f2 = 20.0, 20000.0

    # ---------------------------------------------------------
    # 1. Generar sweep y filtro inverso
    # ---------------------------------------------------------
    sweep, inverse = generate_sine_sweep_pair(
        duration=duration, f1=f1, f2=f2, fs=fs
    )

    # ---------------------------------------------------------
    # 2. Espectrograma del Sine Sweep
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 5))
    frequencies, times, sxx = spectrogram(
        sweep, fs=fs, nperseg=2048, noverlap=1024
    )

    plt.pcolormesh(
        times,
        frequencies,
        10 * np.log10(sxx + 1e-10),
        shading="gouraud",
        cmap="viridis",
    )
    plt.ylabel("Frecuencia (Hz)")
    plt.xlabel("Tiempo (s)")
    plt.title("Espectrograma del Sine Sweep Logarítmico (20 Hz - 20 kHz)")
    plt.yscale("log")
    plt.ylim(10, 22050)
    plt.colorbar(label="Potencia/Frecuencia (dB/Hz)")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig("docs/m1/espectrograma_sweep.png", dpi=300)
    plt.close()
    print("✔ Creado: docs/m1/espectrograma_sweep.png")

    # ---------------------------------------------------------
    # 3. Convolución Sweep * Filtro Inverso (Respuesta al Impulso)
    # ---------------------------------------------------------
    impulso = fftconvolve(sweep, inverse, mode="full")

    # Normalización a 0 dB en el pico
    impulso_norm = impulso / np.max(np.abs(impulso))
    impulso_db = 20 * np.log10(np.abs(impulso_norm) + 1e-6)

    # Vector de tiempo en milisegundos centrado en el pico
    peak_idx = np.argmax(np.abs(impulso))
    t_ms = (np.arange(len(impulso)) - peak_idx) / fs * 1000

    plt.figure(figsize=(10, 6))

    # Vista lineal del pico
    plt.subplot(2, 1, 1)
    plt.plot(t_ms, impulso_norm, color="#1f77b4")
    plt.xlim(-10, 10)
    plt.ylabel("Amplitud lineal")
    plt.title("Convolución Sweep * Filtro Inverso (Respuesta al Impulso)")
    plt.grid(True)

    # Vista logarítmica en dB
    plt.subplot(2, 1, 2)
    plt.plot(t_ms, impulso_db, color="#d62728")
    plt.xlim(-50, 50)
    plt.ylim(-80, 5)
    plt.xlabel("Tiempo respecto al pico (ms)")
    plt.ylabel("Nivel (dB)")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("docs/m1/convolucion_impulso.png", dpi=300)
    plt.close()
    print("✔ Creado: docs/m1/convolucion_impulso.png")

    # ---------------------------------------------------------
    # 4. Pruebas de Reproducción y Grabación Simultánea (Servicio 3)
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # 4. Pruebas de Reproducción y Grabación Simultánea (Servicio 3)
    # ---------------------------------------------------------
    test_duration = 3.0
    sweep_test, _ = generate_sine_sweep_pair(
        duration=test_duration, f1=100.0, f2=8000.0, fs=fs
    )

    print("🔊 Reproduciendo y grabando en hardware real...")
    recording = play_and_record(
        sweep_test, fs, record_duration=test_duration + 0.5
    )

    if recording.ndim > 1:
        recording = recording[:, 0]

    # Remoción de DC offset
    recording = recording - np.mean(recording)

    max_rec = np.max(np.abs(recording))
    recording_norm = recording / max_rec if max_rec > 1e-6 else recording
    sweep_norm = sweep_test / np.max(np.abs(sweep_test))

    t_emit = np.linspace(0, test_duration, len(sweep_test))
    t_rec = np.linspace(0, len(recording) / fs, len(recording))

    plt.figure(figsize=(10, 8))

    # 1. Vista Global: Señal Emitida vs Grabada
    plt.subplot(3, 1, 1)
    plt.plot(t_emit, sweep_norm, color="#1f77b4", linewidth=0.3, label="Emitida")
    plt.title("Visión Global - Señal Emitida (Sine Sweep)")
    plt.ylabel("Amplitud")
    plt.ylim(-1.1, 1.1)
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(t_rec, recording_norm, color="#2ca02c", linewidth=0.3, label="Grabada")
    plt.title("Visión Global - Señal Grabada (Micrófono)")
    plt.ylabel("Amplitud")
    plt.xlabel("Tiempo (s)")
    plt.ylim(-1.1, 1.1)
    plt.grid(True)

    # 2. Detalle Zoom: 20 ms alrededor de t = 0.5 s para ver la senoidal
    t_start, t_end = 0.50, 0.52  # Ventana de 20 ms
    mask_emit = (t_emit >= t_start) & (t_emit <= t_end)
    mask_rec = (t_rec >= t_start) & (t_rec <= t_end)

    plt.subplot(3, 1, 3)
    plt.plot(
        t_emit[mask_emit] * 1000,
        sweep_norm[mask_emit],
        color="#1f77b4",
        label="Emitida",
        linewidth=1.5,
    )
    plt.plot(
        t_rec[mask_rec] * 1000,
        recording_norm[mask_rec],
        color="#2ca02c",
        alpha=0.8,
        label="Grabada",
        linewidth=1.5,
    )
    plt.title(f"Detalle Zoom (Ventana de 20 ms entre {t_start*1000:.0f} ms y {t_end*1000:.0f} ms)")
    plt.xlabel("Tiempo (ms)")
    plt.ylabel("Amplitud")
    plt.legend(loc="upper right")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("docs/m1/prueba_grabacion.png", dpi=300)
    plt.close()
    print("✔ Creado: docs/m1/prueba_grabacion.png")


if __name__ == "__main__":
    main()
