from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from app.services.acoustic_parameters import (
    apply_schroeder_integral,
    apply_smoothing,
    linear_regression,
)
from app.services.signal_utils import filter_single_band, load_audio

# ==============================================================================
# CONFIGURACIÓN DE RUTAS Y ESTILO
# ==============================================================================
OUT_DIR = Path("docs/m3")
OUT_DIR.mkdir(parents=True, exist_ok=True)

RI_REAL_PATH = Path(r"C:\Users\valec\OneDrive\Escritorio\ri_larga.wav")
RI_SINT_PATH = Path(r"C:\Users\valec\OneDrive\Escritorio\synthetic_ir.wav")

plt.rcParams.update(
    {
        "font.size": 10.5,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "legend.fontsize": 9.5,
        "figure.dpi": 160,
    }
)

BANDS = [125, 250, 500, 1000, 2000, 4000]
X_IDX = np.arange(len(BANDS))

# ==============================================================================
# DATOS DE VALIDACIÓN (RIR-API vs. REW vs. API de Cátedra)
# ==============================================================================
# 1. RI Real (ri_larga.wav)
DATA_REAL = {
    "EDT": {
        "api": [1.224, 1.471, 1.540, 1.510, 1.124, 0.528],
        "rew": [1.140, 1.496, 1.602, 1.516, 1.135, 0.535],
        "ref": [1.145, 1.420, 1.657, 1.560, 1.176, 0.610],
    },
    "T20": {
        "api": [1.535, 1.533, 1.762, 1.584, 1.123, 0.599],
        "rew": [1.428, 1.519, 1.714, 1.581, 1.177, 0.638],
        "ref": [1.064, 1.306, 1.587, 1.533, 1.108, 0.578],
    },
    "T30": {
        "api": [1.591, 1.594, 1.787, 1.631, 1.224, 0.658],
        "rew": [1.549, 1.605, 1.766, 1.633, 1.308, 0.710],
        "ref": [1.158, 1.428, 1.678, 1.581, 1.186, 0.620],
    },
    "C80": {
        "api": [2.72, 1.61, -0.25, 0.13, 2.69, 9.03],
        "rew": [2.36, 1.19, -0.20, 0.34, 2.81, 9.44],
    },
}

# 2. RI Sintética (synthetic_ir.wav, T60 nominal = 1.50 s)
DATA_SINT = {
    "EDT": {
        "api": [1.676, 1.326, 1.696, 1.641, 1.345, 1.455],
        "rew": [1.241, 1.352, 1.711, 1.585, 1.363, 1.458],
        "ref": [1.535, 1.480, 1.511, 1.501, 1.496, 1.495],
    },
    "T20": {
        "api": [1.693, 1.589, 1.425, 1.471, 1.542, 1.496],
        "rew": [1.651, 1.594, 1.440, 1.483, 1.526, 1.492],
        "ref": [1.597, 1.558, 1.461, 1.482, 1.518, 1.485],
    },
    "T30": {
        "api": [1.566, 1.501, 1.476, 1.485, 1.524, 1.513],
        "rew": [1.615, 1.505, 1.472, 1.485, 1.515, 1.512],
        "ref": [1.578, 1.490, 1.499, 1.495, 1.508, 1.502],
    },
    "C80": {
        "api": [2.27, -0.05, -1.49, 0.31, 0.59, -0.10],
        "rew": [-0.35, 0.78, 0.29, 0.71, 0.18, 0.27],
    },
}


