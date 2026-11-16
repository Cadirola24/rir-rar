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

  ### Implementación del Cálculo de Parámetros Acústicos por Banda (`app/services/acoustic_parameters.py`)
* **Fecha:** 2026-11-15
* **Herramienta:** Gemini
* **Descripción del problema:** Se necesitaba implementar el Servicio 4 de M3 (`calculate_parameters_from_ir(ir, fs)`), encargado de recibir una Respuesta al Impulso (RI) de banda ancha, descomponerla en bandas de octava (125 Hz a 4000 Hz) y calcular los parámetros acústicos establecidos en la norma ISO 3382-1 (`EDT`, `T10`, `T20`, `T30`, `D50` y `C80`), respetando las restricciones de rango dinámico, límites de Nyquist y firma de retorno tipada.
* **Prompt principal:** Solicitud para desarrollar la implementación completa de `calculate_parameters_from_ir(ir, fs)` en `app/services/acoustic_parameters.py` alineada con la especificación técnica de M3, integrando los servicios previos (`filter_single_band`, `apply_schroeder_integral` y `linear_regression`) con docstrings en formato NumPy y tipado estático.
* **Fragmento de código generado:** Se estructuró la función iterando sobre las bandas centrales estándar (`125.0` a `4000.0` Hz). Para cada banda válida por debajo de Nyquist, se filtra la señal, se detecta el pico del sonido directo ($n_0$) para recortar el inicio del decaimiento y se calculan en dominio lineal los parámetros energéticos ($D_{50}$ en los primeros $50\text{ ms}$ y $C_{80}$ comparando energía temprana y tardía a los $80\text{ ms}$). Posteriormente, se evalúa el rango dinámico disponible y se ajusta la regresión lineal sobre la curva de Schroeder en los tramos normativos de cada tiempo de reverberación ($T = -60 / m$).
* **Modificaciones:**
  * **Pre-padding de 5 ms para evitar distorsión de borde:** Se incorporó un relleno inicial de $5\text{ ms}$ de ceros antes de invocar `filter_single_band` para evitar que el filtrado bidireccional de fase cero (`sosfiltfilt`) deforme el arranque impulsivo en bandas graves (como 125 Hz) y subestime el valor de `EDT`.
  * **Control de rango dinámico y retorno de `None`:** En lugar de asumir que la curva de Schroeder es válida en todo su recorrido, se estimó el rango dinámico comparando la potencia pico en ventanas de $10\text{ ms}$ contra la potencia media del último $10\%$ de la cola. Si el margen no supera el mínimo exigido por ISO 3382-1 ($20, 25, 35$ o $45\text{ dB}$ según el parámetro), se asigna `None` para evitar valores inventados o `NaN` incompatibles con JSON, ajustando la firma de retorno a `dict[str, dict[float, float | None]]`.
  * **Aritmética en escala lineal y conversión única a dB:** Se evitó aplicar suavizado previo al cálculo de $D_{50}$, $C_{80}$ y Schroeder para no sesgar los límites temporales de $50$ y $80\text{ ms}$, realizando todas las sumas y cocientes sobre la energía instantánea ($h^2[n]$) y aplicando `10 * np.log10` una sola vez al final con protección `eps` contra ceros.
  * **Omisión segura por Nyquist:** Se añadió un filtro preventivo ($f_c \cdot \sqrt{2} \ge f_s / 2$) para saltear las bandas agudas cuando se procesan audios con frecuencias de muestreo reducidas sin lanzar excepciones innecesarias.

  ### Implementación del Algoritmo de Lundeby y Endpoint Opcional (`app/services/acoustic_parameters.py`, `app/schemas/utils.py`, `app/routers/utils.py`)
