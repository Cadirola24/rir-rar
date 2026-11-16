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

### Implementación de Reproducción y Grabación Simultánea (`app/services/audio_io.py`)
* **Fecha:** 2026-10-23
* **Herramienta:** Gemini
* **Descripción del problema:** Se necesitaba implementar el Servicio 3 de M1 (`play_and_record`), para reproducir el sine sweep y grabar simultáneamente la respuesta del recinto mediante la interfaz de audio local. La función debía admitir señales mono (1D) y estéreo (2D), extender la captura más allá de la duración del sweep para registrar la cola reverberante y lanzar un `RuntimeError` informativo ante la ausencia de hardware de audio.
* **Prompt:** Solicitud para implementar en Python la función `play_and_record(signal, fs, record_duration)` con `sounddevice.playrec`, contemplando detección automática de canales (1D/2D), relleno con ceros (*zero-padding*) para ajustar la señal a `record_duration` y captura de excepciones del dispositivo de audio.
* **Fragmento de código generado:** Se utilizó `sd.playrec(signal_padded, samplerate=fs, channels=channels, blocking=True)`. Debido a que `playrec` registra la misma cantidad de muestras que reproduce, se implementó un relleno con ceros al final de `signal` mediante `np.pad` (adaptado tanto para arrays 1D como 2D) hasta completar `total_frames = int(record_duration * fs)`, además de un bloque `try...except` que encapsula cualquier fallo de hardware en un `RuntimeError`.
* **Modificaciones:**
  * **Importación local de `sounddevice`:** Se ubicó `import sounddevice as sd` dentro del cuerpo de la función en lugar del encabezado del módulo para evitar que el servidor o el entorno de integración continua (CI) fallen por ausencia de librerías de audio del sistema (PortAudio) al importar `audio_io.py` durante las pruebas automatizadas.
  * **Alcance cliente-servidor:** Se respetó la arquitectura planteada en la consigna sin crear un endpoint HTTP para este servicio, ya que la adquisición física ocurre en la máquina del cliente.
  * **Gestión de latencia y cola:** Si bien la implementación garantiza el registro de la cola de reverberación mediante *post-padding* hasta `record_duration`, no agrega un *pre-roll* inicial de silencio (0,5 a 1 s); el desfase inicial del driver se resuelve posteriormente al alinear el pico de la respuesta al impulso en `get_impulse_response`.

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

### Ejemplo de comandos curl (`README.md`)
* **Fecha:** 2026-11-02
* **Herramienta:** Gemini
* **Problema:** Se necesitaba documentar el uso de los endpoints de la API (Ruido Rosa, Sine Sweep, RI Sintética y Filtrado por Banda) en el README utilizando comandos `curl`.
* **Prompt:** Solicitud para generar comandos `curl` actualizados y precisos, a partir de `main.py` y `signals.py`, extrayendo los nombres de los endpoints, las rutas correctas (`/api/v1/...`) y la estructura de los *schemas*.
* **Fragmento de código generado:** Se generaron cuatro bloques de comandos `curl`. Se destacó la diferencia entre peticiones JSON (`application/json`) y la subida de archivos físicos (`multipart/form-data` usando `-F 'file=@ruta'`).
* **Modificaciones:** Se añadió el sonido "THX Sound" en `tests/data` para validar el funcionamiento del filtro pasabanda. Los comandos fueron revisados para asegurar que los nombres de las variables coincidan exactamente con la implementación del código y que el formato del curl esté correctamente expresado en markdown.

### Validación Gráfica del Ruido Rosa (`generate_evidences.py`)
* **Fecha:** 2026-11-02
* **Herramienta:** Gemini
* **Problema:** Se necesitaba generar la evidencia visual para M1 que demostrara matemáticamente que el algoritmo de Voss-McCartney implementado produce un ruido rosa con la caída espectral correcta (aproximadamente -3 dB/octava).
* **Prompt:** Solicitud para crear un bloque de código en Python que calcule y grafique el espectro del ruido rosa con su respectiva pendiente de regresión, para integrarlo al script existente `generate_evidences.py` y guardar la imagen en `docs/m1`.
* **Fragmento de código generado:** Se proporcionó un bloque de código que utiliza `scipy.signal.welch` para calcular la Densidad Espectral de Potencia (PSD) y `np.polyfit` para realizar la regresión lineal entre las frecuencias de 100 Hz y 10 kHz. Se utilizó `matplotlib` con ejes semilogarítmicos (`semilogx`) para trazar la señal generada frente a la línea de tendencia ideal.
* **Modificaciones:** Al integrar el código generado, se detectó una discrepancia en los argumentos (el código generado usaba `sample_rate`, pero la función original esperaba `fs`). Se corrigió el argumento manualmente a `fs=fs` para evitar un `TypeError`. Posteriormente, se ejecutó exitosamente el script aislando las dependencias mediante el comando `uv run python`.

## Milestone 3 (v1.0.0)

### Manejo de Excepciones por Frecuencia de Nyquist en `/synthetic-ir` (`app/routers/signals.py`)
* **Fecha:** 2026-11-15
* **Herramienta:** Gemini
* **Descripción del problema:** Ante una petición `POST` al endpoint `/api/v1/signals/synthetic-ir` con una banda de octava cuya frecuencia de corte superior superaba el límite de Nyquist (por ejemplo, `{"16000": 1.0}` a $f_s = 44100\text{ Hz}$), el servicio `generate_synthetic_ir` lanzaba un `ValueError` no capturado en el router. Esto provocaba un `500 Internal Server Error` en lugar de devolver un código `422 Unprocessable Entity` para parámetros inválidos.
* **Prompt:** Solicitud para adaptar el manejo de excepciones en `app/routers/signals.py` siguiendo el patrón implementado en `app/routers/filters.py`, junto con su correspondiente test de regresión.
* **Fragmento de código generado:** Se envolvió la invocación a `generate_synthetic_ir(req.duration, req.t60_values, req.sample_rate)` dentro de un bloque `try...except ValueError as e` en `app/routers/signals.py` para lanzar `HTTPException(status_code=422, detail=...) from e`. Asimismo, se incorporó el test `test_synthetic_ir_band_above_nyquist_returns_422` en `tests/test_api.py`.
* **Modificaciones:**
  * **Compatibilidad con el schema Pydantic:** Se verificó que `SyntheticIRRequest` utiliza el atributo `req.sample_rate` (en lugar de `fs`), adaptando tanto la llamada al servicio como el mensaje de error HTTP para evitar un `AttributeError`.
  * **Cumplimiento de reglas de linter (`ruff`):** Se conservó el encadenamiento explícito de excepciones (`from e`) tal como en `app/routers/filters.py` para cumplir con la regla `B904` y evitar fallos en el pipeline de CI.
  * **Cobertura de pruebas:** Se ejecutaron `uv run ruff check` y `uv run pytest -v` para validar que el nuevo caso borde quede cubierto sin afectar los endpoints existentes.