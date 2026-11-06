# Postmortem — Lab 03 · Equipo 5

## Resumen
Se construyó un laboratorio de estrategias de reversión a la media en tres pares con screening, filtros de Kalman, VECM, señales, backtesting con costos, análisis fuera de muestra, comparación de rebalanceo y dashboard. El resultado económico observado fue negativo en los tres pares; no debe interpretarse el laboratorio como una estrategia rentable o una prueba de cointegración estable.

## Hitos técnicos observados
- Pipeline ejecutable y dashboard revisado con métricas OOS consistentes para los tres pares.
- Implementación de Kalman 2 aproximado que estima media y log-varianza.
- Bitácora de operaciones, Johansen móvil y calibración walk-forward con selección en entrenamiento.
- Comparación de rebalanceo diario frente a banda del 2%: pequeñas mejoras de capital final en los tres pares, sin alterar las conclusiones de rentabilidad.
- 36 pruebas automatizadas **reportadas** como aprobadas; deben correrse nuevamente antes de entregar.

## Resultados y limitaciones
| Par | Sharpe OOS observado |
|---|---:|
| NWS–NWSA | -2.390 |
| GOOG–GOOGL | -4.058 |
| TLT–VGLT | -3.559 |

Las pruebas de cointegración y su estabilidad temporal no respaldan afirmaciones uniformes para los tres pares. El rendimiento fuera de muestra fue desfavorable aun al aplicar controles de costos y calibración.

## Problemas y aprendizajes
- **Reproducibilidad:** la configuración de entornos y dependencias debe verificarse en instalaciones nuevas.
- **Coherencia de resultados:** es necesario regenerar artefactos tras cambios de modelo para evitar mezclar versiones.
- **Validación estadística:** un par plausible por intuición de mercado no necesariamente supera el screening ni permanece cointegrado.
- **Costos:** una banda de no-rebalanceo puede reducir operaciones pequeñas, pero no compensa por sí sola señales deficitarias.
- **Comunicación:** distinguir claramente calibración en entrenamiento, métricas OOS y evidencia de cointegración.

## Mejoras para una siguiente iteración
1. Automatizar la generación y validación cruzada de resultados, figuras y reporte.
2. Probar sensibilidad a ventanas de estimación y regímenes sin seleccionar parámetros con el conjunto de validación.
3. Registrar cronología, responsables y decisiones durante el desarrollo, no al cierre.
4. Preparar un procedimiento de instalación desde cero y ejecución previa a la exposición.

## Registro del equipo — pendiente de evidencia
- Integrante 1 / contribución concreta / evidencia: **[completar]**.
- Integrante 2 / contribución concreta / evidencia: **[completar]**.
- Integrante 3 / contribución concreta / evidencia: **[completar]**.
- Fechas reales de hitos y bloqueos: **[completar]**.
- Qué salió según el plan y qué se retrasó: **[completar con cronología real]**.

> Este texto resume resultados técnicos conocidos, pero no certifica autorías individuales ni cronología de sprints.
