Aquí se guardan los CSV generados por `python main.py` y por los scripts auxiliares (`generar_bitacoras.py`, `calibrar_walkforward.py`, `comparar_rebalanceo.py`).

Los `*_backtest.csv` están en `.gitignore` por ser pesados y regenerables, pero se versionaron a propósito porque el dashboard desplegado en Streamlit Cloud los lee directamente y no corre el pipeline. Si se modifica el modelo, regenerar todos los CSV con la secuencia del README antes de volver a subirlos, para no mezclar resultados de versiones distintas.