# ==============================================================================
# GRÁFICA 0: Respuesta al impulso y envolventes de suavizado (1000 Hz)
# ==============================================================================
def plot_envelope_comparison() -> None:
    if not RI_REAL_PATH.exists():
        print(f"[AVISO] No se encontró {RI_REAL_PATH}. Omitiendo Gráfica 0.")
        return

    ir, fs = load_audio(RI_REAL_PATH)
    ir_1k = filter_single_band(ir, fs, center_freq=1000.0)

    peak = np.max(np.abs(ir_1k))
    ir_norm = ir_1k / peak

    env_hilbert = apply_smoothing(ir_norm, fs, method="hilbert", window_ms=20.0)
    env_ma = apply_smoothing(ir_norm, fs, method="moving_average", window_ms=20.0)

    t = np.arange(len(ir_norm)) / fs
    mask = t <= 0.60

    fig, ax = plt.subplots(figsize=(9.5, 4.5))
    ax.plot(t[mask], ir_norm[mask], color="#cbd5e0", lw=0.8, label="RI filtrada (1000 Hz)")
    ax.plot(t[mask], env_hilbert[mask], color="#2b6cb0", lw=1.6, label="Envolvente Hilbert")
    ax.plot(
        t[mask],
        env_ma[mask],
        color="#dd6b20",
        lw=1.6,
        ls="--",
        label="Envolvente Media Móvil (20 ms)",
    )

    ax.set_xlim(0, 0.60)
    ax.set_ylim(-1.05, 1.05)
    ax.set_title("0 · Respuesta al impulso y envolventes de suavizado (1000 Hz)", fontweight="bold")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Amplitud normalizada")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "0_envolvente_suavizado.png")
    plt.close(fig)


# ==============================================================================
# GRÁFICA 1: Curva de decaimiento (Schroeder + regresiones en 1000 Hz)
# ==============================================================================
def plot_schroeder_curve() -> None:
    if not RI_REAL_PATH.exists():
        print(f"[AVISO] No se encontró {RI_REAL_PATH}. Omitiendo Gráfica 1.")
        return

    ir, fs = load_audio(RI_REAL_PATH)
    ir_1k = filter_single_band(ir, fs, center_freq=1000.0)
    edc = apply_schroeder_integral(ir_1k)
    t = np.arange(len(edc)) / fs
    t_max = float(t[-1])

    def fit_range(db_start: float, db_end: float) -> tuple[float, float, float, int, int]:
        idx_start = int(np.argmax(edc <= db_start))
        idx_end = int(np.argmax(edc <= db_end))
        slope, intercept, _ = linear_regression(
            t[idx_start : idx_end + 1], edc[idx_start : idx_end + 1]
        )
        return slope, intercept, -60.0 / slope, idx_start, idx_end

    m_edt, b_edt, edt_val, i0_edt, i1_edt = fit_range(0.0, -10.0)
    m_t20, b_t20, t20_val, i0_t20, i1_t20 = fit_range(-5.0, -25.0)
    m_t30, b_t30, t30_val, i0_t30, i1_t30 = fit_range(-5.0, -35.0)

    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.plot(t, edc, color="#1a202c", lw=2.0, label="Schroeder [dB]")

    t_line = np.linspace(0, t_max, 400)
    ax.plot(
        t_line, m_t30 * t_line + b_t30, "--", color="#2b6cb0", lw=1.6, label="T30 (-5 a -35 dB)"
    )
    ax.plot(
        t_line, m_t20 * t_line + b_t20, "--", color="#dd6b20", lw=1.6, label="T20 (-5 a -25 dB)"
    )
    ax.plot(t_line, m_edt * t_line + b_edt, "--", color="#2f855a", lw=1.6, label="EDT (0 a -10 dB)")

    ax.scatter([t[i0_edt], t[i1_edt]], [edc[i0_edt], edc[i1_edt]], color="#2f855a", s=36, zorder=5)
    ax.scatter([t[i0_t20], t[i1_t20]], [edc[i0_t20], edc[i1_t20]], color="#dd6b20", s=36, zorder=5)
    ax.scatter([t[i1_t30]], [edc[i1_t30]], color="#2b6cb0", s=36, zorder=5)

    levels = [
        (0, "0 dB", "#2f855a"),
        (-5, "-5 dB", "#4a5568"),
        (-10, "-10 dB", "#2f855a"),
        (-25, "-25 dB", "#dd6b20"),
        (-35, "-35 dB", "#2b6cb0"),
    ]
    for lvl, lbl, col in levels:
        ax.axhline(lvl, color="#718096", ls=":", lw=0.9)
        ax.text(0.02, lvl + 1.0, lbl, ha="left", fontsize=8.5, color=col, fontweight="bold")

    ax.set_xlim(0, t_max)
    ax.set_ylim(-70, 4)
    ax.set_title(
        "1 · Curva de decaimiento de Schroeder y regresiones (RI Real · 1000 Hz)", fontweight="bold"
    )
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Nivel [dB]")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")
    ax.text(
        0.985,
        0.05,
        f"EDT = {edt_val:.2f} s   T20 = {t20_val:.2f} s   T30 = {t30_val:.2f} s",
        transform=ax.transAxes,
        ha="right",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cbd5e0"},
    )
    fig.tight_layout()
    fig.savefig(OUT_DIR / "1_curva_schroeder.png")
    plt.close(fig)