* **Fecha:** 2026-11-15
* **Herramienta:** Gemini
* **Descripción del problema:** Se necesitaba implementar el servicio `apply_lundeby(ir, fs)` de M3 para detectar el índice de muestra donde la caída de la Respuesta al Impulso (RI) se cruza con el piso de ruido de fondo, evitando que la cola de ruido deforme la integral de Schroeder e infle los tiempos de reverberación. Asimismo, se requirió exponer esta funcionalidad en la API REST mediante el endpoint `POST /api/v1/utils/lundeby`, creando previamente el archivo de esquemas `app/schemas/utils.py`.
* **Prompt:** Solicitud para implementar `apply_lundeby(ir, fs)` siguiendo los pasos del algoritmo de Lundeby et al. (1995) detallados en la consigna de M3, y posteriormente generar su modelo Pydantic (`LundebyResponse`), su ruta en `app/routers/utils.py` y los tests de validación correspondientes.
* **Fragmento de código generado:** Se desarrolló `apply_lundeby(ir: np.ndarray, fs: int) -> tuple[int, float]` en `app/services/acoustic_parameters.py`, segmentando la energía ($h^2[n]$) en bloques de $20\text{ ms}$, estimando el ruido de fondo inicial con el último $10\%$ de la señal y ajustando iterativamente una recta hasta $10\text{ dB}$ por encima del piso de ruido mediante `linear_regression`. Además, se creó `app/schemas/utils.py` con `LundebyResponse`, se agregó `@router.post("/lundeby")` en `app/routers/utils.py` y se incorporaron pruebas en `tests/test_api.py`.
* **Modificaciones:**
  * **Promediado energético en lineal:** Se verificó que tanto la potencia media de los bloques de $20\text{ ms}$ como la estimación del ruido de fondo se calculen sobre $h^2[n]$ antes de aplicar `10 * np.log10` (con protección `eps`), evitando el error sistemático de $-5,5\text{ dB}$ que ocurre al promediar valores ya expresados en decibeles.
  * **Consistencia de firmas y reutilización interna:** Se respetó la firma `apply_lundeby(ir, fs) -> tuple[int, float]` de la especificación (a diferencia de la API de referencia que recibe `max_tries` y devuelve segundos) y se reutilizó la función `linear_regression(x, y)` del Servicio 3 respetando el orden matemático de sus argumentos.
  * **Estructura de esquemas y manejo de errores HTTP:** Se creó `app/schemas/utils.py` (inexistente hasta M2) y se protegieron las llamadas a `load_audio` y `apply_lundeby` en `app/routers/utils.py` capturando `ValueError` con encadenamiento `from e` para retornar `422 Unprocessable Entity` sin infringir las reglas de `ruff`.
  * **Cobertura de tests:** Se añadieron casos de prueba para respuestas exitosas (`200`) y archivos inválidos (`422`) con el objetivo de sostener la cobertura superior al $80\%$ exigida en `routers/utils.py` y `acoustic_parameters.py`.

### Implementación de Servicios de Análisis Acústico: Suavizado, Schroeder y Regresión Lineal (`app/services/acoustic_parameters.py`)
* **Fecha:** 2026-11-15
* **Herramienta:** Gemini
* **Problema:** Implementar los tres primeros servicios de procesamiento de respuesta al impulso (RI) de M3 (`apply_smoothing`, `apply_schroeder_integral` y `linear_regression`), respetando la distinción entre escalas de amplitud y energía ($20\log_{10}$ vs. $10\log_{10}$), la estabilidad numérica y el orden de argumentos definido en la especificación.
* **Prompt:** Solicitud de guía e implementación en Python de las funciones `apply_smoothing` (envolvente de Hilbert y media móvil RMS), `apply_schroeder_integral` (curva de decaimiento energético en dB) y `linear_regression` (mínimos cuadrados ordinarios con $R^2$) a partir de las consignas del TP.
* **Fragmento de código generado:**
  * `apply_smoothing`: Validación de parámetros (`method` y `window_ms > 0`), cálculo de envolvente analítica mediante `np.abs(scipy.signal.hilbert(x))` y cálculo de envolvente RMS mediante convolución causal recortada (`np.convolve(x ** 2, kernel, mode="full")[:len(x)]`) seguida de raíz cuadrada.
  * `apply_schroeder_integral`: Integración inversa de energía con `np.cumsum((h ** 2)[::-1])[::-1]`, normalización en dB mediante $10 \log_{10}((E[n] + \text{eps}) / (E[0] + \text{eps}))$ y recorte de piso a `-150.0 dB` para evitar valores `-inf` o `NaN` en la serialización JSON.
  * `linear_regression`: Cálculo cerrado de pendiente ($m$), ordenada al origen ($b$) y coeficiente de determinación ($R^2$) mediante sumas centradas en la media, respetando la firma `(x, y)` en orden matemático sin depender de `np.polyfit`.
