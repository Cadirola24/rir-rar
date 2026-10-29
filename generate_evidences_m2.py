import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import fftconvolve

from app.services.filter import filter_single_band
from app.services.signal_utils import (
    generate_synthetic_ir,
    get_impulse_response,
    load_audio,
)
from app.services.sine_sweep import generate_sine_sweep_pair

# Crear directorio de salida
DOCS_DIR = Path("docs/m2")
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def plot_spectrum(signal: np.ndarray, fs: int, label: str, color: str = None):
    """Calcula y grafica el espectro de magnitud en dB."""
    n = len(signal)
    fft_vals = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(n, d=1 / fs)
    magnitude_db = 20 * np.log10(np.abs(fft_vals) / np.max(np.abs(fft_vals)) + 1e-12)
    plt.plot(freqs, magnitude_db, label=label, alpha=0.8, color=color)


def process_real_ir(audio_path: str, name_tag: str, center_freq: float = 1000.0):
    """Procesa una RI real: forma de onda, espectro y decaimiento en dB."""
    if not os.path.exists(audio_path):
        print(f"⚠️  Archivo no encontrado: {audio_path}. Omitiendo {name_tag}...")
        return

    signal, fs = load_audio(audio_path)
    filtered = filter_single_band(signal, fs, center_freq=center_freq, order=4)
    t = np.arange(len(signal)) / fs

    fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=False)
    fig.suptitle(f"Análisis de RI Real ({name_tag}) - Banda {center_freq:g} Hz", fontsize=12)

    # 1. Forma de onda
    axs[0].plot(t, signal, label="Original", alpha=0.5, color="gray")
    axs[0].plot(t, filtered, label=f"Filtrada {center_freq:g} Hz", color="blue")
    axs[0].set_ylabel("Amplitud")
    axs[0].set_xlabel("Tiempo [s]")
    axs[0].legend(loc="upper right")
    axs[0].grid(True, linestyle="--", alpha=0.6)

    # 2. Espectro de frecuencia
    plt.sca(axs[1])
    plot_spectrum(signal, fs, "Original", color="gray")
    plot_spectrum(filtered, fs, f"Filtrada {center_freq:g} Hz", color="blue")
    axs[1].set_xscale("log")
    axs[1].set_xlim([20, fs / 2])
    axs[1].set_ylim([-80, 5])
    axs[1].set_ylabel("Magnitud [dB]")
    axs[1].set_xlabel("Frecuencia [Hz]")
    axs[1].legend(loc="lower left")
    axs[1].grid(True, which="both", linestyle="--", alpha=0.6)

    # 3. Curva de decaimiento en dB
    env_orig = 20 * np.log10(np.abs(signal) / np.max(np.abs(signal)) + 1e-12)
    env_filt = 20 * np.log10(np.abs(filtered) / np.max(np.abs(filtered)) + 1e-12)
    axs[2].plot(t, env_orig, label="Original dB", alpha=0.4, color="gray")
    axs[2].plot(t, env_filt, label="Filtrada dB", color="blue")
    axs[2].set_ylabel("Nivel [dB]")
    axs[2].set_xlabel("Tiempo [s]")
    axs[2].set_ylim([-80, 5])
    axs[2].legend(loc="upper right")
    axs[2].grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    output_fig = DOCS_DIR / f"ri_real_{name_tag}.png"
    plt.savefig(output_fig, dpi=150)
    plt.close()
    print(f" Gráfico guardado: {output_fig}")


def process_synthetic_deconvolution():
    """Genera RI sintética, simula sweep, deconvoluciona y valida correlación."""
    fs = 44100
    duration = 2.0
    t60_values = {500: 1.2, 1000: 1.0, 2000: 0.8}

    # 1. Generar RI Sintética
    synth_ir = generate_synthetic_ir(duration=duration, t60_values=t60_values, fs=fs)

    # 2. Generar Sweep e Inverse Filter
    sweep, inv_filter = generate_sine_sweep_pair(duration=5.0, f1=20.0, f2=20000.0, fs=fs)

    # 3. Simular grabación (convolución: sweep * RI)
    recording = fftconvolve(sweep, synth_ir, mode="full")

    # 4. Deconvolucionar
    recovered_ir = get_impulse_response(recording, inv_filter, fs=fs)

    # 5. Alinear retardo entre señales usando correlación cruzada
    cross_corr = np.correlate(synth_ir, recovered_ir, mode="full")
    delay = np.argmax(cross_corr) - (len(recovered_ir) - 1)

    if delay > 0:
        ir1 = synth_ir[delay:]
        ir2 = recovered_ir[:len(ir1)]
    elif delay < 0:
        ir1 = synth_ir[:len(recovered_ir) + delay]
        ir2 = recovered_ir[-delay:]
    else:
        ir1 = synth_ir
        ir2 = recovered_ir

    min_len = min(len(ir1), len(ir2))
    ir1 = ir1[:min_len] / np.max(np.abs(ir1[:min_len]))
    ir2 = ir2[:min_len] / np.max(np.abs(ir2[:min_len]))

    # 6. Calcular Correlación de Pearson alineada
    r = np.corrcoef(ir1, ir2)[0, 1]
    print(f"\n--- Validación RI Sintética ---")
    print(f"Retardo detectado: {delay} muestras")
    print(f"Coeficiente de correlación (r): {r:.5f}")
    if r > 0.9:
        print(" Correlación > 0.9 VERIFICADA.")
    else:
        print("❌ ALERTA: Correlación es menor a 0.9.")

    # 6. Graficar
    t = np.arange(min_len) / fs
    plt.figure(figsize=(10, 5))
    plt.plot(t, ir1, label="RI Sintética Original", alpha=0.7, color="black")
    plt.plot(t, ir2, label="RI Deconvolucionada", alpha=0.7, linestyle="--", color="crimson")
    plt.title(f"Deconvolución de RI Sintética (Correlación r = {r:.4f})")
    plt.xlabel("Tiempo [s]")
    plt.ylabel("Amplitud Normalizada")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)

    output_fig = DOCS_DIR / "ri_sintetica_deconvolucion.png"
    plt.tight_layout()
    plt.savefig(output_fig, dpi=150)
    plt.close()
    print(f" Gráfico guardado: {output_fig}")


if __name__ == "__main__":
    print("Iniciando generación de evidencia para Milestone 2...\n")

    process_real_ir("tests/data/ri_corta.wav", "corta")
    process_real_ir("tests/data/ri_larga.wav", "larga")

    process_synthetic_deconvolution()

    print("\nProceso finalizado. Revisá la carpeta docs/m2/.")