# Lab 03 — Arbitraje estadístico con cointegración, Kalman y VECM

**Equipo 5 | Ingeniería Financiera | Laboratorio de Sistemas de Trading**

Proyecto de investigación reproducible que analiza tres pares de activos, estima coberturas dinámicas, construye señales basadas en innovaciones VECM y evalúa una estrategia de dos patas con restricciones operativas. **No constituye una recomendación de inversión.**

## Resumen del proyecto

Se estudian tres **pares exploratorios**, no tres relaciones de cointegración robustamente demostradas:

| Par | Fundamento y limitación |
|---|---|
| `NWS_NWSA` | Dos clases de acciones de News Corp. Screening inicial favorable, pero cointegración inestable en ventanas posteriores. |
| `GOOG_GOOGL` | Dos clases de Alphabet. Johansen principal no confirma rango cointegrante 1. |
| `TLT_VGLT` | ETF de bonos del Tesoro a largo plazo. No supera la corrección FDR del screening exploratorio. |

Cada par se simula como **experimento independiente**; no se agregan en una cartera conjunta. La sección 3.7 (Risk Parity) se omite por indicación verbal del profesor; conservar evidencia de esa instrucción si se requiere en la entrega.

## Metodología

1. Precios históricos y división temporal **60% entrenamiento, 20% prueba y 20% validación**.
2. Selección y diagnóstico en entrenamiento: correlación, Engle–Granger, Johansen, ADF e integración indicativa; Johansen móvil como diagnóstico, no como señal de trading.
3. **Kalman 1:** estimación causal de la relación de cobertura dinámica y construcción del spread.
4. **VECM:** parámetros entrenados en la muestra inicial; las innovaciones se proyectan sobre la dirección de cobertura disponible antes de cada observación. Esto **no** es un VECM con cointegración dinámica reestimada.
5. **Kalman 2:** estimación aproximada acoplada de media y log-varianza y cálculo del z-score predictivo. No es un EKF exacto; consultar los módulos y el reporte para la especificación.
6. Decisiones al cierre y ejecución al **cierre siguiente**; acciones enteras, costos de negociación, préstamo y exposición bruta máxima.
7. Evaluación fuera de muestra y calibración *walk-forward* **solo con entrenamiento**. La política calibrada se compara con una política base, pero no sustituye automáticamente la ejecutada por `main.py`.
8. Comparación descriptiva de rebalanceo diario frente a banda del 2%, bitácora de operaciones y visualización en Streamlit.

## Supuestos principales

- Semilla: `42`.
- Inicio de los datos: `2014-01-01`; la fecha final figura en `config.py`.
- Capital inicial: **USD 1,000,000 por par**.
- Exposición bruta máxima: **80% del patrimonio**.
- Comisión: **0.125%** sobre nocional negociado.
- Costo anual de préstamo: **0.25%**, prorrateado por día de tenencia.
- Política base: entrada `|z| >= 2`, salida `|z| < 0.5`, stop `|z| > 4`, tenencia máxima `45` sesiones.
- No se modelan completamente impacto de mercado, deslizamiento, margen ni disponibilidad real del préstamo.

## Instalación desde cero (macOS)

Desde la carpeta raíz del proyecto, con Python compatible con el archivo `requirements.txt` (el equipo trabajó con Python 3.14):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para ejecutar el notebook, si no están incluidas las dependencias necesarias en el archivo principal:

```bash
python -m pip install -r requirements_notebook.txt
```

## Instalación desde cero (Windows)

