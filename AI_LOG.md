# Registro de Uso de IA

## Milestone 1 (v0.1.0)

### Generación de Ruido Rosa (Voss-McCartney)
* **Fecha:** 2026-10-23
* **Herramienta:** Gemini
* **Problema:** Implementación de ruido rosa usando Voss-McCartney, asegurando que el bucle fuera eficiente.
* **Prompt:** Solicitud de explicación paso a paso y fundamentación teórica para traducir la lógica de bits ($n$ y $n-1$) y generadores de la consigna a código eficiente, utilizando el *template* base.
* **Fragmento de código generado:** Se adoptó la optimización de llevar un acumulador (`current_sum`) para evitar la función `sum()` en cada iteración del bucle, y el uso de operaciones bitwise (`(n & -n).bit_length() - 1`) para encontrar eficientemente el generador a renovar, según la variante de McCartney.
* **Modificaciones:** Se cambió la distribución del ruido rosa de uniforme a normal y se cambiaron los nombres de algunas variables.

### Generación de Sine Sweep y Filtro Inverso (Servicio, Schema y Router)
* **Fecha:** 2026-10-23
* **Herramienta:** Gemini
* **Problema:** Implementación del servicio de sine sweep logarítmico y su filtro inverso, integración completa del router de FastAPI para servir las respuestas de audio, resolución de errores de sintaxis y linting y generación automatizada de las evidencias visuales (`docs/m1/`) para el `README.md`.
* **Prompt:** Solicitud de guía paso a paso para programar `generate_sine_sweep_pair`, pasar las pruebas `pytest` y `ruff check` y crear el script `generate_evidences.py` para graficar el espectrograma y la respuesta al impulso por convolución.
* **Fragmento de código generado:** Lógica de generación del sweep logarítmico exponencial y filtro inverso con envolvente $A(t)$, esquemas de validación de entrada, la implementación concreta en el router para responder con `wav_response` según el flag `req.inverse` y Script `generate_evidences.py` utilizando `scipy.signal.spectrogram`, `scipy.signal.fftconvolve` y `matplotlib` para exportar `espectrograma_sweep.png` y `convolucion_impulso.png` a la carpeta `docs/m1/`.
* **Modificaciones:** Se reemplazó la línea orientativa en comentarios provista por la cátedra (`# ... devolver con wav_response el sweep o el filtro inverso, según req.inverse`) por código Python funcional: evaluación condicional del booleano `req.inverse` para seleccionar la señal (`chosen_signal`), asignación dinámica de nombre de archivo (`filename`) y retorno de la respuesta mediante `wav_response(...)` y creación de la carpeta `docs/m1/` con las imágenes de validación visual y adición de los enlaces en el `README.md`.

## Milestone 2 (v0.2.0)

### Endpoints de Filtrado por Octava y RI Sintética (Servicios y Routers)
* **Fecha:** 2026-10-28
* **Herramienta:** Gemini
* **Problema:** Implementación de los servicios `/filters/single-band` y `/signals/synthetic-ir`, corrección de reglas de linteo en Ruff (`E501`, `B008`, `B904`) y verificación de la cobertura mínima de tests exigida ($\ge 80\%$).
* **Prompt:** Solicitud de asistencia para corregir errores de longitud de línea, manejo sintáctico de excepciones (`raise ... from e`) y verificación del reporte de cobertura con `pytest`.
* **Fragmento de código generado:** Ajustes de estructura en `app/routers/filters.py` reubicando comentarios y encadenando excepciones explícitamente para cumplir el estándar de calidad.
* **Modificaciones:** Se reestructuraron los comentarios sobre `except ValueError` a líneas dedicadas, logrando 0 errores en `ruff check` y una cobertura del 93% en `app/services`.

### Script de Validación y Evidencias Visuales (`generate_evidences_m2.py`)
* **Fecha:** 2026-10-28
* **Herramienta:** Gemini
* **Problema:** Generación automatizada de gráficos para `docs/m2/` (RIs reales corta y larga) y validación de precisión de deconvolución sintética con requerimiento de correlación de Pearson $r > 0.9$.
* **Prompt:** Creación del script `generate_evidences_m2.py`, reconciliación de las importaciones internas del módulo (`audio_io`, `sine_sweep`, `signal_utils`, `filter`) y resolución del desfase de muestras que daba $r = 0.04$.
* **Fragmento de código generado:** Lógica de procesamiento espectral FFT y decaimiento en dB, junto con la alineación de señales mediante correlación cruzada (`np.correlate`) previa al cálculo de Pearson.
* **Modificaciones:** Se corrigieron las rutas de importación de acuerdo a la estructura del repositorio y se compensó el retardo de la convolución/filtro inverso, alcanzando una correlación de $r = 0.9999$ y guardando los gráficos `ri_sintetica_deconvolucion.png`, `ri_real_corta.png` y `ri_real_larga.png` en `docs/m2/`.