# ==============================================================================
# GRÁFICA 2: Banco de filtros de octava (IEC 61260)
# ==============================================================================
def plot_filterbank() -> None:
    fs_filt = 48000
    n_imp = 32768
    imp = np.zeros(n_imp)
    imp[n_imp // 2] = 1.0
    freqs_fft = np.fft.rfftfreq(n_imp, d=1.0 / fs_filt)
    bands_all = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]

    fig, ax = plt.subplots(figsize=(9.5, 4.5))
    for fc in bands_all:
        y_band = filter_single_band(imp, fs_filt, center_freq=float(fc))
        mag_db = 20.0 * np.log10(np.maximum(np.abs(np.fft.rfft(y_band)), 1e-12))
        ax.semilogx(freqs_fft, mag_db, lw=1.4, label=f"{fc:g} Hz")

    ax.axhline(-3.0, color="#c53030", ls="--", lw=1.0)
    ax.text(22, -2.0, "-3 dB", color="#c53030", fontsize=9)
    ax.set_xlim(20, 20000)
    ax.set_ylim(-60, 5)
    ax.set_xticks(bands_all)
    ax.set_xticklabels([f"{b:g}" for b in bands_all])
    ax.set_title(
        "2 · Respuesta en frecuencia del banco de filtros de octava (IEC 61260)", fontweight="bold"
    )
    ax.set_xlabel("Frecuencia [Hz]")
    ax.set_ylabel("Magnitud [dB]")
    ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "2_banco_filtros.png")
    plt.close(fig)