En PowerShell, desde la carpeta raíz del proyecto:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell bloquea `Activate.ps1` por la política de ejecución, habilitarla solo para la sesión actual con `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y volver a activar. En `cmd` la activación es `.venv\Scriptsctivate.bat`. Las versiones de `requirements.txt` se fijaron trabajando en macOS con Python 3.14; si `pip` no encuentra *wheels* para tu versión de Python en Windows, revisar la versión del intérprete antes de cambiar dependencias.

**No incluyas `.venv/` en GitHub.** Si los datos no están cacheados, la descarga inicial requiere conexión.

## Ejecución reproducible

Ejecutar **en este orden** desde la raíz del proyecto:

```bash
python -m pytest tests/ -q
python main.py
python generar_bitacoras.py
python calibrar_walkforward.py
python comparar_rebalanceo.py
python -m streamlit run dashboard/app.py
```

El equipo obtuvo **36 pruebas aprobadas** tras la actualización del segundo filtro de Kalman. Se deben volver a ejecutar en el entorno de entrega: esa cifra documenta la última comprobación reportada, no garantiza que cada instalación resulte idéntica.

### Notebook

Abrir `notebooks/Lab03_Principal.ipynb` en VS Code o Jupyter, seleccionar el intérprete `.venv` y ejecutar sus celdas en orden. El notebook **lee artefactos existentes**; regenerarlos primero mediante los comandos anteriores. La variable `pair` controla qué par se muestra en algunas figuras (`NWS_NWSA`, `GOOG_GOOGL` o `TLT_VGLT`).

### Dashboard para exposición

Abrir `http://localhost:8501` después de iniciar Streamlit. Cuenta con modo **Exposición** (objetivo, metodología, resultados y conclusiones) y modo **Análisis completo** (vistas ejecutiva/técnica, operaciones, Johansen móvil y walk-forward). El dashboard **lee CSV**: no recalcula precios ni entrena modelos por sí solo.

Si faltan los archivos `artifacts/*_backtest.csv` —por ejemplo, porque están ignorados en Git— **ejecutar `python main.py`** antes de abrir el dashboard, seguido de los scripts de bitácora y calibración.

## Estructura orientativa

```text
Lab03_MyST_Equipo5/
├── main.py, config.py, requirements.txt
├── data/                 # Descarga/caché de precios
├── cointegration/        # Screening y Johansen móvil
├── kalman/               # Filtros de cobertura y señal
├── strategy/             # VECM y política de decisiones
├── backtest/             # Contabilidad, costos y rebalanceo
├── performance/          # Métricas, bitácora y lectura walk-forward
├── dashboard/app.py      # Streamlit
├── tests/                # Pruebas automatizadas
├── notebooks/            # Notebook principal
├── artifacts/            # Resultados regenerables CSV
├── docs/reporte.pdf      # Reporte técnico
└── project_management/   # Gestión y contribuciones del equipo
```

Los scripts auxiliares `generar_bitacoras.py`, `calibrar_walkforward.py` y `comparar_rebalanceo.py` permanecen en la raíz del proyecto.

## Interpretación de resultados

El informe y el dashboard deben leerse junto con la columna `partition` y con los archivos de la **misma ejecución de Kalman 2**. Los resultados de las versiones previas no deben mezclarse con los actuales.

Los resultados observados muestran Sharpe fuera de muestra negativos para la política base en los tres pares. La calibración interna redujo pérdidas y costos en las evaluaciones posteriores, **pero no demostró rentabilidad neta positiva ni cointegración sostenida**. La selección de umbrales no debe rehacerse a partir de validación.

Las tablas `artifacts/metrics.csv` y `artifacts/walkforward_oos_comparison.csv` registran los resultados numéricos; `artifacts/*_operaciones.csv` contiene las bitácoras y `artifacts/*_johansen_movil.csv` las estimaciones diagnósticas.

## Verificaciones previas a la entrega

- [ ] Volver a ejecutar las pruebas y guardar el resultado obtenido.
- [ ] Ejecutar toda la secuencia de scripts, regenerando artefactos con el código final.
- [ ] Confirmar que notebook, dashboard y `docs/reporte.pdf` utilizan la **misma versión**.
- [ ] Comprobar que Johansen móvil, bitácora, cifras walk-forward y rebalanceo se muestran sin errores.
- [ ] Verificar que `.gitignore` excluye el entorno virtual, cachés y archivos no deseados; si excluye backtests diarios, regenerarlos para exponer.
- [ ] Completar `project_management/` con integrantes, roles, fechas, sprints y retrospectiva **reales**.
- [ ] Revisar la aprobación del profesor respecto a la omisión de Risk Parity y las limitaciones de los pares.
- [ ] Registrar commits auténticos por integrante; no fabricar historial de contribuciones.

## Alcance y límites

El sistema ilustra métodos de arbitraje estadístico, pero una elevada correlación no garantiza cointegración ni reversión aprovechable. Las innovaciones del VECM no son equivalentes al nivel del spread y la mejora de una métrica tras calibración no valida la rentabilidad de la estrategia. Las pruebas unitarias verifican propiedades concretas del software y no certifican validez económica o estadística general.
