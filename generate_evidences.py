import os
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import fftconvolve, spectrogram

from app.services.sine_sweep import generate_sine_sweep_pair


def main() -> None:
    # Crear la carpeta docs/m1 si no existe
    os.makedirs("docs/m1", exist_ok=True)

    fs = 44100
    duration = 5.0
    f1, f2 = 20.0, 20000.0

    # 1. Generar sweep y filtro inverso desde tu servicio
    sweep, inverse = generate_sine_sweep_pair(
        duration=duration, f1=f1, f2=f2, fs=fs
    )

    # 2. Generar Espectrograma del Sine Sweep
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

    # 3. Generar Convolución (Respuesta al Impulso)
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


if __name__ == "__main__":
    main()