# ==============================================================================
# GRÁFICAS 3A–3D: Validación triple por parámetro (RI Real + RI Sintética)
# ==============================================================================
def plot_triple_validation_all_parameters() -> None:
    specs = [
        ("EDT", "Early Decay Time (EDT)", "s", 0.10, None, "3a_validacion_triple_edt.png"),
        ("T20", "Tiempo de Reverberación T20", "s", 0.10, 1.50, "3b_validacion_triple_t20.png"),
        ("T30", "Tiempo de Reverberación T30", "s", 0.10, 1.50, "3c_validacion_triple_t30.png"),
        ("C80", "Claridad Musical C80", "dB", 1.0, None, "3d_validacion_triple_c80.png"),
    ]

    for key, title, unit, tol, nominal_sint, filename in specs:
        fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), sharey=True)
        datasets = [
            ("RI Real (ri_larga.wav)", DATA_REAL[key], None),
            ("RI Sintética (synthetic_ir.wav · T60 = 1.50 s)", DATA_SINT[key], nominal_sint),
        ]
        tol_label = "±10%" if unit == "s" else "±1.0 dB"

        all_vals: list[float] = []
        for d_sub in (DATA_REAL[key], DATA_SINT[key]):
            for series in d_sub.values():
                all_vals.extend(series)

        y_min = min(0.0, min(all_vals))
        y_max = max(all_vals)
        y_span = max(y_max - y_min, 1.0)

        for ax, (subtitle, d_param, nominal) in zip(axes, datasets, strict=True):
            rew_vals = np.array(d_param["rew"])
            tol_rew = (
                [min(tol * abs(v), 0.5) for v in rew_vals] if unit == "s" else [tol] * len(rew_vals)
            )

            if "ref" in d_param:
                w = 0.26
                ax.bar(X_IDX - w, d_param["api"], w, label="RIR-API (nuestra)", color="#2b6cb0")
                ax.bar(
                    X_IDX,
                    d_param["rew"],
                    w,
                    yerr=tol_rew,
                    capsize=3.5,
                    label=f"REW (Ref. + tol. {tol_label})",
                    color="#4a5568",
                    error_kw={"ecolor": "#1a202c", "lw": 1.1},
                )
                ax.bar(
                    X_IDX + w, d_param["ref"], w, label="API Cátedra (c/ Lundeby)", color="#38a169"
                )
                api_x = X_IDX - w
            else:
                w = 0.34
                ax.bar(X_IDX - w / 2, d_param["api"], w, label="RIR-API (nuestra)", color="#2b6cb0")
                ax.bar(
                    X_IDX + w / 2,
                    d_param["rew"],
                    w,
                    yerr=tol_rew,
                    capsize=4.0,
                    label=f"REW (Ref. + tol. {tol_label})",
                    color="#4a5568",
                    error_kw={"ecolor": "#1a202c", "lw": 1.1},
                )
                api_x = X_IDX - w / 2

            if nominal is not None:
                ax.axhline(
                    nominal,
                    color="#d69e2e",
                    ls="--",
                    lw=1.3,
                    label=f"Valor nominal ({nominal:.2f} s)",
                )

            if unit == "dB":
                ax.axhline(0, color="#4a5568", lw=0.9)

            offset = 0.025 * y_span
            for i, v in enumerate(d_param["api"]):
                va = "bottom" if v >= 0 else "top"
                y_pos = v + offset if v >= 0 else v - offset
                ax.text(
                    api_x[i],
                    y_pos,
                    f"{v:.2f}",
                    ha="center",
                    va=va,
                    fontsize=7.8,
                    color="#2b6cb0",
                    fontweight="bold",
                )

            ax.set_xticks(X_IDX)
            ax.set_xticklabels([str(b) for b in BANDS])
            ax.set_title(subtitle, fontweight="bold")
            ax.set_xlabel("Frecuencia central [Hz]")
            ax.grid(True, axis="y", alpha=0.25)

        axes[0].set_ylabel(f"{key} [{unit}]")
        if unit == "dB":
            axes[0].set_ylim(y_min - 1.5, y_max + 2.2)
        else:
            axes[0].set_ylim(0, y_max * 1.28)

        axes[1].legend(loc="upper right")
        fig.suptitle(
            f"Validación de {title} por banda: RIR-API vs. REW vs. API de Cátedra",
            fontsize=13.5,
            fontweight="bold",
        )
        fig.tight_layout()
        fig.savefig(OUT_DIR / filename)
        plt.close(fig)


