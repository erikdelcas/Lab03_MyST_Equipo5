# Project charter — Lab 03 · Equipo 5

## Propósito
Estudiar estrategias cuantitativas de reversión a la media en tres pares (NWS–NWSA, GOOG–GOOGL y TLT–VGLT) mediante screening estadístico, cointegración/Johansen, filtros de Kalman y VECM; evaluar resultados fuera de muestra con costos y comunicar las limitaciones.

## Alcance
- Datos y screening; validación de cointegración y Johansen móvil.
- Kalman 1 para relación de cobertura dinámica y Kalman 2 aproximado para media y log-varianza.
- Señales, VECM con innovaciones proyectadas sobre la cobertura dinámica, backtest, controles de exposición y costos, bitácora de operaciones.
- Separación entrenamiento/prueba/validación (60/20/20), calibración walk-forward sobre entrenamiento.
- Dashboard Streamlit, notebook, pruebas automatizadas y reporte.
- **Fuera de alcance:** sección de Risk Parity, según indicación del profesor. Registrar la confirmación formal si la solicita la rúbrica.

## Hitos y estado observado
| Hito | Estado de trabajo | Evidencia o verificación pendiente |
|---|---|---|
| Datos, screening y selección exploratoria | Ejecutado | Comprobar archivos fuente y fecha de corte |
| Filtros, VECM, señales y backtest | Ejecutado | Código y artefactos del proyecto |
| Johansen móvil y calibración walk-forward | Ejecutado | CSV de resultados y scripts |
| Dashboard y pruebas | Dashboard cotejado con los tres Sharpe OOS; 36 pruebas reportadas aprobadas | Volver a ejecutar pruebas antes de entrega |
| Notebook, reporte y documentación | Actualizados en el proyecto según revisión de trabajo | Verificación final del paquete completo |
| GitHub y exposición | Por cerrar | Historial de contribuciones reales y ensayo |

**Fechas de hitos:** inicio del proyecto el 2026-11-04, integración de la versión funcional el 2026-11-05, datos para Streamlit Cloud el 2026-11-06 y documentación el 2026-11-08.

## Riesgos y mitigaciones
| Riesgo | Severidad | Mitigación |
|---|---|---|
| Cointegración inestable o ausente | Alta | Reportar screening y Johansen móvil sin afirmar estabilidad general |
| Look-ahead y sobreajuste | Alta | Decisiones con información disponible y calibración solo en entrenamiento |
| Datos descargados no disponibles | Media | Caché local y procedimiento de regeneración documentado |
| Inestabilidad de filtros | Alta | Monitorear innovaciones, media y varianza estimadas |
| Costos de transacción | Media | Incluir comisiones, préstamo y comparación de rebalanceo |
| Resultados inconsistentes entre archivos | Alta | Reejecutar scripts y cotejar reporte, dashboard y notebook |
| Colaboración no documentada | Alta | Registrar roles y cambios verificables sin atribuciones ficticias |

## Equipo y responsabilidades
El equipo dividió las responsabilidades en tres partes equivalentes por módulo:

| Integrante | Responsabilidad | Archivos a cargo | Pruebas relacionadas |
|---|---|---|---|
| Adrián Marcelo Ballesteros Herrera | Datos, screening, Johansen móvil, diagnóstico de señales, dashboard y notebook | `data/`, `cointegration/`, `diagnosticar_senales.py`, `dashboard/`, `notebooks/` | `test_johansen_movil.py`, `test_dashboard_exposicion.py`, `test_walkforward_dashboard.py` |
| Erik del Castillo Román | Filtros de Kalman, VECM, política de decisiones, orquestación del pipeline y calibración walk-forward | `kalman/`, `strategy/`, `main.py`, `config.py`, `calibrar_walkforward.py` | `test_filters.py`, `test_innovations.py`, `test_kalman2_varianza.py`, `test_vecm_kalman_consistency.py`, `test_walkforward.py` |
| Jesús Emmanuel Flores Cortés | Backtest, costos, métricas, bitácora, comparación de rebalanceo y documentación de instalación | `backtest/`, `performance/`, `generar_bitacoras.py`, `comparar_rebalanceo.py`, `README.md`, `artifacts/README.md` | `test_backtest.py`, `test_rebalance_band.py`, `test_trade_ledger.py` |

El reporte ejecutivo, la revisión final y la exposición son responsabilidad compartida. Esta tabla indica responsabilidades por área, no la autoría de cada línea; el historial de Git registra quién subió cada cambio.

## Criterio de éxito del proyecto
Pipeline reproducible, controles de ejecución y sesgos, resultados fuera de muestra auditables y presentación clara de hallazgos, **sin exigir rentabilidad positiva** ni afirmar cointegración sostenida cuando no se observa.
