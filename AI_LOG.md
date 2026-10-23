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