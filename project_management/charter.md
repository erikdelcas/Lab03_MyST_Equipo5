# Project charter — Lab 03 · Equipo 5

## Propósito
Estudiar estrategias cuantitativas de reversión a la media en tres pares (NWS–NWSA, GOOG–GOOGL y TLT–VGLT) mediante screening estadístico, cointegración/Johansen, filtros de Kalman y VECM; evaluar resultados fuera de muestra con costos y comunicar las limitaciones.

## Alcance
- Datos y screening; validación de cointegración y Johansen móvil.
- Kalman 1 para relación de cobertura dinámica y Kalman 2 aproximado para media y log-varianza.
- Señales, VECM dinámico, backtest, controles de exposición y costos, bitácora de operaciones.
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

**Fechas de hitos:** por completar con el calendario efectivo del equipo y del curso.

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
**Pendiente:** completar los nombres de los tres integrantes, la responsabilidad efectivamente desempeñada por cada uno y las evidencias de su trabajo. No asignar autoría retroactivamente a actividades que no realizó.

## Criterio de éxito del proyecto
Pipeline reproducible, controles de ejecución y sesgos, resultados fuera de muestra auditables y presentación clara de hallazgos, **sin exigir rentabilidad positiva** ni afirmar cointegración sostenida cuando no se observa.