* **Modificaciones:** Se utilizó convolución causal con recorte a `len(x)` en lugar de `mode="same"` para preservar exactamente la longitud de la señal de entrada ante cualquier tamaño de ventana, verificando los tres servicios mediante los tests unitarios en `tests/test_analisis.py` (`XPASS`).

### Integración de Endpoints HTTP, Schemas Pydantic y Correcciones de Linting/CI (`app/routers/` y `app/schemas/`)
* **Fecha:** 2026-11-15
* **Herramienta:** Gemini
* **Problema:** Completar la lógica de los endpoints `POST /api/v1/utils/smoothing` y `POST /api/v1/utils/schroeder`, integrar los schemas de respuesta y resolver los errores de estilo y formato reportados por `ruff` en el workflow de GitHub Actions (`CI / lint-and-test`).
* **Prompt:** Solicitud de implementación del cuerpo de los endpoints en `app/routers/utils.py`, verificación con `pytest` y resolución de reglas de `ruff check` y `ruff format --check` previo al merge a `main`.
* **Fragmento de código generado:** Implementación de carga de audio mediante `load_audio` con captura de `ValueError` hacia `HTTPException(status_code=422)`, decimación uniforme de las curvas (`env[::step]` y `edc[::step]`) con cálculo de paso temporal `time_step = step / fs`, y retorno estructurado mediante `SmoothingResponse` y `SchroederResponse`.
* **Modificaciones:**
  * Se actualizó `SmoothingMethod` heredando de `enum.StrEnum` (regla `UP042`) y se agregó el import faltante de `datetime` en `app/schemas/responses.py`.
  * Se refactorizaron los parámetros `File(...)` y `Form(...)` en `app/routers/utils.py` y `app/routers/acoustics.py` usando `typing.Annotated` (regla `B008`), se encadenaron excepciones con `raise ... from e` (regla `B904`), se ajustaron comentarios que superaban los 100 caracteres (`E501`) y se ejecutó `ruff format` para dejar el pipeline en verde.

### Validación Acústica ISO 3382-1, Evidencias Gráficas y Documentación Final (`generate_evidences_m3.py`, `README.md`, `docs/m3/`)
* **Fecha:** 2026-11-16
* **Herramienta:** Gemini
* **Problema:** Validar cuantitativamente los parámetros acústicos calculados por `RIR-API` (`EDT`, `T20`, `T30` y `C80`) frente al software de referencia `REW` y la API de cátedra tanto en una respuesta al impulso real (`ri_larga.wav`) como en una sintética (`synthetic_ir.wav`, $T_{60} = 1.50\text{ s}$), generando evidencias visuales del pipeline DSP y documentando los resultados en el `README.md` bajo los criterios de aceptación de la norma ISO 3382-1 ($\pm 10\%$ en tiempos de reverberación y $\pm 1.0\text{ dB}$ en claridad).
* **Prompt:** Solicitud de creación y depuración del script `generate_evidences_m3.py` en `matplotlib` para generar las gráficas del pipeline (suavizado Hilbert/Media Móvil, curva de decaimiento de Schroeder con regresiones extrapoladas y respuesta del banco de filtros IEC 61260) y las comparativas triples por banda de octava para todos los parámetros, además de la redacción estructurada de tablas comparativas y análisis técnico en `README.md`.
* **Fragmento de código generado:**
  * `plot_envelope_comparison` y `plot_schroeder_curve`: Graficación de la envolvente analítica (`method="hilbert"`) frente a la media móvil (`method="moving_average"`, ventana de $20\text{ ms}$) y curva de decaimiento energética completa (`apply_schroeder_integral`) con las rectas extrapoladas de `EDT` ($0$ a $-10\text{ dB}$), `T20` ($-5$ a $-25\text{ dB}$) y `T30` ($-5$ a $-35\text{ dB}$).
  * `plot_triple_validation_all_parameters`, `plot_all_parameters_panel` y `plot_error_analysis`: Generación de gráficos individuales por parámetro (`3a` a `3d`), panel integral por banda y mapas de error relativo/absoluto respecto a `REW` con franjas de aceptación ($\pm 10\%$ y $\pm 1.0\text{ dB}$).