# ==============================================================================
# GRÁFICA 4: Panel completo de parámetros (EDT, T20, T30 y C80) - RI Real
# ==============================================================================
def plot_all_parameters_panel() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.2))
    specs = [
        (axes[0, 0], "EDT", "Early Decay Time (EDT) [s]", "s", 0.10),
        (axes[0, 1], "T20", "Tiempo de Reverberación T20 [s]", "s", 0.10),
        (axes[1, 0], "T30", "Tiempo de Reverberación T30 [s]", "s", 0.10),
        (axes[1, 1], "C80", "Claridad Musical C80 [dB]", "dB", 1.0),
    ]

    for ax, key, title, unit, tol in specs:
        d = DATA_REAL[key]
        rew_vals = np.array(d["rew"])
        band_tol = rew_vals * tol if unit == "s" else np.full_like(rew_vals, tol)

        ax.fill_between(
            BANDS,
            rew_vals - band_tol,
            rew_vals + band_tol,
            color="#cbd5e0",
            alpha=0.45,
            label=f"Tolerancia REW ({'±10%' if unit == 's' else '±1 dB'})",
        )
        ax.plot(
            BANDS, d["api"], "o-", color="#2b6cb0", lw=2.0, markersize=6, label="RIR-API (nuestra)"
        )
        ax.plot(
            BANDS,
            d["rew"],
            "s--",
            color="#2d3748",
            lw=1.7,
            markersize=5.5,
            label="REW (Referencia)",
        )
        if "ref" in d:
            ax.plot(
                BANDS, d["ref"], "^:", color="#38a169", lw=1.7, markersize=6, label="API Cátedra"
            )

        ax.set_xscale("log")
        ax.set_xticks(BANDS)
        ax.set_xticklabels([str(b) for b in BANDS])
        ax.minorticks_off()
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Frecuencia central [Hz]")
        ax.set_ylabel(f"{key} [{unit}]")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best")

    fig.suptitle(
        "4 · Comparación integral por banda (RI Real): RIR-API vs. REW vs. API de Cátedra",
        fontsize=13.5,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(OUT_DIR / "4_comparacion_integral_parametros.png")
    plt.close(fig)


# ==============================================================================
# GRÁFICA 5: Mapa de diferencias relativas/absolutas respecto a REW
# ==============================================================================
def plot_error_analysis() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))

    ax0 = axes[0]
    for key, color, marker in [
        ("EDT", "#805ad5", "o"),
        ("T20", "#dd6b20", "s"),
        ("T30", "#2b6cb0", "^"),
    ]:
        api_v = np.array(DATA_REAL[key]["api"])
        rew_v = np.array(DATA_REAL[key]["rew"])
        err_pct = 100.0 * (api_v - rew_v) / rew_v
        ax0.plot(
            BANDS, err_pct, marker=marker, lw=1.8, color=color, label=f"{key} (RIR-API vs. REW)"
        )

    ax0.axhspan(-10, 10, color="#c6f6d5", alpha=0.45, label="Zona de aceptación (±10%)")
    ax0.axhline(0, color="#4a5568", lw=1.0)
    ax0.axhline(10, color="#2f855a", ls="--", lw=1.0)
    ax0.axhline(-10, color="#2f855a", ls="--", lw=1.0)
    ax0.set_xscale("log")
    ax0.set_xticks(BANDS)
    ax0.set_xticklabels([str(b) for b in BANDS])
    ax0.minorticks_off()
    ax0.set_ylim(-15, 15)
    ax0.set_title("Desviación porcentual en tiempos (RI Real)", fontweight="bold")
    ax0.set_xlabel("Frecuencia central [Hz]")
    ax0.set_ylabel("Error relativo respecto a REW [%]")
    ax0.grid(True, alpha=0.25)
    ax0.legend(loc="lower left", fontsize=8.5)

    ax1 = axes[1]
    diff_c80 = np.array(DATA_REAL["C80"]["api"]) - np.array(DATA_REAL["C80"]["rew"])
    colors_bar = ["#2b6cb0" if abs(d) <= 1.0 else "#c53030" for d in diff_c80]
    ax1.bar(X_IDX, diff_c80, width=0.48, color=colors_bar, label="ΔC80 = RIR-API − REW")
    ax1.axhspan(-1.0, 1.0, color="#c6f6d5", alpha=0.45, label="Zona de aceptación (±1.0 dB)")
    ax1.axhline(0, color="#4a5568", lw=1.0)
    ax1.axhline(1.0, color="#2f855a", ls="--", lw=1.0)
    ax1.axhline(-1.0, color="#2f855a", ls="--", lw=1.0)

    for i, d in enumerate(diff_c80):
        offset = 0.06 if d >= 0 else -0.14
        ax1.text(X_IDX[i], d + offset, f"{d:+.2f} dB", ha="center", fontsize=8.5, fontweight="bold")

    ax1.set_xticks(X_IDX)
    ax1.set_xticklabels([str(b) for b in BANDS])
    ax1.set_ylim(-1.4, 1.4)
    ax1.set_title("Diferencia absoluta en Claridad C80 (RI Real)", fontweight="bold")
    ax1.set_xlabel("Frecuencia central [Hz]")
    ax1.set_ylabel("Diferencia ΔC80 [dB]")
    ax1.grid(True, axis="y", alpha=0.25)
    ax1.legend(loc="lower left", fontsize=8.5)

    fig.suptitle(
        "5 · Verificación de criterios de aceptación (RIR-API vs. REW)",
        fontsize=13.5,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(OUT_DIR / "5_analisis_tolerancias_rew.png")
    plt.close(fig)


if __name__ == "__main__":
    plot_envelope_comparison()
    plot_schroeder_curve()
    plot_filterbank()
    plot_triple_validation_all_parameters()
    plot_all_parameters_panel()
    plot_error_analysis()
    print(f"Gráficas generadas correctamente en: {OUT_DIR.resolve()}")
