"""Pruebas estructurales para el modo exposición, sin ejecutar Streamlit."""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'dashboard' / 'app.py'

def test_dashboard_compila():
    ast.parse(APP.read_text(encoding='utf-8'))

def test_vistas_originales_conservadas():
    data = APP.read_text(encoding='utf-8')
    for part in ('Bitácora por operación', 'Walk-forward · Original vs. calibrada',
                 'Primer eigenvector de Johansen móvil', 'Registro diario (auditoría)'):
        assert part in data

def test_presentacion_lee_artefactos():
    data=APP.read_text(encoding='utf-8')
    assert "mode == 'Exposición'" in data
    assert "'1 · Objetivo y selección'" in data
    assert "'4 · Conclusiones'" in data
    assert "walkforward_oos_comparison.csv" in data