* **Modificaciones:**
  * **Ajuste de escala de amplitud y nombres de métodos:** Se eliminó la conversión errónea de dB a lineal (`10 ** (env / 20)`) al comprobar que `apply_smoothing` retorna amplitud normalizada directa, y se corrigió el identificador de método de `'rms'` a `'moving_average'` según la firma interna de `app/services/acoustic_parameters.py`.
  * **Extensión temporal y anotaciones en curva de Schroeder:** Se amplió el eje temporal hasta la duración real completa de `ri_larga.wav` ($1.78\text{ s}$) y se agregaron marcadores en los umbrales de regresión ($0$, $-5$, $-10$, $-25$ y $-35\text{ dB}$) junto con la recta extrapolada de `EDT`.
  * **Separación de tablas y análisis físico en `README.md`:** Se dividieron los resultados en tablas individuales por parámetro (`EDT`, `T20`, `T30`, `C80`) para ambas señales y se incorporó una nota técnica justificando las diferencias puntuales en bandas graves de la RI sintética debido al filtrado de fase cero (`sosfiltfilt`) frente a los filtros causales de `REW`.
  * **Formateo y linting:** Se ejecutó `uv run ruff format` y `uv run ruff check --fix` sobre los scripts auxiliares para cumplir con el límite de 100 caracteres por línea antes del merge final a `main`[cite: 60].

### Implementación del Endpoint Opcional `GET /filters/frequencies` (`app/schemas/filters.py`, `app/routers/filters.py`)
* **Fecha:** 2026-11-16
* **Herramienta:** Gemini
* **Descripción del problema:** Se necesitaba implementar el endpoint `GET /api/v1/filters/frequencies` para consultar las frecuencias centrales estándar de bandas de octava y tercio de octava IEC 61260 soportadas por la API, permitiendo además filtrar dinámicamente aquellas que entran por debajo del límite de Nyquist al recibir un parámetro opcional `sample_rate`.
* **Prompt:** Solicitud para implementar el schema Pydantic de salida (`FrequenciesResponse`), la ruta `GET /frequencies` en `app/routers/filters.py` con validación por query param y los comandos `curl` de ejemplo para documentar su uso en el `README.md`.
* **Fragmento de código generado:** Se definió el modelo `FrequenciesResponse` con los campos `sample_rate`, `octave_bands` y `third_octave_bands` junto a sus descripciones OpenAPI. En `app/routers/filters.py` se agregaron las constantes estándar de octava ($31.5\text{ Hz}$ a $16\text{ kHz}$) y tercio de octava ($25\text{ Hz}$ a $20\text{ kHz}$) y la ruta `@router.get("/frequencies", response_model=FrequenciesResponse)` con `Query(default=None, gt=0)` para filtrar bandas según $f_c \cdot 2^{1/2} < f_s / 2$ y $f_c \cdot 2^{1/6} < f_s / 2$.
* **Modificaciones:**
  * **Cumplimiento de reglas de linter (`ruff`):** Se dividió el string de `description` dentro de `Query(...)` mediante concatenación implícita entre paréntesis para respetar el límite máximo de longitud de línea (`E501`) configurado en el proyecto.
  * **Validación automática de parámetros y documentación:** Se aprovechó `Query(..., gt=0)` para delegar en FastAPI/Pydantic el rechazo con `422 Unprocessable Entity` ante frecuencias de muestreo nulas o negativas, dejando el endpoint expuesto automáticamente en Swagger (`/docs`) y ReDoc (`/redoc`).

### Implementación del Endpoint Opcional `POST /filters/band` (`app/services/filter.py`, `app/schemas/filters.py`, `app/routers/filters.py`)
* **Fecha:** 2026-11-16
* **Herramienta:** Gemini
* **Descripción del problema:** Se necesitaba implementar el endpoint `POST /api/v1/filters/band` para descomponer y filtrar una señal de audio en todas las bandas de octava estándar (125 Hz a 4000 Hz) en una sola petición, omitiendo de manera segura aquellas bandas cuya frecuencia de corte superior supere el límite de Nyquist.
* **Prompt:** Solicitud para implementar el servicio de filtrado multibanda (`filter_all_octave_bands`), su modelo Pydantic de respuesta (`MultiBandFilterResponse`), la ruta `POST /band` en `app/routers/filters.py` con decimación de salida y el comando `curl` de prueba.
* **Fragmento de código generado:** Se definió `filter_all_octave_bands(signal, fs, order=4)` en `app/services/filter.py` reutilizando `filter_single_band` sobre la constante `STANDARD_OCTAVE_BANDS` con verificación preventiva de Nyquist ($f_c \cdot \sqrt{2} < f_s / 2$). En `app/schemas/filters.py` se creó `MultiBandFilterResponse` (`sample_rate`, `order`, `center_frequencies`, `time_step`, `bands`) y en `app/routers/filters.py` se agregó `@router.post("/band", response_model=MultiBandFilterResponse)` submuestreando cada banda a un máximo aproximado de 1000 puntos.
* **Modificaciones:**
  * **Normalización de entrada y manejo de Nyquist:** Se agregó la conversión automática a mono (`mean(axis=1)`) y validación de señal vacía o `fs <= 0` al inicio de `filter_all_octave_bands` para capturar `ValueError` y retornar `422 Unprocessable Entity`, mientras que las bandas por encima de Nyquist se omiten limpiamente sin producir errores `500`.
  * **Organización PEP 8 y cumplimiento de linter (`ruff`):** Se ubicó la constante `STANDARD_OCTAVE_BANDS` a nivel de módulo debajo de los `import`, se utilizaron anotaciones `Annotated[..., File(...)]` y `Annotated[..., Form(...)]` (regla `B008`) y se encadenaron excepciones con `raise ... from e` (regla `B904`).

### Pruebas Automatizadas para Endpoints Opcionales (`tests/test_api.py`)
* **Fecha:** 2026-11-16
* **Herramienta:** Gemini
* **Descripción del problema:** Al incorporar los nuevos endpoints opcionales (`GET /api/v1/filters/frequencies`, `POST /api/v1/utils/log-scale` y `POST /api/v1/filters/band`), era necesario cubrir sus rutas felices (`200 OK`) y sus casos de error (`422 Unprocessable Entity`) en la suite de tests para asegurar el cumplimiento del umbral mínimo de cobertura ($\ge 80\%$) exigido por la cátedra.
* **Prompt:** Solicitud para generar casos de prueba en `tests/test_api.py` para validar respuestas exitosas, filtrado por Nyquist y manejo de archivos o parámetros inválidos.
* **Fragmento de código generado:** Se añadieron tres funciones de prueba al final de `tests/test_api.py`: `test_filters_frequencies_endpoint` (verificando el listado completo de bandas de octava, el filtrado con `sample_rate=8000` y el rechazo `422` con `sample_rate=0`), `test_utils_log_scale_endpoint` (comprobando que los valores en `signal_db` respeten el techo de $0\text{ dB}$ y el piso `floor_db`) y `test_filters_all_bands_endpoint` (validando la correspondencia entre `center_frequencies` y las claves de `bands`).
* **Modificaciones:**
  * **Reutilización de utilidades internas de test:** Se reemplazaron los fixtures genéricos por los helpers propios del módulo (`_wav_en_memoria` y `_ri_sintetica`), manteniendo la coherencia con el resto de los tests de M3 y validando el pipeline completo mediante `uv run ruff check` y `uv run pytest --cov=app`.